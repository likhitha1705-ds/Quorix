from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.schemas.source import SourceRecord, SourceType, TicketInput


def _rec(**kw):
    base = dict(source_id="s", source_type=SourceType.DOCUMENT, original_record_id="D1",
                title="t", content="c", source_reference="documents/D1.md", authority_level=0.5)
    return SourceRecord(**{**base, **kw})


def test_naive_and_offset_timestamps_become_utc():
    r = _rec(created_at=datetime(2026, 1, 1, 12), updated_at="2026-01-02T12:00:00+05:30")
    assert r.created_at.tzinfo == timezone.utc
    assert r.updated_at == datetime(2026, 1, 2, 6, 30, tzinfo=timezone.utc)
    assert r.ingestion_timestamp.tzinfo == timezone.utc


def test_updated_before_created_rejected():
    with pytest.raises(ValidationError):
        _rec(created_at="2026-02-01T00:00:00Z", updated_at="2026-01-01T00:00:00Z")


def test_authority_range_and_required_fields():
    with pytest.raises(ValidationError):
        _rec(authority_level=1.5)
    with pytest.raises(ValidationError):
        _rec(title="")


def test_document_id_is_stable_and_typed():
    assert _rec().document_id == "document:D1"


def test_ticket_status_normalized_and_time_check():
    now = datetime.now(timezone.utc)
    t = TicketInput(ticket_id="T", title="x", description="d", status="In Progress",
                    created_at=now, updated_at=now)
    assert t.status == "in_progress"
    with pytest.raises(ValidationError):
        TicketInput(ticket_id="T", title="x", description="d", status="open",
                    created_at=now, updated_at=now - timedelta(days=1))
