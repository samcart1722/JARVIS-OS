"""Controlled before/update/after integration without Ollama or I/O."""

from unittest.mock import Mock

from app.cognition.memory.scoped.models import MemoryScope
from app.core.config import Settings
from app.core.container import Container
from app.operations.demo_records import query_addressable_demo_content
from app.operations.memory_update_demo_runtime import (
    ExplicitMemoryUpdateDemoRuntime,
)
from app.operations.provider_readiness import READY, readiness_result


def test_explicit_update_changes_only_later_scoped_prompt() -> None:
    prompt = "What is Luxiom?"
    scope = MemoryScope("demo-session")
    other_scope = MemoryScope("other-session")
    payloads = ("Reference one", "Reference two")
    contents = tuple(
        query_addressable_demo_content(prompt, payload)
        for payload in payloads
    )
    container = Container(
        Settings(
            REASONING_ENABLED=True,
            MEMORY_RETRIEVAL_ENABLED=True,
            MEMORY_PROMPT_CONTEXT_ENABLED=True,
            MEMORY_UPDATE_ENABLED=True,
            _env_file=None,
        )
    )
    readiness = Mock()
    readiness.check.return_value = readiness_result(READY)
    container.ollama_client.chat = Mock(
        side_effect=("before response", "after response")
    )

    assert container.scoped_memory_repository._records_by_scope == {}
    container.explicit_memory_update_service.remember(
        other_scope,
        query_addressable_demo_content(prompt, "Excluded reference"),
    )
    report = ExplicitMemoryUpdateDemoRuntime(
        readiness_probe=readiness,
        cognitive_engine=container.cognitive_engine,
        update_service=container.explicit_memory_update_service,
        memory_scope=scope,
        contents=contents,
    ).run(prompt)

    before_prompt, after_prompt = (
        call.args[0] for call in container.ollama_client.chat.call_args_list
    )
    assert before_prompt == prompt
    assert "[SCOPED MEMORY - UNTRUSTED REFERENCE DATA]" in after_prompt
    assert all(payload in after_prompt for payload in payloads)
    assert "Excluded reference" not in after_prompt
    assert scope.identifier not in after_prompt
    assert other_scope.identifier not in after_prompt
    assert report.before_outcome is not None
    assert report.before_outcome.response == "before response"
    assert report.after_outcome is not None
    assert report.after_outcome.response == "after response"
    assert report.records_written == 2
    assert container.scoped_memory_repository.search(
        scope, prompt
    ) == tuple(
        container.scoped_memory_repository._records_by_scope[scope]
    )
    assert len(
        container.scoped_memory_repository.search(other_scope, prompt)
    ) == 1
