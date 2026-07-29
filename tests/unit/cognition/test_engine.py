"""Tests for CognitiveEngine specialist-selection flow."""

from unittest.mock import Mock

from app.cognition.classification.goal_classifier import GoalClassifier
from app.cognition.domain.domain import Domain
from app.cognition.engine import CognitiveEngine
from app.cognition.planning.capability_executor import CapabilityExecutor
from app.cognition.planning.execution_result import ExecutionResult
from app.cognition.planning.plan import Plan
from app.cognition.planning.plan_step import PlanStep
from app.cognition.pipeline.response_stage import ResponseStage
from app.cognition.specialists.specialist_router import SpecialistRouter


def test_process_executes_the_plan_from_the_selected_specialist() -> None:
    """The engine must forward the specialist plan to the executor."""
    classifier = Mock(spec=GoalClassifier)
    router = Mock(spec=SpecialistRouter)
    executor = Mock(spec=CapabilityExecutor)
    response_stage = Mock(spec=ResponseStage)
    specialist = Mock()
    plan = Plan(
        steps=(
            PlanStep(
                id="step-1",
                description="Prepare a monthly order",
            ),
        )
    )
    execution_result = ExecutionResult(
        success=True,
        completed_steps=("Prepare a monthly order",),
    )
    classifier.classify.return_value = Domain.UNKNOWN
    router.route.return_value = specialist
    specialist.create_plan.return_value = plan
    executor.execute.return_value = execution_result
    response_stage.process.return_value = "Plan executed successfully."

    engine = CognitiveEngine(
        goal_classifier=classifier,
        specialist_router=router,
        capability_executor=executor,
        response_stage=response_stage,
    )

    result = engine.process("Prepare a monthly order")

    assert result == "Plan executed successfully."
    context = classifier.classify.call_args.args[0]
    assert context.raw_input == "Prepare a monthly order"
    assert context.goal is not None
    assert context.goal.description == "Prepare a monthly order"
    router.route.assert_called_once_with(Domain.UNKNOWN)
    specialist.create_plan.assert_called_once_with(context.goal)
    executor.execute.assert_called_once_with(plan)
    assert executor.execute.return_value is execution_result
    response_stage.process.assert_called_once_with(execution_result)
