import os
import sqlite3
import tempfile
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qa_platform.orchestrator import OrchestratorAgent
from qa_platform.agent_runtime import build_agent_runtime_configs
from qa_platform.models import RunControlConfig
from qa_platform.sample_scenarios import DEFAULT_TITLE, load_sample_scenario
from qa_platform.storage import save_run


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
        self.assertGreaterEqual(len(result.stage_traces), 4)
        self.assertEqual(result.stage_traces[0].agent_name, "Requirements Analyst")
        self.assertEqual(result.stage_traces[-1].agent_name, "Orchestrator Agent")
        self.assertTrue(all(trace.reasoning_trace for trace in result.stage_traces))
        self.assertTrue(
            all(trace.reasoning_source == "structured_trace" for trace in result.stage_traces)
        )
        self.assertTrue(
            any("backtrack" in trace.status for trace in result.stage_traces if trace.agent_name == "Orchestrator Agent")
        )
        self.assertEqual(result.run_controls.max_rounds, 2)
        self.assertEqual(result.run_controls.max_feedback_messages, 0)
        self.assertEqual(result.run_controls.max_feedback_per_agent_pair, 0)

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
            "LLM-backed (preview)",
            "HF cheapest/free credits",
            "Qwen 3 32B",
            "Extract strict requirement objects.",
            "LLM-backed (preview)",
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
        self.assertEqual(configs[1].execution_mode, "LLM-backed (preview)")
        self.assertEqual(configs[1].provider_strategy, "HF cheapest/free credits")
        self.assertEqual(configs[1].model_family, "Qwen 3 32B")
        self.assertEqual(configs[1].model_id, "Qwen/Qwen3-32B:cheapest")
        self.assertIn("strict requirement objects", configs[1].directives)
        self.assertEqual(configs[0].provider_strategy, "")
        self.assertEqual(configs[0].model_family, "")
        self.assertEqual(configs[0].model_id, "")
        self.assertEqual(configs[3].provider_strategy, "")
        self.assertEqual(configs[3].model_family, "")
        self.assertEqual(configs[3].model_id, "")

    def test_run_controls_are_stored_and_reflected_in_orchestrator_trace(self) -> None:
        orchestrator = OrchestratorAgent(max_iterations=3)
        result = orchestrator.process(
            title="Feedback budget demo",
            requirements_text="The user must be able to sign in with email and password.",
            run_controls=RunControlConfig(
                max_rounds=3,
                max_feedback_messages=6,
                max_feedback_per_agent_pair=2,
            ),
        )

        self.assertEqual(result.run_controls.max_rounds, 3)
        self.assertEqual(result.run_controls.max_feedback_messages, 6)
        self.assertEqual(result.run_controls.max_feedback_per_agent_pair, 2)
        orchestrator_trace = result.stage_traces[-1]
        self.assertTrue(any("Maximum feedback messages: 6" in line for line in orchestrator_trace.input_summary))
        self.assertTrue(
            any(
                "remaining feedback budget" in line.lower() or "targeted backtracking" in line.lower()
                for line in orchestrator_trace.reasoning_trace
            )
        )

    def test_requirements_trace_shows_targeted_backtracking_feedback(self) -> None:
        orchestrator = OrchestratorAgent(max_iterations=2)
        result = orchestrator.process(
            title="Backtracking feedback demo",
            requirements_text=(
                "The user must be able to sign in with email and password.\n"
                "An administrator shall be able to view an overview of registered users.\n"
                "The user shall be able to register a new account through a form."
            ),
        )

        second_requirements_trace = next(
            trace
            for trace in result.stage_traces
            if trace.agent_name == "Requirements Analyst" and trace.iteration == 2
        )
        self.assertTrue(
            any("Incoming feedback messages:" in line for line in second_requirements_trace.input_summary)
        )
        self.assertTrue(
            any("REQ-001 needs clearer acceptance criteria" in line for line in second_requirements_trace.input_summary)
        )
        self.assertTrue(
            any("upstream feedback was applied" in line for line in second_requirements_trace.reasoning_trace)
        )

    def test_save_run_persists_pipeline_result_in_sqlite(self) -> None:
        orchestrator = OrchestratorAgent(max_iterations=1)
        result = orchestrator.process(
            title="Persistence demo",
            requirements_text="The user must be able to sign in with email and password.",
        )
        payload = result.to_dict()

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "qa_runs_test.sqlite3"
            log_dir = Path(tmpdir) / "run_logs"
            previous = os.environ.get("QA_RUNS_DB_PATH")
            previous_log_dir = os.environ.get("QA_RUNS_LOG_DIR")
            os.environ["QA_RUNS_DB_PATH"] = str(db_path)
            os.environ["QA_RUNS_LOG_DIR"] = str(log_dir)
            try:
                saved_run = save_run(payload)
            finally:
                if previous is None:
                    os.environ.pop("QA_RUNS_DB_PATH", None)
                else:
                    os.environ["QA_RUNS_DB_PATH"] = previous
                if previous_log_dir is None:
                    os.environ.pop("QA_RUNS_LOG_DIR", None)
                else:
                    os.environ["QA_RUNS_LOG_DIR"] = previous_log_dir

            self.assertEqual(saved_run.run_id, 1)
            self.assertTrue(db_path.exists())
            self.assertTrue(Path(saved_run.log_path).exists())
            log_text = Path(saved_run.log_path).read_text(encoding="utf-8")
            self.assertIn("Backtracking cycle", log_text)
            self.assertIn("How this agent works", log_text)
            self.assertIn("Execution:", log_text)

            connection = sqlite3.connect(db_path)
            try:
                row = connection.execute(
                    "SELECT title, requirement_count, design_count, approved FROM qa_runs WHERE id = 1"
                ).fetchone()
            finally:
                connection.close()

            self.assertEqual(row, ("Persistence demo", 1, 1, 1))


if __name__ == "__main__":
    unittest.main()
