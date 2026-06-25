import html
import json
import os
from urllib.parse import quote

import gradio as gr

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qa_platform.literature import load_literature_markdown, render_markdown_document
from qa_platform.orchestrator import OrchestratorAgent


DEFAULT_TITLE = "Demo: webbapplikation för inloggning och registrering"
DEFAULT_REQUIREMENTS = """Användaren måste kunna logga in med e-post och lösenord.
Systemet ska visa ett tydligt felmeddelande vid ogiltiga uppgifter.
En administratör ska kunna se en översikt över registrerade användare.
Användaren ska kunna registrera ett nytt konto via ett formulär."""


def process_requirements(title: str, requirements: str) -> tuple[str, str]:
    normalized_title = (title or "Untitled demo").strip()
    normalized_requirements = (requirements or "").strip()
    if not normalized_requirements:
        raise gr.Error("Fältet 'Kravspecifikation' måste fyllas i.")

    result = OrchestratorAgent().process(
        title=normalized_title,
        requirements_text=normalized_requirements,
    )
    payload = result.to_dict()
    status = (
        "<div class='result-status'>"
        f"Klar. Iterationer: {payload['iterations']}. "
        f"Coverage: {payload['review']['coverage_ratio']}. "
        f"Godkänd: {'ja' if payload['review']['approved'] else 'nej'}."
        "</div>"
    )
    return status, build_agent_report(payload)


def build_demo() -> gr.Blocks:
    literature_html = render_markdown_document(
        title="Litteraturstudie",
        eyebrow="Dokumentation",
        markdown_text=load_literature_markdown(),
    )
    literature_data_url = "data:text/html;charset=utf-8," + quote(literature_html, safe="")
    literature_data_url_json = json.dumps(literature_data_url)

    theme = gr.themes.Soft(
        primary_hue="amber",
        secondary_hue="orange",
        neutral_hue="stone",
    )

    custom_css = """
    body { background:
      radial-gradient(circle at top left, rgba(212, 162, 87, 0.20), transparent 26%),
      radial-gradient(circle at bottom right, rgba(166, 69, 36, 0.14), transparent 24%),
      #f5efe4; }
    .app-shell { max-width: 1120px; margin: 0 auto; }
    .hero-card, .panel-card { border-radius: 24px; border: 1px solid rgba(35, 26, 18, 0.10); }
    .hero-card { background: linear-gradient(180deg, rgba(255,255,255,0.88), rgba(255,248,240,0.94)); }
    .doc-pill button {
      display: inline-flex; align-items: center; min-height: 42px; padding: 0 16px;
      border-radius: 999px; text-decoration: none; font-weight: 700;
      color: #241a12; background: rgba(255,255,255,0.82); border: 1px solid rgba(166, 69, 36, 0.16);
      cursor: pointer;
    }
    .result-status { font-size: 1rem; color: #6a5646; margin-bottom: 8px; }
    .report-shell { display: grid; gap: 18px; }
    .summary-grid {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px;
    }
    .metric-card, .agent-card {
      border: 1px solid rgba(35, 26, 18, 0.10);
      border-radius: 20px;
      background: rgba(255, 252, 247, 0.92);
      box-shadow: 0 14px 32px rgba(74, 45, 16, 0.08);
    }
    .metric-card { padding: 16px 18px; }
    .metric-label { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.12em; color: #8a6a55; }
    .metric-value { margin-top: 8px; font-size: 1.5rem; font-weight: 700; color: #241a12; }
    .agent-grid { display: grid; gap: 14px; }
    .agent-card { overflow: hidden; }
    .agent-head {
      display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(0, 0.8fr) minmax(0, 0.8fr);
      gap: 12px; padding: 16px 18px; background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(246,236,224,0.88));
      border-bottom: 1px solid rgba(35, 26, 18, 0.08);
    }
    .agent-index { font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.14em; color: #a64524; }
    .agent-role { font-size: 1.08rem; font-weight: 700; color: #241a12; }
    .agent-meta { font-size: 0.9rem; color: #6a5646; align-self: end; }
    .agent-body { padding: 16px 18px 18px; }
    .log-title { margin: 0 0 10px; font-size: 0.88rem; text-transform: uppercase; letter-spacing: 0.12em; color: #8a6a55; }
    .log-list { margin: 0; padding-left: 18px; color: #2d241d; line-height: 1.6; }
    .log-list li + li { margin-top: 7px; }
    .empty-state {
      padding: 22px; border-radius: 18px; background: rgba(255,252,247,0.88);
      border: 1px dashed rgba(35,26,18,0.16); color: #6a5646;
    }
    @media (max-width: 820px) {
      .agent-head { grid-template-columns: 1fr; }
    }
    """

    with gr.Blocks(theme=theme, css=custom_css, title="Agentisk QA-plattform") as demo:
        with gr.Column(elem_classes=["app-shell"]):
            gr.HTML(
                f"""
                <section class="hero-card" style="padding: 28px;">
                  <div style="display:flex; gap:16px; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                    <p style="margin:0; text-transform:uppercase; letter-spacing:0.18em; font-size:0.8rem; color:#a64524;">Sommarprojekt</p>
                    <div class="doc-pill">
                      <button
                        type="button"
                        onclick='(function() {{
                          window.open({literature_data_url_json}, "_blank", "noopener,noreferrer");
                        }})()'
                      >
                        Öppna litteraturstudie
                      </button>
                    </div>
                  </div>
                  <h1 style="margin:14px 0 0; font-size:clamp(2.6rem, 5vw, 4.8rem); line-height:0.95;">
                    Agentisk QA-plattform för kravbaserad testdesign
                  </h1>
                  <p style="max-width:72ch; margin:18px 0 0; color:#6a5646; line-height:1.7; font-size:1.04rem;">
                    Kör en regelbaserad agentpipeline lokalt i Gradio och visa litteraturstudien från samma applikation.
                  </p>
                  <p style="margin:14px 0 0; color:#6a5646; line-height:1.6;">
                    Litteraturstudien öppnas i en separat flik som en renderad Markdown-vy.
                  </p>
                </section>
                """
            )

            with gr.Row():
                with gr.Column(scale=5):
                    with gr.Group(elem_classes=["panel-card"]):
                        gr.Markdown("## Kör agentflöde")
                        title_input = gr.Textbox(label="Scenario", value=DEFAULT_TITLE)
                        requirements_input = gr.Textbox(
                            label="Kravspecifikation",
                            value=DEFAULT_REQUIREMENTS,
                            lines=12,
                        )
                        run_button = gr.Button("Kör agentflöde", variant="primary")

                with gr.Column(scale=6):
                    with gr.Group(elem_classes=["panel-card"]):
                        gr.Markdown("## Resultat")
                        status_output = gr.Markdown(
                            value="<div class='result-status'>Väntar på indata.</div>"
                        )
                        result_output = gr.HTML(
                            value="<div class='empty-state'>Ingen körning ännu. Kör agentflödet för att se agenter, status och körningslogg.</div>"
                        )

        run_button.click(
            fn=process_requirements,
            inputs=[title_input, requirements_input],
            outputs=[status_output, result_output],
        )

    return demo


def build_agent_report(payload: dict) -> str:
    review = payload["review"]
    summary_cards = [
        ("Scenario", payload["title"]),
        ("Iterationer", str(payload["iterations"])),
        ("Krav", str(len(payload["requirements"]))),
        ("Testdesigner", str(len(payload["test_designs"]))),
        ("Artefakter", str(len(payload["generated_artifacts"]))),
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

    agent_sections = [
        build_agent_card(
            index=1,
            role="Requirements Analyst",
            stage_status=f"{len(requirements)} krav extraherade",
            output_type="Requirement items",
            logs=[
                f"{item['requirement_id']}: prioritet {item['priority']}, {len(item['acceptance_criteria'])} acceptanskriterier."
                for item in requirements
            ]
            or ["Inga krav extraherades."],
        ),
        build_agent_card(
            index=2,
            role="Test Design Agent",
            stage_status=f"{len(test_designs)} testdesigner skapade",
            output_type="Test case designs",
            logs=[
                f"{item['test_case_id']}: {item['test_type']} med {len(item['steps'])} steg och {len(item['expected_results'])} förväntade resultat."
                for item in test_designs
            ]
            or ["Ingen testdesign genererades."],
        ),
        build_agent_card(
            index=3,
            role="Test Generation Agent",
            stage_status=f"{len(artifacts)} artefakter genererade",
            output_type="Generated artifacts",
            logs=[
                f"{item['artifact_id']}: mål {item['target']}, testnamn {item['test_name']} och {len(item['selectors'])} selektorförslag."
                for item in artifacts
            ]
            or ["Inga testartefakter genererades."],
        ),
        build_agent_card(
            index=4,
            role="Review Agent",
            stage_status="Granskning genomförd",
            output_type="Review report",
            logs=review["findings"] or ["Inga kritiska avvikelser identifierades."],
        ),
        build_agent_card(
            index=5,
            role="Orchestrator Agent",
            stage_status="Flöde sammanställt",
            output_type="Pipeline summary",
            logs=[
                f"Körningen avslutades efter {payload['iterations']} iterationer.",
                f"Coverage ratio: {review['coverage_ratio']}.",
                f"Godkännande: {'ja' if review['approved'] else 'nej'}.",
            ]
            + review["improvement_actions"],
        ),
    ]

    return (
        "<div class='report-shell'>"
        f"<div class='summary-grid'>{summary_html}</div>"
        "<div class='agent-grid'>"
        + "".join(agent_sections)
        + "</div></div>"
    )


def build_agent_card(index: int, role: str, stage_status: str, output_type: str, logs: list[str]) -> str:
    log_items = "".join(f"<li>{html.escape(log)}</li>" for log in logs)
    return (
        "<section class='agent-card'>"
        "<div class='agent-head'>"
        "<div>"
        f"<div class='agent-index'>Agent {index}</div>"
        f"<div class='agent-role'>{html.escape(role)}</div>"
        "</div>"
        f"<div class='agent-meta'><strong>Status:</strong> {html.escape(stage_status)}</div>"
        f"<div class='agent-meta'><strong>Output:</strong> {html.escape(output_type)}</div>"
        "</div>"
        "<div class='agent-body'>"
        "<div class='log-title'>Körningslogg</div>"
        f"<ul class='log-list'>{log_items}</ul>"
        "</div>"
        "</section>"
    )


demo = build_demo()


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
    )
