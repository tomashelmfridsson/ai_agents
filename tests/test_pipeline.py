from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qa_platform.orchestrator import OrchestratorAgent
from qa_platform.agent_runtime import build_agent_runtime_configs
from qa_platform.sample_scenarios import DEFAULT_TITLE, load_sample_scenario


class PipelineTests(unittest.TestCase):
    def test_pipeline_produces_traceable_test_designs(self) -> None:
        orchestrator = OrchestratorAgent()
        result = orchestrator.process(
            title="Login demo",
            requirements_text=(
                "Användaren måste kunna logga in med e-post och lösenord.\n"
                "Systemet ska visa ett tydligt felmeddelande vid ogiltiga uppgifter."
            ),
        )

        self.assertEqual(len(result.requirements), 2)
        self.assertEqual(len(result.test_designs), 2)
        self.assertEqual(len(result.generated_artifacts), 0)
        self.assertEqual(result.review.coverage_ratio, 1.0)
        self.assertGreaterEqual(result.iterations, 1)
        self.assertEqual(len(result.stage_traces), result.iterations * 4)
        self.assertEqual(result.stage_traces[0].agent_name, "Requirements Analyst")
        self.assertEqual(result.stage_traces[-1].agent_name, "Orchestrator Agent")
        self.assertTrue(all(trace.reasoning_trace for trace in result.stage_traces))
        self.assertTrue(
            all(trace.reasoning_source == "structured_trace" for trace in result.stage_traces)
        )

        requirement_ids = {item.requirement_id for item in result.requirements}
        design_ids = {item.requirement_id for item in result.test_designs}
        self.assertEqual(requirement_ids, design_ids)

    def test_review_flags_vague_requirements(self) -> None:
        orchestrator = OrchestratorAgent(max_iterations=1)
        result = orchestrator.process(
            title="Vague requirement demo",
            requirements_text="Systemet bör fungera bra.",
        )

        self.assertFalse(result.review.approved)
        self.assertTrue(result.review.findings)
        self.assertTrue(any("REQ-001" in finding for finding in result.review.findings))

    def test_sample_scenario_loader_uses_selected_preset(self) -> None:
        title, requirements = load_sample_scenario("Scenario 4 - support tickets", DEFAULT_TITLE, "")

        self.assertEqual(title, "Support ticket creation and status tracking")
        self.assertIn("create a support ticket", requirements)

    def test_custom_scenario_loader_clears_fields(self) -> None:
        title, requirements = load_sample_scenario(
            "Custom scenario",
            "Existing title",
            "Existing requirements",
        )

        self.assertEqual(title, "")
        self.assertEqual(requirements, "")

    def test_requirements_trace_explains_derivation_for_req_001(self) -> None:
        orchestrator = OrchestratorAgent(max_iterations=1)
        result = orchestrator.process(
            title="Login demo",
            requirements_text="The user must be able to sign in with email and password.",
        )

        reasoning = result.stage_traces[0].reasoning_trace
        self.assertTrue(any("REQ-001: raw text" in line for line in reasoning))
        self.assertTrue(any("priority -> high" in line for line in reasoning))
        self.assertTrue(any("authentication rule triggered" in line for line in reasoning))
        self.assertTrue(any("error-handling assumption was added" in line for line in reasoning))

    def test_review_trace_explains_false_decision_with_threshold_math(self) -> None:
        orchestrator = OrchestratorAgent(max_iterations=1)
        result = orchestrator.process(
            title="Preset login demo",
            requirements_text=(
                "The user must be able to sign in with email and password.\n"
                "The system shall display a clear error message when credentials are invalid.\n"
                "An administrator shall be able to view an overview of registered users.\n"
                "The user shall be able to register a new account through a form."
            ),
        )

        reasoning = result.stage_traces[2].reasoning_trace
        self.assertFalse(result.review.approved)
        self.assertTrue(any("coverage_ratio=1.0" in line for line in reasoning))
        self.assertTrue(any("Weak-oracle checks triggered for:" in line for line in reasoning))
        self.assertTrue(any("Approval threshold: findings must be <= 2" in line for line in reasoning))
        self.assertTrue(
            any("Final decision: Approved=False because coverage passed" in line for line in reasoning)
        )

    def test_agent_runtime_configs_capture_mode_model_and_directives(self) -> None:
        configs = build_agent_runtime_configs(
            "Structured baseline",
            "HF cheapest/free credits",
            "Qwen 3 32B",
            "Keep routing explicit.",
            "Model-backed (preview)",
            "HF cheapest/free credits",
            "Qwen 3 32B",
            "Extract strict requirement objects.",
            "Model-backed (preview)",
            "HF fastest",
            "DeepSeek R1",
            "Design stronger oracles.",
            "Structured baseline",
            "Ollama local (coming soon)",
            "Llama 3.3 70B Instruct",
            "Be strict during review.",
        )

        self.assertEqual(len(configs), 4)
        self.assertEqual(configs[1].agent_name, "Requirements Analyst Agent")
        self.assertEqual(configs[1].execution_mode, "Model-backed (preview)")
        self.assertEqual(configs[1].provider_strategy, "HF cheapest/free credits")
        self.assertEqual(configs[1].model_family, "Qwen 3 32B")
        self.assertEqual(configs[1].model_id, "Qwen/Qwen3-32B:cheapest")
        self.assertIn("strict requirement objects", configs[1].directives)
        self.assertEqual(configs[3].model_id, "Ollama local / Llama 3.3 70B Instruct")


if __name__ == "__main__":
    unittest.main()
