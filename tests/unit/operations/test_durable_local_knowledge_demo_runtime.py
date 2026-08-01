import sqlite3
from unittest.mock import patch

import pytest

from app.operations.durable_local_knowledge_demo_runtime import (
    EXPECTED_LIST,
    seed_durable_local_knowledge,
    verify_durable_local_knowledge,
)


def test_seed_and_verify_close_reconstruct_and_make_zero_real_boundary_calls(
    tmp_path,
) -> None:
    database = tmp_path / "durable.sqlite3"
    with (
        patch("app.models.ollama_client.OllamaClient.chat") as chat,
        patch("app.models.ollama_readiness_probe.OllamaReadinessProbe.check") as ready,
        patch("requests.get") as network_get,
        patch("requests.post") as network_post,
    ):
        seed = seed_durable_local_knowledge(database)
        verify = verify_durable_local_knowledge(database)
    assert seed.list_items == verify.list_items == EXPECTED_LIST
    assert not seed.workspace_isolated
    assert not seed.denied_read
    assert not seed.denied_mutation
    assert verify.provenance.source_type == "user_asserted"
    assert verify.provenance.source_reference == "actor:wife"
    assert verify.workspace_isolated and verify.denied_read and verify.denied_mutation
    chat.assert_not_called()
    ready.assert_not_called()
    network_get.assert_not_called()
    network_post.assert_not_called()


def test_verify_report_requires_observed_workspace_isolation(tmp_path) -> None:
    database = tmp_path / "durable.sqlite3"
    seed_durable_local_knowledge(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO list_items "
            "(workspace_id, list_id, normalized_item, display_item, position) "
            "VALUES (?, ?, ?, ?, ?)",
            ("family-away", "shopping", "leak", "leak", 0),
        )
    with pytest.raises(RuntimeError, match="verification was incomplete"):
        verify_durable_local_knowledge(database)
