"""Synthetic service evidence: two gates, one operation and no authority."""

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event

import pytest

from app.cognition.intent_preparation import service as module
from app.cognition.intent_preparation.contracts import PreparationProviderUnavailable
from app.cognition.intent_preparation.service import (
    IntentPreparationService,
    PreparationResult,
    PreparationState,
)


class Provider:
    def __init__(self, output=None, error=None):
        self.output = output
        self.error = error
        self.calls = []

    def prepare(self, text):
        self.calls.append(text)
        if self.error:
            raise self.error
        return self.output


def output(intent="CAPTURE_KNOWLEDGE", **fields):
    return json.dumps({"outcome": "supported", "intent": intent, "fields": fields})


def run(provider, text):
    return asyncio.run(IntentPreparationService(provider).prepare(text)).to_wire()


@pytest.mark.parametrize(
    "text",
    [
        None,
        "",
        " ",
        "x" * 8193,
        "\ud800",
        "Recuerda que cafe",
        "Que sabes de esto",
        "Agrega pan a mis pendientes",
        "No conserves cafe",
        "Nunca conserves cafe",
        "Evita guardar cafe",
        '"Conserva cafe"',
        "Por ejemplo: Conserva cafe",
        "Conserva cafe si X",
        "Conserva cafe y agrega pan",
        "knowledge bad",
        "list bad",
        "¿la lista Compras y la lista Hogar?",
    ],
    ids=lambda value: type(value).__name__,
)
def test_protected_or_recognized_never_invokes_provider(text):
    provider = Provider(error=AssertionError("must not be invoked"))
    assert run(provider, text) == {"state": "unsupported", "candidate": None}
    assert provider.calls == []


@pytest.mark.parametrize(
    "text,intent,fields",
    [
        ("Conserva cafe", "CAPTURE_KNOWLEDGE", {"value": "cafe"}),
        ("Busca Tema Ágil", "RECALL_KNOWLEDGE", {"key": "Tema Ágil"}),
        (
            "Incorpora pan a la lista Compras",
            "ADD_FOLLOW_UP",
            {"item": "pan", "list_id": "Compras"},
        ),
        ("Consulta la lista Compras", "READ_FOLLOW_UP", {"list_id": "Compras"}),
        ("¿la lista Compras?", "READ_FOLLOW_UP", {"list_id": "Compras"}),
        ("Conserva cafe", "CAPTURE_KNOWLEDGE", {}),
        ("Incorpora pan", "ADD_FOLLOW_UP", {"item": "pan"}),
        (
            "Conserva cafe\u0301  molido",
            "CAPTURE_KNOWLEDGE",
            {"value": "cafe\u0301  molido"},
        ),
    ],
    ids=lambda value: type(value).__name__,
)
def test_exact_input_four_families_and_partial_candidates(text, intent, fields):
    provider = Provider(output(intent, **fields))
    assert run(provider, text) == {
        "state": "candidate_accepted",
        "candidate": {
            "intent": intent,
            "fields": fields,
            "provenance": "local_model_assisted",
        },
    }
    assert provider.calls == [text]


@pytest.mark.parametrize(
    "text,data",
    [
        ("Conserva cafe", output(value="inventado")),
        ("Conserva cafe", output(value="Cafe")),
        ("Conserva cafe\u0301", output(value="café")),
        ("Consulta mis pendientes", output("READ_FOLLOW_UP", list_id="pendientes")),
        ("Consulta esa lista", output("READ_FOLLOW_UP", list_id="lista")),
        ("Consulta la lista", output("READ_FOLLOW_UP", list_id="lista")),
        (
            "Incorpora pan a la lista Compras",
            output("ADD_FOLLOW_UP", item="Compras", list_id="Compras"),
        ),
        (
            "Incorpora pan a la lista dos palabras",
            output("ADD_FOLLOW_UP", item="pan", list_id="dos palabras"),
        ),
        (
            "Incorpora pan | leche a la lista Compras",
            output("ADD_FOLLOW_UP", item="pan | leche", list_id="Compras"),
        ),
        (
            'La instruccion "consulta la lista Compras" es ejemplo',
            output("READ_FOLLOW_UP", list_id="Compras"),
        ),
    ],
    ids=lambda value: type(value).__name__,
)
def test_grounding_and_destination_rejections(text, data):
    provider = Provider(data)
    assert run(provider, text) == {"state": "provider_failure", "candidate": None}
    assert provider.calls == [text]


@pytest.mark.parametrize(
    "data",
    [
        "[]",
        "{}",
        "null",
        "prose {}",
        "{} {}",
        "```json\n{}\n```",
        '{"outcome":"unsupported","intent":null,"fields":{},"command":"x"}',
        '{"outcome":"unsupported","outcome":"supported","intent":null,"fields":{}}',
        '{"outcome":"supported","intent":"CAPTURE_KNOWLEDGE",'
        '"fields":{"value":"cafe","value":"cafe"}}',
        output("FIFTH", value="cafe"),
        output(value=3),
        output(value=["cafe"]),
        output(value={"nested": "cafe"}),
        output(value="cafe", proof="x"),
        output(value="x" * 8193),
        output(value="\ud800"),
        "x" * 32769,
    ],
    ids=lambda value: type(value).__name__,
)
def test_closed_candidate_failures_are_sanitized_and_never_retried(data):
    provider = Provider(data)
    assert run(provider, "Conserva cafe") == {
        "state": "provider_failure",
        "candidate": None,
    }
    assert len(provider.calls) == 1


def test_closed_unsupported_and_absent_provider_are_distinct():
    assert run(
        Provider('{"outcome":"unsupported","intent":null,"fields":{}}'), "Hola"
    ) == {"state": "unsupported", "candidate": None}
    assert run(Provider(error=PreparationProviderUnavailable("secret")), "Hola") == {
        "state": "provider_unavailable",
        "candidate": None,
    }
    assert run(Provider(error=RuntimeError("secret prompt")), "Hola") == {
        "state": "provider_failure",
        "candidate": None,
    }


@pytest.mark.parametrize(
    "cancel", [False, True], ids=lambda value: type(value).__name__
)
def test_busy_timeout_and_cancellation_keep_admission_until_worker_finishes(
    monkeypatch, cancel
):
    entered, release = Event(), Event()
    provider = Provider()

    def slow(text):
        provider.calls.append(text)
        entered.set()
        release.wait(2)
        return output(value="cafe")

    provider.prepare = slow
    service = IntentPreparationService(provider)
    monkeypatch.setattr(module, "_OPERATION_SECONDS", 0.02)

    async def exercise():
        first = asyncio.create_task(service.prepare("Conserva cafe"))
        try:
            while not entered.is_set():
                await asyncio.sleep(0)
            if cancel:
                first.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await first
            else:
                assert (await first).state is PreparationState.PROVIDER_FAILURE
            assert (await service.prepare("Conserva cafe")).state is (
                PreparationState.PROVIDER_FAILURE
            )
            assert provider.calls == ["Conserva cafe"]
        finally:
            release.set()
            for _ in range(1000):
                if service._slot.acquire(blocking=False):
                    service._slot.release()
                    break
                await asyncio.sleep(0.001)
            else:
                pytest.fail("admission was not released")

    asyncio.run(exercise())


def test_service_has_only_specialized_provider_and_admission_dependencies():
    service = IntentPreparationService(Provider())
    assert set(vars(service)) == {"_provider", "_slot"}
    assert PreparationResult(PreparationState.UNSUPPORTED).to_wire() == {
        "state": "unsupported",
        "candidate": None,
    }
    with pytest.raises(ValueError):
        PreparationResult(PreparationState.CANDIDATE_ACCEPTED)


@pytest.mark.parametrize("cancel", [False, True], ids=["timeout", "cancel"])
def test_queued_attempt_never_launches_provider_after_finalization(monkeypatch, cancel):
    provider = Provider(output(value="cafe"))
    service = IntentPreparationService(provider)
    monkeypatch.setattr(module, "_OPERATION_SECONDS", 30.0 if cancel else 0.01)

    async def exercise():
        queued, release, finished = asyncio.Event(), asyncio.Event(), asyncio.Event()

        async def queued_thread(function, *args, **kwargs):
            queued.set()
            await release.wait()
            try:
                return function(*args, **kwargs)
            finally:
                finished.set()

        monkeypatch.setattr(module.asyncio, "to_thread", queued_thread)
        request = asyncio.create_task(service.prepare("Conserva cafe"))
        try:
            await asyncio.wait_for(queued.wait(), timeout=1)
            if cancel:
                request.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await request
            else:
                assert (await request).to_wire() == {
                    "state": "provider_failure",
                    "candidate": None,
                }
            assert provider.calls == []
            # Deliver the queued callable only AFTER the terminal outcome.
            release.set()
            await asyncio.wait_for(finished.wait(), timeout=1)
            assert provider.calls == []
        finally:
            release.set()
            if not request.done():
                request.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await request

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "worker_time,expected_calls", [(129.0, 1), (130.0, 0), (131.0, 0)]
)
def test_one_absolute_deadline_includes_queue_wait(
    monkeypatch, worker_time, expected_calls
):
    clock = [100.0]
    monkeypatch.setattr(module, "monotonic", lambda: clock[0])
    monkeypatch.setattr(module, "_OPERATION_SECONDS", 30.0)
    original_assess = module.assess_eligibility

    def inspect(text):
        clock[0] = 105.0
        return original_assess(text)

    monkeypatch.setattr(module, "assess_eligibility", inspect)
    provider = Provider(output(value="cafe"))
    service = IntentPreparationService(provider)

    async def exercise():
        queued, release = asyncio.Event(), asyncio.Event()
        real_wait_for = asyncio.wait_for
        real_wait = asyncio.wait
        budgets = []

        async def wait(awaitables, timeout):
            budgets.append(timeout)
            return await real_wait(awaitables, timeout=timeout)

        async def queued_thread(function, *args, **kwargs):
            queued.set()
            await release.wait()
            return function(*args, **kwargs)

        monkeypatch.setattr(module.asyncio, "wait", wait)
        monkeypatch.setattr(module.asyncio, "to_thread", queued_thread)
        request = asyncio.create_task(service.prepare("Conserva cafe"))
        try:
            await real_wait_for(queued.wait(), timeout=1)
            clock[0] = worker_time
            release.set()
            result = await real_wait_for(request, timeout=1)
            assert budgets == [25.0]
            if expected_calls:
                assert result.to_wire() == {
                    "state": "candidate_accepted",
                    "candidate": {
                        "intent": "CAPTURE_KNOWLEDGE",
                        "fields": {"value": "cafe"},
                        "provenance": "local_model_assisted",
                    },
                }
            else:
                assert result.to_wire() == {
                    "state": "provider_failure",
                    "candidate": None,
                }
            assert provider.calls == ["Conserva cafe"] * expected_calls
        finally:
            release.set()
            if not request.done():
                request.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await request

    asyncio.run(exercise())


@pytest.mark.parametrize("cancel", [False, True], ids=["timeout", "cancel"])
def test_actual_occupied_executor_cannot_launch_a_finalized_attempt(
    monkeypatch, cancel
):
    provider = Provider(output(value="cafe"))
    service = IntentPreparationService(provider)
    monkeypatch.setattr(module, "_OPERATION_SECONDS", 30.0 if cancel else 0.01)

    async def exercise():
        loop = asyncio.get_running_loop()
        occupied, queued = asyncio.Event(), asyncio.Event()
        release = Event()

        class Executor(ThreadPoolExecutor):
            def __init__(self):
                super().__init__(max_workers=1)
                self.submissions = 0

            def submit(self, *args, **kwargs):
                future = super().submit(*args, **kwargs)
                self.submissions += 1
                if self.submissions == 2:
                    queued.set()
                return future

        executor = Executor()
        loop.set_default_executor(executor)

        def occupy():
            loop.call_soon_threadsafe(occupied.set)
            release.wait()

        blocker = loop.run_in_executor(None, occupy)
        request = None
        try:
            await asyncio.wait_for(occupied.wait(), timeout=1)
            request = asyncio.create_task(service.prepare("Conserva cafe"))
            await asyncio.wait_for(queued.wait(), timeout=1)
            if cancel:
                request.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await request
            else:
                assert (await request).state is PreparationState.PROVIDER_FAILURE
            assert provider.calls == []
            # Capacity remains held while the invalidated work is still queued.
            assert (await service.prepare("Conserva cafe")).state is (
                PreparationState.PROVIDER_FAILURE
            )
            assert executor.submissions == 2
            release.set()
            await asyncio.wait_for(blocker, timeout=1)
            # This FIFO sentinel runs only after the invalidated callable.
            await asyncio.wait_for(loop.run_in_executor(None, lambda: None), timeout=1)
            assert provider.calls == []
            await asyncio.sleep(0)
            assert service._slot.acquire(blocking=False)
            service._slot.release()
        finally:
            release.set()
            if request is not None and not request.done():
                request.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await request
            await asyncio.wait_for(blocker, timeout=1)

    asyncio.run(exercise())


def test_terminal_finalization_wins_before_worker_start_permission(monkeypatch):
    monkeypatch.setattr(module, "monotonic", lambda: 1.0)
    attempt = module._Attempt(30.0)
    provider = Provider(output(value="cafe"))
    barrier = Barrier(2)

    def worker():
        barrier.wait(timeout=2)
        if attempt.claim_start():
            provider.prepare("Conserva cafe")

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(worker)
        attempt.finalize()
        barrier.wait(timeout=2)
        future.result(timeout=2)
    assert provider.calls == []
    assert not attempt.claim_start()
    assert not attempt.finish()


def test_admitted_worker_wins_before_finalization_and_cannot_start_twice(monkeypatch):
    monkeypatch.setattr(module, "monotonic", lambda: 1.0)
    attempt = module._Attempt(30.0)
    entered, release = Event(), Event()
    calls = []

    def worker():
        assert attempt.claim_start()
        calls.append("Conserva cafe")
        entered.set()
        assert release.wait(2)
        return output(value="cafe")

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(worker)
        try:
            assert entered.wait(2)
            attempt.finalize()
            assert not attempt.claim_start()
            assert not attempt.finish()
            assert calls == ["Conserva cafe"]
        finally:
            release.set()
        assert future.result(timeout=2) == output(value="cafe")
    assert calls == ["Conserva cafe"]


def test_late_task_exception_is_retrieved_and_capacity_is_released(monkeypatch):
    service = IntentPreparationService(Provider())

    async def exercise():
        queued, release, finished = asyncio.Event(), asyncio.Event(), asyncio.Event()
        errors = []
        asyncio.get_running_loop().set_exception_handler(
            lambda loop, context: errors.append(context)
        )

        async def failing_thread(function, *args, **kwargs):
            queued.set()
            await release.wait()
            try:
                raise RuntimeError("synthetic worker failure")
            finally:
                finished.set()

        monkeypatch.setattr(module.asyncio, "to_thread", failing_thread)
        request = asyncio.create_task(service.prepare("Conserva cafe"))
        try:
            await asyncio.wait_for(queued.wait(), timeout=1)
            request.cancel()
            with pytest.raises(asyncio.CancelledError):
                await request
        finally:
            release.set()
            await asyncio.wait_for(finished.wait(), timeout=1)
        # Drain task-completion callbacks, not a wall-clock delay.
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        assert service._slot.acquire(blocking=False)
        service._slot.release()
        assert errors == []
        assert service._provider.calls == []

    asyncio.run(exercise())


def test_result_after_absolute_deadline_is_inert_even_before_timer_dispatch(
    monkeypatch,
):
    clock = [100.0]
    monkeypatch.setattr(module, "monotonic", lambda: clock[0])
    monkeypatch.setattr(module, "_OPERATION_SECONDS", 30.0)
    provider = Provider()

    def prepare(text):
        provider.calls.append(text)
        # Start was valid, but completion loses to the same absolute deadline.
        clock[0] = 130.0
        return output(value="cafe")

    provider.prepare = prepare
    assert run(provider, "Conserva cafe") == {
        "state": "provider_failure",
        "candidate": None,
    }
    assert provider.calls == ["Conserva cafe"]
