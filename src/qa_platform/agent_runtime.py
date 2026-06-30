from __future__ import annotations

from .llm_runtime import resolve_live_model_id
from .models import AgentRuntimeConfig


EXECUTION_MODE_CHOICES = ["LLM-backed", "Structured baseline"]
PROVIDER_STRATEGY_CHOICES = [
    "HF cheapest/free credits",
    "HF fastest",
    "Ollama local",
    "Custom OpenAI-compatible",
]
MODEL_FAMILY_CHOICES = [
    "Auto / recommended",
    "Qwen 3 32B",
    "Llama 3.3 70B Instruct",
    "DeepSeek R1",
    "gpt-oss-120b",
]
AGENT_PROVIDER_DEFAULTS = {
    "orchestrator": "Ollama local",
    "requirements_analyst": "Ollama local",
    "test_design": "Ollama local",
    "review": "Ollama local",
}
AGENT_MODEL_FAMILY_DEFAULTS = {
    "orchestrator": "Qwen 3 32B",
    "requirements_analyst": "Qwen 3 32B",
    "test_design": "Qwen 3 32B",
    "review": "DeepSeek R1",
}
AGENT_MODEL_OVERRIDE_DEFAULTS = {
    "orchestrator": "",
    "requirements_analyst": "",
    "test_design": "",
    "review": "",
}
AGENT_TIMEOUT_DEFAULTS = {
    "orchestrator": 60,
    "requirements_analyst": 120,
    "test_design": 90,
    "review": 60,
}
AGENT_CONFIG_SPECS = [
    (
        "orchestrator",
        "Orchestrator Agent",
        "Controls routing and decides whether the run should stop or continue.",
        (
            "Purpose: route the workflow to the next most relevant agent and minimize unnecessary work.\n"
            "Required behavior: prefer the smallest valid backtracking step, send concrete actionable feedback, and stop when quality is sufficient or control limits are exhausted.\n"
            "Forbidden behavior: do not restart the full pipeline when a narrower backtracking route is available; do not send vague feedback.\n"
            "Quality bar: every routing decision must name the reason, the target agent, and the exact issue that triggered the handoff."
        ),
    ),
    (
        "requirements_analyst",
        "Requirements Analyst Agent",
        "Extracts structured requirements, priorities, assumptions, and acceptance criteria.",
        (
            "Purpose: extract only what the requirement text supports and make uncertainty explicit.\n"
            "Required output: stable requirement IDs, normalized requirement text, priority, explicit acceptance criteria, assumptions, and open clarification points when needed.\n"
            "Forbidden behavior: do not invent missing business rules or silently resolve ambiguity.\n"
            "Quality bar: requirements must be testable, traceable, and clearly separated from assumptions."
        ),
    ),
    (
        "test_design",
        "Test Design Agent",
        "Turns requirements into test cases with type, steps, expected results, and oracle.",
        (
            "Purpose: create concrete, reviewable test cases rather than placeholders.\n"
            "Required output: preconditions, concrete test data, executable steps, observable expected results, explicit oracle logic, and traceability to requirement IDs.\n"
            "Forbidden behavior: do not use vague steps such as 'execute the primary flow' or generic expected results without observable outcomes.\n"
            "Quality bar: every test case must be specific enough to run and judge as pass or fail."
        ),
    ),
    (
        "review",
        "Review Agent",
        "Evaluates coverage, unresolved assumptions, and the strength of each planned test case.",
        (
            "Purpose: challenge weak test design and decide whether the current result is good enough.\n"
            "Required checks: traceability, oracle strength, negative coverage, edge cases, unresolved assumptions, and placeholder language.\n"
            "Forbidden behavior: do not approve generic or weakly testable cases just because coverage looks complete.\n"
            "Quality bar: explain exactly why quality passes or fails, identify the weakest test cases first, and send targeted feedback to the most relevant upstream agent."
        ),
    ),
]


def compose_model_id(provider_strategy: str, model_family: str, model_override: str = "") -> str:
    override = (model_override or "").strip()
    if override:
        return override
    if not provider_strategy or not model_family:
        return ""
    if provider_strategy == "Ollama local":
        return f"Ollama local / {model_family}"
    if provider_strategy == "Custom OpenAI-compatible":
        return f"Custom OpenAI-compatible / {model_family}"
    if model_family == "Auto / recommended":
        return (
            "HF router / auto fastest provider"
            if provider_strategy == "HF fastest"
            else "HF router / auto cheapest provider"
        )
    family_map = {
        "Qwen 3 32B": "Qwen/Qwen3-32B",
        "Llama 3.3 70B Instruct": "meta-llama/Llama-3.3-70B-Instruct",
        "DeepSeek R1": "deepseek-ai/DeepSeek-R1",
        "gpt-oss-120b": "openai/gpt-oss-120b",
    }
    provider_suffix = ":fastest" if provider_strategy == "HF fastest" else ":cheapest"
    return f"{family_map.get(model_family, model_family)}{provider_suffix}"


def build_agent_runtime_configs(*values: str) -> list[AgentRuntimeConfig]:
    configs = []
    legacy_stride = 4
    extended_stride = 5
    timeout_stride = 6
    if len(values) >= len(AGENT_CONFIG_SPECS) * timeout_stride:
        stride = timeout_stride
    elif len(values) >= len(AGENT_CONFIG_SPECS) * extended_stride:
        stride = extended_stride
    else:
        stride = legacy_stride
    for index, (agent_key, agent_name, _description, default_directives) in enumerate(AGENT_CONFIG_SPECS):
        base = index * stride
        execution_mode = values[base] if len(values) > base else EXECUTION_MODE_CHOICES[0]
        provider_strategy = (
            values[base + 1]
            if len(values) > base + 1
            else AGENT_PROVIDER_DEFAULTS.get(agent_key, PROVIDER_STRATEGY_CHOICES[0])
        )
        model_family = (
            values[base + 2]
            if len(values) > base + 2
            else AGENT_MODEL_FAMILY_DEFAULTS.get(agent_key, MODEL_FAMILY_CHOICES[0])
        )
        model_override = (
            values[base + 3]
            if stride in {extended_stride, timeout_stride} and len(values) > base + 3
            else AGENT_MODEL_OVERRIDE_DEFAULTS.get(agent_key, "")
        )
        timeout_seconds = (
            max(1, int(float(values[base + 4])))
            if stride == timeout_stride and len(values) > base + 4
            else AGENT_TIMEOUT_DEFAULTS.get(agent_key, 60)
        )
        directives_index = (
            base + 5
            if stride == timeout_stride
            else base + 4
            if stride == extended_stride
            else base + 3
        )
        directives = values[directives_index] if len(values) > directives_index else default_directives
        llm_active = execution_mode == "LLM-backed"
        config = AgentRuntimeConfig(
            agent_key=agent_key,
            agent_name=agent_name,
            execution_mode=execution_mode,
            timeout_seconds=timeout_seconds,
            provider_strategy=provider_strategy if llm_active else "",
            model_family=model_family if llm_active else "",
            model_override=model_override if llm_active else "",
            model_id=compose_model_id(provider_strategy, model_family, model_override) if llm_active else "",
            directives=(directives or "").strip(),
        )
        if llm_active:
            config.model_id = resolve_live_model_id(config)
        configs.append(config)
    return configs
