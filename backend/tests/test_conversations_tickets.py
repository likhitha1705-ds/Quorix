import pytest

from app.ingestion.base import RecordValidationError
from app.ingestion.conversations import ConversationAdapter
from app.ingestion.tickets import TicketAdapter
from tests.conftest import write_json

CONV = {
    "conversation_id": "C-1", "title": "Redis TTL", "channel": "#eng",
    "participants": ["ann"], "metadata": {"decision": True},
    "messages": [
        {"message_id": "a", "speaker": "bob", "content": "second", "timestamp": "2026-01-01T10:05:00Z"},
        {"speaker": "ann", "content": "first   message", "timestamp": "2026-01-01T10:00:00Z"},
    ],
}
TICKET = {
    "ticket_id": "T-1", "title": "Bug", "description": "It breaks.", "status": "Closed",
    "priority": "high", "reporter": "ann", "assignee": "bob",
    "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-03T00:00:00Z",
    "resolution": "Fixed it.", "labels": ["bug"],
    "comments": [{"author": "bob", "timestamp": "2026-01-02T00:00:00Z", "content": "Looking."}],
}


def test_conversation_normalization(data_dir):
    p = data_dir / "conversations" / "c.json"
    write_json(p, CONV)
    [rec] = ConversationAdapter(data_dir).parse(p)
    assert rec.original_record_id == "C-1" and rec.author == "ann"          # earliest speaker
    assert [s.speaker for s in rec.segments] == ["ann", "bob"]               # sorted by time
    assert rec.segments[0].text == "ann [2026-01-01 10:00 UTC]: first message"
    assert rec.metadata["participants"] == ["ann", "bob"] and rec.metadata["message_count"] == 2
    assert rec.segments[0].label == "m1" and rec.segments[1].label == "a"    # id preserved / generated
    assert rec.authority_level == 0.7 and rec.source_reference == "conversations/c.json#C-1"
    assert rec.created_at.hour == 10 and rec.updated_at.minute == 5


def test_conversation_validation_errors(data_dir):
    p = data_dir / "conversations" / "bad.json"
    for bad in ({**CONV, "messages": []},
                {**CONV, "messages": [{"speaker": "a", "content": " ", "timestamp": "2026-01-01T00:00:00Z"}]},
                {**CONV, "messages": [CONV["messages"][0], CONV["messages"][0]]}):
        write_json(p, bad)
        with pytest.raises(RecordValidationError):
            ConversationAdapter(data_dir).parse(p)


def test_ticket_normalization_preserves_fields(data_dir):
    p = data_dir / "tickets" / "t.json"
    write_json(p, TICKET)
    [rec] = TicketAdapter(data_dir).parse(p)
    assert rec.status == "closed" and rec.authority_level == 0.7 and rec.author == "ann"
    assert rec.metadata["priority"] == "high" and rec.metadata["assignee"] == "bob"
    assert rec.metadata["labels"] == ["bug"] and rec.metadata["resolution"] == "Fixed it."
    assert [s.label for s in rec.segments] == ["description", "comment-1", "resolution"]
    assert "Status: closed" in rec.segments[0].text


def test_ticket_invalid(data_dir):
    p = data_dir / "tickets" / "bad.json"
    write_json(p, {**TICKET, "updated_at": "2025-01-01T00:00:00Z"})
    with pytest.raises(RecordValidationError):
        TicketAdapter(data_dir).parse(p)
    p.write_text("{not json")
    with pytest.raises(RecordValidationError):
        TicketAdapter(data_dir).parse(p)
