from app.ingestion.conversations import ConversationAdapter
from app.ingestion.pipeline import IngestionPipeline
from app.schemas.source import SourceType
from app.services.chunking import ChunkingService
from tests.conftest import REPO_DATA, write_json


class FakeMeta:
    def __init__(self):
        self.docs, self.sources, self.jobs = {}, {}, {}
    def upsert_source(self, s): self.sources[s.source_id] = {"status": "never"}
    def set_source_status(self, sid, st): self.sources[sid]["status"] = st
    def start_job(self, sid): self.jobs["j"] = {}; return "j"
    def finish_job(self, r, error_info=None): self.jobs["j"] = {"status": r.status, "failed": r.failed}
    def get_index_state(self, did): return self.docs.get(did)
    def upsert_document(self, rec, h): self.docs[rec.document_id] = {"index_fingerprint": None, "indexed_at": None, "hash": h}
    def mark_indexed(self, did, fp, n): self.docs[did].update(index_fingerprint=fp, indexed_at="now", chunks=n)


class FakeVectors:
    def __init__(self, fail_on=None):
        self.points, self.fail_on = {}, fail_on
    def delete_document(self, did):
        self.points = {k: v for k, v in self.points.items() if v["document_id"] != did}
    def upsert_chunks(self, chunks, vectors):
        if self.fail_on and any(self.fail_on in c.document_id for c in chunks):
            raise ConnectionError("qdrant down")
        for c in chunks:
            self.points[c.point_id] = c.to_payload()


class FakeEmbedder:
    model_name = "fake"
    def embed_documents(self, texts): return [[0.0] * 4 for _ in texts]


def conv(i, text="hello world"):
    return {"conversation_id": f"C-{i}", "title": f"Conv {i}", "messages": [
        {"speaker": "ann", "content": text, "timestamp": "2026-01-01T10:00:00Z"}]}


def make(data_dir, fail_on=None):
    m, v = FakeMeta(), FakeVectors(fail_on)
    return m, v, IngestionPipeline(m, v, FakeEmbedder(), ChunkingService(500, 80)), ConversationAdapter(data_dir)


def test_reingestion_creates_no_duplicates(data_dir):
    for i in (1, 2):
        write_json(data_dir / "conversations" / f"c{i}.json", conv(i))
    m, v, pipe, ad = make(data_dir)
    r1 = pipe.run_source(ad)
    n = len(v.points)
    r2 = pipe.run_source(ad)
    assert (r1.status, r1.processed, r1.skipped) == ("succeeded", 2, 0)
    assert (r2.status, r2.processed, r2.skipped) == ("succeeded", 0, 2)
    assert len(v.points) == n == 2
    r3 = pipe.run_source(ad, force=True)                 # forced re-index still no duplicates
    assert r3.processed == 2 and len(v.points) == 2


def test_changed_record_is_reindexed_and_old_chunks_removed(data_dir):
    p = data_dir / "conversations" / "c1.json"
    write_json(p, conv(1, "word " * 400))               # many chunks
    m, v, pipe, ad = make(data_dir)
    pipe.run_source(ad)
    many = len(v.points)
    write_json(p, conv(1, "short"))
    r = pipe.run_source(ad)
    assert many > 1 and r.processed == 1 and len(v.points) == 1


def test_partial_failure_is_reported_not_hidden(data_dir):
    write_json(data_dir / "conversations" / "ok.json", conv(1))
    write_json(data_dir / "conversations" / "bad.json", {"conversation_id": "X", "title": "t", "messages": []})
    write_json(data_dir / "conversations" / "infra.json", conv(3))
    m, v, pipe, ad = make(data_dir, fail_on="C-3")
    r = pipe.run_source(ad)
    assert r.status == "partial" and r.processed == 1 and r.failed == 2 and r.total == 3
    assert {f.reference.split("#")[0] for f in r.failures} == {"conversations/bad.json", "conversations/infra.json"}
    assert m.jobs["j"]["status"] == "partial" and m.sources[ad.source_id]["status"] == "partial"
    # the record whose indexing failed must not be marked as indexed -> retried next run
    assert m.docs["conversation:C-3"]["indexed_at"] is None


def test_all_failed_is_failed(data_dir):
    write_json(data_dir / "conversations" / "bad.json", {"nope": 1})
    m, v, pipe, ad = make(data_dir)
    assert pipe.run_source(ad).status == "failed"


def test_duplicate_record_ids_flagged(data_dir):
    write_json(data_dir / "conversations" / "a.json", conv(1))
    write_json(data_dir / "conversations" / "b.json", conv(1))
    m, v, pipe, ad = make(data_dir)
    r = pipe.run_source(ad)
    assert r.processed == 1 and r.failed == 1 and "duplicate" in r.failures[0].error


def test_synthetic_dataset_loads_cleanly():
    import pytest
    if not REPO_DATA.exists():
        pytest.skip(f"Synthetic dataset {REPO_DATA} not found")
    from app.ingestion.documents import DocumentAdapter
    from app.ingestion.tickets import TicketAdapter
    counts = {}
    for a in (DocumentAdapter(REPO_DATA), ConversationAdapter(REPO_DATA), TicketAdapter(REPO_DATA)):
        res = list(a.iter_records())
        assert not [r for r in res if r.error], [r.error for r in res if r.error]
        counts[a.source_type] = sum(len(r.records) for r in res)
    assert counts == {SourceType.DOCUMENT: 10, SourceType.CONVERSATION: 15, SourceType.TICKET: 15}
