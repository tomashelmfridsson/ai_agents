import html
import os
import sys
from pathlib import Path

import gradio as gr


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qa_platform.agent_runtime import (
    AGENT_CONFIG_SPECS,
    AGENT_MODEL_FAMILY_DEFAULTS,
    AGENT_PROVIDER_DEFAULTS,
    EXECUTION_MODE_CHOICES,
    MODEL_FAMILY_CHOICES,
    PROVIDER_STRATEGY_CHOICES,
    build_agent_runtime_configs,
)
from qa_platform.orchestrator import OrchestratorAgent
from qa_platform.models import RunControlConfig
from qa_platform.sample_scenarios import (
    DEFAULT_REQUIREMENTS,
    DEFAULT_SCENARIO,
    DEFAULT_TITLE,
    SAMPLE_SCENARIOS,
    load_sample_scenario,
)
from qa_platform.storage import save_run
LITERATURE_URL = "https://tomashelmfridsson.github.io/ai_agents/literature-study/"
PROJECT_BRIEF_URL = "https://tomashelmfridsson.github.io/ai_agents/project-brief/"


def process_requirements(
    title: str,
    requirements: str,
    max_rounds: float,
    max_feedback_messages: float,
    max_feedback_per_agent_pair: float,
    *agent_values: str,
) -> tuple[str, str]:
    normalized_title = (title or "Untitled demo").strip()
    normalized_requirements = (requirements or "").strip()
    if not normalized_requirements:
        raise gr.Error("The requirements field is required.")
    round_limit = max(1, int(max_rounds))
    run_controls = RunControlConfig(
        max_rounds=round_limit,
        max_feedback_messages=max(0, int(max_feedback_messages)),
        max_feedback_per_agent_pair=max(0, int(max_feedback_per_agent_pair)),
    )
    agent_configs = build_agent_runtime_configs(*agent_values)
    result = OrchestratorAgent(max_iterations=round_limit).process(
        title=normalized_title,
        requirements_text=normalized_requirements,
        agent_configs=agent_configs,
        run_controls=run_controls,
    )
    payload = result.to_dict()
    saved_run = save_run(payload)
    payload["run_id"] = saved_run.run_id
    payload["stored_at"] = saved_run.stored_at
    payload["storage_path"] = saved_run.db_path
    payload["log_path"] = saved_run.log_path
    findings_count = len(payload["review"]["findings"])
    improvement_count = len(payload["review"]["improvement_actions"])
    live_llm_agents = [config.agent_name for config in agent_configs if config.execution_mode == "LLM-backed"]
    llm_note = (
        " Live LLM execution was enabled for: " + ", ".join(live_llm_agents) + "."
        if live_llm_agents
        else ""
    )
    status = (
        "<div class='result-status'>"
        f"Saved as run #{payload['run_id']}. "
        f"Completed with {payload['iterations']} backtracking cycle(s) within a limit of {round_limit}. "
        f"Coverage ratio: {payload['review']['coverage_ratio']}. "
        f"Approved: {'yes' if payload['review']['approved'] else 'no'}. "
        f"Findings: {findings_count}. Improvement actions: {improvement_count}. "
        f"Log file: {html.escape(payload['log_path'])}.{llm_note}"
        "</div>"
    )
    return status, build_workflow_report(payload)


def mark_custom_scenario(*_args: str) -> str:
    return "Custom scenario"


def format_llm_config_summary(provider_strategy: str, model_family: str) -> str:
    provider = provider_strategy or "Provider not set"
    model = model_family or "Model not set"
    return f"LLM configuration: {provider} / {model}"


def format_execution_mode_help(execution_mode: str) -> str:
    if execution_mode == "LLM-backed":
        return "LLM-backed enables live model execution where implemented and stores the resolved runtime details in the trace. Orchestration limits are still enforced locally."
    return "Structured baseline - deterministic implementation."


def toggle_llm_configuration_fields(execution_mode: str) -> tuple[dict, dict, dict, dict]:
    is_llm = execution_mode == "LLM-backed"
    return (
        gr.update(visible=is_llm),
        gr.update(visible=is_llm),
        gr.update(visible=is_llm),
        gr.update(visible=is_llm),
    )


def build_pipeline_visualization_section() -> str:
    return """
    <section class='diagram-card'>
      <h3>Pipeline visualization</h3>
      <div class='diagram-flow'>
        <div class='diagram-node'><strong>Input</strong><span>Scenario title and raw requirement statements.</span></div>
        <div class='diagram-node'><strong>Orchestrator Agent</strong><span>Controls routing, collects results, and decides whether another pass is needed.</span></div>
        <div class='diagram-node'><strong>Requirements Analyst Agent</strong><span>Requirement IDs, priority tags, assumptions, acceptance criteria.</span></div>
        <div class='diagram-node'><strong>Test Design Agent</strong><span>Test type selection, steps, oracle, expected results.</span></div>
        <div class='diagram-node'><strong>Review Agent</strong><span>Coverage ratio, findings, improvement actions, approval signal.</span></div>
      </div>
    </section>
    """


def build_demo() -> gr.Blocks:
    theme = gr.themes.Soft(
        primary_hue="amber",
        secondary_hue="orange",
        neutral_hue="stone",
    )

    custom_css = """
    :root {
      --app-ink: #1d140d;
      --app-muted: #3d3027;
      --app-soft: #5f4d40;
      --app-paper: rgba(255, 250, 244, 0.98);
      --app-paper-2: rgba(247, 238, 226, 0.98);
      --app-paper-3: rgba(252, 246, 238, 1);
      --app-line: rgba(29, 20, 13, 0.18);
      --app-accent: #8f3518;
      --app-accent-2: #cb9132;
    }
    body, .gradio-container {
      background:
        radial-gradient(circle at top left, rgba(212, 162, 87, 0.18), transparent 24%),
        radial-gradient(circle at bottom right, rgba(166, 69, 36, 0.12), transparent 22%),
        #eee5d7;
      color: var(--app-ink) !important;
    }
    .gradio-container, .gradio-container * {
      color: var(--app-ink);
    }
    .gradio-container .prose,
    .gradio-container .prose p,
    .gradio-container .prose li,
    .gradio-container .prose strong,
    .gradio-container label,
    .gradio-container h1,
    .gradio-container h2,
    .gradio-container h3,
    .gradio-container span,
    .gradio-container div {
      color: inherit;
    }
    .app-shell { max-width: 1080px; margin: 0 auto; }
    .hero-card, .hero-card > div, .panel-card, .panel-card > div, .info-card, .info-card > div {
      border-radius: 24px;
      border: 1px solid var(--app-line) !important;
      background: linear-gradient(180deg, var(--app-paper), var(--app-paper-2)) !important;
      box-shadow: 0 18px 42px rgba(50, 28, 8, 0.14) !important;
    }
    .hero-card {
      overflow: hidden;
      background:
        radial-gradient(circle at top right, rgba(203, 145, 50, 0.18), transparent 28%),
        linear-gradient(180deg, rgba(255, 252, 247, 1), rgba(245, 234, 220, 1)) !important;
      border: 1px solid rgba(29, 20, 13, 0.16) !important;
      box-shadow: 0 20px 46px rgba(50, 28, 8, 0.16) !important;
    }
    .hero-card * {
      color: var(--app-ink) !important;
    }
    .panel-card {
      background: linear-gradient(180deg, rgba(255, 251, 246, 1), rgba(246, 236, 223, 1)) !important;
    }
    .configuration-panel,
    .configuration-panel > div,
    .configuration-panel .block,
    .configuration-panel .gr-group,
    .configuration-panel .form,
    .configuration-panel .wrap,
    .configuration-panel fieldset,
    .configuration-panel [class*="container"] {
      background: linear-gradient(180deg, rgba(255, 251, 246, 1), rgba(246, 236, 223, 1)) !important;
    }
    .panel-card > div,
    .panel-card .block,
    .panel-card .gr-group {
      background: transparent !important;
    }
    .panel-card, .info-card, .metric-card, .stage-card, .diagram-card, .diagram-node, .workflow-step {
      color: var(--app-ink) !important;
    }
    .hero-kicker {
      margin: 0;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      font-size: 0.78rem;
      color: #7a2d12 !important;
      font-weight: 800;
    }
    .hero-title {
      margin: 10px 0 0;
      font-size: clamp(1.7rem, 3.4vw, 3.1rem);
      line-height: 1.02;
      color: #160e09 !important;
      text-shadow: 0 1px 0 rgba(255, 255, 255, 0.35);
    }
    .hero-copy {
      max-width: 68ch;
      margin: 14px 0 0;
      color: #2c2119 !important;
      line-height: 1.68;
      font-size: 0.97rem;
      font-weight: 600;
    }
    .doc-pill-button,
    .doc-pill-button button {
      display: inline-flex; align-items: center; justify-content: center; min-height: 42px; padding: 0 16px;
      border-radius: 999px; text-decoration: none; font-weight: 700;
      color: #ffffff !important;
      background: linear-gradient(180deg, #8f3518, #6f250d) !important;
      border: 1px solid rgba(86, 27, 8, 0.88);
      font-size: 0.9rem;
      box-shadow: 0 8px 18px rgba(50, 28, 8, 0.18);
    }
    .doc-pill-button button:hover {
      background: linear-gradient(180deg, #9f4220, #7f2b10) !important;
      border-color: rgba(86, 27, 8, 1);
    }
    .doc-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: flex-end;
    }
    .workflow-strip {
      display: grid;
      gap: 12px;
      margin-top: 10px;
    }
    .workflow-step {
      border-radius: 18px;
      border: 1px solid var(--app-line) !important;
      background: var(--app-paper-3) !important;
      padding: 14px 16px 16px;
    }
    .workflow-step > div,
    .workflow-step .block {
      background: transparent !important;
    }
    .workflow-step strong {
      display: block;
      color: #130d08 !important;
      margin-bottom: 6px;
      font-size: 1rem;
      font-weight: 800;
    }
    .workflow-step span {
      display: block;
      color: #2d221a !important;
      font-size: 0.96rem;
      line-height: 1.5;
      font-weight: 600;
    }
    .agent-description {
      margin-bottom: 6px;
    }
    .execution-mode-help {
      margin: 8px 0 12px;
      color: #3a2b20 !important;
      font-size: 0.92rem;
      line-height: 1.55;
      font-weight: 600;
    }
    .llm-summary {
      margin: 0 0 12px;
      padding: 10px 12px;
      border-radius: 12px;
      background: rgba(255, 249, 240, 0.98);
      border: 1px solid rgba(143, 53, 24, 0.14);
      color: var(--app-accent) !important;
      font-size: 0.84rem;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      font-weight: 700;
    }
    .config-accordion {
      margin-top: 8px;
      border: 1px solid rgba(29, 20, 13, 0.14);
      border-radius: 16px;
      overflow: hidden;
      background: rgba(252, 246, 238, 0.98);
    }
    .agent-accordion {
      border: 1px solid rgba(29, 20, 13, 0.16);
      border-radius: 18px;
      overflow: hidden;
      background: var(--app-paper-3) !important;
    }
    .agent-accordion > div,
    .agent-accordion section,
    .agent-accordion details {
      background: var(--app-paper-3) !important;
    }
    .agent-accordion button,
    .agent-accordion summary,
    .agent-accordion [role="button"] {
      background: linear-gradient(180deg, rgba(255, 252, 247, 1), rgba(248, 239, 226, 1)) !important;
      color: #130d08 !important;
      font-weight: 800 !important;
      border: none !important;
      box-shadow: none !important;
    }
    .agent-accordion .label-wrap,
    .agent-accordion .label-wrap span,
    .agent-accordion .label-wrap p,
    .agent-accordion .icon-wrap {
      color: #130d08 !important;
      fill: #130d08 !important;
    }
    .controls-accordion {
      border: 1px solid rgba(29, 20, 13, 0.16);
      border-radius: 18px;
      overflow: hidden;
      background: var(--app-paper-3) !important;
      margin-bottom: 12px;
    }
    .controls-accordion > div,
    .controls-accordion section,
    .controls-accordion details {
      background: var(--app-paper-3) !important;
    }
    .controls-accordion button,
    .controls-accordion summary,
    .controls-accordion [role="button"] {
      background: linear-gradient(180deg, rgba(255, 252, 247, 1), rgba(248, 239, 226, 1)) !important;
      color: #130d08 !important;
      font-weight: 800 !important;
      border: none !important;
      box-shadow: none !important;
    }
    .controls-accordion .label-wrap,
    .controls-accordion .label-wrap span,
    .controls-accordion .label-wrap p,
    .controls-accordion .icon-wrap {
      color: #130d08 !important;
      fill: #130d08 !important;
    }
    .config-accordion > div,
    .config-accordion section,
    .config-accordion details {
      background: transparent !important;
      color: var(--app-ink) !important;
    }
    .config-accordion button,
    .config-accordion summary,
    .config-accordion [role="button"] {
      background: linear-gradient(180deg, rgba(255, 252, 247, 0.99), rgba(248, 239, 226, 0.99)) !important;
      color: var(--app-ink) !important;
      font-weight: 700 !important;
      border: none !important;
      box-shadow: none !important;
    }
    .config-accordion button:hover,
    .config-accordion summary:hover,
    .config-accordion [role="button"]:hover {
      background: rgba(255, 248, 239, 1) !important;
    }
    .config-accordion .label-wrap,
    .config-accordion .label-wrap span,
    .config-accordion .label-wrap p,
    .config-accordion .icon-wrap {
      color: var(--app-ink) !important;
      fill: var(--app-ink) !important;
    }
    .config-accordion textarea,
    .config-accordion input,
    .config-accordion select {
      background: rgba(255, 255, 255, 0.99) !important;
    }
    .config-accordion .form,
    .config-accordion .wrap,
    .config-accordion .block {
      background: transparent !important;
    }
    .gradio-container .gr-group,
    .gradio-container .block,
    .gradio-container .form,
    .gradio-container .wrap,
    .gradio-container .container {
      color: var(--app-ink) !important;
    }
    .gradio-container .gr-group,
    .gradio-container .block {
      background-color: transparent !important;
    }
    .configuration-panel .gradio-container .gr-group,
    .configuration-panel .gradio-container .block,
    .configuration-panel .gradio-container .form,
    .configuration-panel .gradio-container .wrap {
      background: transparent !important;
    }
    .panel-card h2,
    .panel-card h3,
    .panel-card label,
    .panel-card p,
    .panel-card span,
    .panel-card div,
    .workflow-step p,
    .workflow-step label,
    .workflow-step span,
    .workflow-step div {
      color: var(--app-ink) !important;
    }
    .gradio-container textarea,
    .gradio-container input,
    .gradio-container select,
    .gradio-container .scroll-hide,
    .gradio-container .input-container {
      background: rgba(255, 255, 255, 0.99) !important;
      color: var(--app-ink) !important;
      border-color: var(--app-line) !important;
    }
    .configuration-panel input[type="range"],
    .configuration-panel .slider-container,
    .configuration-panel [data-testid="block-slider"] {
      background: transparent !important;
    }
    .gradio-container select,
    .gradio-container option {
      background: #fffaf4 !important;
      color: var(--app-ink) !important;
    }
    .gradio-container [role="listbox"],
    .gradio-container [role="option"] {
      background: #fffaf4 !important;
      color: var(--app-ink) !important;
    }
    .gradio-container [role="option"][aria-selected="true"] {
      background: rgba(203, 145, 50, 0.22) !important;
      color: var(--app-ink) !important;
    }
    .gradio-container textarea::placeholder,
    .gradio-container input::placeholder {
      color: var(--app-soft) !important;
    }
    .scenario-help {
      margin: -2px 0 8px;
      color: var(--app-muted) !important;
      font-size: 0.93rem;
      line-height: 1.5;
      font-weight: 500;
    }
    .baseline-note {
      margin: 4px 0 10px;
      padding: 14px 16px;
      border-radius: 16px;
      border: 1px solid rgba(143, 53, 24, 0.16);
      background: linear-gradient(180deg, rgba(255, 249, 240, 0.98), rgba(248, 239, 226, 0.98));
      color: var(--app-muted) !important;
      font-size: 0.94rem;
      line-height: 1.6;
      font-weight: 500;
    }
    .baseline-note strong {
      color: var(--app-ink) !important;
      font-weight: 700;
    }
    .config-subhead {
      margin: 10px 0 4px;
      color: var(--app-accent) !important;
      font-size: 0.82rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      font-weight: 800;
    }
    .agent-config-grid {
      display: grid;
      gap: 14px;
    }
    .agent-config-card {
      padding: 16px 18px;
      border-radius: 18px;
      border: 1px solid var(--app-line);
      background: rgba(255, 253, 249, 0.99);
    }
    .agent-config-card h4 {
      margin: 0 0 8px;
      color: var(--app-ink) !important;
      font-size: 1rem;
    }
    .agent-config-card p {
      margin: 0 0 12px;
      color: var(--app-muted) !important;
      line-height: 1.6;
      font-size: 0.94rem;
      font-weight: 500;
    }
    .gradio-container button.primary,
    .gradio-container button[variant="primary"] {
      background: linear-gradient(135deg, var(--app-accent), var(--app-accent-2)) !important;
      color: #fff !important;
      border: none !important;
    }
    .result-status {
      font-size: 1rem;
      color: var(--app-muted) !important;
      margin-bottom: 8px;
      font-weight: 600;
    }
    .report-shell { display: grid; gap: 18px; }
    .summary-grid {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px;
    }
    .summary-card-wide {
      padding: 18px 20px;
    }
    .summary-lead {
      margin: 0 0 10px;
      color: var(--app-ink) !important;
      font-size: 1.05rem;
      line-height: 1.65;
      font-weight: 600;
    }
    .summary-list {
      margin: 0;
      padding-left: 18px;
      color: var(--app-muted) !important;
      line-height: 1.7;
      font-weight: 500;
    }
    .metric-card, .stage-card, .diagram-card {
      border: 1px solid var(--app-line);
      border-radius: 20px;
      background: rgba(255, 253, 248, 0.99);
      box-shadow: 0 14px 32px rgba(50, 28, 8, 0.10);
    }
    .metric-card { padding: 16px 18px; }
    .metric-label { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.12em; color: var(--app-accent) !important; font-weight: 700; }
    .metric-value { margin-top: 8px; font-size: 1.5rem; font-weight: 700; color: var(--app-ink) !important; }
    .diagram-card { padding: 18px; }
    .diagram-card h3 {
      margin: 0 0 10px;
      font-size: 1rem;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--app-accent) !important;
    }
    .agent-config-text {
      color: var(--app-muted) !important;
      line-height: 1.7;
      font-size: 0.98rem;
      font-weight: 500;
      margin: 0 0 12px;
    }
    .iteration-summary + .iteration-summary {
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid var(--app-line);
    }
    .diagram-flow {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 12px;
    }
    .diagram-node {
      border-radius: 18px;
      padding: 14px 16px;
      background: linear-gradient(180deg, rgba(255,255,255,0.99), rgba(244,232,220,0.96));
      border: 1px solid var(--app-line);
    }
    .diagram-node strong { display: block; margin-bottom: 6px; color: var(--app-ink) !important; font-weight: 700; }
    .diagram-node span { display: block; color: var(--app-muted) !important; font-size: 0.92rem; line-height: 1.5; font-weight: 500; }
    .diagram-card table {
      width: 100%;
      table-layout: fixed;
      border-collapse: collapse;
      margin-top: 14px;
      background: rgba(255,255,255,0.9);
      border-radius: 16px;
      overflow: hidden;
    }
    .diagram-card th,
    .diagram-card td {
      padding: 12px 14px;
      border: 1px solid rgba(29, 20, 13, 0.16);
      text-align: left;
      vertical-align: top;
      color: var(--app-ink) !important;
      background: rgba(255,255,255,0.78);
      white-space: normal;
      overflow-wrap: anywhere;
      word-break: break-word;
    }
    .diagram-card th {
      background: rgba(203, 145, 50, 0.18);
      font-weight: 700;
    }
    .table-scroll {
      width: 100%;
      overflow-x: auto;
      overflow-y: visible;
      padding-bottom: 4px;
    }
    .stage-grid { display: grid; gap: 14px; }
    .stage-card { overflow: hidden; }
    .stage-toggle {
      border-bottom: 1px solid var(--app-line);
    }
    .stage-toggle summary {
      list-style: none;
      cursor: pointer;
    }
    .stage-toggle summary::-webkit-details-marker {
      display: none;
    }
    .stage-head {
      display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, 0.9fr) minmax(0, 0.9fr);
      gap: 12px; padding: 16px 18px;
      background: linear-gradient(180deg, rgba(255,255,255,0.99), rgba(246,236,224,0.96));
    }
    .stage-index { font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.14em; color: var(--app-accent) !important; font-weight: 700; }
    .stage-role { font-size: 1.08rem; font-weight: 700; color: var(--app-ink) !important; }
    .stage-meta { font-size: 0.92rem; color: var(--app-muted) !important; align-self: end; font-weight: 500; }
    .stage-chevron { justify-self: end; align-self: center; color: var(--app-accent) !important; font-weight: 700; }
    .stage-toggle[open] .stage-chevron::before { content: "Collapse"; }
    .stage-toggle:not([open]) .stage-chevron::before { content: "Expand"; }
    .stage-body { padding: 16px 18px 18px; }
    .stage-details {
      margin-bottom: 16px;
      padding: 12px 14px;
      border-radius: 14px;
      background: rgba(247, 238, 226, 0.78);
      border: 1px solid var(--app-line);
    }
    .stage-details summary {
      cursor: pointer;
      color: var(--app-accent) !important;
      font-weight: 700;
      margin-bottom: 10px;
    }
    .io-stack {
      display: grid;
      gap: 14px;
    }
    .io-section {
      padding: 14px 16px;
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.68);
      border: 1px solid var(--app-line);
    }
    .io-summary {
      color: var(--app-ink) !important;
      line-height: 1.6;
      font-weight: 600;
      margin: 0;
    }
    .io-details {
      margin-top: 12px;
      padding-top: 10px;
      border-top: 1px solid rgba(29, 20, 13, 0.12);
    }
    .io-details summary {
      cursor: pointer;
      color: var(--app-accent) !important;
      font-weight: 700;
      margin-bottom: 10px;
    }
    .log-title { margin: 0 0 10px; font-size: 0.88rem; text-transform: uppercase; letter-spacing: 0.12em; color: var(--app-accent) !important; font-weight: 700; }
    .log-list { margin: 0; padding-left: 18px; color: var(--app-ink) !important; line-height: 1.7; font-weight: 500; }
    .log-list li + li { margin-top: 7px; }
    .empty-state {
      padding: 22px;
      border-radius: 18px;
      background: rgba(255,252,247,0.97);
      border: 1px dashed rgba(32,24,17,0.26);
      color: var(--app-muted) !important;
      font-weight: 500;
    }
    @media (max-width: 820px) {
      .stage-head { grid-template-columns: 1fr; }
      .stage-chevron { justify-self: start; }
      .doc-actions { justify-content: flex-start; }
    }
    """

    with gr.Blocks(theme=theme, css=custom_css, title="QA Agent Research Workbench") as demo:
        with gr.Column(elem_classes=["app-shell"]):
            with gr.Group(elem_classes=["hero-card"]):
                gr.HTML(
                    """
                    <section style="padding: 28px;">
                      <div style="display:flex; gap:12px; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                        <div style="max-width:58ch;">
                          <p class="hero-kicker">Research prototype</p>
                          <h1 class="hero-title">
                            QA agent research workbench for LLM and orchestration comparisons
                          </h1>
                        </div>
                        <div class="doc-actions" id="literature-button-slot"></div>
                      </div>
                      <p class="hero-copy">
                        The broader project evaluates multiple LLMs, local versus cloud inference, and alternative agentic orchestration patterns for QA. The current demo is the deterministic baseline: a synchronous rule-based workflow used as a controlled reference point.
                      </p>
                    </section>
                    """
                )
                gr.Button(
                    "Open literature review",
                    link=LITERATURE_URL,
                    link_target="_blank",
                    elem_classes=["doc-pill-button"],
                )
                gr.Button(
                    "Open project brief",
                    link=PROJECT_BRIEF_URL,
                    link_target="_blank",
                    elem_classes=["doc-pill-button"],
                )
            with gr.Group(elem_classes=["panel-card"]):
                gr.HTML(build_pipeline_visualization_section())
            with gr.Group(elem_classes=["panel-card", "configuration-panel"]):
                gr.Markdown("## Configuration")
                with gr.Accordion("Run controls", open=False, elem_classes=["controls-accordion"]):
                    max_iterations_input = gr.Slider(
                        label="Maximum rounds",
                        minimum=1,
                        maximum=5,
                        step=1,
                        value=2,
                    )
                    max_feedback_messages_input = gr.Slider(
                        label="Maximum feedback messages",
                        minimum=0,
                        maximum=12,
                        step=1,
                        value=4,
                    )
                    max_feedback_per_pair_input = gr.Slider(
                        label="Maximum feedback messages per agent pair",
                        minimum=0,
                        maximum=4,
                        step=1,
                        value=2,
                    )
                    gr.HTML(
                        """
                        <div class="baseline-note">
                          <strong>Agent feedback budget</strong> defines how much direct back-and-forth the future LLM agents may use.
                          Use it to stop Requirements Analyst, Test Design, and Review from sending too many correction messages to each other.
                          The current structured baseline stores these limits now, but still reruns the full pipeline instead of routing targeted feedback.
                        </div>
                        """
                    )
                gr.HTML("<div class='config-subhead'>Per-agent model setup</div>")
                agent_config_inputs = []
                with gr.Group(elem_classes=["agent-config-grid"]):
                    for agent_key, agent_name, description, default_directives in AGENT_CONFIG_SPECS:
                        with gr.Accordion(
                            agent_name,
                            open=False,
                            elem_classes=["agent-accordion"],
                        ):
                            with gr.Group(elem_classes=["workflow-step"]):
                                gr.HTML(
                                    f"<div class='agent-description'><strong>{html.escape(agent_name)}</strong><span>{html.escape(description)}</span></div>"
                                )
                                execution_mode_input = gr.Dropdown(
                                    label="Execution mode",
                                    choices=EXECUTION_MODE_CHOICES,
                                    value=EXECUTION_MODE_CHOICES[0],
                                )
                                execution_mode_help = gr.Markdown(
                                    value=format_execution_mode_help(EXECUTION_MODE_CHOICES[0]),
                                    elem_classes=["execution-mode-help"],
                                )
                                llm_summary = gr.Markdown(
                                    value=format_llm_config_summary(
                                        AGENT_PROVIDER_DEFAULTS.get(agent_key, PROVIDER_STRATEGY_CHOICES[0]),
                                        AGENT_MODEL_FAMILY_DEFAULTS.get(agent_key, MODEL_FAMILY_CHOICES[0]),
                                    ),
                                    elem_classes=["llm-summary"],
                                    visible=True,
                                )
                                provider_strategy_input = gr.Dropdown(
                                    label="Provider strategy",
                                    choices=PROVIDER_STRATEGY_CHOICES,
                                    value=AGENT_PROVIDER_DEFAULTS.get(agent_key, PROVIDER_STRATEGY_CHOICES[0]),
                                    visible=True,
                                )
                                model_family_input = gr.Dropdown(
                                    label="Model family",
                                    choices=MODEL_FAMILY_CHOICES,
                                    value=AGENT_MODEL_FAMILY_DEFAULTS.get(agent_key, MODEL_FAMILY_CHOICES[0]),
                                    visible=True,
                                )
                                directives_input = gr.Textbox(
                                    label="Directives",
                                    value=default_directives,
                                    lines=3,
                                    visible=True,
                                )
                                provider_strategy_input.change(
                                    fn=format_llm_config_summary,
                                    inputs=[provider_strategy_input, model_family_input],
                                    outputs=[llm_summary],
                                )
                                model_family_input.change(
                                    fn=format_llm_config_summary,
                                    inputs=[provider_strategy_input, model_family_input],
                                    outputs=[llm_summary],
                                )
                                execution_mode_input.change(
                                    fn=format_execution_mode_help,
                                    inputs=[execution_mode_input],
                                    outputs=[execution_mode_help],
                                )
                                execution_mode_input.change(
                                    fn=toggle_llm_configuration_fields,
                                    inputs=[execution_mode_input],
                                    outputs=[
                                        llm_summary,
                                        provider_strategy_input,
                                        model_family_input,
                                        directives_input,
                                    ],
                                )
                            agent_config_inputs.extend(
                                [
                                    execution_mode_input,
                                    provider_strategy_input,
                                    model_family_input,
                                    directives_input,
                                ]
                            )
            with gr.Group(elem_classes=["panel-card"]):
                gr.Markdown("## Scenario")
                scenario_picker = gr.Dropdown(
                    label="Preset scenario",
                    choices=["Custom scenario", *SAMPLE_SCENARIOS.keys()],
                    value=DEFAULT_SCENARIO,
                )
                title_input = gr.Textbox(label="Scenario", value=DEFAULT_TITLE)
                requirements_input = gr.Textbox(
                    label="Requirements",
                    value=DEFAULT_REQUIREMENTS,
                    lines=12,
                )
                run_button = gr.Button("Run workflow", variant="primary")

            with gr.Group(elem_classes=["panel-card"]):
                gr.Markdown("## Result")
                status_output = gr.Markdown(
                    value="<div class='result-status'>Waiting for input.</div>"
                )
                result_output = gr.HTML(
                    value="<div class='empty-state'>No run has been executed yet. Start the workflow to inspect stages, technical outputs, review findings, and orchestration decisions.</div>"
                )

        run_button.click(
            fn=process_requirements,
            inputs=[
                title_input,
                requirements_input,
                max_iterations_input,
                max_feedback_messages_input,
                max_feedback_per_pair_input,
                *agent_config_inputs,
            ],
            outputs=[status_output, result_output],
        )
        scenario_picker.change(
            fn=load_sample_scenario,
            inputs=[scenario_picker, title_input, requirements_input],
            outputs=[title_input, requirements_input],
        )
        title_input.input(
            fn=mark_custom_scenario,
            inputs=[title_input],
            outputs=[scenario_picker],
        )
        requirements_input.input(
            fn=mark_custom_scenario,
            inputs=[requirements_input],
            outputs=[scenario_picker],
        )

    return demo


def build_workflow_report(payload: dict) -> str:
    review = payload["review"]
    summary_html = build_summary_overview(payload)
    config_html = build_agent_config_overview(
        payload.get("run_controls", {}),
        payload.get("agent_configs", []),
    )
    trace_overview = build_trace_overview(payload)

    trace_sections = build_trace_sections(
        payload["stage_traces"],
        payload.get("agent_configs", []),
    )

    return (
        "<div class='report-shell'>"
        f"{summary_html}"
        f"{config_html}"
        f"{trace_overview}"
        "<div class='stage-grid'>"
        + trace_sections
        + "</div></div>"
    )


def build_summary_overview(payload: dict) -> str:
    review = payload["review"]
    run_controls = payload.get("run_controls", {})
    approved = "yes" if review["approved"] else "no"
    findings = review["findings"]
    improvement_actions = review["improvement_actions"]
    run_id = payload.get("run_id")
    storage_path = payload.get("storage_path")
    log_path = payload.get("log_path")
    lead = (
        f"Scenario \"{payload['title']}\" produced {len(payload['requirements'])} requirement item(s), "
        f"{len(payload['test_designs'])} planned test case(s). The run ended after {payload['iterations']} backtracking cycle(s) with "
        f"coverage ratio {review['coverage_ratio']} and approved={approved}."
    )
    bullets = [
        f"Stored run ID: {run_id}" if run_id is not None else "Stored run ID: not available",
        f"Configured max rounds: {run_controls.get('max_rounds', payload['iterations'])}",
        f"Configured max feedback messages: {run_controls.get('max_feedback_messages', 0)}",
        f"Configured max feedback per agent pair: {run_controls.get('max_feedback_per_agent_pair', 0)}",
        f"Review findings: {len(findings)}",
        f"Improvement actions: {len(improvement_actions)}",
        f"Final approval decision: {approved}",
    ]
    if storage_path:
        bullets.append(f"Run database: {storage_path}")
    if log_path:
        bullets.append(f"Run log: {log_path}")
    if findings:
        bullets.append(f"Most important review issue: {findings[0]}")
    if improvement_actions:
        bullets.append(f"Primary requested improvement: {improvement_actions[0]}")
    items = "".join(f"<li>{html.escape(item)}</li>" for item in bullets)
    return (
        "<section class='diagram-card summary-card-wide'>"
        "<h3>Run summary</h3>"
        f"<p class='summary-lead'>{html.escape(lead)}</p>"
        f"<ul class='summary-list'>{items}</ul>"
        "</section>"
    )


def build_trace_overview(payload: dict) -> str:
    requirement_map = {item["requirement_id"]: item["normalized_text"] for item in payload["requirements"]}
    rows = []
    for test_case in payload["test_designs"]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(test_case['test_case_id'])}</td>"
            f"<td>{html.escape(test_case['requirement_id'])}</td>"
            f"<td>{html.escape(requirement_map.get(test_case['requirement_id'], ''))}</td>"
            f"<td>{html.escape(test_case['title'])}</td>"
            f"<td>{html.escape(test_case['test_type'])}</td>"
            "</tr>"
        )
    return (
        "<section class='diagram-card'>"
        "<h3>Requirement to test case mapping</h3>"
        "<p class='agent-config-text'>In this app, the summary label 'Test cases' refers to the designed test cases created by the Test Design Agent. Each one is linked directly to a requirement ID and reviewed without a separate generation stage.</p>"
        "<div class='table-scroll'><table><thead><tr><th>Test case</th><th>Requirement</th><th>Requirement text</th><th>Title</th><th>Type</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
        "</section>"
    )


def build_agent_config_overview(run_controls: dict, agent_configs: list[dict]) -> str:
    if not run_controls and not agent_configs:
        return ""
    controls_table = (
        "<table><thead><tr><th>Setting</th><th>Value</th><th>Meaning</th></tr></thead><tbody>"
        f"<tr><td>Maximum rounds</td><td>{html.escape(str(run_controls.get('max_rounds', 'Not set')))}</td><td>Upper limit for full pipeline passes.</td></tr>"
        f"<tr><td>Maximum feedback messages</td><td>{html.escape(str(run_controls.get('max_feedback_messages', 'Not set')))}</td><td>Upper limit for direct agent-to-agent correction messages during LLM-backed orchestration.</td></tr>"
        f"<tr><td>Maximum feedback per agent pair</td><td>{html.escape(str(run_controls.get('max_feedback_per_agent_pair', 'Not set')))}</td><td>Caps repeated back-and-forth between the same two agents.</td></tr>"
        "</tbody></table>"
    )
    if not agent_configs:
        return (
            "<section class='diagram-card'>"
            "<h3>Run configuration</h3>"
            "<p class='agent-config-text'>This run stores global control settings for future agent-to-agent feedback and rerun limits.</p>"
            f"{controls_table}"
            "</section>"
        )
    rows = []
    for config in agent_configs:
        directives = config.get("directives") or "No extra directives."
        llm_active = config.get("execution_mode") == "LLM-backed"
        model_id = config.get("model_id") or ("Not active in structured baseline" if not llm_active else "Not set")
        provider_strategy = config.get("provider_strategy") or ("Not active in structured baseline" if not llm_active else "Not set")
        model_family = config.get("model_family") or ("Not active in structured baseline" if not llm_active else "Not set")
        rows.append(
            "<tr>"
            f"<td>{html.escape(config['agent_name'])}</td>"
            f"<td>{html.escape(config['execution_mode'])}</td>"
            f"<td>{html.escape(provider_strategy)}</td>"
            f"<td>{html.escape(model_family)}</td>"
            f"<td>{html.escape(model_id)}</td>"
            f"<td>{html.escape(directives)}</td>"
            "</tr>"
        )
    return (
        "<section class='diagram-card'>"
        "<h3>Run configuration</h3>"
        "<p class='agent-config-text'>This run stores both the global control settings and the per-agent runtime setup. The feedback limits matter once model-backed agents can send targeted repair messages to each other.</p>"
        f"{controls_table}"
        "<h3>Agent runtime configuration</h3>"
        "<p class='agent-config-text'>This run stores per-agent execution settings and the resolved live model details for every LLM-backed agent.</p>"
        "<table><thead><tr><th>Agent</th><th>Execution mode</th><th>Provider strategy</th><th>Model family</th><th>Resolved model</th><th>Directives</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
        "</section>"
    )


def normalize_agent_name(agent_name: str) -> str:
    normalized = (agent_name or "").strip().lower()
    if normalized.endswith(" agent"):
        normalized = normalized[: -len(" agent")]
    return normalized


def build_agent_runtime_lookup(agent_configs: list[dict]) -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    for config in agent_configs:
        lookup[normalize_agent_name(config.get("agent_name", ""))] = config
    return lookup


def group_stage_traces_by_iteration(stage_traces: list[dict]) -> dict[int, list[dict]]:
    grouped: dict[int, list[dict]] = {}
    for trace in stage_traces:
        grouped.setdefault(trace["iteration"], []).append(trace)
    return grouped


def build_trace_sections(stage_traces: list[dict], agent_configs: list[dict]) -> str:
    sections = []
    run_index = 1
    runtime_lookup = build_agent_runtime_lookup(agent_configs)
    for iteration, traces in group_stage_traces_by_iteration(stage_traces).items():
        sections.append(
            "<section class='diagram-card'>"
            f"<h3>Backtracking cycle {iteration}</h3>"
            "<p class='agent-config-text'>Below is the full sequence of agent passes for this backtracking cycle, with explicit input, output, and routing context.</p>"
            "</section>"
        )
        for trace in traces:
            runtime_config = runtime_lookup.get(normalize_agent_name(trace["agent_name"]), {})
            sections.append(
                build_stage_card(
                    run_index=run_index,
                    iteration=trace["iteration"],
                    stage_index=trace["stage_index"],
                    role=trace["agent_name"],
                    stage_status=trace["status"],
                    execution_mode=runtime_config.get("execution_mode", "Structured baseline"),
                    model_used=runtime_config.get("model_id", ""),
                    configured_directives=runtime_config.get("directives", ""),
                    input_summary=trace["input_summary"],
                    reasoning_trace=trace.get("reasoning_trace", []),
                    reasoning_source=trace.get("reasoning_source", "structured_trace"),
                    output_summary=trace["output_summary"],
                    agent_explanation=trace.get("agent_explanation", ""),
                    decision_explanation=trace.get("decision_explanation", ""),
                )
            )
            run_index += 1
    return "".join(sections)


def build_stage_card(
    run_index: int,
    iteration: int,
    stage_index: int,
    role: str,
    stage_status: str,
    execution_mode: str,
    model_used: str,
    configured_directives: str,
    input_summary: list[str],
    reasoning_trace: list[str],
    reasoning_source: str,
    output_summary: list[str],
    agent_explanation: str,
    decision_explanation: str,
) -> str:
    input_lead = input_summary[0] if input_summary else "No input recorded."
    reasoning_lead = reasoning_trace[0] if reasoning_trace else "No reasoning trace recorded."
    output_lead = output_summary[0] if output_summary else "No output recorded."
    input_rest = input_summary[1:] if len(input_summary) > 1 else []
    reasoning_rest = reasoning_trace[1:] if len(reasoning_trace) > 1 else []
    output_rest = output_summary[1:] if len(output_summary) > 1 else []
    runtime_label = execution_mode or "Structured baseline"
    runtime_detail = (
        f"{runtime_label} / {model_used}"
        if model_used
        else f"{runtime_label} / deterministic implementation"
    )
    input_items = "".join(f"<li>{html.escape(log)}</li>" for log in input_rest)
    reasoning_items = "".join(f"<li>{html.escape(log)}</li>" for log in reasoning_rest)
    output_items = "".join(f"<li>{html.escape(log)}</li>" for log in output_rest)
    input_details = (
        "<details class='io-details'><summary>Show input details</summary>"
        f"<ul class='log-list'>{input_items}</ul>"
        "</details>"
        if input_rest
        else ""
    )
    reasoning_details = (
        "<details class='io-details'><summary>Show reasoning details</summary>"
        f"<ul class='log-list'>{reasoning_items}</ul>"
        "</details>"
        if reasoning_rest
        else ""
    )
    output_details = (
        "<details class='io-details'><summary>Show output details</summary>"
        f"<ul class='log-list'>{output_items}</ul>"
        "</details>"
        if output_rest
        else ""
    )
    configured_directive_block = (
        f"<p class='agent-config-text'><strong>Configured directive:</strong> {html.escape(configured_directives)}</p>"
        if configured_directives
        else ""
    )
    explanation_block = (
        "<details class='stage-details'>"
        "<summary>How this agent works</summary>"
        f"<p class='agent-config-text'>{html.escape(agent_explanation)}</p>"
        f"<p class='agent-config-text'>{html.escape(decision_explanation)}</p>"
        f"{configured_directive_block}"
        "</details>"
        if agent_explanation or decision_explanation
        else ""
    )
    return (
        "<section class='stage-card'>"
        "<details class='stage-toggle'>"
        "<summary>"
        "<div class='stage-head'>"
        "<div>"
        f"<div class='stage-index'>Run {run_index} • Cycle {iteration} • Stage {stage_index}</div>"
        f"<div class='stage-role'>{html.escape(role)}</div>"
        "</div>"
        f"<div class='stage-meta'><strong>Status:</strong> {html.escape(stage_status)}</div>"
        f"<div class='stage-meta'><strong>Execution:</strong> {html.escape(runtime_detail)}</div>"
        "<div class='stage-chevron'></div>"
        "</div>"
        "</summary>"
        "<div class='stage-body'>"
        f"{explanation_block}"
        "<div class='io-stack'>"
        "<div class='io-section'>"
        "<div class='log-title'>Input</div>"
        f"<p class='io-summary'>{html.escape(input_lead)}</p>"
        f"{input_details}"
        "</div>"
        "<div class='io-section'>"
        "<div class='log-title'>Reasoning trace</div>"
        f"<p class='io-summary'>{html.escape(reasoning_lead)}</p>"
        f"<p class='agent-config-text'>Source: {html.escape(reasoning_source)}</p>"
        f"{reasoning_details}"
        "</div>"
        "<div class='io-section'>"
        "<div class='log-title'>Output</div>"
        f"<p class='io-summary'>{html.escape(output_lead)}</p>"
        f"{output_details}"
        "</div>"
        "</div>"
        "</div>"
        "</details>"
        "</section>"
    )


demo = build_demo()


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
    )
