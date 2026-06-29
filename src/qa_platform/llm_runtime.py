from __future__ import annotations

import json
import os
import socket
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any
from urllib import error, request

from .models import AgentRuntimeConfig


class LLMRuntimeError(RuntimeError):
    pass


HTTP_TIMEOUT_SECONDS = 55


@dataclass
class LLMCallMetadata:
    endpoint: str
    model_id: str
    provider_strategy: str
    response_format_used: bool
    usage: dict[str, Any]


def load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def is_llm_enabled(runtime_config: AgentRuntimeConfig | None) -> bool:
    return bool(runtime_config and runtime_config.execution_mode == "LLM-backed")


def resolve_live_model_id(runtime_config: AgentRuntimeConfig) -> str:
    hf_family_map = {
        "Qwen 3 32B": "Qwen/Qwen3-32B",
        "Llama 3.3 70B Instruct": "meta-llama/Llama-3.3-70B-Instruct",
        "DeepSeek R1": "deepseek-ai/DeepSeek-R1",
        "gpt-oss-120b": "openai/gpt-oss-120b",
    }
    ollama_family_map = {
        "Qwen 3 32B": "qwen3:32b",
        "Llama 3.3 70B Instruct": "llama3.3:70b",
        "DeepSeek R1": "deepseek-r1:32b",
        "gpt-oss-120b": "gpt-oss:120b",
    }
    recommended_family = {
        "orchestrator": "Qwen 3 32B",
        "requirements_analyst": "Qwen 3 32B",
        "test_design": "Llama 3.3 70B Instruct",
        "review": "DeepSeek R1",
    }.get(runtime_config.agent_key, "Qwen 3 32B")
    family = runtime_config.model_family or recommended_family
    strategy = runtime_config.provider_strategy

    if strategy == "HF cheapest/free credits":
        return f"{hf_family_map.get(family, hf_family_map[recommended_family])}:cheapest"
    if strategy == "HF fastest":
        return f"{hf_family_map.get(family, hf_family_map[recommended_family])}:fastest"
    if strategy == "Ollama local":
        return ollama_family_map.get(family, ollama_family_map[recommended_family])
    if strategy == "Custom OpenAI-compatible":
        return hf_family_map.get(family, hf_family_map[recommended_family])
    return runtime_config.model_id or hf_family_map[recommended_family]


def call_structured_llm(
    runtime_config: AgentRuntimeConfig,
    system_prompt: str,
    user_prompt: str,
    schema_name: str,
    schema: dict[str, Any],
    temperature: float = 0.2,
) -> tuple[dict[str, Any], LLMCallMetadata]:
    load_local_env()
    if runtime_config.provider_strategy.startswith("HF "):
        return _call_hf_structured_llm(
            runtime_config=runtime_config,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema_name=schema_name,
            schema=schema,
            temperature=temperature,
        )

    endpoint, api_key = _resolve_endpoint_and_key(runtime_config)
    messages = [
        {"role": "system", "content": system_prompt.strip()},
        {"role": "user", "content": user_prompt.strip()},
    ]
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": schema_name,
            "schema": schema,
            "strict": True,
        },
    }

    errors: list[str] = []
    for model_id in _candidate_model_ids(runtime_config):
        try:
            payload = _post_chat_completion(
                endpoint=endpoint,
                api_key=api_key,
                model_id=model_id,
                messages=messages,
                temperature=temperature,
                response_format=response_format,
            )
            content = _extract_message_content(payload)
            return json.loads(content), LLMCallMetadata(
                endpoint=endpoint,
                model_id=model_id,
                provider_strategy=runtime_config.provider_strategy,
                response_format_used=True,
                usage=payload.get("usage") or {},
            )
        except (LLMRuntimeError, json.JSONDecodeError) as first_error:
            errors.append(f"{model_id} structured-output attempt: {first_error}")
            fallback_system_prompt = (
                system_prompt.strip()
                + "\nReturn only valid JSON matching the requested schema. Do not add markdown fences or commentary."
            )
            fallback_user_prompt = (
                user_prompt.strip()
                + "\nJSON schema to satisfy exactly:\n"
                + json.dumps(schema, ensure_ascii=False)
            )
            try:
                fallback_payload = _post_chat_completion(
                    endpoint=endpoint,
                    api_key=api_key,
                    model_id=model_id,
                    messages=[
                        {"role": "system", "content": fallback_system_prompt},
                        {"role": "user", "content": fallback_user_prompt},
                    ],
                    temperature=temperature,
                    response_format=None,
                )
                content = _extract_message_content(fallback_payload)
                return _extract_json_object(content), LLMCallMetadata(
                    endpoint=endpoint,
                    model_id=model_id,
                    provider_strategy=runtime_config.provider_strategy,
                    response_format_used=False,
                    usage=fallback_payload.get("usage") or {},
                )
            except Exception as second_error:  # noqa: BLE001
                errors.append(f"{model_id} fallback attempt: {second_error}")

    raise LLMRuntimeError(
        f"Live LLM call failed for {runtime_config.agent_name}. Attempts: {' | '.join(errors)}"
    )


def _call_hf_structured_llm(
    runtime_config: AgentRuntimeConfig,
    system_prompt: str,
    user_prompt: str,
    schema_name: str,
    schema: dict[str, Any],
    temperature: float,
) -> tuple[dict[str, Any], LLMCallMetadata]:
    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        raise LLMRuntimeError("HF_TOKEN is required for Hugging Face live LLM execution.")

    errors: list[str] = []
    for model_id in _candidate_model_ids(runtime_config):
        try:
            content, usage = _post_hf_inference_chat_completion(
                api_key=token,
                model_id=model_id,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            system_prompt.strip()
                            + "\nReturn only valid JSON matching the requested schema. "
                            + "Do not add markdown fences or commentary."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            user_prompt.strip()
                            + "\nJSON schema to satisfy exactly:\n"
                            + json.dumps(
                                {
                                    "name": schema_name,
                                    "schema": schema,
                                },
                                ensure_ascii=False,
                            )
                        ),
                    },
                ],
                temperature=temperature,
            )
            return _extract_json_object(content), LLMCallMetadata(
                endpoint="huggingface_hub.InferenceClient.chat_completion",
                model_id=model_id,
                provider_strategy=runtime_config.provider_strategy,
                response_format_used=False,
                usage=usage,
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{model_id} inference-client attempt: {exc}")

    endpoint, api_key = _resolve_endpoint_and_key(runtime_config)
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": schema_name,
            "schema": schema,
            "strict": True,
        },
    }
    messages = [
        {"role": "system", "content": system_prompt.strip()},
        {"role": "user", "content": user_prompt.strip()},
    ]
    for model_id in _candidate_model_ids(runtime_config):
        try:
            payload = _post_chat_completion(
                endpoint=endpoint,
                api_key=api_key,
                model_id=model_id,
                messages=messages,
                temperature=temperature,
                response_format=response_format,
            )
            content = _extract_message_content(payload)
            return json.loads(content), LLMCallMetadata(
                endpoint=endpoint,
                model_id=model_id,
                provider_strategy=runtime_config.provider_strategy,
                response_format_used=True,
                usage=payload.get("usage") or {},
            )
        except (LLMRuntimeError, json.JSONDecodeError) as first_error:
            errors.append(f"{model_id} router structured-output attempt: {first_error}")
            fallback_system_prompt = (
                system_prompt.strip()
                + "\nReturn only valid JSON matching the requested schema. Do not add markdown fences or commentary."
            )
            fallback_user_prompt = (
                user_prompt.strip()
                + "\nJSON schema to satisfy exactly:\n"
                + json.dumps(schema, ensure_ascii=False)
            )
            try:
                fallback_payload = _post_chat_completion(
                    endpoint=endpoint,
                    api_key=api_key,
                    model_id=model_id,
                    messages=[
                        {"role": "system", "content": fallback_system_prompt},
                        {"role": "user", "content": fallback_user_prompt},
                    ],
                    temperature=temperature,
                    response_format=None,
                )
                content = _extract_message_content(fallback_payload)
                return _extract_json_object(content), LLMCallMetadata(
                    endpoint=endpoint,
                    model_id=model_id,
                    provider_strategy=runtime_config.provider_strategy,
                    response_format_used=False,
                    usage=fallback_payload.get("usage") or {},
                )
            except Exception as second_error:  # noqa: BLE001
                errors.append(f"{model_id} router fallback attempt: {second_error}")

    raise LLMRuntimeError(
        f"Live LLM call failed for {runtime_config.agent_name}. Attempts: {' | '.join(errors)}"
    )


def _resolve_endpoint_and_key(runtime_config: AgentRuntimeConfig) -> tuple[str, str]:
    strategy = runtime_config.provider_strategy
    if strategy in {"HF cheapest/free credits", "HF fastest"}:
        token = os.environ.get("HF_TOKEN", "").strip()
        if not token:
            raise LLMRuntimeError("HF_TOKEN is required for Hugging Face live LLM execution.")
        return "https://router.huggingface.co/v1/chat/completions", token

    if strategy == "Ollama local":
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        return _normalize_chat_endpoint(base_url), os.environ.get("OLLAMA_API_KEY", "ollama")

    if strategy == "Custom OpenAI-compatible":
        base_url = os.environ.get("OPENAI_BASE_URL", "").strip()
        if not base_url:
            raise LLMRuntimeError("OPENAI_BASE_URL is required for custom OpenAI-compatible execution.")
        return _normalize_chat_endpoint(base_url.rstrip("/")), os.environ.get("OPENAI_API_KEY", "")

    raise LLMRuntimeError(f"Unsupported provider strategy: {strategy}")


def _candidate_model_ids(runtime_config: AgentRuntimeConfig) -> list[str]:
    resolved = resolve_live_model_id(runtime_config)
    candidates = [resolved]
    if runtime_config.provider_strategy.startswith("HF ") and ":" in resolved:
        base_model = resolved.split(":", 1)[0]
        if base_model not in candidates:
            candidates.append(base_model)
    return candidates


def _normalize_chat_endpoint(base_url: str) -> str:
    if base_url.endswith("/chat/completions"):
        return base_url
    if base_url.endswith("/v1"):
        return f"{base_url}/chat/completions"
    return f"{base_url}/v1/chat/completions"


def _post_hf_inference_chat_completion(
    api_key: str,
    model_id: str,
    messages: list[dict[str, str]],
    temperature: float,
) -> tuple[str, dict[str, Any]]:
    try:
        huggingface_hub = import_module("huggingface_hub")
    except ModuleNotFoundError as exc:
        raise LLMRuntimeError(
            "huggingface_hub is not installed. Install it to use Hugging Face live execution."
        ) from exc

    client = huggingface_hub.InferenceClient(model=model_id, token=api_key)
    try:
        response = client.chat_completion(
            messages=messages,
            max_tokens=2000,
            temperature=temperature,
        )
    except (TimeoutError, socket.timeout) as exc:
        raise LLMRuntimeError(
            f"Hugging Face InferenceClient timed out after {HTTP_TIMEOUT_SECONDS} seconds."
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise LLMRuntimeError(str(exc)) from exc

    choice = response.choices[0]
    message = getattr(choice, "message", None)
    content = None
    if message is not None:
        content = getattr(message, "content", None)
        if content is None and isinstance(message, dict):
            content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise LLMRuntimeError("Model response did not contain text content.")

    usage_obj = getattr(response, "usage", None)
    usage = {
        "prompt_tokens": getattr(usage_obj, "prompt_tokens", None),
        "completion_tokens": getattr(usage_obj, "completion_tokens", None),
        "total_tokens": getattr(usage_obj, "total_tokens", None),
    }
    return content, {key: value for key, value in usage.items() if value is not None}


def _post_chat_completion(
    endpoint: str,
    api_key: str,
    model_id: str,
    messages: list[dict[str, str]],
    temperature: float,
    response_format: dict[str, Any] | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": model_id,
        "messages": messages,
        "stream": False,
        "temperature": temperature,
    }
    if response_format:
        body["response_format"] = response_format

    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    encoded = json.dumps(body).encode("utf-8")
    req = request.Request(endpoint, data=encoded, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise LLMRuntimeError(
            f"HTTP {exc.code} from model endpoint {endpoint}: {_summarize_error_detail(detail)}"
        ) from exc
    except error.URLError as exc:
        raise LLMRuntimeError(f"Could not reach model endpoint {endpoint}: {exc.reason}") from exc
    except (TimeoutError, socket.timeout) as exc:
        raise LLMRuntimeError(
            f"Model endpoint {endpoint} timed out after {HTTP_TIMEOUT_SECONDS} seconds."
        ) from exc


def _extract_message_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices:
        raise LLMRuntimeError("Model response did not contain any choices.")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = [
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") in {"text", "output_text"}
        ]
        combined = "".join(text_parts).strip()
        if combined:
            return combined
    raise LLMRuntimeError("Model response did not contain text content.")


def _extract_json_object(content: str) -> dict[str, Any]:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise LLMRuntimeError("Could not locate a JSON object in the model response.")
    return json.loads(stripped[start : end + 1])


def _summarize_error_detail(detail: str) -> str:
    compact = " ".join(detail.split())
    lowered = compact.lower()
    if "error 1010" in lowered or "access denied" in lowered:
        return "Access denied by the routed provider (Cloudflare 1010). Try another provider strategy or a local/custom backend."
    if len(compact) > 320:
        return compact[:317] + "..."
    return compact
