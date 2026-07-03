import os
import sqlite3
import tempfile
import json
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qa_platform.orchestrator import OrchestratorAgent
from qa_platform.agent_runtime import build_agent_runtime_configs
from qa_platform.agents import RequirementsAnalystAgent, ReviewAgent
from qa_platform.llm_runtime import LLMRuntimeError, call_structured_llm
import qa_platform.llm_runtime as llm_runtime_module
import qa_platform.orchestrator as orchestrator_module
from qa_platform import models as qa_models
from qa_platform.models import AgentRuntimeConfig, ReviewReport
from qa_platform.models import RunControlConfig, RunSession
from qa_platform.sample_scenarios import DEFAULT_TITLE, load_sample_scenario
from qa_platform.storage import export_run_evaluations_csv, get_export_dir, save_run, save_run_evaluation
import app as app_module
from app import process_requirements
from qa_platform.storage import get_db_path, get_log_dir


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
        self.assertGreaterEqual(len(result.test_designs), 3)
        self.assertEqual(len(result.generated_artifacts), 0)
        self.assertEqual(result.review.coverage_ratio, 1.0)
        self.assertGreaterEqual(result.iterations, 1)
        self.assertGreaterEqual(len(result.stage_traces), 5)
        self.assertEqual(result.stage_traces[0].agent_name, "Orchestrator Agent")
        self.assertEqual(result.stage_traces[1].agent_name, "Requirements Analyst")
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
        self.assertTrue(requirement_ids.issubset(design_ids))
        self.assertGreater(len(result.test_designs), len(result.requirements))

    def test_pipeline_persists_shared_working_memory_across_agents(self) -> None:
        orchestrator = OrchestratorAgent(max_iterations=1)
        result = orchestrator.process(
            title="Shared memory demo",
            requirements_text="The user must be able to sign in with email and password.",
        )

        self.assertIsNotNone(result.run_session)
        working_memory = result.run_session.working_memory
        self.assertIn("requirements", working_memory.shared)
        self.assertIn("test_designs", working_memory.shared)
        self.assertIn("review", working_memory.shared)
        self.assertTrue(any("Requirements Analyst produced" in note for note in working_memory.timeline))
        self.assertTrue(any("Test Design Agent produced" in note for note in working_memory.timeline))
        self.assertTrue(any("Review Agent recorded" in note for note in working_memory.timeline))

    def test_orchestrator_uses_registry_and_workflow_graph_defaults(self) -> None:
        orchestrator = OrchestratorAgent()

        self.assertEqual(orchestrator.workflow_graph.start_stage, "orchestrator")
        self.assertEqual(orchestrator.workflow_graph.get_node("design").agent_key, "test_design")
        self.assertEqual(orchestrator.registry.get_spec("review").stage_key, "review")
        self.assertEqual(orchestrator.requirements_analyst.name, "Requirements Analyst")

    def test_orchestrator_directives_target_review_approval(self) -> None:
        orchestrator = OrchestratorAgent()

        directives = orchestrator.registry.get_spec("orchestrator").default_directives

        self.assertIn("approved=true from the Review Agent", directives)
        self.assertIn("Review Agent returns approved=true", directives)

    def test_review_flags_vague_requirements(self) -> None:
        orchestrator = OrchestratorAgent(max_iterations=1)
        result = orchestrator.process(
            title="Vague requirement demo",
            requirements_text="Systemet bör fungera bra.",
        )

        self.assertFalse(result.review.approved)
        self.assertTrue(result.review.findings)
        self.assertTrue(any("REQ-001" in finding for finding in result.review.findings))

    def test_review_flags_thin_one_to_one_coverage_for_multi_behavior_requirement(self) -> None:
        agent = ReviewAgent()
        report = agent.review(
            requirements=[
                qa_models.RequirementItem(
                    requirement_id="REQ-001",
                    original_text="The user must be able to sign in with email and password.",
                    normalized_text="The user must be able to sign in with email and password.",
                    priority="high",
                    acceptance_criteria=[
                        "The user shall be authenticated with valid credentials.",
                        "Invalid credentials shall produce a clear error message.",
                    ],
                    assumptions=[],
                )
            ],
            test_designs=[
                qa_models.TestCaseDesign(
                    test_case_id="TC-001",
                    requirement_id="REQ-001",
                    title="Successful sign-in with valid credentials",
                    test_type="scenario",
                    preconditions=["The application is available."],
                    steps=["Open sign-in", "Enter valid credentials", "Submit form"],
                    expected_results=["The user is authenticated.", "The dashboard is shown."],
                    oracle="Authentication succeeds and the dashboard is visible.",
                    risks=[],
                )
            ],
        )

        self.assertFalse(report.approved)
        self.assertTrue(any("has only one designed test case" in finding for finding in report.findings))

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

    def test_gradio_launch_whitelists_saved_artifact_paths(self) -> None:
        allowed_paths = app_module._build_allowed_file_paths()

        self.assertIn(str(get_log_dir().resolve()), allowed_paths)
        self.assertIn(str(get_db_path().parent.resolve()), allowed_paths)
        self.assertIn(str(get_export_dir().resolve()), allowed_paths)

    def test_requirements_trace_explains_derivation_for_req_001(self) -> None:
        orchestrator = OrchestratorAgent(max_iterations=1)
        result = orchestrator.process(
            title="Login demo",
            requirements_text="The user must be able to sign in with email and password.",
        )

        reasoning = result.stage_traces[1].reasoning_trace
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

        reasoning = result.stage_traces[3].reasoning_trace
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
            "LLM-backed",
            "HF cheapest/free credits",
            "Qwen 3 32B",
            "Extract strict requirement objects.",
            "LLM-backed",
            "HF fastest",
            "DeepSeek R1",
            "Design stronger oracles.",
            "Structured baseline",
            "Ollama local",
            "Llama 3.3 70B Instruct",
            "Be strict during review.",
        )

        self.assertEqual(len(configs), 4)
        self.assertEqual(configs[1].agent_name, "Requirements Analyst Agent")
        self.assertEqual(configs[1].execution_mode, "LLM-backed")
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

    def test_default_runtime_presets_resolve_to_hf_gpt_oss_20b(self) -> None:
        configs = build_agent_runtime_configs()

        self.assertTrue(all(config.provider_strategy == "HF cheapest/free credits" for config in configs))
        self.assertTrue(all(config.timeout_seconds == 150 for config in configs))
        self.assertTrue(all(config.model_id == "openai/gpt-oss-20b:cheapest" for config in configs))

    def test_model_family_choices_include_new_hf_candidates(self) -> None:
        self.assertIn("Qwen3-30B-A3B", app_module.MODEL_FAMILY_CHOICES)
        self.assertIn("DeepSeek-V3.1", app_module.MODEL_FAMILY_CHOICES)
        self.assertIn("gpt-oss-20b", app_module.MODEL_FAMILY_CHOICES)

    def test_build_agent_runtime_configs_supports_new_hf_candidates(self) -> None:
        configs = build_agent_runtime_configs(
            "LLM-backed",
            "HF cheapest/free credits",
            "gpt-oss-20b",
            "Route clearly.",
            "LLM-backed",
            "HF cheapest/free credits",
            "Qwen3-30B-A3B",
            "Extract strict requirement objects.",
            "LLM-backed",
            "HF fastest",
            "DeepSeek-V3.1",
            "Design stronger oracles.",
            "LLM-backed",
            "HF cheapest/free credits",
            "gpt-oss-120b",
            "Review thoroughly.",
        )

        self.assertEqual(configs[0].model_id, "openai/gpt-oss-20b:cheapest")
        self.assertEqual(configs[1].model_id, "Qwen/Qwen3-30B-A3B:cheapest")
        self.assertEqual(configs[2].model_id, "deepseek-ai/DeepSeek-V3.1:fastest")

    def test_agent_runtime_configs_accept_per_agent_timeout_values(self) -> None:
        configs = build_agent_runtime_configs(
            "LLM-backed",
            "Ollama local",
            "qwen3:8b",
            "",
            "150",
            "Route clearly.",
            "LLM-backed",
            "Ollama local",
            "qwen3:8b",
            "",
            "180",
            "Extract strict requirement objects.",
            "LLM-backed",
            "Ollama local",
            "qwen3:8b",
            "",
            "90",
            "Design stronger oracles.",
            "LLM-backed",
            "Ollama local",
            "deepseek-r1:8b",
            "",
            "75",
            "Review thoroughly.",
        )

        self.assertEqual([config.timeout_seconds for config in configs], [150, 180, 90, 75])

    def test_ollama_list_is_parsed_into_model_choices(self) -> None:
        fake_output = (
            "NAME                           ID              SIZE      MODIFIED\n"
            "gemma3:4b                      a2af6cc3eb7f    3.3 GB    36 seconds ago\n"
            "deepseek-r1:8b                 6995872bfe4c    5.2 GB    3 minutes ago\n"
            "qwen3:8b                       500a1f067a9f    5.2 GB    8 minutes ago\n"
        )
        with patch.object(
            app_module.subprocess,
            "run",
            return_value=SimpleNamespace(stdout=fake_output),
        ):
            choices = app_module.get_ollama_model_choices()

        self.assertEqual(choices, ["gemma3:4b", "deepseek-r1:8b", "qwen3:8b"])

    def test_execution_mode_help_uses_plain_language(self) -> None:
        help_text = app_module.format_execution_mode_help("LLM-backed")

        self.assertIn("agent calls the selected model", help_text)
        self.assertIn("Timeouts and run limits", help_text)

    def test_build_error_report_includes_model_and_progress_context(self) -> None:
        runtime_events = [
            {
                "event_type": "stage_started",
                "agent_name": "Requirements Analyst",
                "iteration": 1,
                "stage_index": 1,
                "message": "Running Requirements Analyst.",
                "duration_ms": 0,
            }
        ]
        agent_configs = [
            AgentRuntimeConfig(
                agent_key="requirements_analyst",
                agent_name="Requirements Analyst Agent",
                execution_mode="LLM-backed",
                timeout_seconds=120,
                provider_strategy="Ollama local",
                model_family="qwen3:8b",
                model_override="",
                model_id="qwen3:8b",
                directives="",
            )
        ]

        report_html = app_module.build_error_report("Timed out.", runtime_events, agent_configs, "/tmp/live.log")

        self.assertIn("Run summary", report_html)
        self.assertIn("<details class='stage-toggle' open>", report_html)
        self.assertIn("Last active agent: Requirements Analyst", report_html)
        self.assertIn("Model for that agent: qwen3:8b", report_html)
        self.assertIn("Configured timeout for that agent: 120 seconds", report_html)
        self.assertIn("Last runtime event: stage_started", report_html)
        self.assertIn("Completed stages before the stop: 0", report_html)
        self.assertIn("Log file: /tmp/live.log", report_html)

    def test_build_runtime_timeline_shows_model_and_runtime_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "live.txt"
            log_path.write_text("line 1\nline 2\nmessage: Running Requirements Analyst.\n", encoding="utf-8")
            html_output = app_module.build_runtime_timeline(
                [
                    {
                        "iteration": 1,
                        "stage_index": 1,
                        "agent_name": "Requirements Analyst",
                        "model_id": "gemma3:4b",
                        "event_type": "stage_started",
                        "duration_ms": 0,
                        "message": "Running Requirements Analyst.",
                    }
                ],
                str(log_path),
            )

        self.assertIn("gemma3:4b", html_output)
        self.assertIn("Runtime activity", html_output)
        self.assertNotIn("Live log tail", html_output)

    def test_build_memory_panel_renders_shared_and_private_memory(self) -> None:
        html_output = app_module.build_memory_panel(
            {
                "shared": {
                    "current_stage": "design",
                    "requirements": [{"requirement_id": "REQ-001"}],
                },
                "agent_private": {
                    "requirements_analyst": {"validation_findings": ["none"]},
                },
                "timeline": [
                    "Run session started.",
                    "Requirements Analyst produced 1 requirement item(s).",
                ],
            }
        )

        self.assertIn("Working memory", html_output)
        self.assertIn("<details", html_output)
        self.assertIn("Shared memory", html_output)
        self.assertIn("memory-value", html_output)
        self.assertIn("current_stage", html_output)

    def test_build_workflow_report_surfaces_planned_test_case_details(self) -> None:
        html_output = app_module.build_workflow_report(
            {
                "title": "Demo",
                "requirements": [
                    {"requirement_id": "REQ-001", "normalized_text": "User can sign in."},
                ],
                "test_designs": [
                    {
                        "test_case_id": "TC-001",
                        "requirement_id": "REQ-001",
                        "title": "Sign in with valid credentials",
                        "test_type": "functional",
                        "steps": ["Enter valid email", "Enter valid password", "Submit form"],
                        "expected_results": ["User is authenticated", "Dashboard is shown"],
                        "oracle": "Authentication succeeds and the dashboard is visible.",
                        "risks": [],
                    }
                ],
                "iterations": 1,
                "review": {
                    "approved": True,
                    "coverage_ratio": 1.0,
                    "findings": [],
                    "improvement_actions": [],
                },
                "run_controls": {
                    "max_rounds": 2,
                    "max_feedback_messages": 0,
                    "max_feedback_per_agent_pair": 0,
                },
                "agent_configs": [],
                "stage_traces": [],
            }
        )

        self.assertIn("Planned test cases", html_output)
        self.assertIn("TC-001", html_output)
        self.assertIn("Enter valid email", html_output)
        self.assertIn("Dashboard is shown", html_output)
        self.assertIn("Authentication succeeds and the dashboard is visible.", html_output)

    def test_default_export_dir_points_to_downloads(self) -> None:
        previous_export_dir = os.environ.get("QA_EXPORT_DIR")
        os.environ.pop("QA_EXPORT_DIR", None)
        try:
            export_dir = get_export_dir()
        finally:
            if previous_export_dir is None:
                os.environ.pop("QA_EXPORT_DIR", None)
            else:
                os.environ["QA_EXPORT_DIR"] = previous_export_dir

        self.assertEqual(export_dir, Path.home() / "Downloads")

    def test_apply_global_agent_settings_updates_all_agents(self) -> None:
        updates = app_module.apply_global_agent_settings(
            "LLM-backed",
            "Ollama local",
            "DeepSeek R1",
            "",
            150,
        )

        self.assertEqual(len(updates), len(app_module.AGENT_CONFIG_SPECS) * 8 + 1)
        self.assertEqual(updates[0]["value"], "LLM-backed")
        self.assertEqual(updates[1]["value"], "Ollama local")
        self.assertEqual(updates[2]["value"], "deepseek-r1:8b")
        self.assertEqual(updates[2]["allow_custom_value"], True)
        self.assertEqual(updates[4]["value"], 150)
        self.assertIn("Applied common settings", updates[-1]["value"])

    def test_build_error_report_shows_completed_agent_results(self) -> None:
        agent_configs = [
            AgentRuntimeConfig(
                agent_key="requirements_analyst",
                agent_name="Requirements Analyst Agent",
                execution_mode="LLM-backed",
                timeout_seconds=120,
                provider_strategy="Ollama local",
                model_family="qwen3:8b",
                model_override="",
                model_id="qwen3:8b",
                directives="",
            )
        ]
        completed_traces = [
            {
                "iteration": 1,
                "stage_index": 1,
                "agent_name": "Requirements Analyst",
                "input_summary": ["Raw requirement lines: 1"],
                "output_summary": ["Extracted 1 requirement item(s).", 'REQ-001: "Login"'],
                "status": "completed",
                "reasoning_trace": ["REQ-001: raw text"],
                "reasoning_source": "structured_trace",
                "agent_explanation": "",
                "decision_explanation": "",
                "duration_ms": 1234,
            }
        ]

        report_html = app_module.build_error_report(
            "Timed out.",
            runtime_events=[],
            agent_configs=agent_configs,
            log_path="/tmp/live.log",
            completed_traces=completed_traces,
        )

        self.assertIn("Completed agent results", report_html)
        self.assertIn("Requirements Analyst", report_html)
        self.assertIn("Extracted 1 requirement item", report_html)

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

    def test_orchestrator_explains_pair_limit_stop_reason_exactly(self) -> None:
        orchestrator = OrchestratorAgent(max_iterations=10)
        stop_reason, stop_details = orchestrator._determine_review_stop_reason(
            backtrack_route={
                "from_agent": "Review Agent",
                "to_agent": "Test Design Agent",
                "feedback_messages": ["Strengthen oracle quality."],
            },
            run_controls=RunControlConfig(
                max_rounds=10,
                max_feedback_messages=12,
                max_feedback_per_agent_pair=4,
            ),
            route_round=6,
            total_feedback_messages=5,
            pair_feedback_counts={("Review Agent", "Test Design Agent"): 4},
        )

        self.assertIn("Maximum feedback messages per agent pair", stop_reason)
        self.assertIn("Review Agent -> Test Design Agent", stop_reason)
        self.assertTrue(any("Configured pair limit: 4" in item for item in stop_details))

    def test_orchestrator_explains_missing_route_stop_reason_exactly(self) -> None:
        orchestrator = OrchestratorAgent(max_iterations=10)
        stop_reason, stop_details = orchestrator._determine_review_stop_reason(
            backtrack_route=None,
            run_controls=RunControlConfig(
                max_rounds=10,
                max_feedback_messages=12,
                max_feedback_per_agent_pair=4,
            ),
            route_round=6,
            total_feedback_messages=5,
            pair_feedback_counts={},
        )

        self.assertEqual(stop_reason, "Stop pipeline because no valid backtracking route was available.")
        self.assertTrue(any("did not produce a usable routing target" in item for item in stop_details))

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
            any("needs" in line and "acceptance criteria" in line for line in second_requirements_trace.input_summary)
        )
        self.assertTrue(
            any("upstream feedback was applied" in line for line in second_requirements_trace.reasoning_trace)
        )

    def test_requirements_agent_can_run_in_live_llm_mode(self) -> None:
        configs = build_agent_runtime_configs(
            "LLM-backed",
            "HF cheapest/free credits",
            "Qwen 3 32B",
            "Route clearly.",
            "LLM-backed",
            "HF cheapest/free credits",
            "Qwen 3 32B",
            "Extract strict requirement objects.",
            "Structured baseline",
            "HF fastest",
            "DeepSeek R1",
            "Design stronger oracles.",
            "Structured baseline",
            "HF fastest",
            "DeepSeek R1",
            "Review thoroughly.",
        )
        runtime_config = configs[1]

        fake_response = (
            {
                "requirements": [
                    {
                        "original_text": "The user must be able to sign in with email and password.",
                        "normalized_text": "The user must be able to sign in with email and password",
                        "priority": "high",
                        "acceptance_criteria": [
                            "The user shall be authenticated when valid credentials are supplied.",
                            "Invalid credentials shall produce a clear error message.",
                        ],
                        "assumptions": ["Password policy is not described explicitly."],
                        "trace_notes": ["Mapped the line to one authentication requirement."],
                    }
                ],
                "run_notes": ["Used the configured LLM schema for requirement extraction."],
            },
            {
                "model_id": runtime_config.model_id,
                "provider_strategy": runtime_config.provider_strategy,
            },
        )

        with patch("qa_platform.agents.call_structured_llm", return_value=fake_response):
            agent = RequirementsAnalystAgent()
            result = agent.analyze(
                "The user must be able to sign in with email and password.",
                runtime_config=runtime_config,
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].requirement_id, "REQ-001")
        self.assertEqual(result[0].priority, "high")
        self.assertEqual(agent.last_execution["reasoning_source"], "llm_structured_output")
        self.assertTrue(agent.last_execution["llm_used"])
        self.assertTrue(any("configured LLM schema" in note for note in agent.last_execution["notes"]))

    def test_review_agent_adds_fallback_finding_when_llm_rejects_without_findings(self) -> None:
        runtime_config = AgentRuntimeConfig(
            agent_key="review",
            agent_name="Review Agent",
            execution_mode="LLM-backed",
            timeout_seconds=60,
            provider_strategy="HF cheapest/free credits",
            model_family="Qwen 3 32B",
            model_id="Qwen/Qwen3-32B:cheapest",
            directives="Review thoroughly.",
        )
        fake_response = (
            {
                "approved": False,
                "coverage_ratio": 0.0,
                "findings": [],
                "improvement_actions": [],
                "routing_focus": [],
                "evaluation_notes": ["The model could not form a stable review decision."],
            },
            {
                "model_id": runtime_config.model_id,
                "provider_strategy": runtime_config.provider_strategy,
            },
        )

        with patch("qa_platform.agents.call_structured_llm", return_value=fake_response):
            agent = ReviewAgent()
            report = agent.review(
                requirements=[],
                test_designs=[],
                runtime_config=runtime_config,
            )

        self.assertFalse(report.approved)
        self.assertEqual(report.coverage_ratio, 0.0)
        self.assertTrue(report.findings)
        self.assertTrue(report.improvement_actions)
        self.assertTrue(any("rejected the run without concrete findings" in item for item in report.findings))

    def test_ollama_missing_local_model_fails_before_chat_request(self) -> None:
        runtime_config = AgentRuntimeConfig(
            agent_key="orchestrator",
            agent_name="Orchestrator Agent",
            execution_mode="LLM-backed",
            provider_strategy="Ollama local",
            model_family="Qwen 3 32B",
            model_override="missing-model:latest",
            model_id="missing-model:latest",
            directives="Route clearly.",
        )

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self) -> bytes:
                return json.dumps({"models": [{"model": "qwen3:8b"}]}).encode("utf-8")

        with patch("qa_platform.llm_runtime.request.urlopen", return_value=FakeResponse()) as mock_urlopen:
            with self.assertRaises(LLMRuntimeError) as context:
                call_structured_llm(
                    runtime_config=runtime_config,
                    system_prompt="Return JSON.",
                    user_prompt="Test prompt",
                    schema_name="test_schema",
                    schema={"type": "object", "properties": {}, "required": []},
                )

        self.assertIn("missing-model:latest", str(context.exception))
        self.assertIn("not installed", str(context.exception))
        self.assertEqual(mock_urlopen.call_count, 1)

    def test_agent_timeout_returns_without_waiting_for_worker_shutdown(self) -> None:
        orchestrator = OrchestratorAgent()

        def slow_call():
            time.sleep(1.1)
            return "done"

        started_at = time.perf_counter()
        with patch.object(orchestrator_module, "AGENT_TIMEOUT_SECONDS", 1):
            with self.assertRaises(orchestrator_module.AgentTimeoutError):
                orchestrator._run_with_timeout("Slow Agent", None, slow_call, ())
        elapsed = time.perf_counter() - started_at

        self.assertLess(elapsed, 1.05)

    def test_agent_timeout_uses_runtime_config_value(self) -> None:
        orchestrator = OrchestratorAgent()
        runtime_config = AgentRuntimeConfig(
            agent_key="requirements_analyst",
            agent_name="Requirements Analyst Agent",
            execution_mode="LLM-backed",
            timeout_seconds=1,
        )

        def slow_call():
            time.sleep(1.1)
            return "done"

        started_at = time.perf_counter()
        with self.assertRaises(orchestrator_module.AgentTimeoutError) as context:
            orchestrator._run_with_timeout("Requirements Analyst", runtime_config, slow_call, ())
        elapsed = time.perf_counter() - started_at

        self.assertLess(elapsed, 1.05)
        self.assertEqual(context.exception.timeout_seconds, 1)

    def test_process_requirements_returns_formatted_error_panel_for_missing_requirements(self) -> None:
        updates = list(
            process_requirements(
                "Demo",
                "",
                2,
                0,
                0,
                "http://127.0.0.1:11434",
                "",
            )
        )
        status_html, report_html, log_file, runtime_html, memory_html, feedback_text, run_json_file = updates[-1]

        self.assertEqual(len(updates), 1)
        self.assertIn("Run stopped because of an error", status_html)
        self.assertIn("Requirements saknas", status_html)
        self.assertIn("Retry after correcting the configuration", status_html)
        self.assertEqual(report_html, "")
        self.assertIsNone(log_file)
        self.assertIn("Runtime activity", runtime_html)
        self.assertIn("Working memory", memory_html)
        self.assertIn("Run blocked", feedback_text)
        self.assertIsNone(run_json_file)

    def test_process_requirements_streams_runtime_updates_before_final_result(self) -> None:
        class FakeResult:
            def to_dict(self):
                return {
                    "title": "Demo",
                    "source_requirements": "The user can log in.",
                    "requirements": [{"requirement_id": "REQ-001"}],
                    "test_designs": [{"test_case_id": "TC-001"}],
                    "generated_artifacts": [],
                    "review": {
                        "approved": True,
                        "coverage_ratio": 1.0,
                        "findings": [],
                        "improvement_actions": [],
                    },
                    "iterations": 1,
                    "run_controls": {
                        "max_rounds": 2,
                        "max_feedback_messages": 0,
                        "max_feedback_per_agent_pair": 0,
                    },
                    "agent_configs": [],
                    "stage_traces": [],
                    "run_session": {
                        "title": "Demo",
                        "source_requirements": "The user can log in.",
                        "working_memory": {
                            "shared": {"requirements": [{"requirement_id": "REQ-001"}]},
                            "agent_private": {"requirements_analyst": {"validation_findings": []}},
                            "timeline": ["Run session started."],
                        },
                    },
                }

        def fake_process(
            self,
            title,
            requirements_text,
            agent_configs=None,
            run_controls=None,
            event_callback=None,
            stop_requested=None,
        ):
            assert event_callback is not None
            del stop_requested
            event_callback(
                {
                    "event_type": "stage_started",
                    "agent_name": "Requirements Analyst",
                    "iteration": 1,
                    "stage_index": 1,
                    "message": "Running Requirements Analyst.",
                    "duration_ms": 0,
                    "memory_snapshot": {
                        "shared": {"current_stage": "requirements"},
                        "agent_private": {"requirements_analyst": {"last_feedback_messages": []}},
                        "timeline": ["Run session started."],
                    },
                }
            )
            event_callback(
                {
                    "event_type": "stage_completed",
                    "agent_name": "Requirements Analyst",
                    "iteration": 1,
                    "stage_index": 1,
                    "message": "Requirements Analyst completed.",
                    "duration_ms": 12,
                    "memory_snapshot": {
                        "shared": {"current_stage": "requirements", "requirements": [{"requirement_id": "REQ-001"}]},
                        "agent_private": {"requirements_analyst": {"validation_findings": []}},
                        "timeline": ["Run session started.", "Requirements Analyst produced 1 requirement item(s)."],
                    },
                }
            )
            return FakeResult()

        with patch.object(app_module.OrchestratorAgent, "process", new=fake_process):
            with patch.object(
                app_module,
                "save_run",
                return_value=SimpleNamespace(run_id=7, stored_at="now", db_path="/tmp/run.db", log_path="/tmp/run.log"),
            ):
                with patch.object(app_module, "build_workflow_report", return_value="<section>final report</section>"):
                    updates = list(
                        process_requirements(
                            "Demo",
                            "The user can log in.",
                            2,
                            0,
                            0,
                            "http://127.0.0.1:11434",
                            "",
                        )
                    )

        self.assertGreaterEqual(len(updates), 3)
        running_status, running_report, running_file, running_runtime, running_memory, running_feedback, running_json_file = updates[1]
        final_status, final_report, final_file, _final_runtime, final_memory, final_feedback, final_json_file = updates[-1]

        self.assertIn("Workflow is running", running_status)
        self.assertIn("Runtime events recorded: 1", running_status)
        self.assertEqual(running_report, "")
        self.assertEqual(running_file["value"].endswith("-live.txt"), True)
        self.assertIn("Requirements Analyst", running_runtime)
        self.assertIn("Working memory", running_memory)
        self.assertIn("current_stage", running_memory)
        self.assertIn("Workflow is running", running_feedback)
        self.assertIsNone(running_json_file)
        self.assertIn("Saved as run #7", final_status)
        self.assertEqual(final_report, "<section>final report</section>")
        self.assertEqual(final_file["value"], "/tmp/run.log")
        self.assertIn("Working memory", final_memory)
        self.assertIn("Workflow finished", final_feedback)
        self.assertTrue(final_json_file["value"].endswith(".json"))

    def test_requirements_agent_drops_invalid_requirement_items_from_llm_output(self) -> None:
        configs = build_agent_runtime_configs(
            "Structured baseline",
            "HF cheapest/free credits",
            "Qwen 3 32B",
            "Route clearly.",
            "LLM-backed",
            "HF cheapest/free credits",
            "Qwen 3 32B",
            "Extract strict requirement objects.",
            "Structured baseline",
            "HF fastest",
            "DeepSeek R1",
            "Design stronger oracles.",
            "Structured baseline",
            "HF fastest",
            "DeepSeek R1",
            "Review thoroughly.",
        )
        runtime_config = configs[1]
        fake_response = (
            {
                "requirements": [
                    {
                        "original_text": "   ",
                        "normalized_text": "",
                        "priority": "high",
                        "acceptance_criteria": [],
                        "assumptions": [],
                        "trace_notes": ["Invalid output from model."],
                    }
                ],
                "run_notes": ["Model returned one malformed item."],
            },
            {
                "model_id": runtime_config.model_id,
                "provider_strategy": runtime_config.provider_strategy,
            },
        )

        with patch("qa_platform.agents.call_structured_llm", return_value=fake_response):
            agent = RequirementsAnalystAgent()
            result = agent.analyze(
                "The user must be able to sign in with email and password.",
                runtime_config=runtime_config,
            )

        self.assertEqual(result, [])
        self.assertTrue(any("requirements.v1 contract" in item for item in agent.last_execution["validation_findings"]))

    def test_hf_inference_client_falls_back_without_stacked_provider_retries(self) -> None:
        runtime_config = AgentRuntimeConfig(
            agent_key="requirements_analyst",
            agent_name="Requirements Analyst Agent",
            execution_mode="LLM-backed",
            timeout_seconds=120,
            provider_strategy="HF cheapest/free credits",
            model_family="Qwen 3 32B",
            model_override="Qwen/Qwen3-32B",
            model_id="Qwen/Qwen3-32B",
            directives="Extract strict requirement objects.",
        )

        with patch.dict(os.environ, {"HF_TOKEN": "test-token"}, clear=False):
            with patch.object(
                llm_runtime_module,
                "_post_hf_inference_chat_completion",
                side_effect=LLMRuntimeError("HTTP 503 from provider"),
            ) as mock_hf_call:
                with patch.object(llm_runtime_module, "_post_chat_completion") as mock_router_call:
                    mock_router_call.return_value = {
                        "choices": [{"message": {"content": "{\"ok\": true}"}}],
                        "usage": {},
                    }
                    payload, metadata = call_structured_llm(
                        runtime_config=runtime_config,
                        system_prompt="Return JSON.",
                        user_prompt="Test prompt",
                        schema_name="test_schema",
                        schema={
                            "type": "object",
                            "properties": {"ok": {"type": "boolean"}},
                            "required": ["ok"],
                        },
                    )

        self.assertEqual(mock_hf_call.call_count, 1)
        self.assertEqual(payload, {"ok": True})
        self.assertEqual(metadata.provider_strategy, "HF cheapest/free credits")

    def test_orchestrator_blocks_test_design_when_no_valid_requirements_exist(self) -> None:
        orchestrator = OrchestratorAgent(max_iterations=1)

        def fake_analyze(*_args, **_kwargs):
            orchestrator.requirements_analyst.last_execution = {
                "llm_used": True,
                "reasoning_source": "llm_structured_output",
                "notes": ["Model returned malformed requirement payload."],
                "validation_findings": [
                    "Requirements Analyst did not produce any valid requirement items that satisfy the requirements.v1 contract."
                ],
            }
            return []

        with patch.object(orchestrator.requirements_analyst, "analyze", side_effect=fake_analyze):
            result = orchestrator.process(
                title="Broken requirements contract",
                requirements_text="The user must be able to sign in with email and password.",
                run_controls=RunControlConfig(
                    max_rounds=1,
                    max_feedback_messages=0,
                    max_feedback_per_agent_pair=0,
                ),
            )

        self.assertFalse(result.review.approved)
        self.assertEqual(len(result.test_designs), 0)
        self.assertEqual(
            [trace.agent_name for trace in result.stage_traces],
            ["Orchestrator Agent", "Requirements Analyst", "Orchestrator Agent"],
        )
        self.assertTrue(
            any("requirements.v1 contract" in finding for finding in result.review.findings)
        )

    def test_requirements_llm_recovers_previous_valid_items_when_feedback_rerun_returns_zero(self) -> None:
        runtime_config = AgentRuntimeConfig(
            agent_key="requirements_analyst",
            agent_name="Requirements Analyst Agent",
            execution_mode="LLM-backed",
            timeout_seconds=120,
            provider_strategy="HF cheapest/free credits",
            model_family="Qwen 3 32B",
            model_id="Qwen/Qwen3-32B:cheapest",
            directives="Extract strict requirement objects.",
        )
        run_session = RunSession(
            title="Recovery demo",
            source_requirements="The user must be able to sign in with email and password.",
        )
        run_session.working_memory.write_shared(
            "requirements",
            [
                {
                    "requirement_id": "REQ-001",
                    "original_text": "The user must be able to sign in with email and password.",
                    "normalized_text": "The system shall allow users to sign in using their email and password.",
                    "priority": "high",
                    "acceptance_criteria": [
                        "The system displays a login form with email and password fields.",
                        "The system successfully authenticates users with valid email and password combinations.",
                    ],
                    "assumptions": ["The system stores user credentials securely."],
                }
            ],
            author="Requirements Analyst",
        )
        fake_response = (
            {
                "requirements": [],
                "run_notes": ["Model failed to preserve requirements during feedback rerun."],
            },
            {
                "model_id": runtime_config.model_id,
                "provider_strategy": runtime_config.provider_strategy,
            },
        )

        with patch("qa_platform.agents.call_structured_llm", return_value=fake_response):
            agent = RequirementsAnalystAgent()
            result = agent.analyze(
                "The user must be able to sign in with email and password.",
                feedback_messages=["REQ-001 needs clearer acceptance criteria."],
                runtime_config=runtime_config,
                run_session=run_session,
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].requirement_id, "REQ-001")
        self.assertTrue(
            any("previous valid requirement set was preserved" in item for item in agent.last_execution["validation_findings"])
        )

    def test_design_stage_does_not_backtrack_to_requirements_without_explicit_feedback(self) -> None:
        orchestrator = OrchestratorAgent(max_iterations=2)
        result = orchestrator.process(
            title="No heuristic requirement loop",
            requirements_text="The user must be able to sign in with email and password.",
        )

        orchestrator_routes = [
            trace for trace in result.stage_traces
            if trace.agent_name == "Orchestrator Agent" and "backtrack to requirements analyst" in trace.status
        ]
        self.assertEqual(orchestrator_routes, [])

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
            self.assertIn("Backtracking round", log_text)
            self.assertIn("How this agent works", log_text)
            self.assertIn("Execution:", log_text)
            self.assertIn("Configured directive:", log_text)

            connection = sqlite3.connect(db_path)
            try:
                row = connection.execute(
                    "SELECT title, requirement_count, design_count, approved FROM qa_runs WHERE id = 1"
                ).fetchone()
            finally:
                connection.close()

            self.assertEqual(row, ("Persistence demo", 1, 2, 1))

    def test_save_run_evaluation_and_export_csv(self) -> None:
        orchestrator = OrchestratorAgent(max_iterations=1)
        result = orchestrator.process(
            title="Evaluation persistence demo",
            requirements_text="The user must be able to sign in with email and password.",
        )
        payload = result.to_dict()

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "qa_runs_test.sqlite3"
            log_dir = Path(tmpdir) / "run_logs"
            export_dir = Path(tmpdir) / "exports"
            previous_db = os.environ.get("QA_RUNS_DB_PATH")
            previous_log_dir = os.environ.get("QA_RUNS_LOG_DIR")
            previous_export_dir = os.environ.get("QA_EXPORT_DIR")
            os.environ["QA_RUNS_DB_PATH"] = str(db_path)
            os.environ["QA_RUNS_LOG_DIR"] = str(log_dir)
            os.environ["QA_EXPORT_DIR"] = str(export_dir)
            try:
                saved_run = save_run(payload)
                evaluation_id = save_run_evaluation(
                    run_id=saved_run.run_id,
                    evaluator_type="human",
                    evaluator_name="Human QA specialist",
                    approved=True,
                    score=82.5,
                    dimensions={
                        "relevance": 4.0,
                        "completeness": 4.0,
                        "oracle_quality": 4.5,
                        "executability": 4.0,
                    },
                    findings=["Strong negative-path coverage."],
                    notes="Good overall quality.",
                )
                export_result = export_run_evaluations_csv(saved_run.run_id)
            finally:
                if previous_db is None:
                    os.environ.pop("QA_RUNS_DB_PATH", None)
                else:
                    os.environ["QA_RUNS_DB_PATH"] = previous_db
                if previous_log_dir is None:
                    os.environ.pop("QA_RUNS_LOG_DIR", None)
                else:
                    os.environ["QA_RUNS_LOG_DIR"] = previous_log_dir
                if previous_export_dir is None:
                    os.environ.pop("QA_EXPORT_DIR", None)
                else:
                    os.environ["QA_EXPORT_DIR"] = previous_export_dir

            self.assertGreater(evaluation_id, 0)
            self.assertGreaterEqual(export_result.row_count, 1)
            self.assertTrue(Path(export_result.csv_path).exists())
            csv_text = Path(export_result.csv_path).read_text(encoding="utf-8")
            self.assertIn("test_case_id", csv_text)
            self.assertIn("test_case_title", csv_text)
            self.assertIn("human_score", csv_text)
            self.assertIn("review_agent_score", csv_text)
            self.assertIn("82.5", csv_text)


if __name__ == "__main__":
    unittest.main()
