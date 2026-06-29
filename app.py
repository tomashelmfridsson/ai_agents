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
    AGENT_MODEL_HINTS,
    AGENT_PROVIDER_DEFAULTS,
    EXECUTION_MODE_CHOICES,
    MODEL_FAMILY_CHOICES,
    PROVIDER_STRATEGY_CHOICES,
    build_agent_runtime_configs,
)
from qa_platform.orchestrator import OrchestratorAgent
from qa_platform.sample_scenarios import (
    DEFAULT_REQUIREMENTS,
    DEFAULT_SCENARIO,
    DEFAULT_TITLE,
    SAMPLE_SCENARIOS,
    load_sample_scenario,
)
LITERATURE_URL = "https://tomashelmfridsson.github.io/ai_agents/literature-study/"
PROJECT_BRIEF_URL = "https://tomashelmfridsson.github.io/ai_agents/project-brief/"


def process_requirements(title: str, requirements: str, max_iterations: float, *agent_values: str) -> tuple[str, str]:
    normalized_title = (title or "Untitled demo").strip()
    normalized_requirements = (requirements or "").strip()
    if not normalized_requirements:
        raise gr.Error("The requirements field is required.")
    iteration_limit = max(1, int(max_iterations))
    agent_configs = build_agent_runtime_configs(*agent_values)
    preview_agents = [config.agent_name for config in agent_configs if config.execution_mode != "Structured baseline"]

    result = OrchestratorAgent(max_iterations=iteration_limit).process(
        title=normalized_title,
        requirements_text=normalized_requirements,
        agent_configs=agent_configs,
    )
    payload = result.to_dict()
    findings_count = len(payload["review"]["findings"])
    improvement_count = len(payload["review"]["improvement_actions"])
    preview_note = (
        " Model-backed selections are saved in the run configuration, but this first step still executes the structured baseline."
        if preview_agents
        else ""
    )
    status = (
        "<div class='result-status'>"
        f"Completed after {payload['iterations']} of {iteration_limit} allowed iteration(s). "
        f"Coverage ratio: {payload['review']['coverage_ratio']}. "
        f"Approved: {'yes' if payload['review']['approved'] else 'no'}. "
        f"Findings: {findings_count}. Improvement actions: {improvement_count}.{preview_note}"
        "</div>"
    )
    return status, build_workflow_report(payload)


def mark_custom_scenario(*_args: str) -> str:
    return "Custom scenario"


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
    .app-shell { max-width: 1160px; margin: 0 auto; }
    .hero-card, .panel-card, .info-card {
      border-radius: 24px;
      border: 1px solid var(--app-line);
      background: linear-gradient(180deg, var(--app-paper), var(--app-paper-2));
      box-shadow: 0 18px 42px rgba(50, 28, 8, 0.14);
    }
    .hero-card { overflow: hidden; }
    .panel-card, .info-card, .metric-card, .stage-card, .diagram-card, .diagram-node, .workflow-step {
      color: var(--app-ink) !important;
    }
    .doc-pill-button,
    .doc-pill-button button {
      display: inline-flex; align-items: center; min-height: 44px; padding: 0 16px;
      border-radius: 999px; text-decoration: none; font-weight: 700;
      color: var(--app-ink) !important;
      background: rgba(255,255,255,0.97);
      border: 1px solid rgba(143, 53, 24, 0.28);
    }
    .doc-pill-button button:hover { background: #fff; }
    .doc-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: flex-end;
    }
    .info-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
    }
    .info-card { padding: 18px 20px; }
    .info-label {
      font-size: 0.76rem;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      color: var(--app-accent) !important;
      margin-bottom: 8px;
      font-weight: 700;
    }
    .info-card p, .info-card li {
      color: var(--app-muted) !important;
      line-height: 1.7;
      margin: 0;
      font-size: 1rem;
      font-weight: 500;
    }
    .info-card ul { margin: 10px 0 0 18px; padding: 0; }
    .workflow-strip {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 12px;
      margin-top: 14px;
    }
    .workflow-step {
      border-radius: 18px;
      border: 1px solid var(--app-line);
      background: rgba(255, 253, 249, 0.99);
      padding: 14px 16px;
    }
    .workflow-step strong {
      display: block;
      color: var(--app-ink) !important;
      margin-bottom: 6px;
      font-size: 0.98rem;
      font-weight: 700;
    }
    .workflow-step span {
      display: block;
      color: var(--app-muted) !important;
      font-size: 0.95rem;
      line-height: 1.5;
      font-weight: 500;
    }
    .gradio-container .gr-group,
    .gradio-container .block,
    .gradio-container .form,
    .gradio-container .wrap,
    .gradio-container .container {
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
    }
    .diagram-card th {
      background: rgba(203, 145, 50, 0.18);
      font-weight: 700;
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
                      <div style="display:flex; gap:16px; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                        <div style="max-width:62ch;">
                          <p style="margin:0; text-transform:uppercase; letter-spacing:0.18em; font-size:0.8rem; color:var(--app-accent); font-weight:700;">Research prototype</p>
                          <h1 style="margin:12px 0 0; font-size:clamp(2.4rem, 5vw, 4.7rem); line-height:0.95;">
                            QA agent research workbench for LLM and orchestration comparisons
                          </h1>
                        </div>
                        <div class="doc-actions" id="literature-button-slot"></div>
                      </div>
                      <p style="max-width:72ch; margin:18px 0 0; color:var(--app-muted); line-height:1.7; font-size:1.04rem; font-weight:500;">
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

            gr.HTML(
                """
                <section class="info-grid">
                  <article class="info-card">
                    <div class="info-label">Current baseline</div>
                    <p>A fixed synchronous orchestrator runs the same four agent passes in the same order on every run. This version is deterministic and intentionally non-agentic so future LLM and orchestration variants can be compared against it.</p>
                  </article>
                  <article class="info-card">
                    <div class="info-label">Research direction</div>
                    <p>The target application compares LLM quality, orchestration patterns, observability, local versus cloud inference, and QA-specific suitability across multiple agent frameworks using a shared execution and reporting structure.</p>
                  </article>
                  <article class="info-card">
                    <div class="info-label">Iterations</div>
                    <p>In this baseline, the Orchestrator Agent coordinates one full pass across the Requirements Analyst Agent, Test Design Agent, and Review Agent. The orchestrator repeats the pass until approval or the iteration limit is reached.</p>
                  </article>
                  <article class="info-card">
                    <div class="info-label">Technical flow</div>
                    <ul>
                      <li>Requirement extraction with heuristic enrichment</li>
                      <li>Test case design from structured requirement items</li>
                      <li>Review and orchestration decision-making</li>
                      <li>Test case quality feedback for iteration decisions</li>
                    </ul>
                  </article>
                </section>
                <section class="workflow-strip">
                  <div class="workflow-step"><strong>Orchestrator Agent</strong><span>Decide which agent should act next, collect outputs, and either stop the run or trigger more work based on the review result and iteration budget.</span></div>
                  <div class="workflow-step"><strong>Requirements Analyst Agent</strong><span>Split the input into requirement items and enrich them with priority, acceptance criteria, and assumptions.</span></div>
                  <div class="workflow-step"><strong>Test Design Agent</strong><span>Turn each requirement item into a planned test case with type, steps, expected results, and oracle.</span></div>
                  <div class="workflow-step"><strong>Review Agent</strong><span>Evaluate coverage, assumptions, and the strength of the planned checks to decide whether the result is good enough.</span></div>
                </section>
                """
            )

            with gr.Group(elem_classes=["panel-card"]):
                gr.Markdown("## Run workflow")
                scenario_picker = gr.Dropdown(
                    label="Preset scenario",
                    choices=["Custom scenario", *SAMPLE_SCENARIOS.keys()],
                    value=DEFAULT_SCENARIO,
                )
                gr.Markdown(
                    "Choose a preset, or switch to `Custom scenario` and write your own title and requirements below.",
                    elem_classes=["scenario-help"],
                )
                title_input = gr.Textbox(label="Scenario", value=DEFAULT_TITLE)
                requirements_input = gr.Textbox(
                    label="Requirements",
                    value=DEFAULT_REQUIREMENTS,
                    lines=12,
                )
                max_iterations_input = gr.Slider(
                    label="Maximum iterations",
                    minimum=1,
                    maximum=5,
                    step=1,
                    value=2,
                )
                gr.Markdown("## Agent execution configuration")
                gr.Markdown(
                    "Use `Structured baseline` for the current deterministic implementation, or choose `Model-backed (preview)` to save intended model settings per agent before we wire in live LLM execution. The GUI now separates provider strategy from model family so we can later plug in Hugging Face, Ollama, or custom OpenAI-compatible backends.",
                    elem_classes=["scenario-help"],
                )
                agent_config_inputs = []
                with gr.Group(elem_classes=["agent-config-grid"]):
                    for agent_key, agent_name, description, default_directives in AGENT_CONFIG_SPECS:
                        with gr.Group(elem_classes=["agent-config-card"]):
                            hint = AGENT_MODEL_HINTS.get(agent_key, "")
                            description_html = html.escape(description)
                            hint_html = (
                                f" <strong>Cheap/free candidate:</strong> {html.escape(hint)}"
                                if hint
                                else ""
                            )
                            gr.HTML(f"<h4>{html.escape(agent_name)}</h4><p>{description_html}{hint_html}</p>")
                            execution_mode_input = gr.Dropdown(
                                label=f"{agent_name} execution mode",
                                choices=EXECUTION_MODE_CHOICES,
                                value=EXECUTION_MODE_CHOICES[0],
                            )
                            provider_strategy_input = gr.Dropdown(
                                label=f"{agent_name} provider strategy",
                                choices=PROVIDER_STRATEGY_CHOICES,
                                value=AGENT_PROVIDER_DEFAULTS.get(agent_key, PROVIDER_STRATEGY_CHOICES[0]),
                            )
                            model_family_input = gr.Dropdown(
                                label=f"{agent_name} model family",
                                choices=MODEL_FAMILY_CHOICES,
                                value=AGENT_MODEL_FAMILY_DEFAULTS.get(agent_key, MODEL_FAMILY_CHOICES[0]),
                            )
                            directives_input = gr.Textbox(
                                label=f"{agent_name} directives",
                                value=default_directives,
                                lines=3,
                            )
                            agent_config_inputs.extend(
                                [
                                    execution_mode_input,
                                    provider_strategy_input,
                                    model_family_input,
                                    directives_input,
                                ]
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
            inputs=[title_input, requirements_input, max_iterations_input, *agent_config_inputs],
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
    config_html = build_agent_config_overview(payload.get("agent_configs", []))
    trace_overview = build_trace_overview(payload)

    trace_sections = build_trace_sections(payload["stage_traces"])

    flow_diagram = """
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

    return (
        "<div class='report-shell'>"
        f"{summary_html}"
        f"{config_html}"
        f"{trace_overview}"
        f"{flow_diagram}"
        "<div class='stage-grid'>"
        + trace_sections
        + "</div></div>"
    )


def build_summary_overview(payload: dict) -> str:
    review = payload["review"]
    approved = "yes" if review["approved"] else "no"
    findings = review["findings"]
    improvement_actions = review["improvement_actions"]
    lead = (
        f"Scenario \"{payload['title']}\" produced {len(payload['requirements'])} requirement item(s), "
        f"{len(payload['test_designs'])} planned test case(s). The run ended after {payload['iterations']} iteration(s) with "
        f"coverage ratio {review['coverage_ratio']} and approved={approved}."
    )
    bullets = [
        f"Review findings: {len(findings)}",
        f"Improvement actions: {len(improvement_actions)}",
        f"Final approval decision: {approved}",
    ]
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
        "<table><thead><tr><th>Test case</th><th>Requirement</th><th>Requirement text</th><th>Title</th><th>Type</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
        "</section>"
    )


def build_agent_config_overview(agent_configs: list[dict]) -> str:
    if not agent_configs:
        return ""
    rows = []
    for config in agent_configs:
        directives = config.get("directives") or "No extra directives."
        model_id = config.get("model_id") or "Not set"
        provider_strategy = config.get("provider_strategy") or "Not set"
        model_family = config.get("model_family") or "Not set"
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
        "<h3>Agent runtime configuration</h3>"
        "<p class='agent-config-text'>This run stores per-agent execution settings. `Model-backed (preview)` means the intended model and directives are captured now, while the current baseline still executes deterministic logic.</p>"
        "<table><thead><tr><th>Agent</th><th>Execution mode</th><th>Provider strategy</th><th>Model family</th><th>Resolved model</th><th>Directives</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
        "</section>"
    )


def group_stage_traces_by_iteration(stage_traces: list[dict]) -> dict[int, list[dict]]:
    grouped: dict[int, list[dict]] = {}
    for trace in stage_traces:
        grouped.setdefault(trace["iteration"], []).append(trace)
    return grouped


def build_trace_sections(stage_traces: list[dict]) -> str:
    sections = []
    run_index = 1
    for iteration, traces in group_stage_traces_by_iteration(stage_traces).items():
        sections.append(
            "<section class='diagram-card'>"
            f"<h3>Iteration {iteration} execution</h3>"
            "<p class='agent-config-text'>Below is the full sequence of agent passes for this iteration, with explicit input, output, and decision context.</p>"
            "</section>"
        )
        for trace in traces:
            sections.append(
                build_stage_card(
                    run_index=run_index,
                    iteration=trace["iteration"],
                    stage_index=trace["stage_index"],
                    role=trace["agent_name"],
                    stage_status=trace["status"],
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
    explanation_block = (
        "<details class='stage-details'>"
        "<summary>How this agent works</summary>"
        f"<p class='agent-config-text'>{html.escape(agent_explanation)}</p>"
        f"<p class='agent-config-text'>{html.escape(decision_explanation)}</p>"
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
        f"<div class='stage-index'>Run {run_index} • Iteration {iteration} • Stage {stage_index}</div>"
        f"<div class='stage-role'>{html.escape(role)}</div>"
        "</div>"
        f"<div class='stage-meta'><strong>Status:</strong> {html.escape(stage_status)}</div>"
        f"<div class='stage-meta'><strong>Agent pass:</strong> {html.escape(role)}</div>"
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
