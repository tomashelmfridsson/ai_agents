import html
import os
import sys
from pathlib import Path

import gradio as gr


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qa_platform.orchestrator import OrchestratorAgent


DEFAULT_TITLE = "Demo: web application for login and registration"
DEFAULT_REQUIREMENTS = """The user must be able to sign in with email and password.
The system shall display a clear error message when credentials are invalid.
An administrator shall be able to view an overview of registered users.
The user shall be able to register a new account through a form."""
LITERATURE_URL = "https://tomashelmfridsson.github.io/ai_agents/literature-study/"
PROJECT_BRIEF_URL = "https://tomashelmfridsson.github.io/ai_agents/project-brief/"


def process_requirements(title: str, requirements: str) -> tuple[str, str]:
    normalized_title = (title or "Untitled demo").strip()
    normalized_requirements = (requirements or "").strip()
    if not normalized_requirements:
        raise gr.Error("The requirements field is required.")

    result = OrchestratorAgent().process(
        title=normalized_title,
        requirements_text=normalized_requirements,
    )
    payload = result.to_dict()
    status = (
        "<div class='result-status'>"
        f"Completed after {payload['iterations']} iteration(s). "
        f"Coverage ratio: {payload['review']['coverage_ratio']}. "
        f"Approved: {'yes' if payload['review']['approved'] else 'no'}."
        "</div>"
    )
    return status, build_workflow_report(payload)


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
    .gradio-container .scroll-hide,
    .gradio-container .input-container {
      background: rgba(255, 255, 255, 0.99) !important;
      color: var(--app-ink) !important;
      border-color: var(--app-line) !important;
    }
    .gradio-container textarea::placeholder,
    .gradio-container input::placeholder {
      color: var(--app-soft) !important;
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
    .stage-grid { display: grid; gap: 14px; }
    .stage-card { overflow: hidden; }
    .stage-head {
      display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, 0.9fr) minmax(0, 0.9fr);
      gap: 12px; padding: 16px 18px;
      background: linear-gradient(180deg, rgba(255,255,255,0.99), rgba(246,236,224,0.96));
      border-bottom: 1px solid var(--app-line);
    }
    .stage-index { font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.14em; color: var(--app-accent) !important; font-weight: 700; }
    .stage-role { font-size: 1.08rem; font-weight: 700; color: var(--app-ink) !important; }
    .stage-meta { font-size: 0.92rem; color: var(--app-muted) !important; align-self: end; font-weight: 500; }
    .stage-body { padding: 16px 18px 18px; }
    .io-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 18px;
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
                    <p>A fixed synchronous pipeline executes the same stages in order on every run. This version is deterministic and intentionally non-agentic so future LLM and orchestration variants can be compared against it.</p>
                  </article>
                  <article class="info-card">
                    <div class="info-label">Research direction</div>
                    <p>The target application compares LLM quality, orchestration patterns, observability, local versus cloud inference, and QA-specific suitability across multiple agent frameworks.</p>
                  </article>
                  <article class="info-card">
                    <div class="info-label">Iterations</div>
                    <p>An iteration is one full pass through analysis, design, generation, and review. The orchestrator repeats the pass until approval or the iteration limit is reached.</p>
                  </article>
                  <article class="info-card">
                    <div class="info-label">Technical flow</div>
                    <ul>
                      <li>Input parsing and requirement splitting</li>
                      <li>Heuristic acceptance criteria extraction</li>
                      <li>Rule-based test design and artifact generation</li>
                      <li>Coverage and assumption review</li>
                    </ul>
                  </article>
                </section>
                <section class="workflow-strip">
                  <div class="workflow-step"><strong>1. Parse</strong><span>Normalize the scenario and split requirement statements.</span></div>
                  <div class="workflow-step"><strong>2. Analyze</strong><span>Extract requirement IDs, assumptions, and acceptance criteria.</span></div>
                  <div class="workflow-step"><strong>3. Design</strong><span>Create test-case structures, steps, expected results, and oracles.</span></div>
                  <div class="workflow-step"><strong>4. Generate</strong><span>Produce selectors, test data, and pseudocode artifacts.</span></div>
                  <div class="workflow-step"><strong>5. Review</strong><span>Check coverage, findings, and approval status before the next iteration.</span></div>
                </section>
                """
            )

            with gr.Row():
                with gr.Column(scale=5):
                    with gr.Group(elem_classes=["panel-card"]):
                        gr.Markdown("## Run workflow")
                        title_input = gr.Textbox(label="Scenario", value=DEFAULT_TITLE)
                        requirements_input = gr.Textbox(
                            label="Requirements",
                            value=DEFAULT_REQUIREMENTS,
                            lines=12,
                        )
                        run_button = gr.Button("Run workflow", variant="primary")

                with gr.Column(scale=6):
                    with gr.Group(elem_classes=["panel-card"]):
                        gr.Markdown("## Result")
                        status_output = gr.Markdown(
                            value="<div class='result-status'>Waiting for input.</div>"
                        )
                        result_output = gr.HTML(
                            value="<div class='empty-state'>No run has been executed yet. Start the workflow to inspect stages, technical outputs, and review findings.</div>"
                        )

        run_button.click(
            fn=process_requirements,
            inputs=[title_input, requirements_input],
            outputs=[status_output, result_output],
        )

    return demo


def build_workflow_report(payload: dict) -> str:
    review = payload["review"]
    summary_cards = [
        ("Scenario", payload["title"]),
        ("Iterations", str(payload["iterations"])),
        ("Requirements", str(len(payload["requirements"]))),
        ("Designs", str(len(payload["test_designs"]))),
        ("Artifacts", str(len(payload["generated_artifacts"]))),
        ("Coverage", str(review["coverage_ratio"])),
    ]
    summary_html = "".join(
        "<div class='metric-card'>"
        f"<div class='metric-label'>{html.escape(label)}</div>"
        f"<div class='metric-value'>{html.escape(value)}</div>"
        "</div>"
        for label, value in summary_cards
    )

    requirements = payload["requirements"]
    test_designs = payload["test_designs"]
    artifacts = payload["generated_artifacts"]
    iteration_explanation = build_iteration_explanation(payload)
    agent_configuration = build_agent_configuration_summary()

    trace_sections = build_trace_sections(payload["stage_traces"])

    flow_diagram = """
    <section class='diagram-card'>
      <h3>Pipeline visualization</h3>
      <div class='diagram-flow'>
        <div class='diagram-node'><strong>Input</strong><span>Scenario title and raw requirement statements.</span></div>
        <div class='diagram-node'><strong>Requirements analyst</strong><span>Requirement IDs, priority tags, assumptions, acceptance criteria.</span></div>
        <div class='diagram-node'><strong>Test designer</strong><span>Test type selection, steps, oracle, expected results.</span></div>
        <div class='diagram-node'><strong>Artifact generator</strong><span>Selectors, test data, pseudocode, target mapping.</span></div>
        <div class='diagram-node'><strong>Reviewer</strong><span>Coverage ratio, findings, improvement actions, approval signal.</span></div>
      </div>
    </section>
    """

    return (
        "<div class='report-shell'>"
        f"<div class='summary-grid'>{summary_html}</div>"
        f"{iteration_explanation}"
        f"{agent_configuration}"
        f"{flow_diagram}"
        "<div class='stage-grid'>"
        + trace_sections
        + "</div></div>"
    )


def build_iteration_explanation(payload: dict) -> str:
    review = payload["review"]
    findings = review["findings"]
    finding_items = "".join(f"<li>{html.escape(item)}</li>" for item in findings[:4])

    if payload["iterations"] == 1:
        summary = (
            "The workflow completed in a single pass because the review step accepted the output "
            "without requiring a rerun."
        )
    else:
        summary = (
            "Iteration 2 happened because iteration 1 was not approved by the review step. "
            "In the current baseline there is no adaptive repair between passes, so the same "
            "deterministic logic is executed again until the iteration limit is reached."
        )

    detail = (
        "The review agent asks whether every requirement has generated coverage, whether expected "
        "results are strong enough, and whether assumptions need clarification."
    )

    if payload["iterations"] > 1:
        detail += (
            " Since no new state, prompt, or tool output is injected between passes, an extra "
            "iteration currently signals unresolved review findings rather than learning or refinement."
        )

    findings_block = (
        "<ul class='log-list'>" + finding_items + "</ul>"
        if finding_items
        else "<p class='agent-config-text'>No review findings were recorded.</p>"
    )

    return (
        "<section class='diagram-card'>"
        "<h3>Why this iteration count?</h3>"
        f"<p class='agent-config-text'>{html.escape(summary)}</p>"
        f"<p class='agent-config-text'>{html.escape(detail)}</p>"
        f"{findings_block}"
        "</section>"
    )


def build_agent_configuration_summary() -> str:
    cards = [
        (
            "Requirements analyst",
            "Rule-based text splitter",
            "Splits the input into requirement statements, assigns sequential IDs, classifies priority from keywords such as 'must' and 'should', and adds acceptance criteria plus assumptions from hard-coded heuristics.",
        ),
        (
            "Test designer",
            "Keyword-driven test shaping",
            "Maps each requirement to a coarse test type such as scenario, GUI/E2E, API/integration, or unit. It then creates preconditions, steps, expected results, an oracle, and risk notes from fixed templates.",
        ),
        (
            "Artifact generator",
            "Template artifact synthesis",
            "Generates test names, placeholder test data, selector suggestions, and pseudocode from deterministic templates derived from the requirement text and the chosen test type.",
        ),
        (
            "Review agent",
            "Coverage and assumption gate",
            "Checks whether every requirement produced an artifact, whether expected results are specific enough, and whether assumptions remain unresolved. Approval is calculated from hard-coded thresholds rather than an LLM judgment.",
        ),
        (
            "Orchestrator",
            "Synchronous controller",
            "Runs the stages in a fixed order with a maximum of two passes. It does not re-plan, alter prompts, or route work dynamically between agents in the current baseline.",
        ),
    ]

    card_html = "".join(
        "<div class='diagram-node'>"
        f"<strong>{html.escape(title)}</strong>"
        f"<span><strong style='display:inline; margin:0; color:inherit;'>Configuration:</strong> {html.escape(config)}</span>"
        f"<span>{html.escape(description)}</span>"
        "</div>"
        for title, config, description in cards
    )
    return (
        "<section class='diagram-card'>"
        "<h3>How the current agents are configured</h3>"
        "<div class='diagram-flow'>"
        f"{card_html}"
        "</div>"
        "</section>"
    )


def build_trace_sections(stage_traces: list[dict]) -> str:
    return "".join(
        build_stage_card(
            run_index=index,
            iteration=trace["iteration"],
            stage_index=trace["stage_index"],
            role=trace["agent_name"],
            stage_status=trace["status"],
            input_summary=trace["input_summary"],
            output_summary=trace["output_summary"],
        )
        for index, trace in enumerate(stage_traces, start=1)
    )


def build_stage_card(
    run_index: int,
    iteration: int,
    stage_index: int,
    role: str,
    stage_status: str,
    input_summary: list[str],
    output_summary: list[str],
) -> str:
    input_items = "".join(f"<li>{html.escape(log)}</li>" for log in input_summary)
    output_items = "".join(f"<li>{html.escape(log)}</li>" for log in output_summary)
    return (
        "<section class='stage-card'>"
        "<div class='stage-head'>"
        "<div>"
        f"<div class='stage-index'>Run {run_index} • Iteration {iteration} • Stage {stage_index}</div>"
        f"<div class='stage-role'>{html.escape(role)}</div>"
        "</div>"
        f"<div class='stage-meta'><strong>Status:</strong> {html.escape(stage_status)}</div>"
        f"<div class='stage-meta'><strong>Agent pass:</strong> {html.escape(role)}</div>"
        "</div>"
        "<div class='stage-body'>"
        "<div class='io-grid'>"
        "<div>"
        "<div class='log-title'>Input</div>"
        f"<ul class='log-list'>{input_items}</ul>"
        "</div>"
        "<div>"
        "<div class='log-title'>Output</div>"
        f"<ul class='log-list'>{output_items}</ul>"
        "</div>"
        "</div>"
        "</div>"
        "</section>"
    )


demo = build_demo()


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
    )
