from __future__ import annotations

from .models import AgentRuntimeConfig


EXECUTION_MODE_CHOICES = ["LLM-backed (preview)", "Structured baseline"]
PROVIDER_STRATEGY_CHOICES = [
    "HF cheapest/free credits",
    "HF fastest",
    "Ollama local (coming soon)",
    "Custom OpenAI-compatible (coming soon)",
]
MODEL_FAMILY_CHOICES = [
    "Auto / recommended",
    "Qwen 3 32B",
    "Llama 3.3 70B Instruct",
    "DeepSeek R1",
    "gpt-oss-120b",
]
AGENT_PROVIDER_DEFAULTS = {
    "orchestrator": "HF cheapest/free credits",
    "requirements_analyst": "HF cheapest/free credits",
    "test_design": "HF cheapest/free credits",
    "review": "HF cheapest/free credits",
}
AGENT_MODEL_FAMILY_DEFAULTS = {
    "orchestrator": "Qwen 3 32B",
    "requirements_analyst": "Qwen 3 32B",
    "test_design": "Llama 3.3 70B Instruct",
    "review": "DeepSeek R1",
}
AGENT_CONFIG_SPECS = [
    (
        "orchestrator",
        "Orchestrator Agent",
        "Controls routing and decides whether the run should stop or continue.",
        "Keep decisions explicit. Prefer short structured outputs and conservative reruns.",
    ),
    (
        "requirements_analyst",
        "Requirements Analyst Agent",
        "Extracts structured requirements, priorities, assumptions, and acceptance criteria.",
        "Focus on precise requirement decomposition, explicit assumptions, and traceable acceptance criteria.",
    ),
    (
        "test_design",
        "Test Design Agent",
        "Turns requirements into test cases with type, steps, expected results, and oracle.",
        "Design test cases with strong coverage, concrete expected results, and explicit oracle logic.",
    ),
    (
        "review",
        "Review Agent",
        "Evaluates coverage, unresolved assumptions, and the strength of each planned test case.",
        "Be strict. Explain exactly why quality passes or fails and surface the weakest tests first.",
    ),
]


def compose_model_id(provider_strategy: str, model_family: str) -> str:
    if not provider_strategy or not model_family:
        return ""
    if provider_strategy == "Ollama local (coming soon)":
        return f"Ollama local / {model_family}"
    if provider_strategy == "Custom OpenAI-compatible (coming soon)":
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
    for index, (agent_key, agent_name, _description, default_directives) in enumerate(AGENT_CONFIG_SPECS):
        base = index * 4
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
        directives = values[base + 3] if len(values) > base + 3 else default_directives
        llm_active = execution_mode == "LLM-backed (preview)"
        configs.append(
            AgentRuntimeConfig(
                agent_key=agent_key,
                agent_name=agent_name,
                execution_mode=execution_mode,
                provider_strategy=provider_strategy if llm_active else "",
                model_family=model_family if llm_active else "",
                model_id=compose_model_id(provider_strategy, model_family) if llm_active else "",
                directives=(directives or "").strip(),
            )
        )
    return configs
