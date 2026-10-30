import pytest

from app.core.ids import chunk_point_id, make_chunk_id
from app.schemas.source import SourceRecord, SourceType, TextSegment
from app.services.chunking import ChunkingService
from app.services.embedding import EmbeddingService


def record(segments, **kw):
    return SourceRecord(
        source_id="s", source_type=SourceType.CONVERSATION, original_record_id="C1", title="T",
        content="\n\n".join(s.text for s in segments), source_reference="conversations/c.json#C1",
        authority_level=0.5, status="open", author="ann", segments=segments, **kw)


def test_messages_are_not_split_and_overlap_carries_context():
    segs = [TextSegment(text=f"ann: message number {i} " + "x" * 40, label=f"m{i}", speaker="ann") for i in range(6)]
    chunks = ChunkingService(chunk_size=150, chunk_overlap=70).chunk_record(record(segs))
    assert len(chunks) > 1
    for c in chunks:                                   # every chunk is made of whole messages
        for part in c.text.split("\n\n"):
            assert part in {s.text for s in segs}
    assert set(chunks[0].segment_labels) & set(chunks[1].segment_labels)   # overlap


def test_long_segment_is_split_with_speaker_prefix_and_bounded_size():
    seg = TextSegment(text="bob: " + "word " * 200, speaker="bob")
    chunks = ChunkingService(chunk_size=200, chunk_overlap=30).chunk_record(record([seg]))
    assert len(chunks) > 3 and all(len(c.text) <= 200 and c.text.startswith("bob: ") for c in chunks)


def test_no_empty_chunks_and_metadata_preserved():
    chunks = ChunkingService().chunk_record(record([TextSegment(text="ann: hi", label="m1", speaker="ann")]))
    assert len(chunks) == 1
    p = chunks[0].to_payload()
    assert p["source_id"] == "s" and p["source_type"] == "conversation" and p["document_id"] == "conversation:C1"
    assert p["original_record_id"] == "C1" and p["chunk_index"] == 0 and p["text"] == "ann: hi"
    assert p["source_reference"] == "conversations/c.json#C1" and p["authority_level"] == 0.5
    assert p["speakers"] == ["ann"] and p["segment_labels"] == ["m1"] and p["status"] == "open"


def test_chunk_ids_are_stable_and_unique():
    segs = [TextSegment(text="a " * 60) for _ in range(5)]
    a = ChunkingService(150, 20).chunk_record(record(segs))
    b = ChunkingService(150, 20).chunk_record(record(segs))
    assert [c.chunk_id for c in a] == [c.chunk_id for c in b] == [make_chunk_id("conversation:C1", i) for i in range(len(a))]
    assert len({c.point_id for c in a}) == len(a)
    assert a[0].point_id == chunk_point_id("conversation:C1#c0000")


def test_invalid_chunk_settings():
    with pytest.raises(ValueError):
        ChunkingService(chunk_size=100, chunk_overlap=80)


class FakeModel:
    loads = 0
    def __init__(self, name):
        FakeModel.loads += 1
    def get_sentence_embedding_dimension(self):
        return 8
    def encode(self, texts, **kw):
        return [[0.1] * 8 for _ in texts]


def test_embedding_dimension_lazy_load_and_batching():
    svc = EmbeddingService("fake", model_factory=FakeModel)
    assert FakeModel.loads == 0                        # not loaded at construction/import
    assert svc.dimension == 8
    vecs = svc.embed_documents(["a", "b", "c"])
    assert len(vecs) == 3 and all(len(v) == 8 for v in vecs)
    assert svc.embed_documents([]) == [] and FakeModel.loads == 1   # model reused
