import html
import inspect
import os
import queue
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Iterator

import gradio as gr


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qa_platform.agent_runtime import (
    AGENT_CONFIG_SPECS,
    AGENT_MODEL_FAMILY_DEFAULTS,
    AGENT_MODEL_OVERRIDE_DEFAULTS,
    AGENT_PROVIDER_DEFAULTS,
    AGENT_TIMEOUT_DEFAULTS,
    EXECUTION_MODE_CHOICES,
    MODEL_FAMILY_CHOICES,
    PROVIDER_STRATEGY_CHOICES,
    build_agent_runtime_configs,
)
from qa_platform.llm_runtime import LLMRuntimeError
from qa_platform.orchestrator import (
    AGENT_TIMEOUT_SECONDS,
    AgentTimeoutError,
    OrchestratorAgent,
    WorkflowCancelledError,
)
from qa_platform.models import AgentRuntimeConfig, RunControlConfig
from qa_platform.sample_scenarios import (
    DEFAULT_REQUIREMENTS,
    DEFAULT_SCENARIO,
    DEFAULT_TITLE,
    SAMPLE_SCENARIOS,
    load_sample_scenario,
)
from qa_platform.storage import get_log_dir, save_run
LITERATURE_URL = "https://tomashelmfridsson.github.io/ai_agents/literature-study/"
PROJECT_BRIEF_URL = "https://tomashelmfridsson.github.io/ai_agents/project-brief/"
AI_DEVELOPING_GUIDELINES_URL = "https://tomashelmfridsson.github.io/ai_agents/ai-developing-guidelines/"
QA_AGENT_DEVELOPING_REQUIREMENTS_URL = "https://tomashelmfridsson.github.io/ai_agents/qa-agent-developing-requirements/"
DEFAULT_OLLAMA_MODEL_CHOICES = [
    "qwen3:8b",
    "deepseek-r1:8b",
    "gemma3:4b",
    "llama3:latest",
]


APP_THEME = gr.themes.Soft(
    primary_hue="amber",
    secondary_hue="orange",
    neutral_hue="stone",
)
_ACTIVE_RUN_LOCK = threading.Lock()
_ACTIVE_RUN_STOP_EVENT: threading.Event | None = None


def _blocks_support_launch_theming() -> bool:
    launch_signature = inspect.signature(gr.Blocks.launch)
    return "theme" in launch_signature.parameters and "css" in launch_signature.parameters


def build_idle_status() -> str:
    return (
        "<section class='diagram-card'>"
        "<h3>Run status</h3>"
        "<p class='agent-config-text'>Ready to run. Start the workflow to execute the configured agents and save a traceable run log.</p>"
        "</section>"
    )


def build_idle_report() -> str:
    return (
        "<section class='diagram-card'>"
        "<h3>Run report</h3>"
        "<p class='agent-config-text'>No run has been executed yet. After the first run, this panel will show summaries, mappings, agent traces, review findings, and orchestrator decisions.</p>"
        "</section>"
    )


def build_idle_runtime_timeline() -> str:
    return (
        "<section class='diagram-card'>"
        "<h3>Runtime activity</h3>"
        "<p class='agent-config-text'>No runtime activity yet. After a run starts, this panel will show agent events, model names, and a live tail of the current run log.</p>"
        "</section>"
    )


def build_idle_memory_panel() -> str:
    return (
        "<section class='diagram-card'>"
        "<h3>Working memory</h3>"
        "<p class='agent-config-text'>No shared memory has been recorded yet. After a run starts, this panel will show shared keys, per-agent notes, and the memory timeline.</p>"
        "</section>"
    )


def build_interaction_feedback(message: str, tone: str = "info") -> str:
    normalized_message = (message or "").strip() or "Ready."
    normalized_tone = tone if tone in {"info", "success", "warning"} else "info"
    timestamp = datetime.now().strftime("%H:%M:%S")
    return (
        f"<div class='interaction-feedback interaction-feedback-{normalized_tone}'>"
        f"<strong>Status</strong><span>{html.escape(normalized_message)}</span>"
        f"<div class='interaction-feedback-time'>Updated {html.escape(timestamp)}</div>"
        "</div>"
    )


def _register_active_run(stop_event: threading.Event) -> None:
    global _ACTIVE_RUN_STOP_EVENT
    with _ACTIVE_RUN_LOCK:
        _ACTIVE_RUN_STOP_EVENT = stop_event


def _clear_active_run(stop_event: threading.Event) -> None:
    global _ACTIVE_RUN_STOP_EVENT
    with _ACTIVE_RUN_LOCK:
        if _ACTIVE_RUN_STOP_EVENT is stop_event:
            _ACTIVE_RUN_STOP_EVENT = None


def request_stop_current_run() -> str:
    with _ACTIVE_RUN_LOCK:
        stop_event = _ACTIVE_RUN_STOP_EVENT
    if stop_event is None:
        return build_interaction_feedback("No workflow is currently running.", "warning")
    stop_event.set()
    return build_interaction_feedback(
        "Stop requested. The current agent pass will finish before the workflow stops.",
        "warning",
    )


def _build_live_log_path(title: str) -> Path:
    log_dir = get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in (title or "scenario")).strip("-")
    slug = "-".join(part for part in slug.split("-") if part) or "scenario"
    return log_dir / f"{slug}-{timestamp}-live.txt"


def _write_live_log_header(
    log_path: Path,
    *,
    title: str,
    requirements: str,
    agent_configs: list[AgentRuntimeConfig],
) -> None:
    lines = [
        f"Scenario: {title}",
        f"Started at: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Source requirements:",
        requirements,
        "",
        "Configured agent runtime:",
    ]
    for config in agent_configs:
        lines.extend(
            [
                f"- {config.agent_name}",
                f"  Execution mode: {config.execution_mode}",
                f"  Timeout: {config.timeout_seconds} seconds",
                f"  Provider: {config.provider_strategy or 'Structured baseline'}",
                f"  Resolved model: {config.model_id or 'deterministic implementation'}",
            ]
        )
    lines.extend(["", "Runtime events:"])
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _append_live_log(log_path: Path, lines: list[str]) -> None:
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def _append_runtime_event_to_live_log(
    log_path: Path,
    event: dict[str, object],
    agent_configs: list[AgentRuntimeConfig],
) -> None:
    runtime_config = _find_agent_runtime_config(str(event.get("agent_name", "")), agent_configs)
    model_label = runtime_config.model_id if runtime_config and runtime_config.model_id else "not available"
    _append_live_log(
        log_path,
        [
            (
                f"[{datetime.now().isoformat(timespec='seconds')}] "
                f"cycle={event.get('iteration', '-')} stage={event.get('stage_index', '-')} "
                f"agent={event.get('agent_name', '-')} event={event.get('event_type', '-')} "
                f"model={model_label} duration_ms={event.get('duration_ms', 0)}"
            ),
            f"message: {event.get('message', '')}",
            "",
        ],
    )


def build_error_status(message: str) -> str:
    return (
        "<section class='diagram-card error-card'>"
        "<h3>Run status</h3>"
        "<p class='result-status error-status'>Run stopped because of an error.</p>"
        f"<p class='agent-config-text error-text'>{html.escape(message)}</p>"
        "</section>"
    )


def _find_agent_runtime_config(
    agent_name: str | None,
    agent_configs: list[AgentRuntimeConfig],
) -> AgentRuntimeConfig | None:
    if not agent_name:
        return None
    normalized = agent_name.strip().lower()
    for config in agent_configs:
        candidate = config.agent_name.strip().lower()
        if candidate == normalized or candidate.replace(" agent", "") == normalized:
            return config
    return None


def build_error_report(
    message: str,
    runtime_events: list[dict[str, object]] | None = None,
    agent_configs: list[AgentRuntimeConfig] | None = None,
    log_path: str | None = None,
    completed_traces: list[dict[str, object]] | None = None,
) -> str:
    runtime_events = runtime_events or []
    agent_configs = agent_configs or []
    last_event = runtime_events[-1] if runtime_events else {}
    last_agent = str(last_event.get("agent_name", "")) or None
    last_event_type = str(last_event.get("event_type", "-")) if runtime_events else "-"
    completed_count = sum(1 for event in runtime_events if event.get("event_type") == "stage_completed")
    last_iteration = str(last_event.get("iteration", "-")) if runtime_events else "-"
    runtime_config = _find_agent_runtime_config(last_agent, agent_configs)
    model_label = runtime_config.model_id if runtime_config and runtime_config.model_id else "not available"
    timeout_label = (
        f"{runtime_config.timeout_seconds} seconds"
        if runtime_config and getattr(runtime_config, "timeout_seconds", None)
        else "not available"
    )
    items = [
        f"<li>Last active agent: {html.escape(last_agent or 'not available')}</li>",
        f"<li>Model for that agent: {html.escape(model_label)}</li>",
        f"<li>Configured timeout for that agent: {html.escape(timeout_label)}</li>",
        f"<li>Last runtime event: {html.escape(last_event_type)}</li>",
        f"<li>Workflow cycle reached: {html.escape(last_iteration)}</li>",
        f"<li>Completed stages before the stop: {completed_count}</li>",
        f"<li>Log file: {html.escape(log_path or 'not available')}</li>",
        "<li>Check local services such as `ollama serve` and the configured base URL if the model did not answer.</li>",
        "<li>Retry after correcting the configuration, or switch the affected agent to `Structured baseline`.</li>",
    ]
    partial_results = ""
    if completed_traces:
        partial_results = (
            "<div class='report-shell'>"
            "<section class='diagram-card'>"
            "<h3>Completed agent results</h3>"
            "<p class='agent-config-text'>These agent results were completed before the run stopped.</p>"
            "</section>"
            "<div class='stage-grid'>"
            + build_trace_sections(completed_traces, [config.__dict__ for config in agent_configs])
            + "</div></div>"
        )
    return (
        "<section class='diagram-card error-card'>"
        "<h3>Run report</h3>"
        "<p class='agent-config-text error-text'>"
        f"{html.escape(message)}"
        "</p>"
        f"<ul class='summary-list'>{''.join(items)}</ul>"
        "</section>"
        + partial_results
    )


def build_running_status(runtime_events: list[dict[str, object]]) -> str:
    last_message = (
        str(runtime_events[-1].get("message", "Workflow is running."))
        if runtime_events
        else "Workflow is starting."
    )
    completed_count = sum(1 for event in runtime_events if event.get("event_type") == "stage_completed")
    return (
        "<section class='diagram-card'>"
        "<h3>Run status</h3>"
        "<p class='result-status'>Workflow is running.</p>"
        f"<p class='agent-config-text'>{html.escape(last_message)}</p>"
        f"<p class='agent-config-text'>Completed stages so far: {completed_count}.</p>"
        "</section>"
    )


def build_running_report(runtime_events: list[dict[str, object]]) -> str:
    return build_running_report_with_log(runtime_events, None)


def build_running_report_with_log(runtime_events: list[dict[str, object]], log_path: str | None) -> str:
    last_agent = str(runtime_events[-1].get("agent_name", "-")) if runtime_events else "-"
    last_event = str(runtime_events[-1].get("event_type", "-")) if runtime_events else "-"
    items = [
        f"<li>Latest agent: {html.escape(last_agent)}</li>",
        f"<li>Latest event: {html.escape(last_event)}</li>",
        f"<li>Runtime events recorded: {len(runtime_events)}</li>",
        f"<li>Live log file: {html.escape(log_path or 'not available')}</li>",
    ]
    return (
        "<section class='diagram-card'>"
        "<h3>Run report</h3>"
        "<p class='agent-config-text'>Workflow is in progress. This panel updates as agents start, complete, or route work.</p>"
        f"<ul class='summary-list'>{''.join(items)}</ul>"
        "</section>"
    )


def _format_memory_value(value: object) -> str:
    text = html.escape(repr(value))
    if len(text) > 320:
        text = text[:317] + "..."
    return text


def build_memory_panel(memory_snapshot: dict[str, object] | None) -> str:
    if not memory_snapshot:
        return build_idle_memory_panel()

    shared = memory_snapshot.get("shared", {}) if isinstance(memory_snapshot, dict) else {}
    agent_private = memory_snapshot.get("agent_private", {}) if isinstance(memory_snapshot, dict) else {}
    timeline = memory_snapshot.get("timeline", []) if isinstance(memory_snapshot, dict) else []

    if not isinstance(shared, dict):
        shared = {}
    if not isinstance(agent_private, dict):
        agent_private = {}
    if not isinstance(timeline, list):
        timeline = []

    shared_rows = []
    for key, value in shared.items():
        shared_rows.append(
            "<tr>"
            f"<td>{html.escape(str(key))}</td>"
            f"<td><code class='memory-value'>{_format_memory_value(value)}</code></td>"
            "</tr>"
        )
    shared_table = (
        "<div class='table-scroll'><table><thead><tr><th>Shared key</th><th>Value</th></tr></thead><tbody>"
        + "".join(shared_rows)
        + "</tbody></table></div>"
        if shared_rows
        else "<p class='agent-config-text'>No shared memory keys have been written yet.</p>"
    )

    private_rows = []
    for agent_key, values in agent_private.items():
        if isinstance(values, dict):
            for key, value in values.items():
                private_rows.append(
                    "<tr>"
                    f"<td>{html.escape(str(agent_key))}</td>"
                    f"<td>{html.escape(str(key))}</td>"
                    f"<td><code class='memory-value'>{_format_memory_value(value)}</code></td>"
                    "</tr>"
                )
    private_table = (
        "<div class='table-scroll'><table><thead><tr><th>Agent</th><th>Private key</th><th>Value</th></tr></thead><tbody>"
        + "".join(private_rows)
        + "</tbody></table></div>"
        if private_rows
        else "<p class='agent-config-text'>No agent-private memory entries have been written yet.</p>"
    )

    timeline_html = (
        "<div class='live-log-preview'><pre>"
        + html.escape("\n".join(str(item) for item in timeline[-16:]))
        + "</pre></div>"
        if timeline
        else "<p class='agent-config-text'>No memory timeline entries recorded yet.</p>"
    )

    return (
        "<section class='diagram-card'>"
        "<h3>Working memory</h3>"
        "<p class='agent-config-text'>This panel shows the run-scoped shared memory, per-agent private notes, and the memory timeline collected so far.</p>"
        "<details open><summary>Shared memory</summary>"
        f"{shared_table}"
        "</details>"
        "<details><summary>Agent private memory</summary>"
        f"{private_table}"
        "</details>"
        "<details><summary>Memory timeline</summary>"
        f"{timeline_html}"
        "</details>"
        "</section>"
    )


def build_live_log_preview(log_path: str | None, line_count: int = 12) -> str:
    if not log_path:
        return "<p class='agent-config-text'>Live log file is not available yet.</p>"
    path = Path(log_path)
    if not path.exists():
        return f"<p class='agent-config-text'>Waiting for live log file: {html.escape(log_path)}</p>"
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    preview = "\n".join(lines[-line_count:])
    return (
        "<div class='live-log-preview'>"
        f"<pre>{html.escape(preview)}</pre>"
        "</div>"
    )


def apply_global_agent_settings(
    execution_mode: str,
    provider_strategy: str,
    model_family: str,
    model_override: str,
    timeout_seconds: float,
) -> list[dict]:
    is_llm = execution_mode == "LLM-backed"
    model_value = get_initial_model_value(provider_strategy, model_family)
    model_choices = get_model_choices(provider_strategy)
    summary = format_llm_config_summary(provider_strategy, model_value, model_override)
    help_text = format_execution_mode_help(execution_mode)
    updates: list[dict] = []
    for _ in AGENT_CONFIG_SPECS:
        updates.extend(
            [
                gr.update(value=execution_mode),
                gr.update(value=provider_strategy, visible=is_llm),
                gr.update(
                    choices=model_choices,
                    value=model_value,
                    label="Model",
                    visible=is_llm,
                    allow_custom_value=True,
                ),
                gr.update(value=model_override, visible=is_llm),
                gr.update(value=max(30, int(timeout_seconds)), visible=is_llm),
                gr.update(value=help_text),
                gr.update(value=summary, visible=is_llm),
                gr.update(visible=is_llm),
            ]
        )
    updates.append(
        gr.update(
            value=build_interaction_feedback(
                (
                    f"Applied common settings to {len(AGENT_CONFIG_SPECS)} agents. "
                    f"Provider: {provider_strategy}. Model: {model_value}."
                ),
                "success",
            )
        )
    )
    return updates


def process_requirements(
    title: str,
    requirements: str,
    max_rounds: float,
    max_feedback_messages: float,
    max_feedback_per_agent_pair: float,
    ollama_base_url: str,
    openai_base_url: str,
    *agent_values: str,
    progress=gr.Progress(track_tqdm=False),
) -> Iterator[tuple[str, str, str | None, str, str, str]]:
    normalized_title = (title or "Untitled demo").strip()
    normalized_requirements = (requirements or "").strip()
    if not normalized_requirements:
        message = "Requirements saknas. Fyll i minst ett krav innan du kör workflow."
        yield (
            build_error_status(message),
            build_error_report(message),
            None,
            build_idle_runtime_timeline(),
            build_idle_memory_panel(),
            build_interaction_feedback("Run blocked. Add requirements before starting the workflow.", "warning"),
        )
        return
    round_limit = max(1, int(max_rounds))
    run_controls = RunControlConfig(
        max_rounds=round_limit,
        max_feedback_messages=max(0, int(max_feedback_messages)),
        max_feedback_per_agent_pair=max(0, int(max_feedback_per_agent_pair)),
    )
    os.environ["OLLAMA_BASE_URL"] = (ollama_base_url or "http://127.0.0.1:11434").strip()
    custom_openai_base_url = (openai_base_url or "").strip()
    if custom_openai_base_url:
        os.environ["OPENAI_BASE_URL"] = custom_openai_base_url
    agent_configs = build_agent_runtime_configs(*agent_values)
    live_log_path = _build_live_log_path(normalized_title)
    _write_live_log_header(
        live_log_path,
        title=normalized_title,
        requirements=normalized_requirements,
        agent_configs=agent_configs,
    )
    runtime_events: list[dict[str, object]] = []
    completed_stage_traces: list[dict[str, object]] = []
    latest_memory_snapshot: dict[str, object] | None = None
    event_queue: queue.Queue[tuple[str, object]] = queue.Queue()
    worker_state: dict[str, object] = {
        "done": False,
        "result": None,
        "error": None,
    }
    stop_event = threading.Event()
    _register_active_run(stop_event)

    yield (
        build_running_status(runtime_events),
        build_running_report_with_log(runtime_events, str(live_log_path)),
        gr.update(value=str(live_log_path)),
        build_idle_runtime_timeline(),
        build_idle_memory_panel(),
        build_interaction_feedback(
            "Workflow starting. Press Stop workflow to stop after the current agent pass."
        ),
    )

    def handle_runtime_event(event: dict[str, object]) -> None:
        event_queue.put(("event", event))

    def run_workflow() -> None:
        try:
            worker_state["result"] = OrchestratorAgent(max_iterations=round_limit).process(
                title=normalized_title,
                requirements_text=normalized_requirements,
                agent_configs=agent_configs,
                run_controls=run_controls,
                event_callback=handle_runtime_event,
                stop_requested=stop_event.is_set,
            )
        except Exception as exc:  # noqa: BLE001
            worker_state["error"] = exc
        finally:
            worker_state["done"] = True
            event_queue.put(("done", None))
            _clear_active_run(stop_event)

    progress(None, desc="Starting workflow.")
    worker = threading.Thread(target=run_workflow, daemon=True)
    worker.start()
    stop_notice_emitted = False

    while True:
        emitted = False
        while True:
            try:
                kind, payload = event_queue.get_nowait()
            except queue.Empty:
                break

            if kind == "event":
                event = payload
                assert isinstance(event, dict)
                runtime_config = _find_agent_runtime_config(str(event.get("agent_name", "")), agent_configs)
                if runtime_config and runtime_config.model_id:
                    event = {**event, "model_id": runtime_config.model_id}
                runtime_events.append(event)
                trace = event.get("trace")
                if isinstance(trace, dict):
                    completed_stage_traces.append(trace)
                memory_snapshot = event.get("memory_snapshot")
                if isinstance(memory_snapshot, dict):
                    latest_memory_snapshot = memory_snapshot
                _append_runtime_event_to_live_log(live_log_path, event, agent_configs)
                progress(None, desc=str(event.get("message", "Processing workflow...")))
                yield (
                    build_running_status(runtime_events),
                    build_running_report_with_log(runtime_events, str(live_log_path)),
                    gr.update(value=str(live_log_path)),
                    build_runtime_timeline(runtime_events, str(live_log_path)),
                    build_memory_panel(latest_memory_snapshot),
                    build_interaction_feedback("Workflow is running."),
                )
                emitted = True
        if worker_state["done"] and event_queue.empty():
            break
        if stop_event.is_set() and not stop_notice_emitted:
            stop_notice_emitted = True
            yield (
                build_running_status(runtime_events),
                build_running_report_with_log(runtime_events, str(live_log_path)),
                gr.update(value=str(live_log_path)),
                build_runtime_timeline(runtime_events, str(live_log_path)),
                build_memory_panel(latest_memory_snapshot),
                build_interaction_feedback(
                    "Stop requested. Waiting for the current agent pass to finish.",
                    "warning",
                ),
            )
        if not emitted:
            time.sleep(0.1)

    error = worker_state["error"]
    if isinstance(error, WorkflowCancelledError):
        message = "Workflow was stopped by the user."
        _append_live_log(
            live_log_path,
            [
                f"[{datetime.now().isoformat(timespec='seconds')}] RUN STOPPED",
                message,
                "",
            ],
        )
        yield (
            build_error_status(message),
            build_error_report(message, runtime_events, agent_configs, str(live_log_path), completed_stage_traces),
            gr.update(value=str(live_log_path)),
            build_runtime_timeline(runtime_events, str(live_log_path)),
            build_memory_panel(latest_memory_snapshot),
            build_interaction_feedback("Workflow stopped.", "warning"),
        )
        return
    if isinstance(error, LLMRuntimeError):
        message = format_user_error(str(error))
        yield (
            build_error_status(message),
            build_error_report(message, runtime_events, agent_configs, str(live_log_path), completed_stage_traces),
            gr.update(value=str(live_log_path)),
            build_runtime_timeline(runtime_events, str(live_log_path)),
            build_memory_panel(latest_memory_snapshot),
            build_interaction_feedback("Workflow stopped because of an LLM/backend error.", "warning"),
        )
        return
    if isinstance(error, AgentTimeoutError):
        message = f"An agent did not finish within its configured timeout. {error}"
        _append_live_log(
            live_log_path,
            [
                f"[{datetime.now().isoformat(timespec='seconds')}] ERROR timeout",
                message,
                "",
            ],
        )
        yield (
            build_error_status(message),
            build_error_report(message, runtime_events, agent_configs, str(live_log_path), completed_stage_traces),
            gr.update(value=str(live_log_path)),
            build_runtime_timeline(runtime_events, str(live_log_path)),
            build_memory_panel(latest_memory_snapshot),
            build_interaction_feedback("Workflow stopped because an agent hit its timeout.", "warning"),
        )
        return
    if error is not None:
        raise error

    result = worker_state["result"]
    if result is None:
        raise RuntimeError("Workflow finished without result or error.")
    payload = result.to_dict()
    saved_run = save_run(payload)
    payload["run_id"] = saved_run.run_id
    payload["stored_at"] = saved_run.stored_at
    payload["storage_path"] = saved_run.db_path
    payload["log_path"] = saved_run.log_path
    _append_live_log(
        live_log_path,
        [
            f"[{datetime.now().isoformat(timespec='seconds')}] RUN COMPLETED",
            f"Saved run id: {saved_run.run_id}",
            f"Detailed saved log: {saved_run.log_path}",
            "",
        ],
    )
    findings_count = len(payload["review"]["findings"])
    improvement_count = len(payload["review"]["improvement_actions"])
    live_llm_agents = [config.agent_name for config in agent_configs if config.execution_mode == "LLM-backed"]
    llm_note = (
        " Live LLM execution was enabled for: " + ", ".join(live_llm_agents) + "."
        if live_llm_agents
        else ""
    )
    status_items = [
        f"<li>Completed with {payload['iterations']} backtracking round(s) within a limit of {round_limit}.</li>",
        f"<li>Coverage ratio: {payload['review']['coverage_ratio']}.</li>",
        f"<li>Approved: {'yes' if payload['review']['approved'] else 'no'}.</li>",
        f"<li>Findings: {findings_count}. Improvement actions: {improvement_count}.</li>",
        f"<li>Log file: {html.escape(payload['log_path'])}</li>",
    ]
    if llm_note:
        status_items.append(f"<li>{html.escape(llm_note.strip())}</li>")
    status = (
        "<section class='diagram-card'>"
        "<h3>Run status</h3>"
        f"<p class='result-status'>Saved as run #{payload['run_id']}.</p>"
        "<ul class='summary-list'>"
        + "".join(status_items)
        + "</ul>"
        "</section>"
    )
    yield (
        status,
        build_workflow_report(payload),
        gr.update(value=saved_run.log_path),
        build_runtime_timeline(runtime_events, str(live_log_path)),
        build_memory_panel((payload.get("run_session") or {}).get("working_memory")),
        build_interaction_feedback(f"Workflow finished. Run #{payload['run_id']} was saved.", "success"),
    )


def mark_custom_scenario(*_args: str) -> str:
    return "Custom scenario"


def format_user_error(raw_message: str) -> str:
    lowered = raw_message.lower()
    if "hf_token is required" in lowered:
        return (
            "Live LLM-körning kunde inte starta. `HF_TOKEN` saknas, så Hugging Face-backenden kan inte användas. "
            "Lägg till token i `.env` eller byt agenten till `Structured baseline`, `Ollama local` eller `Custom OpenAI-compatible`."
        )
    if "openai_base_url is required" in lowered:
        return (
            "Live LLM-körning kunde inte starta. `OPENAI_BASE_URL` saknas för `Custom OpenAI-compatible`. "
            "Ange en bas-URL i miljön eller välj en annan provider-strategi."
        )
    if "access denied by the routed provider" in lowered or "cloudflare 1010" in lowered:
        return (
            "Live LLM-körningen stoppades av den routade modellen hos providerledet. "
            "Det betyder att backend-anropet nekades innan agenten kunde få svar. "
            "Prova `Ollama local`, `Custom OpenAI-compatible` eller en annan Hugging Face-strategi/modell."
        )
    if "could not reach model endpoint" in lowered:
        return (
            "Live LLM-körningen kunde inte nå modellens endpoint. Kontrollera nätverk, lokal backend eller bas-URL och försök igen."
        )
    if "requested local ollama model" in lowered and "is not installed" in lowered:
        return (
            "Live LLM-körningen stoppades direkt eftersom den valda Ollama-modellen inte finns lokalt. "
            "Pull:a modellen först med `ollama pull ...`, eller välj en modell som redan är installerad."
        )
    if "could not reach local ollama" in lowered or "did not respond to model discovery" in lowered:
        return (
            "Live LLM-körningen kunde inte verifiera lokala Ollama-modeller. "
            "Kontrollera att `ollama serve` kör, att bas-URL:en stämmer, och försök igen."
        )
    if "model response did not contain" in lowered or "could not locate a json object" in lowered:
        return (
            "Modellen svarade, men i ett format som inte kunde tolkas korrekt. "
            "Prova samma agent igen, byt modell eller använd `Structured baseline` tills modellen är stabil."
        )
    if "live llm call failed" in lowered:
        return (
            "Live LLM-körningen misslyckades för en agent. "
            "Öppna loggfilen efter körningen för tekniska detaljer, eller byt provider/modell för agenten som stoppades."
        )
    return f"Körningen stoppades av ett fel: {raw_message}"


def build_runtime_timeline(runtime_events: list[dict[str, object]], log_path: str | None = None) -> str:
    del log_path
    if not runtime_events:
        return build_idle_runtime_timeline()

    rows = []
    for event in runtime_events:
        duration_ms = int(event.get("duration_ms", 0) or 0)
        duration_label = f"{duration_ms} ms" if duration_ms > 0 else "-"
        model_label = str(event.get("model_id", "-"))
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(event.get('iteration', '')))}</td>"
            f"<td>{html.escape(str(event.get('stage_index', '')))}</td>"
            f"<td>{html.escape(str(event.get('agent_name', '')))}</td>"
            f"<td>{html.escape(model_label)}</td>"
            f"<td>{html.escape(str(event.get('event_type', '')))}</td>"
            f"<td>{html.escape(duration_label)}</td>"
            f"<td>{html.escape(str(event.get('message', '')))}</td>"
            "</tr>"
        )
    return (
        "<section class='diagram-card'>"
        "<h3>Runtime activity</h3>"
        "<p class='agent-config-text'>This panel shows which agent was active, when routing happened, and how long completed agent passes took.</p>"
        "<div class='table-scroll'><table><thead><tr><th>Cycle</th><th>Stage</th><th>Agent</th><th>Model</th><th>Event</th><th>Time</th><th>Message</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
        "</section>"
    )


def build_debug_panel(payload: dict) -> str:
    stage_traces = payload.get("stage_traces", []) or []
    contract_rows = []
    orchestrator_rows = []

    for trace in stage_traces:
        if trace.get("agent_name") == "Requirements Analyst":
            contract_messages = [
                item
                for item in trace.get("reasoning_trace", [])
                if "requirements.v1 contract" in str(item).lower()
                or "was dropped because" in str(item).lower()
            ]
            if contract_messages:
                contract_rows.append(
                    "<tr>"
                    f"<td>{html.escape(str(trace.get('iteration', '')))}</td>"
                    f"<td>{html.escape(str(trace.get('status', '')))}</td>"
                    f"<td>{html.escape('; '.join(contract_messages[:3]))}</td>"
                    "</tr>"
                )
        if trace.get("agent_name") == "Orchestrator Agent":
            lead = (trace.get("output_summary") or ["No decision recorded."])[0]
            orchestrator_rows.append(
                "<tr>"
                f"<td>{html.escape(str(trace.get('iteration', '')))}</td>"
                f"<td>{html.escape(str(trace.get('status', '')))}</td>"
                f"<td>{html.escape(str(lead))}</td>"
                "</tr>"
            )

    contract_table = (
        "<div class='table-scroll'><table><thead><tr><th>Cycle</th><th>Status</th><th>Contract validation</th></tr></thead><tbody>"
        + "".join(contract_rows)
        + "</tbody></table></div>"
        if contract_rows
        else "<p class='agent-config-text'>No requirement-contract violations were recorded in this run.</p>"
    )
    orchestrator_table = (
        "<div class='table-scroll'><table><thead><tr><th>Cycle</th><th>Status</th><th>Decision</th></tr></thead><tbody>"
        + "".join(orchestrator_rows)
        + "</tbody></table></div>"
        if orchestrator_rows
        else "<p class='agent-config-text'>No orchestrator decisions were recorded in this run.</p>"
    )

    return (
        "<section class='diagram-card'>"
        "<h3>Debug panel</h3>"
        "<p class='agent-config-text'>This panel focuses on the standardized agent contract checks and the orchestrator decisions that moved, backtracked, or stopped the run.</p>"
        "<h3>Requirement contract</h3>"
        f"{contract_table}"
        "<h3>Orchestrator decisions</h3>"
        f"{orchestrator_table}"
        "</section>"
    )


def format_llm_config_summary(provider_strategy: str, model_family: str, model_override: str) -> str:
    provider = provider_strategy or "Provider not set"
    override = (model_override or "").strip()
    if override:
        return f"LLM configuration: {provider} / model: {override}"
    model = model_family or "Model not set"
    return f"LLM configuration: {provider} / model: {model}"


def format_execution_mode_help(execution_mode: str) -> str:
    if execution_mode == "LLM-backed":
        return "LLM-backed means the agent calls the selected model during execution. Timeouts and run limits are still enforced by the app."
    return "Structured baseline means the agent uses the built-in deterministic logic without calling a model."


def get_ollama_model_choices() -> list[str]:
    try:
        completed = subprocess.run(
            ["ollama", "list"],
            check=True,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (FileNotFoundError, subprocess.SubprocessError, TimeoutError):
        return DEFAULT_OLLAMA_MODEL_CHOICES.copy()

    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) <= 1:
        return DEFAULT_OLLAMA_MODEL_CHOICES.copy()

    models: list[str] = []
    for line in lines[1:]:
        name = line.split()[0].strip()
        if name and name not in models:
            models.append(name)
    return models or DEFAULT_OLLAMA_MODEL_CHOICES.copy()


def get_model_choices(provider_strategy: str) -> list[str]:
    if provider_strategy == "Ollama local":
        return get_ollama_model_choices()
    return MODEL_FAMILY_CHOICES


def get_initial_model_value(provider_strategy: str, model_family: str) -> str:
    choices = get_model_choices(provider_strategy)
    if provider_strategy == "Ollama local":
        ollama_map = {
            "Qwen 3 32B": "qwen3:8b",
            "Llama 3.3 70B Instruct": "llama3:latest",
            "DeepSeek R1": "deepseek-r1:8b",
            "gpt-oss-120b": "gpt-oss:120b",
        }
        resolved = ollama_map.get(model_family, model_family)
        if resolved in choices:
            return resolved
    return model_family if model_family in choices else choices[0]


def update_model_dropdown(provider_strategy: str, current_value: str, model_override: str) -> tuple[dict, str]:
    choices = get_model_choices(provider_strategy)
    value = current_value if current_value in choices else get_initial_model_value(provider_strategy, current_value)
    return (
        gr.update(choices=choices, value=value, label="Model", allow_custom_value=True),
        format_llm_config_summary(provider_strategy, value, model_override),
    )


def toggle_llm_configuration_fields(execution_mode: str) -> tuple[dict, dict, dict, dict, dict]:
    is_llm = execution_mode == "LLM-backed"
    return (
        gr.update(visible=is_llm),
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


CUSTOM_CSS = """
    :root {
      --app-ink: #1d140d;
      --app-muted: #1d140d;
      --app-soft: #1d140d;
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
    .gradio-container .toast-wrap,
    .gradio-container .toast-wrap *,
    .gradio-container .toast,
    .gradio-container .toast *,
    .gradio-container [role="alert"],
    .gradio-container [role="alert"] *,
    .gradio-container .error,
    .gradio-container .error * {
      color: #1d140d !important;
    }
    .gradio-container .toast-wrap,
    .gradio-container .toast,
    .gradio-container [role="alert"],
    .gradio-container .error {
      background: linear-gradient(180deg, #fff8f1, #f8e8d9) !important;
      border: 1px solid rgba(143, 53, 24, 0.32) !important;
      box-shadow: 0 18px 40px rgba(50, 28, 8, 0.18) !important;
    }
    .gradio-container .toast-title,
    .gradio-container .toast-text,
    .gradio-container .toast-body,
    .gradio-container [role="alert"] strong {
      color: #1d140d !important;
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
    .interaction-feedback {
      margin: 10px 0 0;
      padding: 12px 14px;
      border-radius: 14px;
      border: 1px solid rgba(29, 20, 13, 0.16);
      background: rgba(255, 250, 243, 0.98);
      color: #130d08 !important;
      box-shadow: 0 8px 20px rgba(50, 28, 8, 0.08);
    }
    .interaction-feedback strong {
      display: block;
      margin: 0 0 4px;
      color: #130d08 !important;
      font-size: 0.78rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      font-weight: 800;
    }
    .interaction-feedback span,
    .interaction-feedback div {
      color: #130d08 !important;
      font-size: 0.95rem;
      line-height: 1.5;
      font-weight: 600;
    }
    .interaction-feedback-time {
      margin-top: 6px;
      color: #5a493b !important;
      font-size: 0.82rem !important;
      font-weight: 600;
    }
    .interaction-feedback-success {
      border-color: rgba(44, 118, 73, 0.22);
      background: rgba(240, 251, 244, 0.98);
    }
    .interaction-feedback-warning {
      border-color: rgba(143, 53, 24, 0.22);
      background: rgba(255, 247, 241, 0.98);
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
      font-size: 1.05rem;
      color: var(--app-ink) !important;
      margin-bottom: 8px;
      font-weight: 700;
    }
    .error-card {
      border-color: rgba(143, 53, 24, 0.28);
      background: linear-gradient(180deg, rgba(255, 247, 243, 0.99), rgba(255, 251, 247, 0.99));
    }
    .error-status {
      color: var(--app-accent) !important;
    }
    .error-text {
      color: var(--app-ink) !important;
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
    .diagram-card details summary {
      color: var(--app-ink) !important;
      font-weight: 700;
      cursor: pointer;
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
    .memory-value {
      color: #000 !important;
    }
    .live-log-preview,
    .live-log-preview pre,
    .live-log-preview code {
      color: #000 !important;
    }
    .live-log-preview pre {
      background: rgba(255, 255, 255, 0.96);
      border: 2px solid rgba(29, 20, 13, 0.32);
      border-radius: 10px;
      padding: 10px 12px;
      font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Monaco, Consolas, Liberation Mono, monospace;
      font-size: 0.84rem;
      line-height: 1.45;
      white-space: pre-wrap;
      word-break: break-word;
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


def build_demo() -> gr.Blocks:
    block_kwargs = {"title": "QA Agent Research Workbench"}
    if not _blocks_support_launch_theming():
        block_kwargs["theme"] = APP_THEME
        block_kwargs["css"] = CUSTOM_CSS

    with gr.Blocks(**block_kwargs) as demo:
        with gr.Column(elem_classes=["app-shell"]):
            with gr.Group(elem_classes=["hero-card"]):
                gr.HTML(
                    """
                    <section style="padding: 28px;">
                      <div style="display:flex; gap:12px; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                        <div style="max-width:58ch;">
                          <p class="hero-kicker">Research prototype</p>
                          <h1 class="hero-title">
                            QA Agent workbench for requirements analysis, test design, and orchestration comparison
                          </h1>
                        </div>
                        <div class="doc-actions" id="literature-button-slot"></div>
                      </div>
                      <p class="hero-copy">
                        This project evaluates how a QA-oriented multi-agent system can transform raw requirements into structured QA outputs such as requirement analysis, test design, review findings, runtime traces, and working memory. It also compares local and cloud LLM execution, orchestration strategies, and controlled backtracking in a traceable QA workflow.
                      </p>
                    </section>
                    """
                )
                gr.Button(
                    "Literature study",
                    link=LITERATURE_URL,
                    elem_classes=["doc-pill-button"],
                )
                gr.Button(
                    "Project brief",
                    link=PROJECT_BRIEF_URL,
                    elem_classes=["doc-pill-button"],
                )
                gr.Button(
                    "AI developing guidelines",
                    link=AI_DEVELOPING_GUIDELINES_URL,
                    elem_classes=["doc-pill-button"],
                )
                gr.Button(
                    "QA agent requirements",
                    link=QA_AGENT_DEVELOPING_REQUIREMENTS_URL,
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
                        maximum=10,
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
                          <strong>Run controls</strong> define how far the workflow is allowed to iterate before it stops.
                          <br><br>
                          <strong>Maximum rounds</strong> is the total number of workflow rounds the orchestrator may run, including reruns after feedback.
                          <br>
                          <strong>Maximum feedback messages</strong> is the total number of correction messages agents may send during one run.
                          <br>
                          <strong>Maximum feedback messages per agent pair</strong> limits repeated back-and-forth between the same two agents.
                          <br><br>
                          Use lower values for fast, controlled runs. Use higher values when you want the agents to spend more time repairing weak intermediate results.
                        </div>
                        """
                    )
                with gr.Accordion("Local backends", open=False, elem_classes=["controls-accordion"]):
                    ollama_base_url_input = gr.Textbox(
                        label="Ollama base URL",
                        value=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
                    )
                    openai_base_url_input = gr.Textbox(
                        label="Custom OpenAI-compatible base URL",
                        value=os.getenv("OPENAI_BASE_URL", ""),
                        placeholder="http://host:port/v1",
                    )
                    gr.HTML(
                        """
                        <div class="baseline-note">
                          <strong>Local Ollama</strong> reads installed models from your local Ollama environment.
                          The list under <em>Model</em> should therefore match `ollama list`.
                          If you want to enter an exact model name manually, use <em>Model override</em>, for example `qwen3:8b`.
                        </div>
                        """
                    )
                with gr.Accordion("Global agent LLM settings", open=False, elem_classes=["controls-accordion"]):
                    gr.HTML(
                        """
                        <div class="baseline-note">
                          Apply one common LLM configuration across all agents, then fine-tune only the agents that need exceptions.
                        </div>
                        """
                    )
                    global_execution_mode_input = gr.Dropdown(
                        label="Execution mode for all agents",
                        choices=EXECUTION_MODE_CHOICES,
                        value=EXECUTION_MODE_CHOICES[0],
                    )
                    global_provider_strategy_input = gr.Dropdown(
                        label="Provider strategy for all agents",
                        choices=PROVIDER_STRATEGY_CHOICES,
                        value="Ollama local",
                    )
                    global_model_input = gr.Dropdown(
                        label="Model for all agents",
                        choices=get_model_choices("Ollama local"),
                        value=get_initial_model_value("Ollama local", "Qwen 3 32B"),
                        allow_custom_value=True,
                    )
                    global_llm_summary = gr.Markdown(
                        value=format_llm_config_summary(
                            "Ollama local",
                            get_initial_model_value("Ollama local", "Qwen 3 32B"),
                            "",
                        ),
                        elem_classes=["llm-summary"],
                    )
                    global_model_override_input = gr.Textbox(
                        label="Model override for all agents (optional)",
                        value="",
                        placeholder="Examples: qwen3:8b, llama3:latest, deepseek-r1:8b",
                    )
                    global_timeout_input = gr.Slider(
                        label="Timeout for all agents (seconds)",
                        minimum=30,
                        maximum=300,
                        step=15,
                        value=120,
                    )
                    apply_global_settings_button = gr.Button("Apply to all agents")
                    global_provider_strategy_input.change(
                        fn=update_model_dropdown,
                        inputs=[global_provider_strategy_input, global_model_input, global_model_override_input],
                        outputs=[global_model_input, global_llm_summary],
                    )
                    global_model_input.change(
                        fn=format_llm_config_summary,
                        inputs=[global_provider_strategy_input, global_model_input, global_model_override_input],
                        outputs=[global_llm_summary],
                    )
                    global_model_override_input.change(
                        fn=format_llm_config_summary,
                        inputs=[global_provider_strategy_input, global_model_input, global_model_override_input],
                        outputs=[global_llm_summary],
                    )
                gr.HTML("<div class='config-subhead'>Per-agent model setup</div>")
                agent_config_inputs = []
                agent_bulk_outputs = []
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
                                initial_provider = AGENT_PROVIDER_DEFAULTS.get(agent_key, PROVIDER_STRATEGY_CHOICES[0])
                                initial_model = get_initial_model_value(
                                    initial_provider,
                                    AGENT_MODEL_FAMILY_DEFAULTS.get(agent_key, MODEL_FAMILY_CHOICES[0]),
                                )
                                llm_summary = gr.Markdown(
                                    value=format_llm_config_summary(
                                        initial_provider,
                                        initial_model,
                                        AGENT_MODEL_OVERRIDE_DEFAULTS.get(agent_key, ""),
                                    ),
                                    elem_classes=["llm-summary"],
                                    visible=True,
                                )
                                provider_strategy_input = gr.Dropdown(
                                    label="Provider strategy",
                                    choices=PROVIDER_STRATEGY_CHOICES,
                                    value=initial_provider,
                                    visible=True,
                                )
                                model_family_input = gr.Dropdown(
                                    label="Model",
                                    choices=get_model_choices(initial_provider),
                                    value=initial_model,
                                    visible=True,
                                    allow_custom_value=True,
                                )
                                model_override_input = gr.Textbox(
                                    label="Model override (optional)",
                                    value=AGENT_MODEL_OVERRIDE_DEFAULTS.get(agent_key, ""),
                                    placeholder="Examples: qwen3:8b, llama3:latest, deepseek-r1:8b, openai/gpt-oss-120b",
                                    visible=True,
                                )
                                timeout_input = gr.Slider(
                                    label="Agent timeout (seconds)",
                                    minimum=30,
                                    maximum=300,
                                    step=15,
                                    value=AGENT_TIMEOUT_DEFAULTS.get(agent_key, AGENT_TIMEOUT_SECONDS),
                                    visible=True,
                                )
                                directives_input = gr.Textbox(
                                    label="Directives",
                                    value=default_directives,
                                    lines=3,
                                    visible=True,
                                )
                                provider_strategy_input.change(
                                    fn=update_model_dropdown,
                                    inputs=[provider_strategy_input, model_family_input, model_override_input],
                                    outputs=[model_family_input, llm_summary],
                                )
                                model_family_input.change(
                                    fn=format_llm_config_summary,
                                    inputs=[provider_strategy_input, model_family_input, model_override_input],
                                    outputs=[llm_summary],
                                )
                                model_override_input.change(
                                    fn=format_llm_config_summary,
                                    inputs=[provider_strategy_input, model_family_input, model_override_input],
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
                                        model_override_input,
                                        timeout_input,
                                        directives_input,
                                    ],
                                )
                                agent_config_inputs.extend(
                                    [
                                        execution_mode_input,
                                        provider_strategy_input,
                                        model_family_input,
                                        model_override_input,
                                        timeout_input,
                                        directives_input,
                                    ]
                                )
                                agent_bulk_outputs.extend(
                                    [
                                        execution_mode_input,
                                        provider_strategy_input,
                                        model_family_input,
                                        model_override_input,
                                        timeout_input,
                                        execution_mode_help,
                                        llm_summary,
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
                interaction_feedback_output = gr.HTML(
                    value=build_interaction_feedback("Ready."),
                    elem_classes=["interaction-feedback-shell"],
                )

            with gr.Group(elem_classes=["panel-card"]):
                gr.Markdown("## Result")
                status_output = gr.HTML(
                    value=build_idle_status(),
                    show_label=False,
                    container=False,
                )
                result_output = gr.HTML(
                    value=build_idle_report(),
                    show_label=False,
                    container=False,
                )
                runtime_output = gr.HTML(
                    value=build_idle_runtime_timeline(),
                    show_label=False,
                    container=False,
                )
                memory_output = gr.HTML(
                    value=build_idle_memory_panel(),
                    show_label=False,
                    container=False,
                )
                log_file_output = gr.File(
                    label="Download run log",
                    value=None,
                    interactive=False,
                )
            with gr.Group(elem_classes=["panel-card"]):
                stop_button = gr.Button("Stop workflow")

        run_button.click(
            fn=process_requirements,
            inputs=[
                title_input,
                requirements_input,
                max_iterations_input,
                max_feedback_messages_input,
                max_feedback_per_pair_input,
                ollama_base_url_input,
                openai_base_url_input,
                *agent_config_inputs,
            ],
            outputs=[status_output, result_output, log_file_output, runtime_output, memory_output, interaction_feedback_output],
        )
        stop_button.click(
            fn=request_stop_current_run,
            inputs=[],
            outputs=[interaction_feedback_output],
        )
        apply_global_settings_button.click(
            fn=apply_global_agent_settings,
            inputs=[
                global_execution_mode_input,
                global_provider_strategy_input,
                global_model_input,
                global_model_override_input,
                global_timeout_input,
            ],
            outputs=[*agent_bulk_outputs, interaction_feedback_output],
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
    test_case_overview = build_test_case_overview(payload)
    trace_overview = build_trace_overview(payload)
    debug_panel = build_debug_panel(payload)

    trace_sections = build_trace_sections(
        payload["stage_traces"],
        payload.get("agent_configs", []),
    )

    return (
        "<div class='report-shell'>"
        f"{summary_html}"
        f"{config_html}"
        f"{test_case_overview}"
        f"{trace_overview}"
        f"{debug_panel}"
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
        f"{len(payload['test_designs'])} planned test case(s). The run ended after {payload['iterations']} backtracking round(s) with "
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


def build_test_case_overview(payload: dict) -> str:
    test_designs = payload.get("test_designs", [])
    if not test_designs:
        return (
            "<section class='diagram-card'>"
            "<h3>Planned test cases</h3>"
            "<p class='agent-config-text'>No planned test cases were produced in this run.</p>"
            "</section>"
        )

    cards = []
    for test_case in test_designs:
        steps = test_case.get("steps") or []
        expected_results = test_case.get("expected_results") or []
        risks = test_case.get("risks") or []
        step_items = "".join(f"<li>{html.escape(str(item))}</li>" for item in steps) or "<li>No steps recorded.</li>"
        expected_items = "".join(
            f"<li>{html.escape(str(item))}</li>" for item in expected_results
        ) or "<li>No expected results recorded.</li>"
        risk_items = "".join(f"<li>{html.escape(str(item))}</li>" for item in risks)
        risk_block = (
            "<div class='io-section'>"
            "<div class='log-title'>Risks</div>"
            f"<ul class='log-list'>{risk_items}</ul>"
            "</div>"
            if risk_items
            else ""
        )
        cards.append(
            "<section class='stage-card'>"
            f"<div class='stage-index'>{html.escape(str(test_case.get('test_case_id', 'Unknown test case')))}</div>"
            f"<div class='stage-role'>{html.escape(str(test_case.get('title', 'Untitled test case')))}</div>"
            f"<p class='agent-config-text'><strong>Requirement:</strong> {html.escape(str(test_case.get('requirement_id', 'Not linked')))}</p>"
            f"<p class='agent-config-text'><strong>Type:</strong> {html.escape(str(test_case.get('test_type', 'Not set')))}</p>"
            "<div class='io-stack'>"
            "<div class='io-section'>"
            "<div class='log-title'>Steps</div>"
            f"<ul class='log-list'>{step_items}</ul>"
            "</div>"
            "<div class='io-section'>"
            "<div class='log-title'>Expected results</div>"
            f"<ul class='log-list'>{expected_items}</ul>"
            "</div>"
            "<div class='io-section'>"
            "<div class='log-title'>Oracle</div>"
            f"<p class='io-summary'>{html.escape(str(test_case.get('oracle', 'No oracle recorded.')))}</p>"
            "</div>"
            f"{risk_block}"
            "</div>"
            "</section>"
        )
    return (
        "<section class='diagram-card'>"
        "<h3>Planned test cases</h3>"
        "<p class='agent-config-text'>This section shows the actual test cases produced by the Test Design Agent, including steps, expected results, and oracle.</p>"
        "</section>"
        "<div class='stage-grid'>"
        + "".join(cards)
        + "</div>"
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
        timeout_seconds = config.get("timeout_seconds", AGENT_TIMEOUT_SECONDS)
        rows.append(
            "<tr>"
            f"<td>{html.escape(config['agent_name'])}</td>"
            f"<td>{html.escape(config['execution_mode'])}</td>"
            f"<td>{html.escape(str(timeout_seconds))}</td>"
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
        "<table><thead><tr><th>Agent</th><th>Execution mode</th><th>Timeout (s)</th><th>Resolved model</th><th>Directives</th></tr></thead><tbody>"
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
            f"<h3>Backtracking round {iteration}</h3>"
            "<p class='agent-config-text'>Below is the full sequence of agent passes for this backtracking round, with explicit input, output, and routing context.</p>"
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
                    duration_ms=int(trace.get("duration_ms", 0) or 0),
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
    duration_ms: int,
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
    duration_label = f"{duration_ms} ms" if duration_ms > 0 else "under 1 ms"
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
        f"<div class='stage-meta'><strong>Time:</strong> {html.escape(duration_label)}</div>"
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
    launch_kwargs = {
        "server_name": "0.0.0.0",
        "server_port": int(os.getenv("PORT", "7860")),
    }
    if _blocks_support_launch_theming():
        launch_kwargs["theme"] = APP_THEME
        launch_kwargs["css"] = CUSTOM_CSS
    demo.launch(**launch_kwargs)
