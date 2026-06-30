from __future__ import annotations

from .llm_runtime import resolve_live_model_id
from .models import AgentRuntimeConfig
from .registry import build_default_agent_registry


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
DEFAULT_AGENT_REGISTRY = build_default_agent_registry()
AGENT_PROVIDER_DEFAULTS = {
    spec.agent_key: spec.default_provider_strategy for spec in DEFAULT_AGENT_REGISTRY.specs()
}
AGENT_MODEL_FAMILY_DEFAULTS = {
    spec.agent_key: spec.default_model_family for spec in DEFAULT_AGENT_REGISTRY.specs()
}
AGENT_MODEL_OVERRIDE_DEFAULTS = {
    spec.agent_key: spec.default_model_override for spec in DEFAULT_AGENT_REGISTRY.specs()
}
AGENT_TIMEOUT_DEFAULTS = {
    spec.agent_key: spec.default_timeout_seconds for spec in DEFAULT_AGENT_REGISTRY.specs()
}
AGENT_CONFIG_SPECS = [
    (
        spec.agent_key,
        spec.agent_name,
        spec.description,
        spec.default_directives,
    )
    for spec in DEFAULT_AGENT_REGISTRY.specs()
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
