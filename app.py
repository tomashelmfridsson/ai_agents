import html
import inspect
import json
import os
import queue
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator
from urllib import error, request

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
from qa_platform.llm_runtime import OLLAMA_MODEL_FAMILY_MAP
from qa_platform.orchestrator import (
    AGENT_TIMEOUT_SECONDS,
    AgentTimeoutError,
    OrchestratorAgent,
    WorkflowCancelledError,
)
from qa_platform.models import AgentRuntimeConfig, RequirementItem, ReviewReport, RunControlConfig, TestCaseDesign
from qa_platform.registry import build_default_agent_registry
from qa_platform.sample_scenarios import (
    DEFAULT_REQUIREMENTS,
    DEFAULT_SCENARIO,
    DEFAULT_TITLE,
    SAMPLE_SCENARIOS,
    load_sample_scenario,
)
from qa_platform.storage import export_run_payload_json, get_db_path, get_export_dir, get_log_dir, save_run
LITERATURE_URL = "https://tomashelmfridsson.github.io/ai_agents/literature-study/"
PROJECT_BRIEF_URL = "https://tomashelmfridsson.github.io/ai_agents/project-brief/"
THEORETICAL_BACKGROUND_URL = "https://tomashelmfridsson.github.io/ai_agents/theoretical-background-and-central-concepts/"
AI_AGENTS_POC_REPORT_URL = "https://tomashelmfridsson.github.io/ai_agents/ai-agents-poc-report/"
LITERATURE_EN_URL = "https://tomashelmfridsson.github.io/ai_agents/literature-study-en/"
PROJECT_BRIEF_EN_URL = "https://tomashelmfridsson.github.io/ai_agents/project-brief-en/"
THEORETICAL_BACKGROUND_EN_URL = "https://tomashelmfridsson.github.io/ai_agents/theoretical-background-and-central-concepts-en/"
AI_AGENTS_POC_REPORT_EN_URL = "https://tomashelmfridsson.github.io/ai_agents/ai-agents-poc-report-en/"
AI_DEVELOPING_GUIDELINES_URL = "https://tomashelmfridsson.github.io/ai_agents/ai-developing-guidelines/"
QA_AGENT_DEVELOPING_REQUIREMENTS_URL = "https://tomashelmfridsson.github.io/ai_agents/qa-agent-developing-requirements/"
DEFAULT_OLLAMA_MODEL_CHOICES = [
    "qwen3:8b",
    "deepseek-r1:8b",
    "gemma3:4b",
    "llama3:latest",
]
EXECUTION_BACKEND_CHOICES = [
    "QA agent service",
    "Custom agent runtime",
]
DEFAULT_QA_AGENT_SERVICE_BASE_URL = os.getenv(
    "QA_AGENT_SERVICE_URL",
    "https://helmfridsson-qa-agent-service.hf.space",
)
ORCHESTRATOR_CONFIG_SPEC = next(spec for spec in AGENT_CONFIG_SPECS if spec[0] == "orchestrator")
WORKER_AGENT_CONFIG_SPECS = [spec for spec in AGENT_CONFIG_SPECS if spec[0] != "orchestrator"]


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


def _build_allowed_file_paths() -> list[str]:
    allowed_roots = {
        ROOT,
        get_log_dir(),
        get_db_path().parent,
        get_export_dir(),
        ROOT / "data" / "exports",
    }
    return sorted(str(path.resolve()) for path in allowed_roots)


def _build_run_summary_panel(
    title: str,
    status_text: str,
    summary_text: str,
    details_html: str = "",
    *,
    open_by_default: bool = True,
    tone: str = "default",
) -> str:
    open_attr = " open" if open_by_default else ""
    card_class = "diagram-card error-card" if tone == "error" else "diagram-card"
    status_class = "result-status error-status" if tone == "error" else "result-status"
    summary_class = "agent-config-text error-text" if tone == "error" else "agent-config-text"
    return (
        f"<section class='{card_class}'>"
        f"<details class='stage-toggle'{open_attr}>"
        "<summary>"
        "<div class='stage-head'>"
        "<div><div class='stage-index'>Run</div><div class='stage-role'>Run summary</div></div>"
        "<div class='stage-meta'>Expanded by default. Collapse when you want more room for runtime activity and results.</div>"
        "<div class='stage-chevron'></div>"
        "</div>"
        "</summary>"
        "<div class='stage-body'>"
        f"<h3>{html.escape(title)}</h3>"
        f"<p class='{status_class}'>{html.escape(status_text)}</p>"
        f"<p class='{summary_class}'>{html.escape(summary_text)}</p>"
        f"{details_html}"
        "</div>"
        "</details>"
        "</section>"
    )


def _build_collapsible_report_section(
    section_title: str,
    summary_text: str,
    body_html: str,
    *,
    section_index: str = "Section",
    open_by_default: bool = False,
) -> str:
    open_attr = " open" if open_by_default else ""
    return (
        "<section class='diagram-card'>"
        f"<details class='stage-toggle'{open_attr}>"
        "<summary>"
        "<div class='stage-head'>"
        f"<div><div class='stage-index'>{html.escape(section_index)}</div><div class='stage-role'>{html.escape(section_title)}</div></div>"
        f"<div class='stage-meta'>{html.escape(summary_text)}</div>"
        "<div class='stage-chevron'></div>"
        "</div>"
        "</summary>"
        f"<div class='stage-body'>{body_html}</div>"
        "</details>"
        "</section>"
    )


def build_idle_status() -> str:
    return _build_run_summary_panel(
        "Run summary",
        "Ready to run.",
        (
            "Start the workflow to execute the configured agents and save a traceable run log. "
            "After the first run, this panel will show status, progress, resolved models, and saved run details."
        ),
    )


def build_idle_report() -> str:
    return ""


def build_idle_runtime_timeline() -> str:
    return (
        "<section class='diagram-card'>"
        "<details class='stage-toggle' open>"
        "<summary>"
        "<div class='stage-head'>"
        "<div><div class='stage-index'>Runtime</div><div class='stage-role'>Runtime activity</div></div>"
        "<div class='stage-meta'>Expand or collapse live runtime details.</div>"
        "<div class='stage-chevron'></div>"
        "</div>"
        "</summary>"
        "<div class='stage-body'>"
        "<p class='agent-config-text'>No runtime activity yet. After a run starts, this panel will show agent events, model names, and a live tail of the current run log.</p>"
        "</div>"
        "</details>"
        "</section>"
    )


def build_idle_memory_panel() -> str:
    return (
        "<section class='diagram-card'>"
        "<details class='stage-toggle'>"
        "<summary>"
        "<div class='stage-head'>"
        "<div><div class='stage-index'>Memory</div><div class='stage-role'>Working memory</div></div>"
        "<div class='stage-meta'>Collapsed by default. Expand when you want to inspect shared and private memory.</div>"
        "<div class='stage-chevron'></div>"
        "</div>"
        "</summary>"
        "<div class='stage-body'>"
        "<p class='agent-config-text'>No shared memory has been recorded yet. After a run starts, this panel will show shared keys, per-agent notes, and the memory timeline.</p>"
        "</div>"
        "</details>"
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
    return _build_run_summary_panel(
        "Run summary",
        "Run stopped because of an error.",
        message,
        tone="error",
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
    return _build_run_summary_panel(
        "Run summary",
        "Run stopped because of an error.",
        message,
        f"<ul class='summary-list'>{''.join(items)}</ul>" + partial_results,
        tone="error",
    )


def _parse_event_timestamp(raw_value: object) -> datetime | None:
    if not raw_value:
        return None
    text = str(raw_value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _format_clock_time(raw_value: object) -> str:
    timestamp = _parse_event_timestamp(raw_value)
    return timestamp.strftime("%H:%M:%S") if timestamp else "-"


def _format_elapsed_ms(duration_ms: int) -> str:
    if duration_ms < 1000:
        return f"{duration_ms} ms"
    seconds = duration_ms / 1000
    return f"{seconds:.1f}s"


def _get_active_agent_timing(runtime_events: list[dict[str, object]]) -> dict[str, object] | None:
    active_starts: dict[tuple[object, object, object], dict[str, object]] = {}
    for event in runtime_events:
        key = (
            event.get("iteration"),
            event.get("stage_index"),
            event.get("agent_name"),
        )
        event_type = str(event.get("event_type", ""))
        if event_type == "stage_started":
            active_starts[key] = event
        elif event_type == "stage_completed":
            active_starts.pop(key, None)

    if not active_starts:
        return None

    latest_key, latest_event = max(
        active_starts.items(),
        key=lambda item: _parse_event_timestamp(item[1].get("timestamp")) or datetime.min,
    )
    del latest_key
    started_at = _parse_event_timestamp(latest_event.get("timestamp"))
    if not started_at:
        return None
    elapsed_ms = max(0, int((datetime.now() - started_at).total_seconds() * 1000))
    return {
        "agent_name": latest_event.get("agent_name", "-"),
        "iteration": latest_event.get("iteration", "-"),
        "stage_index": latest_event.get("stage_index", "-"),
        "started_at": latest_event.get("timestamp"),
        "elapsed_ms": elapsed_ms,
    }


def build_running_status(runtime_events: list[dict[str, object]]) -> str:
    return build_running_summary_panel(runtime_events, None)


def _extract_latest_runtime_metrics(runtime_events: list[dict[str, object]]) -> dict[str, object]:
    for event in reversed(runtime_events):
        metrics = event.get("metrics")
        if isinstance(metrics, dict):
            return metrics
    return {}


def _build_feedback_usage_lines(metrics: dict[str, object]) -> list[str]:
    if not metrics:
        return []
    current_round = metrics.get("current_round", "-")
    max_rounds = metrics.get("max_rounds", "-")
    total_feedback = metrics.get("total_feedback_messages", 0)
    max_feedback = metrics.get("max_feedback_messages", 0)
    max_pair_feedback = metrics.get("max_feedback_per_agent_pair", 0)
    lines = [
        f"<li>Current round: {html.escape(str(current_round))}/{html.escape(str(max_rounds))}</li>",
        f"<li>Feedback handoffs used: {html.escape(str(total_feedback))}/{html.escape(str(max_feedback))}</li>",
        f"<li>Per-pair feedback cap: {html.escape(str(max_pair_feedback))}</li>",
    ]
    pair_counts = metrics.get("pair_feedback_counts")
    if isinstance(pair_counts, dict) and pair_counts:
        formatted_counts = ", ".join(
            f"{pair}: {count}" for pair, count in sorted(pair_counts.items(), key=lambda item: str(item[0]))
        )
        lines.append(f"<li>Feedback by pair: {html.escape(formatted_counts)}</li>")
    return lines


def _read_int(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _extract_runtime_token_totals(runtime_events: list[dict[str, object]]) -> dict[str, int]:
    totals = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }
    found = False
    for event in runtime_events:
        if event.get("event_type") != "stage_completed":
            continue
        trace = event.get("trace")
        if not isinstance(trace, dict):
            continue
        prompt_tokens = _read_int(trace.get("prompt_tokens"))
        completion_tokens = _read_int(trace.get("completion_tokens"))
        total_tokens = _read_int(trace.get("total_tokens"))
        if prompt_tokens is None and completion_tokens is None and total_tokens is None:
            continue
        if total_tokens is None and (prompt_tokens is not None or completion_tokens is not None):
            total_tokens = (prompt_tokens or 0) + (completion_tokens or 0)
        totals["prompt_tokens"] += prompt_tokens or 0
        totals["completion_tokens"] += completion_tokens or 0
        totals["total_tokens"] += total_tokens or 0
        found = True
    return totals if found else {}


def build_running_summary_panel(runtime_events: list[dict[str, object]], log_path: str | None = None) -> str:
    last_message = (
        str(runtime_events[-1].get("message", "Workflow is running."))
        if runtime_events
        else "Workflow is starting."
    )
    completed_count = sum(1 for event in runtime_events if event.get("event_type") == "stage_completed")
    active_timing = _get_active_agent_timing(runtime_events)
    metrics = _extract_latest_runtime_metrics(runtime_events)
    timing_items = []
    if active_timing:
        timing_items.extend(
            [
                f"<li>Current agent: {html.escape(str(active_timing['agent_name']))}</li>",
                f"<li>Started at: {html.escape(_format_clock_time(active_timing['started_at']))}</li>",
                f"<li>Running for: {html.escape(_format_elapsed_ms(int(active_timing['elapsed_ms'])))}</li>",
            ]
        )
    last_agent = str(runtime_events[-1].get("agent_name", "-")) if runtime_events else "-"
    last_event = str(runtime_events[-1].get("event_type", "-")) if runtime_events else "-"
    last_timestamp = _format_clock_time(runtime_events[-1].get("timestamp")) if runtime_events else "-"
    active_timing = _get_active_agent_timing(runtime_events)
    token_totals = _extract_runtime_token_totals(runtime_events)
    items = [
        f"<li>Latest agent: {html.escape(last_agent)}</li>",
        f"<li>Latest event: {html.escape(last_event)}</li>",
        f"<li>Latest event time: {html.escape(last_timestamp)}</li>",
        f"<li>Runtime events recorded: {len(runtime_events)}</li>",
        f"<li>Live log file: {html.escape(log_path or 'not available')}</li>",
    ]
    if active_timing:
        items.extend(
            [
                f"<li>Current agent started: {html.escape(_format_clock_time(active_timing['started_at']))}</li>",
                f"<li>Current agent running time: {html.escape(_format_elapsed_ms(int(active_timing['elapsed_ms'])))}</li>",
            ]
        )
    usage_lines = _build_feedback_usage_lines(metrics)
    details_html = (
        f"<p class='agent-config-text'>Completed stages so far: {completed_count}.</p>"
        + (f"<ul class='summary-list'>{''.join(timing_items)}</ul>" if timing_items else "")
        + (
            "<p class='agent-config-text'>Live workflow limits and usage.</p>"
            f"<ul class='summary-list'>{''.join(usage_lines)}</ul>"
            if usage_lines
            else ""
        )
        + (
            "<p class='agent-config-text'>Accumulated model tokens from completed qa-agent-service worker calls.</p>"
            f"<ul class='summary-list'>"
            f"<li>Prompt tokens: {html.escape(str(token_totals['prompt_tokens']))}</li>"
            f"<li>Completion tokens: {html.escape(str(token_totals['completion_tokens']))}</li>"
            f"<li>Total tokens: {html.escape(str(token_totals['total_tokens']))}</li>"
            "</ul>"
            if token_totals
            else ""
        )
        + "<p class='agent-config-text'>Workflow is in progress. This panel updates as agents start, complete, or route work.</p>"
        + f"<ul class='summary-list'>{''.join(items)}</ul>"
    )
    return _build_run_summary_panel(
        "Run summary",
        "Workflow is running.",
        last_message,
        details_html,
    )


def build_running_report(runtime_events: list[dict[str, object]]) -> str:
    del runtime_events
    return ""


def build_running_report_with_log(runtime_events: list[dict[str, object]], log_path: str | None) -> str:
    del runtime_events, log_path
    return ""


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
        "<details class='stage-toggle'>"
        "<summary>"
        "<div class='stage-head'>"
        "<div><div class='stage-index'>Memory</div><div class='stage-role'>Working memory</div></div>"
        "<div class='stage-meta'>Collapsed by default. Expand when you want to inspect shared and private memory.</div>"
        "<div class='stage-chevron'></div>"
        "</div>"
        "</summary>"
        "<div class='stage-body'>"
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
        "</div>"
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


def _normalize_service_base_url(base_url: str) -> str:
    normalized = (base_url or DEFAULT_QA_AGENT_SERVICE_BASE_URL).strip().rstrip("/")
    if not normalized:
        normalized = DEFAULT_QA_AGENT_SERVICE_BASE_URL
    return normalized


def _serialize_shared_memory_for_service(run_session) -> dict[str, object]:
    if run_session is None:
        return {"facts": {}, "assumptions": [], "decisions": [], "timeline": []}
    shared = run_session.working_memory.shared if getattr(run_session, "working_memory", None) else {}
    timeline = run_session.working_memory.timeline if getattr(run_session, "working_memory", None) else []
    return {
        "facts": dict(shared),
        "assumptions": [],
        "decisions": [],
        "timeline": [{"note": str(item)} for item in timeline],
    }


def _serialize_agent_private_memory_for_service(run_session, agent_key: str) -> dict[str, object]:
    if run_session is None or not getattr(run_session, "working_memory", None):
        return {"data": {}}
    private_data = run_session.working_memory.agent_private.get(agent_key, {})
    return {"data": dict(private_data) if isinstance(private_data, dict) else {}}


def _build_service_model_config(runtime_config: AgentRuntimeConfig | None) -> dict[str, object] | None:
    if not runtime_config or runtime_config.execution_mode != "LLM-backed":
        return None
    provider = (runtime_config.provider_strategy or "").strip()
    if provider.startswith("HF "):
        provider = "huggingface"
    elif provider == "Ollama local":
        provider = "ollama"
    elif provider == "Custom OpenAI-compatible":
        provider = "openai"
    else:
        provider = provider.lower() or "huggingface"
    return {
        "provider": provider,
        "model_id": runtime_config.model_id,
        "temperature": 0.2,
        "timeout_seconds": runtime_config.timeout_seconds,
    }


def _invoke_qa_agent_service(
    *,
    base_url: str,
    service_agent_key: str,
    run_session,
    iteration: int,
    stage_index: int,
    agent_input: dict[str, object],
    runtime_config: AgentRuntimeConfig | None,
    output_contract: str,
) -> dict[str, object]:
    payload = {
        "run_id": f"qa-workbench-{uuid.uuid4().hex[:12]}",
        "iteration": iteration,
        "stage_index": stage_index,
        "scenario": {
            "title": getattr(run_session, "title", "QA workbench run"),
            "source_requirements": getattr(run_session, "source_requirements", ""),
        },
        "agent_input": agent_input,
        "shared_memory": _serialize_shared_memory_for_service(run_session),
        "agent_private_memory": _serialize_agent_private_memory_for_service(run_session, service_agent_key),
        "instructions": {
            "additional_directives": runtime_config.directives if runtime_config else "",
        },
        "model_config": _build_service_model_config(runtime_config),
        "output_contract": output_contract,
    }
    endpoint = f"{_normalize_service_base_url(base_url)}/agents/{service_agent_key}/invoke"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    http_request = request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with request.urlopen(http_request, timeout=(runtime_config.timeout_seconds if runtime_config else 150)) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise LLMRuntimeError(
            f"QA agent service call failed for {service_agent_key} with HTTP {exc.code}. {details}"
        ) from exc
    except error.URLError as exc:
        raise LLMRuntimeError(
            f"QA agent service at {_normalize_service_base_url(base_url)} could not be reached. {exc.reason}"
        ) from exc


def _apply_service_memory_updates(run_session, service_agent_key: str, memory_updates: dict[str, object]) -> None:
    if run_session is None or not memory_updates:
        return
    facts = memory_updates.get("facts")
    if isinstance(facts, dict):
        for key, value in facts.items():
            run_session.working_memory.write_shared(str(key), value, author=service_agent_key)
    assumptions = memory_updates.get("assumptions")
    if isinstance(assumptions, list):
        run_session.working_memory.write_agent(service_agent_key, "assumptions", list(assumptions))
    decisions = memory_updates.get("decisions")
    if isinstance(decisions, list):
        run_session.working_memory.write_agent(service_agent_key, "decisions", list(decisions))
    private_data = memory_updates.get("agent_private")
    if isinstance(private_data, dict):
        for key, value in private_data.items():
            run_session.working_memory.write_agent(service_agent_key, str(key), value)
    timeline = memory_updates.get("timeline")
    if isinstance(timeline, list):
        for item in timeline:
            run_session.working_memory.add_note(str(item))


def _extract_service_token_usage(response: dict[str, object]) -> dict[str, int | None]:
    token_usage = response.get("token_usage")
    if not isinstance(token_usage, dict):
        return {}
    prompt_tokens = _read_int(token_usage.get("prompt_tokens"))
    completion_tokens = _read_int(token_usage.get("completion_tokens"))
    total_tokens = _read_int(token_usage.get("total_tokens"))
    if total_tokens is None and (prompt_tokens is not None or completion_tokens is not None):
        total_tokens = (prompt_tokens or 0) + (completion_tokens or 0)
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def _format_service_review_finding(finding: dict[str, object]) -> str:
    severity = str(finding.get("severity", ""))
    target_type = str(finding.get("target_type", ""))
    target_id = str(finding.get("target_id", ""))
    issue = str(finding.get("issue", "")).strip()
    recommendation = str(finding.get("recommendation", "")).strip()
    return " | ".join(
        part for part in [
            f"[{severity}]" if severity else "",
            f"{target_type}:{target_id}" if target_type or target_id else "",
            issue,
            f"Recommendation: {recommendation}" if recommendation else "",
        ] if part
    )


class QAAgentServiceRequirementsAdapter:
    name = "Requirements Analyst"

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.last_execution: dict[str, object] = {}

    def analyze(
        self,
        requirements_text: str,
        feedback_messages: list[str] | None = None,
        runtime_config: AgentRuntimeConfig | None = None,
        run_session=None,
    ):
        feedback_messages = feedback_messages or []
        response = _invoke_qa_agent_service(
            base_url=self.base_url,
            service_agent_key="requirements_analyst",
            run_session=run_session,
            iteration=1,
            stage_index=1,
            agent_input={"feedback_messages": list(feedback_messages)},
            runtime_config=runtime_config,
            output_contract="requirements_analyst.v1",
        )
        if response.get("status") != "completed":
            errors = response.get("errors") or []
            raise LLMRuntimeError(
                "QA agent service requirements_analyst failed: "
                + "; ".join(str(item.get("message", "unknown error")) for item in errors)
            )
        _apply_service_memory_updates(run_session, "requirements_analyst", response.get("memory_updates", {}))
        raw_output = response.get("output", {})
        raw_requirements = raw_output.get("requirements") or []
        items = [
            RequirementItem(
                requirement_id=str(item.get("requirement_id", f"REQ-{index:03d}")),
                original_text=str(item.get("original_text", "")),
                normalized_text=str(item.get("normalized_text", "")),
                priority=str(item.get("priority", "medium")),
                acceptance_criteria=[str(value) for value in item.get("acceptance_criteria", [])],
                assumptions=[str(value) for value in item.get("assumptions", [])],
            )
            for index, item in enumerate(raw_requirements, start=1)
        ]
        if run_session is not None:
            run_session.working_memory.write_agent(
                "requirements_analyst",
                "service_output",
                raw_output,
            )
        self.last_execution = {
            "mode": "qa_agent_service",
            "reasoning_source": "qa_agent_service",
            "notes": [str(item) for item in raw_output.get("decision_basis", [])],
            "llm_used": True,
            "metadata": {"base_url": _normalize_service_base_url(self.base_url)},
            "validation_findings": [str(item.get("message", "")) for item in response.get("errors", [])],
            "contract_version": "requirements_analyst.v1",
            "token_usage": _extract_service_token_usage(response),
        }
        return items


class QAAgentServiceTestDesignAdapter:
    name = "Test Design Agent"

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.last_execution: dict[str, object] = {}

    def design(
        self,
        requirements,
        feedback_messages: list[str] | None = None,
        runtime_config: AgentRuntimeConfig | None = None,
        run_session=None,
    ):
        feedback_messages = feedback_messages or []
        requirements_service_output = {}
        if run_session is not None and getattr(run_session, "working_memory", None):
            requirements_service_output = run_session.working_memory.agent_private.get("requirements_analyst", {}).get("service_output", {})
        response = _invoke_qa_agent_service(
            base_url=self.base_url,
            service_agent_key="test_designer",
            run_session=run_session,
            iteration=1,
            stage_index=2,
            agent_input={
                "requirements": requirements_service_output.get("requirements", [asdict(item) for item in requirements]),
                "requirements_analysis": requirements_service_output,
                "feedback_messages": list(feedback_messages),
            },
            runtime_config=runtime_config,
            output_contract="test_designer.v1",
        )
        if response.get("status") != "completed":
            errors = response.get("errors") or []
            raise LLMRuntimeError(
                "QA agent service test_designer failed: "
                + "; ".join(str(item.get("message", "unknown error")) for item in errors)
            )
        _apply_service_memory_updates(run_session, "test_designer", response.get("memory_updates", {}))
        raw_output = response.get("output", {})
        raw_designs = raw_output.get("test_designs") or []
        designs = []
        for item in raw_designs:
            requirement_ids = [str(value) for value in item.get("requirement_ids", [])]
            risks = [str(value) for value in item.get("risks", [])]
            if len(requirement_ids) > 1:
                risks = [f"Additional requirement links: {', '.join(requirement_ids[1:])}", *risks]
            oracle = item.get("oracle") or {}
            designs.append(
                TestCaseDesign(
                    test_case_id=str(item.get("test_case_id", "")),
                    requirement_id=(requirement_ids[0] if requirement_ids else "REQ-UNKNOWN"),
                    title=str(item.get("title", "")),
                    test_type=str(item.get("test_type", "other")),
                    preconditions=[str(value) for value in item.get("preconditions", [])],
                    steps=[str(value) for value in item.get("steps", [])],
                    expected_results=[str(value) for value in item.get("expected_results", [])],
                    oracle=str(oracle.get("description", "")),
                    risks=risks,
                )
            )
        if run_session is not None:
            run_session.working_memory.write_agent("test_designer", "service_output", raw_output)
        self.last_execution = {
            "mode": "qa_agent_service",
            "reasoning_source": "qa_agent_service",
            "notes": [str(item) for item in raw_output.get("decision_basis", [])],
            "llm_used": True,
            "metadata": {"base_url": _normalize_service_base_url(self.base_url)},
            "validation_findings": [str(item.get("message", "")) for item in response.get("errors", [])],
            "contract_version": "test_designer.v1",
            "token_usage": _extract_service_token_usage(response),
        }
        return designs


class QAAgentServiceReviewAdapter:
    name = "Review Agent"

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.last_execution: dict[str, object] = {}

    def review(
        self,
        requirements,
        designs,
        runtime_config: AgentRuntimeConfig | None = None,
        run_session=None,
    ):
        requirements_service_output = {}
        design_service_output = {}
        if run_session is not None and getattr(run_session, "working_memory", None):
            requirements_service_output = run_session.working_memory.agent_private.get("requirements_analyst", {}).get("service_output", {})
            design_service_output = run_session.working_memory.agent_private.get("test_designer", {}).get("service_output", {})
        response = _invoke_qa_agent_service(
            base_url=self.base_url,
            service_agent_key="reviewer",
            run_session=run_session,
            iteration=1,
            stage_index=3,
            agent_input={
                "requirements": requirements_service_output.get("requirements", [asdict(item) for item in requirements]),
                "requirements_analysis": requirements_service_output,
                "test_designs": design_service_output.get("test_designs", []),
                "test_design": design_service_output,
            },
            runtime_config=runtime_config,
            output_contract="reviewer.v1",
        )
        if response.get("status") != "completed":
            errors = response.get("errors") or []
            raise LLMRuntimeError(
                "QA agent service reviewer failed: "
                + "; ".join(str(item.get("message", "unknown error")) for item in errors)
            )
        _apply_service_memory_updates(run_session, "reviewer", response.get("memory_updates", {}))
        raw_output = response.get("output", {})
        raw_review = raw_output.get("review") or {}
        review = ReviewReport(
            approved=bool(raw_review.get("approved", False)),
            coverage_ratio=float(raw_review.get("coverage_ratio", 0.0)),
            findings=[_format_service_review_finding(item) for item in raw_review.get("findings", [])],
            improvement_actions=[str(item) for item in raw_review.get("improvement_actions", [])],
        )
        self.last_execution = {
            "mode": "qa_agent_service",
            "reasoning_source": "qa_agent_service",
            "notes": [str(item) for item in raw_output.get("decision_basis", [])],
            "llm_used": True,
            "metadata": {"base_url": _normalize_service_base_url(self.base_url)},
            "validation_findings": [str(item.get("message", "")) for item in response.get("errors", [])],
            "contract_version": "reviewer.v1",
            "token_usage": _extract_service_token_usage(response),
        }
        return review


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


def build_backend_agent_runtime_configs(
    execution_backend: str,
    qa_agent_service_base_url: str,
    *agent_values: str,
) -> list[AgentRuntimeConfig]:
    agent_configs = build_agent_runtime_configs(*agent_values)
    if execution_backend != "QA agent service":
        return agent_configs
    normalized_url = _normalize_service_base_url(qa_agent_service_base_url)
    service_backed = []
    for config in agent_configs:
        if config.agent_key == "orchestrator":
            service_backed.append(config)
            continue
        service_backed.append(
            AgentRuntimeConfig(
                agent_key=config.agent_key,
                agent_name=config.agent_name,
                execution_mode="QA agent service",
                timeout_seconds=config.timeout_seconds,
                provider_strategy="qa-agent-service",
                model_family="",
                model_override="",
                model_id=f"Managed by qa-agent-service at {normalized_url}",
                directives=config.directives,
            )
        )
    return service_backed


def build_orchestrator_for_backend(execution_backend: str, qa_agent_service_base_url: str) -> OrchestratorAgent:
    if execution_backend != "QA agent service":
        return OrchestratorAgent()
    registry = build_default_agent_registry()
    registry.set_agent("requirements_analyst", QAAgentServiceRequirementsAdapter(qa_agent_service_base_url))
    registry.set_agent("test_design", QAAgentServiceTestDesignAdapter(qa_agent_service_base_url))
    registry.set_agent("review", QAAgentServiceReviewAdapter(qa_agent_service_base_url))
    return OrchestratorAgent(registry=registry)


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
) -> Iterator[tuple[str, str, Any, str, str, str, Any]]:
    execution_backend = "Custom agent runtime"
    qa_agent_service_base_url = DEFAULT_QA_AGENT_SERVICE_BASE_URL
    parsed_agent_values = list(agent_values)
    if parsed_agent_values and parsed_agent_values[0] in EXECUTION_BACKEND_CHOICES:
        execution_backend = str(parsed_agent_values.pop(0))
        if parsed_agent_values:
            qa_agent_service_base_url = str(parsed_agent_values.pop(0))
    normalized_title = (title or "Untitled demo").strip()
    normalized_requirements = (requirements or "").strip()
    if not normalized_requirements:
        message = "Requirements saknas. Fyll i minst ett krav innan du kör workflow."
        yield (
            build_error_report(message),
            "",
            None,
            build_idle_runtime_timeline(),
            build_idle_memory_panel(),
            build_interaction_feedback("Run blocked. Add requirements before starting the workflow.", "warning"),
            None,
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
    agent_configs = build_backend_agent_runtime_configs(
        execution_backend,
        qa_agent_service_base_url,
        *parsed_agent_values,
    )
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
        build_running_summary_panel(runtime_events, str(live_log_path)),
        build_live_trace_overview(completed_stage_traces, [config.__dict__ for config in agent_configs]),
        gr.update(value=str(live_log_path)),
        build_idle_runtime_timeline(),
        build_idle_memory_panel(),
        build_interaction_feedback(
            "Workflow starting. Press Stop workflow to stop after the current agent pass."
        ),
        None,
    )

    def handle_runtime_event(event: dict[str, object]) -> None:
        event_queue.put(("event", event))

    def run_workflow() -> None:
        try:
            worker_state["result"] = build_orchestrator_for_backend(
                execution_backend,
                qa_agent_service_base_url,
            ).process(
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
                    build_running_summary_panel(runtime_events, str(live_log_path)),
                    build_live_trace_overview(completed_stage_traces, [config.__dict__ for config in agent_configs]),
                    gr.update(value=str(live_log_path)),
                    build_runtime_timeline(runtime_events, str(live_log_path)),
                    build_memory_panel(latest_memory_snapshot),
                    build_interaction_feedback("Workflow is running."),
                    None,
                )
                emitted = True
        if worker_state["done"] and event_queue.empty():
            break
        if stop_event.is_set() and not stop_notice_emitted:
            stop_notice_emitted = True
            yield (
                build_running_summary_panel(runtime_events, str(live_log_path)),
                build_live_trace_overview(completed_stage_traces, [config.__dict__ for config in agent_configs]),
                gr.update(value=str(live_log_path)),
                build_runtime_timeline(runtime_events, str(live_log_path)),
                build_memory_panel(latest_memory_snapshot),
                build_interaction_feedback(
                    "Stop requested. Waiting for the current agent pass to finish.",
                    "warning",
                ),
                None,
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
            build_error_report(message, runtime_events, agent_configs, str(live_log_path), completed_stage_traces),
            "",
            gr.update(value=str(live_log_path)),
            build_runtime_timeline(runtime_events, str(live_log_path)),
            build_memory_panel(latest_memory_snapshot),
            build_interaction_feedback("Workflow stopped.", "warning"),
            None,
        )
        return
    if isinstance(error, LLMRuntimeError):
        message = format_user_error(str(error))
        yield (
            build_error_report(message, runtime_events, agent_configs, str(live_log_path), completed_stage_traces),
            "",
            gr.update(value=str(live_log_path)),
            build_runtime_timeline(runtime_events, str(live_log_path)),
            build_memory_panel(latest_memory_snapshot),
            build_interaction_feedback("Workflow stopped because of an LLM/backend error.", "warning"),
            None,
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
            build_error_report(message, runtime_events, agent_configs, str(live_log_path), completed_stage_traces),
            "",
            gr.update(value=str(live_log_path)),
            build_runtime_timeline(runtime_events, str(live_log_path)),
            build_memory_panel(latest_memory_snapshot),
            build_interaction_feedback("Workflow stopped because an agent hit its timeout.", "warning"),
            None,
        )
        return
    if error is not None:
        raise error

    result = worker_state["result"]
    if result is None:
        raise RuntimeError("Workflow finished without result or error.")
    payload = result.to_dict()
    payload["execution_backend"] = execution_backend
    payload["qa_agent_service_base_url"] = (
        _normalize_service_base_url(qa_agent_service_base_url)
        if execution_backend == "QA agent service"
        else ""
    )
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
        f"<li>Feedback handoffs used: {payload.get('total_feedback_messages', 0)}/{run_controls.max_feedback_messages}.</li>",
        f"<li>Coverage ratio: {payload['review']['coverage_ratio']}.</li>",
        f"<li>Approved: {'yes' if payload['review']['approved'] else 'no'}.</li>",
        f"<li>Findings: {findings_count}. Improvement actions: {improvement_count}.</li>",
        f"<li>Log file: {html.escape(payload['log_path'])}</li>",
    ]
    if llm_note:
        status_items.append(f"<li>{html.escape(llm_note.strip())}</li>")
    run_export = export_run_payload_json(payload, int(payload["run_id"]))
    status = _build_run_summary_panel(
        "Run summary",
        f"Saved as run #{payload['run_id']}.",
        "Workflow finished and the run was stored successfully.",
        "<ul class='summary-list'>" + "".join(status_items) + "</ul>",
    )
    yield (
        status,
        build_workflow_report(payload),
        gr.update(value=saved_run.log_path),
        build_runtime_timeline(runtime_events, str(live_log_path)),
        build_memory_panel((payload.get("run_session") or {}).get("working_memory")),
        build_interaction_feedback(f"Workflow finished. Run #{payload['run_id']} was saved.", "success"),
        gr.update(value=run_export.json_path),
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

    active_timing = _get_active_agent_timing(runtime_events)
    active_lookup: dict[tuple[object, object, object], int] = {}
    started_lookup: dict[tuple[object, object, object], object] = {}
    for event in runtime_events:
        if str(event.get("event_type", "")) == "stage_started":
            started_lookup[
                (
                    event.get("iteration"),
                    event.get("stage_index"),
                    event.get("agent_name"),
                )
            ] = event.get("timestamp")
    if active_timing:
        active_lookup[
            (
                active_timing["iteration"],
                active_timing["stage_index"],
                active_timing["agent_name"],
            )
        ] = int(active_timing["elapsed_ms"])

    rows = []
    for event in runtime_events:
        duration_ms = int(event.get("duration_ms", 0) or 0)
        elapsed_label = "-"
        if str(event.get("event_type", "")) == "stage_completed":
            elapsed_label = _format_elapsed_ms(duration_ms)
        elif str(event.get("event_type", "")) == "stage_started":
            active_duration = active_lookup.get(
                (
                    event.get("iteration"),
                    event.get("stage_index"),
                    event.get("agent_name"),
                )
            )
            if active_duration is not None:
                elapsed_label = _format_elapsed_ms(active_duration)
        model_label = str(event.get("model_id", "-"))
        event_key = (
            event.get("iteration"),
            event.get("stage_index"),
            event.get("agent_name"),
        )
        started_value = (
            started_lookup.get(event_key)
            if str(event.get("event_type", "")) == "stage_completed"
            else event.get("timestamp")
        )
        finished_value = (
            event.get("timestamp")
            if str(event.get("event_type", "")) == "stage_completed"
            else event.get("finished_at")
        )
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(event.get('iteration', '')))}</td>"
            f"<td>{html.escape(str(event.get('stage_index', '')))}</td>"
            f"<td>{html.escape(str(event.get('agent_name', '')))}</td>"
            f"<td>{html.escape(model_label)}</td>"
            f"<td>{html.escape(str(event.get('event_type', '')))}</td>"
            f"<td>{html.escape(_format_clock_time(started_value))}</td>"
            f"<td>{html.escape(_format_clock_time(finished_value))}</td>"
            f"<td>{html.escape(elapsed_label)}</td>"
            f"<td>{html.escape(str(event.get('message', '')))}</td>"
            "</tr>"
        )
    return (
        "<section class='diagram-card'>"
        "<details class='stage-toggle' open>"
        "<summary>"
        "<div class='stage-head'>"
        "<div><div class='stage-index'>Runtime</div><div class='stage-role'>Runtime activity</div></div>"
        "<div class='stage-meta'>Expand or collapse live runtime details.</div>"
        "<div class='stage-chevron'></div>"
        "</div>"
        "</summary>"
        "<div class='stage-body'>"
        "<p class='agent-config-text'>This panel shows which agent was active, when each agent pass started and finished, and how long the current or completed pass has run.</p>"
        "<div class='table-scroll'><table><thead><tr><th>Cycle</th><th>Stage</th><th>Agent</th><th>Model</th><th>Event</th><th>Started</th><th>Finished</th><th>Elapsed</th><th>Message</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
        "</div>"
        "</details>"
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
        resolved = OLLAMA_MODEL_FAMILY_MAP.get(model_family, model_family)
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


def toggle_llm_configuration_fields(execution_mode: str) -> tuple[dict, dict, dict, dict, dict, dict]:
    is_llm = execution_mode == "LLM-backed"
    return (
        gr.update(visible=is_llm),
        gr.update(visible=is_llm),
        gr.update(visible=is_llm),
        gr.update(visible=is_llm),
        gr.update(visible=is_llm),
        gr.update(visible=True),
    )


def toggle_execution_backend_sections(execution_backend: str) -> tuple[dict, dict, dict]:
    service_selected = execution_backend == "QA agent service"
    return (
        gr.update(visible=service_selected),
        gr.update(visible=not service_selected),
        gr.update(visible=not service_selected),
    )


def build_pipeline_visualization_section() -> str:
    return """
    <section class='diagram-card'>
      <div class='solution-callout'>
        <div class='solution-callout-label'>Alternative solution</div>
        <a href='https://huggingface.co/spaces/helmfridsson/qa-agent-langgraph' target='_blank' rel='noreferrer'>
          QA Agent LangGraph
        </a>
        <p>Used as a comparison track for graph-based orchestration where node transitions, state handling, and flow control are more explicit than in the orchestrator-led setup in this app.</p>
      </div>
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
    .doc-pill-button:hover,
    .doc-pill-button:focus-visible,
    .doc-pill-button button:hover {
      background: linear-gradient(180deg, #9f4220, #7f2b10) !important;
      border-color: rgba(86, 27, 8, 1);
    }
    .doc-library {
      display: grid;
      gap: 12px;
    }
    .doc-row {
      display: grid;
      grid-template-columns: minmax(0, 1.25fr) auto;
      gap: 12px;
      align-items: center;
      padding: 12px 14px;
      border-radius: 20px;
      border: 1px solid rgba(29, 20, 13, 0.12);
      background: rgba(255, 251, 245, 0.72);
    }
    .doc-copy {
      display: grid;
      gap: 4px;
    }
    .doc-copy strong {
      color: #160e09 !important;
      font-size: 1rem;
    }
    .doc-copy span {
      color: #4a3b31 !important;
      font-size: 0.92rem;
      line-height: 1.4;
      font-weight: 600;
    }
    .doc-actions,
    .doc-tail {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .doc-actions {
      justify-content: flex-end;
    }
    .doc-tail {
      justify-content: flex-start;
    }
    .app-tabs [role="tablist"] {
      gap: 8px;
      border-bottom: 1px solid rgba(29, 20, 13, 0.14);
      margin-bottom: 16px;
      padding-bottom: 8px;
    }
    .app-tabs {
      margin-top: 10px;
    }
    .app-tabs [role="tab"] {
      border-radius: 999px !important;
      border: 1px solid rgba(29, 20, 13, 0.16) !important;
      background: rgba(255, 250, 243, 0.98) !important;
      color: var(--app-ink) !important;
      font-weight: 700 !important;
      padding: 8px 14px !important;
    }
    .app-tabs [role="tab"][aria-selected="true"] {
      background: linear-gradient(135deg, rgba(143, 53, 24, 0.14), rgba(203, 145, 50, 0.18)) !important;
      border-color: rgba(143, 53, 24, 0.28) !important;
    }
    .solution-callout {
      margin-bottom: 18px;
      padding: 16px 18px;
      border-radius: 18px;
      border: 1px solid rgba(29, 20, 13, 0.16);
      background: linear-gradient(180deg, rgba(255, 251, 246, 0.98), rgba(243, 232, 219, 0.98));
    }
    .solution-callout-label {
      margin-bottom: 6px;
      color: var(--app-accent) !important;
      font-size: 0.76rem;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      font-weight: 800;
    }
    .solution-callout a {
      color: #160e09 !important;
      font-size: 1.05rem;
      font-weight: 800;
      text-decoration: none;
    }
    .solution-callout p {
      margin: 8px 0 0;
      color: var(--app-muted) !important;
      line-height: 1.55;
      font-weight: 500;
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
    .panel-card > .prose,
    .panel-card .prose {
      margin: 0 0 10px 0 !important;
      padding: 0 !important;
    }
    .panel-card > .prose h2,
    .panel-card .prose h2 {
      margin: 0 0 14px 0 !important;
      padding: 0 2px !important;
      font-size: 1.7rem !important;
      line-height: 1.15 !important;
      font-weight: 800 !important;
      color: #160e09 !important;
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
    .result-panel-output,
    .result-panel-output > div,
    .result-panel-output .html-container,
    .result-panel-output .prose,
    .result-panel-output .prose * {
      opacity: 1 !important;
      filter: none !important;
      transform: none !important;
      color: #000 !important;
    }
    .result-panel-output .pending,
    .result-panel-output [data-loading="true"],
    .result-panel-output [class*="pending"],
    .result-panel-output [class*="loading"] {
      opacity: 1 !important;
      filter: none !important;
      transform: none !important;
      animation: none !important;
    }
    .result-panel-output .spinner,
    .result-panel-output [class*="spinner"],
    .result-panel-output svg[class*="spin"],
    .result-panel-output [class*="loading"] svg,
    .result-panel-output [class*="pending"] svg {
      display: none !important;
      animation: none !important;
      transform: none !important;
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
    .export-file,
    .export-file > div,
    .export-file label,
    .export-file [data-testid="file"],
    .export-file .wrap,
    .export-file .block {
      background: transparent !important;
      color: var(--app-ink) !important;
    }
    .export-file button,
    .export-file a,
    .export-file .file-preview,
    .export-file .file-preview-holder {
      background: rgba(255, 251, 246, 0.98) !important;
      color: var(--app-ink) !important;
      border-color: var(--app-line) !important;
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
      .doc-row { grid-template-columns: 1fr; }
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
                gr.HTML(
                    f"""
                    <div class="doc-library">
                      <div class="doc-row">
                        <div class="doc-copy">
                          <strong>Project Brief</strong>
                          <span>Projektbrief</span>
                        </div>
                        <div class="doc-actions">
                          <a class="doc-pill-button" href="{PROJECT_BRIEF_URL}" target="_blank" rel="noreferrer">SV</a>
                          <a class="doc-pill-button" href="{PROJECT_BRIEF_EN_URL}" target="_blank" rel="noreferrer">EN</a>
                        </div>
                      </div>
                      <div class="doc-row">
                        <div class="doc-copy">
                          <strong>Theoretical Background</strong>
                          <span>Teoretisk bakgrund och centrala begrepp</span>
                        </div>
                        <div class="doc-actions">
                          <a class="doc-pill-button" href="{THEORETICAL_BACKGROUND_URL}" target="_blank" rel="noreferrer">SV</a>
                          <a class="doc-pill-button" href="{THEORETICAL_BACKGROUND_EN_URL}" target="_blank" rel="noreferrer">EN</a>
                        </div>
                      </div>
                      <div class="doc-row">
                        <div class="doc-copy">
                          <strong>Literature Study</strong>
                          <span>Litteraturstudie</span>
                        </div>
                        <div class="doc-actions">
                          <a class="doc-pill-button" href="{LITERATURE_URL}" target="_blank" rel="noreferrer">SV</a>
                          <a class="doc-pill-button" href="{LITERATURE_EN_URL}" target="_blank" rel="noreferrer">EN</a>
                        </div>
                      </div>
                      <div class="doc-row">
                        <div class="doc-copy">
                          <strong>AI Agents POC Report</strong>
                          <span>AI Agents POC Rapport</span>
                        </div>
                        <div class="doc-actions">
                          <a class="doc-pill-button" href="{AI_AGENTS_POC_REPORT_URL}" target="_blank" rel="noreferrer">SV</a>
                          <a class="doc-pill-button" href="{AI_AGENTS_POC_REPORT_EN_URL}" target="_blank" rel="noreferrer">EN</a>
                        </div>
                      </div>
                      <div class="doc-tail">
                        <a class="doc-pill-button" href="{QA_AGENT_DEVELOPING_REQUIREMENTS_URL}" target="_blank" rel="noreferrer">QA agent requirements</a>
                        <a class="doc-pill-button" href="{AI_DEVELOPING_GUIDELINES_URL}" target="_blank" rel="noreferrer">AI developing guidelines</a>
                      </div>
                    </div>
                    """
                )
            with gr.Group(elem_classes=["panel-card"]):
                gr.HTML(build_pipeline_visualization_section())
            with gr.Group(elem_classes=["panel-card", "configuration-panel"]):
                gr.Markdown("## Configuration")
                agent_config_inputs = []
                agent_bulk_outputs = []
                with gr.Tabs(elem_classes=["app-tabs", "config-tabs"]):
                    with gr.Tab("Execution mode"):
                        gr.HTML(
                            """
                            <div class="baseline-note">
                              <strong>QA agent service</strong> is the default backend. In that mode the orchestrator and run controls stay in this app, while Requirements Analyst, Test Design, and Review execute through the separate service.
                              <br><br>
                              Switch to <strong>Custom agent runtime</strong> when you want full per-agent control over Hugging Face, Ollama, or another OpenAI-compatible backend directly from this GUI.
                            </div>
                            """
                        )
                        execution_backend_input = gr.Radio(
                            label="Agent execution backend",
                            choices=EXECUTION_BACKEND_CHOICES,
                            value=EXECUTION_BACKEND_CHOICES[0],
                        )
                        with gr.Group(visible=True) as service_backend_group:
                            qa_agent_service_base_url_input = gr.Textbox(
                                label="QA agent service base URL",
                                value=DEFAULT_QA_AGENT_SERVICE_BASE_URL,
                                placeholder="http://127.0.0.1:8009 or https://.../api/v1",
                            )
                            gr.HTML(
                                """
                                <div class="baseline-note">
                              This backend invokes `requirements_analyst`, `test_designer`, and `reviewer` one step at a time through the service REST API. Open the published Space here:
                              <a href="https://huggingface.co/spaces/helmfridsson/qa-agent-service" target="_blank" rel="noreferrer">qa-agent-service</a>.
                              The service keeps its own default model configuration unless you explicitly allow caller-side model overrides there.
                                </div>
                                """
                            )
                        with gr.Group(visible=False) as custom_runtime_group:
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
                    with gr.Tab("Run controls"):
                        max_iterations_input = gr.Slider(
                            label="Maximum rounds",
                            minimum=1,
                            maximum=20,
                            step=1,
                            value=10,
                        )
                        max_feedback_messages_input = gr.Slider(
                            label="Maximum feedback messages",
                            minimum=0,
                            maximum=24,
                            step=1,
                            value=12,
                        )
                        max_feedback_per_pair_input = gr.Slider(
                            label="Maximum feedback messages per agent pair",
                            minimum=0,
                            maximum=8,
                            step=1,
                            value=4,
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
                            </div>
                            """
                        )
                    with gr.Tab("Orchestrator"):
                        gr.HTML(
                            """
                            <div class="baseline-note">
                              The orchestrator always stays in this app. Configure its model, timeout, and directives here regardless of whether downstream agents run directly in this app or through `qa-agent-service`.
                            </div>
                            """
                        )
                        with gr.Group(elem_classes=["workflow-step", "agent-config-card"]):
                            orchestrator_key, orchestrator_name, orchestrator_description, orchestrator_directives = ORCHESTRATOR_CONFIG_SPEC
                            gr.HTML(
                                f"<div class='agent-description'><strong>{html.escape(orchestrator_name)}</strong><span>{html.escape(orchestrator_description)}</span></div>"
                            )
                            orchestrator_execution_mode_input = gr.Dropdown(
                                label="Execution mode",
                                choices=EXECUTION_MODE_CHOICES,
                                value=EXECUTION_MODE_CHOICES[0],
                            )
                            orchestrator_execution_mode_help = gr.Markdown(
                                value=format_execution_mode_help(EXECUTION_MODE_CHOICES[0]),
                                elem_classes=["execution-mode-help"],
                            )
                            orchestrator_provider = AGENT_PROVIDER_DEFAULTS.get(orchestrator_key, PROVIDER_STRATEGY_CHOICES[0])
                            orchestrator_model = get_initial_model_value(
                                orchestrator_provider,
                                AGENT_MODEL_FAMILY_DEFAULTS.get(orchestrator_key, MODEL_FAMILY_CHOICES[0]),
                            )
                            orchestrator_llm_summary = gr.Markdown(
                                value=format_llm_config_summary(
                                    orchestrator_provider,
                                    orchestrator_model,
                                    AGENT_MODEL_OVERRIDE_DEFAULTS.get(orchestrator_key, ""),
                                ),
                                elem_classes=["llm-summary"],
                                visible=True,
                            )
                            orchestrator_provider_strategy_input = gr.Dropdown(
                                label="Provider strategy",
                                choices=PROVIDER_STRATEGY_CHOICES,
                                value=orchestrator_provider,
                                visible=True,
                            )
                            orchestrator_model_family_input = gr.Dropdown(
                                label="Model",
                                choices=get_model_choices(orchestrator_provider),
                                value=orchestrator_model,
                                visible=True,
                                allow_custom_value=True,
                            )
                            orchestrator_model_override_input = gr.Textbox(
                                label="Model override (optional)",
                                value=AGENT_MODEL_OVERRIDE_DEFAULTS.get(orchestrator_key, ""),
                                placeholder="Examples: qwen3:8b, llama3:latest, deepseek-r1:8b, openai/gpt-oss-120b",
                                visible=True,
                            )
                            orchestrator_timeout_input = gr.Slider(
                                label="Agent timeout (seconds)",
                                minimum=30,
                                maximum=300,
                                step=15,
                                value=AGENT_TIMEOUT_DEFAULTS.get(orchestrator_key, AGENT_TIMEOUT_SECONDS),
                                visible=True,
                            )
                            orchestrator_directives_input = gr.Textbox(
                                label="Directives",
                                value=orchestrator_directives,
                                lines=4,
                                visible=True,
                            )
                            orchestrator_provider_strategy_input.change(
                                fn=update_model_dropdown,
                                inputs=[
                                    orchestrator_provider_strategy_input,
                                    orchestrator_model_family_input,
                                    orchestrator_model_override_input,
                                ],
                                outputs=[orchestrator_model_family_input, orchestrator_llm_summary],
                            )
                            orchestrator_model_family_input.change(
                                fn=format_llm_config_summary,
                                inputs=[
                                    orchestrator_provider_strategy_input,
                                    orchestrator_model_family_input,
                                    orchestrator_model_override_input,
                                ],
                                outputs=[orchestrator_llm_summary],
                            )
                            orchestrator_model_override_input.change(
                                fn=format_llm_config_summary,
                                inputs=[
                                    orchestrator_provider_strategy_input,
                                    orchestrator_model_family_input,
                                    orchestrator_model_override_input,
                                ],
                                outputs=[orchestrator_llm_summary],
                            )
                            orchestrator_execution_mode_input.change(
                                fn=format_execution_mode_help,
                                inputs=[orchestrator_execution_mode_input],
                                outputs=[orchestrator_execution_mode_help],
                            )
                            orchestrator_execution_mode_input.change(
                                fn=toggle_llm_configuration_fields,
                                inputs=[orchestrator_execution_mode_input],
                                outputs=[
                                    orchestrator_llm_summary,
                                    orchestrator_provider_strategy_input,
                                    orchestrator_model_family_input,
                                    orchestrator_model_override_input,
                                    orchestrator_timeout_input,
                                    orchestrator_directives_input,
                                ],
                            )
                            agent_config_inputs.extend(
                                [
                                    orchestrator_execution_mode_input,
                                    orchestrator_provider_strategy_input,
                                    orchestrator_model_family_input,
                                    orchestrator_model_override_input,
                                    orchestrator_timeout_input,
                                    orchestrator_directives_input,
                                ]
                            )
                            agent_bulk_outputs.extend(
                                [
                                    orchestrator_execution_mode_input,
                                    orchestrator_provider_strategy_input,
                                    orchestrator_model_family_input,
                                    orchestrator_model_override_input,
                                    orchestrator_timeout_input,
                                    orchestrator_execution_mode_help,
                                    orchestrator_llm_summary,
                                    orchestrator_directives_input,
                                ]
                            )
                    with gr.Tab("Custom agents"):
                        with gr.Group(visible=False) as custom_agents_group:
                            gr.HTML(
                                """
                                <div class="baseline-note">
                                  Apply one common LLM configuration across all agents, then fine-tune only the agents that need exceptions. The orchestrator still has its own tab so you can override it again afterward if needed.
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
                                value="HF cheapest/free credits",
                            )
                            global_model_input = gr.Dropdown(
                                label="Model for all agents",
                                choices=get_model_choices("HF cheapest/free credits"),
                                value=get_initial_model_value("HF cheapest/free credits", "gpt-oss-20b"),
                                allow_custom_value=True,
                            )
                            global_llm_summary = gr.Markdown(
                                value=format_llm_config_summary(
                                    "HF cheapest/free credits",
                                    get_initial_model_value("HF cheapest/free credits", "gpt-oss-20b"),
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
                                value=150,
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
                            gr.HTML("<div class='config-subhead'>Detailed agent model setup</div>")
                            with gr.Tabs(elem_classes=["app-tabs", "agent-tabs"]):
                                for agent_key, agent_name, description, default_directives in WORKER_AGENT_CONFIG_SPECS:
                                    with gr.Tab(agent_name.replace(" Agent", "")):
                                        with gr.Group(elem_classes=["workflow-step", "agent-config-card"]):
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
                    with gr.Tab("Scenario"):
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
                        with gr.Row():
                            run_button = gr.Button("Run workflow", variant="primary")
                            stop_button = gr.Button("Stop workflow")
                        interaction_feedback_output = gr.HTML(
                            value=build_interaction_feedback("Ready."),
                            elem_classes=["interaction-feedback-shell"],
                        )

            with gr.Group(elem_classes=["panel-card"]):
                gr.Markdown("## Result")
                with gr.Tabs(elem_classes=["app-tabs", "result-tabs"]):
                    with gr.Tab("Summary"):
                        status_output = gr.HTML(
                            value=build_idle_status(),
                            show_label=False,
                            container=False,
                            elem_classes=["result-panel-output"],
                        )
                    with gr.Tab("Report"):
                        result_output = gr.HTML(
                            value=build_idle_report(),
                            show_label=False,
                            container=False,
                            elem_classes=["result-panel-output"],
                        )
                    with gr.Tab("Runtime"):
                        runtime_output = gr.HTML(
                            value=build_idle_runtime_timeline(),
                            show_label=False,
                            container=False,
                            elem_classes=["result-panel-output"],
                        )
                    with gr.Tab("Memory"):
                        memory_output = gr.HTML(
                            value=build_idle_memory_panel(),
                            show_label=False,
                            container=False,
                            elem_classes=["result-panel-output"],
                        )
                    with gr.Tab("Exports"):
                        log_file_output = gr.File(
                            label="Download run log",
                            value=None,
                            interactive=False,
                            elem_classes=["result-panel-output", "export-file"],
                        )
                        run_json_file_output = gr.File(
                            label="Download run JSON for evaluation",
                            value=None,
                            interactive=False,
                            elem_classes=["result-panel-output", "export-file"],
                        )

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
                execution_backend_input,
                qa_agent_service_base_url_input,
                *agent_config_inputs,
            ],
            outputs=[
                status_output,
                result_output,
                log_file_output,
                runtime_output,
                memory_output,
                interaction_feedback_output,
                run_json_file_output,
            ],
            show_progress="hidden",
        )
        execution_backend_input.change(
            fn=toggle_execution_backend_sections,
            inputs=[execution_backend_input],
            outputs=[service_backend_group, custom_runtime_group, custom_agents_group],
            show_progress="hidden",
        )
        stop_button.click(
            fn=request_stop_current_run,
            inputs=[],
            outputs=[interaction_feedback_output],
            show_progress="hidden",
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
            show_progress="hidden",
        )
        scenario_picker.change(
            fn=load_sample_scenario,
            inputs=[scenario_picker, title_input, requirements_input],
            outputs=[title_input, requirements_input],
            show_progress="hidden",
        )
        title_input.input(
            fn=mark_custom_scenario,
            inputs=[title_input],
            outputs=[scenario_picker],
            show_progress="hidden",
        )
        requirements_input.input(
            fn=mark_custom_scenario,
            inputs=[requirements_input],
            outputs=[scenario_picker],
            show_progress="hidden",
        )
    return demo


def build_workflow_report(payload: dict) -> str:
    summary_html = build_summary_overview(payload)
    run_controls = dict(payload.get("run_controls", {}))
    run_controls["execution_backend"] = payload.get("execution_backend", "")
    run_controls["qa_agent_service_base_url"] = payload.get("qa_agent_service_base_url", "")
    config_html = build_agent_config_overview(
        run_controls,
        payload.get("agent_configs", []),
    )
    test_case_overview = build_test_case_overview(payload)
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
        f"{test_case_overview}"
        f"{trace_sections}"
        "</div>"
    )


def build_summary_overview(payload: dict) -> str:
    review = payload["review"]
    run_controls = payload.get("run_controls", {})
    total_feedback_messages = payload.get("total_feedback_messages", 0)
    pair_feedback_counts = payload.get("pair_feedback_counts", {}) or {}
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
        f"Feedback handoffs used: {total_feedback_messages}/{run_controls.get('max_feedback_messages', 0)}",
        f"Configured max rounds: {run_controls.get('max_rounds', payload['iterations'])}",
        f"Configured max feedback messages: {run_controls.get('max_feedback_messages', 0)}",
        f"Configured max feedback per agent pair: {run_controls.get('max_feedback_per_agent_pair', 0)}",
        f"Review findings: {len(findings)}",
        f"Improvement actions: {len(improvement_actions)}",
        f"Final approval decision: {approved}",
    ]
    if pair_feedback_counts:
        pair_summary = ", ".join(
            f"{pair}: {count}" for pair, count in sorted(pair_feedback_counts.items(), key=lambda item: str(item[0]))
        )
        bullets.append(f"Feedback by pair: {pair_summary}")
    if storage_path:
        bullets.append(f"Run database: {storage_path}")
    if log_path:
        bullets.append(f"Run log: {log_path}")
    if findings:
        bullets.append(f"Most important review issue: {findings[0]}")
    if improvement_actions:
        bullets.append(f"Primary requested improvement: {improvement_actions[0]}")
    items = "".join(f"<li>{html.escape(item)}</li>" for item in bullets)
    return _build_collapsible_report_section(
        "Result summary",
        "Stored results, approval outcome, and final run totals.",
        f"<p class='summary-lead'>{html.escape(lead)}</p><ul class='summary-list'>{items}</ul>",
        section_index="Summary",
        open_by_default=False,
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
    return _build_collapsible_report_section(
        "Requirement to test case mapping",
        "Expand to inspect how requirements were covered by one or more designed test cases.",
        "<p class='agent-config-text'>In this app, the summary label 'Test cases' refers to the designed test cases created by the Test Design Agent. Each case is linked directly to a requirement ID and reviewed without a separate generation stage, and one requirement can map to several test cases.</p>"
        "<div class='table-scroll'><table><thead><tr><th>Test case</th><th>Requirement</th><th>Requirement text</th><th>Title</th><th>Type</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>",
        section_index="Mapping",
        open_by_default=False,
    )


def build_test_case_overview(payload: dict) -> str:
    test_designs = payload.get("test_designs", [])
    if not test_designs:
        return _build_collapsible_report_section(
            "Planned test cases",
            "No designed test cases were produced in this run.",
            "<p class='agent-config-text'>No planned test cases were produced in this run.</p>",
            section_index="Test cases",
            open_by_default=False,
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
            "<details class='stage-toggle'>"
            "<summary>"
            "<div class='stage-head'>"
            "<div>"
            f"<div class='stage-index'>{html.escape(str(test_case.get('test_case_id', 'Unknown test case')))}</div>"
            f"<div class='stage-role'>{html.escape(str(test_case.get('title', 'Untitled test case')))}</div>"
            "</div>"
            f"<div class='stage-meta'><strong>Requirement:</strong> {html.escape(str(test_case.get('requirement_id', 'Not linked')))}</div>"
            f"<div class='stage-meta'><strong>Type:</strong> {html.escape(str(test_case.get('test_type', 'Not set')))}</div>"
            "<div class='stage-chevron'></div>"
            "</div>"
            "</summary>"
            "<div class='stage-body'>"
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
            "</div>"
            "</details>"
            "</section>"
        )
    return _build_collapsible_report_section(
        "Planned test cases",
        "Expand to inspect the designed test cases, then open each test case for full details.",
        "<p class='agent-config-text'>This section shows the actual test cases produced by the Test Design Agent, including steps, expected results, and oracle. Requirements can expand into multiple focused test cases.</p>"
        "<div class='stage-grid'>"
        + "".join(cards)
        + "</div>",
        section_index="Test cases",
        open_by_default=False,
    )


def build_agent_config_overview(run_controls: dict, agent_configs: list[dict]) -> str:
    if not run_controls and not agent_configs:
        return ""
    backend_rows = ""
    execution_backend = run_controls.get("execution_backend") or "Not recorded"
    backend_rows += (
        f"<tr><td>Execution backend</td><td>{html.escape(str(execution_backend))}</td>"
        "<td>Determines whether worker agents ran through qa-agent-service or directly in this app.</td></tr>"
    )
    service_url = run_controls.get("qa_agent_service_base_url") or ""
    if service_url:
        backend_rows += (
            f"<tr><td>QA agent service base URL</td><td>{html.escape(str(service_url))}</td>"
            "<td>Base URL used for the service-backed worker agents in this run.</td></tr>"
        )
    controls_table = (
        "<table><thead><tr><th>Setting</th><th>Value</th><th>Meaning</th></tr></thead><tbody>"
        f"{backend_rows}"
        f"<tr><td>Maximum rounds</td><td>{html.escape(str(run_controls.get('max_rounds', 'Not set')))}</td><td>Upper limit for full pipeline passes.</td></tr>"
        f"<tr><td>Maximum feedback messages</td><td>{html.escape(str(run_controls.get('max_feedback_messages', 'Not set')))}</td><td>Upper limit for direct agent-to-agent correction messages during LLM-backed orchestration.</td></tr>"
        f"<tr><td>Maximum feedback per agent pair</td><td>{html.escape(str(run_controls.get('max_feedback_per_agent_pair', 'Not set')))}</td><td>Caps repeated back-and-forth between the same two agents.</td></tr>"
        "</tbody></table>"
    )
    if not agent_configs:
        return _build_collapsible_report_section(
            "Run configuration",
            "Expand to inspect workflow limits and feedback budgets.",
            "<p class='agent-config-text'>This run stores global control settings for future agent-to-agent feedback and rerun limits.</p>"
            f"{controls_table}",
            section_index="Config",
            open_by_default=False,
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
    run_config_html = _build_collapsible_report_section(
        "Run configuration",
        "Expand to inspect workflow limits and feedback budgets.",
        "<p class='agent-config-text'>This run stores both the global control settings and the per-agent runtime setup. The feedback limits matter once model-backed agents can send targeted repair messages to each other.</p>"
        f"{controls_table}",
        section_index="Config",
        open_by_default=False,
    )
    agent_runtime_html = _build_collapsible_report_section(
        "Agent runtime configuration",
        "Expand to inspect per-agent mode, timeout, resolved model, and directives.",
        "<p class='agent-config-text'>This run stores per-agent execution settings and the resolved live model details for every LLM-backed agent.</p>"
        "<div class='table-scroll'><table><thead><tr><th>Agent</th><th>Execution mode</th><th>Timeout (s)</th><th>Resolved model</th><th>Directives</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>",
        section_index="Runtime",
        open_by_default=False,
    )
    return run_config_html + agent_runtime_html


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


def build_live_trace_overview(stage_traces: list[dict], agent_configs: list[dict]) -> str:
    if not stage_traces:
        return ""
    return _build_trace_section_panel(stage_traces, agent_configs, panel_title="Backtracking activity", open_by_default=True)


def build_trace_sections(stage_traces: list[dict], agent_configs: list[dict]) -> str:
    return _build_trace_section_panel(stage_traces, agent_configs, panel_title="Backtracking rounds", open_by_default=False)


def _build_trace_section_panel(
    stage_traces: list[dict],
    agent_configs: list[dict],
    *,
    panel_title: str,
    open_by_default: bool,
) -> str:
    if not stage_traces:
        return _build_collapsible_report_section(
            panel_title,
            "No stage traces were recorded.",
            "<p class='agent-config-text'>No agent traces were recorded for this run.</p>",
            section_index="Trace",
            open_by_default=open_by_default,
        )
    sections = []
    run_index = 1
    runtime_lookup = build_agent_runtime_lookup(agent_configs)
    for iteration, traces in group_stage_traces_by_iteration(stage_traces).items():
        sections.append(
            "<details class='stage-details'>"
            f"<summary>Backtracking round {html.escape(str(iteration))}</summary>"
            "<p class='agent-config-text'>Below is the full sequence of agent passes for this backtracking round, with explicit input, output, and routing context.</p>"
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
                    prompt_tokens=_read_int(trace.get("prompt_tokens")),
                    completion_tokens=_read_int(trace.get("completion_tokens")),
                    total_tokens=_read_int(trace.get("total_tokens")),
                )
            )
            run_index += 1
        sections.append("</details>")
    return _build_collapsible_report_section(
        panel_title,
        "Expand to inspect all rounds, then open a round to inspect its agent passes.",
        "".join(sections),
        section_index="Trace",
        open_by_default=open_by_default,
    )


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
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    total_tokens: int | None = None,
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
    total_token_label = total_tokens
    if total_token_label is None and (prompt_tokens is not None or completion_tokens is not None):
        total_token_label = (prompt_tokens or 0) + (completion_tokens or 0)
    token_block = (
        "<div class='io-section'>"
        "<div class='log-title'>Token usage</div>"
        f"<p class='io-summary'>Total tokens: {html.escape(str(total_token_label))}</p>"
        "<ul class='log-list'>"
        f"<li>Prompt tokens: {html.escape(str(prompt_tokens if prompt_tokens is not None else 0))}</li>"
        f"<li>Completion tokens: {html.escape(str(completion_tokens if completion_tokens is not None else 0))}</li>"
        f"<li>Total tokens: {html.escape(str(total_token_label if total_token_label is not None else 0))}</li>"
        "</ul>"
        "</div>"
        if prompt_tokens is not None or completion_tokens is not None or total_tokens is not None
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
        f"{token_block}"
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
        "allowed_paths": _build_allowed_file_paths(),
    }
    if _blocks_support_launch_theming():
        launch_kwargs["theme"] = APP_THEME
        launch_kwargs["css"] = CUSTOM_CSS
    demo.launch(**launch_kwargs)
