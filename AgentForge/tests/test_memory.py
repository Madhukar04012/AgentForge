"""Tests for memory components."""

from __future__ import annotations

import pytest

from agentforge.memory.conversation import ConversationMemory
from agentforge.memory.vector import InMemoryVectorStore
from agentforge.providers.base import Message


def test_conversation_memory_bounded() -> None:
    m = ConversationMemory(max_messages=2)
    m.add(Message(role="user", content="a"))
    m.add(Message(role="assistant", content="b"))
    m.add(Message(role="user", content="c"))
    assert [x.content for x in m.messages()] == ["b", "c"]


def test_conversation_memory_rejects_nonpositive() -> None:
    with pytest.raises(ValueError):
        ConversationMemory(max_messages=0)


def test_vector_store_search_ranks_closer_higher() -> None:
    vs = InMemoryVectorStore()
    vs.add("1", "the quick brown fox")
    vs.add("2", "completely unrelated content about databases")
    vs.add("3", "a quick fox jumps")
    results = vs.search("quick fox", k=3)
    ids = [doc_id for doc_id, _ in results]
    assert "3" in ids and "1" in ids
    assert "2" not in ids[:2]


def test_vector_store_zero_query_handled() -> None:
    vs = InMemoryVectorStore()
    vs.add("1", "hello world")
    assert vs.search("!!!", k=1) == [("1", 0.0)]


def test_vector_store_delete() -> None:
    vs = InMemoryVectorStore()
    vs.add("1", "alpha")
    vs.delete("1")
    assert len(vs) == 0