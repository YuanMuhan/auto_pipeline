import os
import time
from pathlib import Path
from typing import Dict, Any, Callable

import yaml

from autopipeline.llm.cache import LLMDiskCache
from autopipeline.llm.hash_utils import stable_hash, text_hash
from autopipeline.llm.prompt_loader import PromptLoader
from autopipeline.llm.types import LLMConfig, LLMResponse
from autopipeline.llm import providers as provider_module
from autopipeline.catalog.render import load_component_profiles, load_endpoint_types, component_types_summary, endpoint_types_summary


class LLMClient:
    """Unified LLM client with caching and provider abstraction."""

    def __init__(self, base_dir: str, config: LLMConfig, logger: Callable[[str], None]):
        self.base_dir = base_dir
        self.config = config
        self.logger = logger
        self.cache = LLMDiskCache(config.cache_dir, enabled=config.cache_enabled)
        self.prompt_loader = PromptLoader(Path(base_dir) / "prompts")
        comp = load_component_profiles(base_dir)
        ep = load_endpoint_types(base_dir)
        self.catalog_summary = {
            "components": component_types_summary(comp["profiles"]),
            "endpoint_types": endpoint_types_summary(ep["data"]),
        }
        self.stats = {
            "provider": config.provider,
            "model": config.model,
            "temperature": config.temperature,
            "cache_dir": config.cache_dir,
            "cache_enabled": config.cache_enabled,
            "calls_total": 0,
            "calls_by_stage": {},
            "cache_hits": 0,
            "cache_misses": 0,
            "usage_tokens_total": 0,
            "prompt_template_hashes": {},
        }

    def _log_call(self, stage: str, cache_hit: bool, cache_key: str, elapsed: float, usage: Any):
        cache_mark = "HIT" if cache_hit else "MISS"
        usage_repr = ""
        if usage and isinstance(usage, dict):
            usage_repr = f", usage={usage}"
        self.logger(f"[LLM] stage={stage} cache={cache_mark} key={cache_key[:8]} time={elapsed:.3f}s{usage_repr}")

    def _get_provider(self):
        name = self.config.provider.lower()
        if name == "mock":
            return provider_module.MockProvider(self.base_dir)
        if name == "anthropic":
            return provider_module.AnthropicProvider()
        raise ValueError(f"Unsupported provider: {name}")

    def _compute_cache_key(self, stage: str, provider_name: str, model: str, params: Dict[str, Any],
                           prompt_hash: str, rendered_hash: str, rules_hash: str,
                           schema_versions: Dict[str, Any], inputs_hash: str) -> str:
        key_obj = {
            "stage": stage,
            "provider": provider_name,
            "model": model,
            "params": params,
            "prompt_template_text_hash": prompt_hash,
            "rendered_prompt_hash": rendered_hash,
            "rules_hash": rules_hash,
            "schema_versions": schema_versions,
            "inputs_hash": inputs_hash,
        }
        return stable_hash(key_obj)

    def _render_prompt(self, prompt_name: str, context: Dict[str, Any]) -> Dict[str, str]:
        extras = f"Component types:\n{self.catalog_summary['components']}\n\nEndpoint types:\n{self.catalog_summary['endpoint_types']}"
        rendered = self.prompt_loader.render(prompt_name, context, extras=extras)
        # Track template hashes
        self.stats["prompt_template_hashes"][prompt_name] = rendered["template_hash"]
        return rendered

    def _invoke(self, stage: str, prompt_name: str, context: Dict[str, Any], rules_hash: str,
                schema_versions: Dict[str, Any], inputs_hash: str) -> str:
        provider = self._get_provider()
        model = self.config.model or "mock-model"
        params = {
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        prompt_obj = self._render_prompt(prompt_name, context)
        cache_key = self._compute_cache_key(
            stage=stage,
            provider_name=provider.name,
            model=model,
            params=params,
            prompt_hash=prompt_obj["template_hash"],
            rendered_hash=prompt_obj["rendered_hash"],
            rules_hash=rules_hash,
            schema_versions=schema_versions,
            inputs_hash=inputs_hash,
        )

        cache_hit = False
        cached_text = None
        cached_usage = None
        start = time.time()

        hit, cache_payload = self.cache.get(cache_key)
        if hit:
            cache_hit = True
            cached_text = cache_payload.get("response_text")
            cached_usage = cache_payload.get("usage")
            self.stats["cache_hits"] += 1
        else:
            self.stats["cache_misses"] += 1

        if cached_text is None:
            resp = provider.call(
                prompt=prompt_obj["rendered"],
                stage=stage,
                model=model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                case_id=context.get("case_id"),
            )
            cached_text = resp["text"]
            cached_usage = resp.get("usage")
            cache_payload = {
                "request_meta": {
                    "stage": stage,
                    "provider": provider.name,
                    "model": model,
                    "params": params,
                    "prompt_template_hash": prompt_obj["template_hash"],
                    "rendered_prompt_hash": prompt_obj["rendered_hash"],
                    "rules_hash": rules_hash,
                    "schema_versions": schema_versions,
                    "inputs_hash": inputs_hash,
                },
                "response_text": cached_text,
                "usage": cached_usage,
            }
            self.cache.set(cache_key, cache_payload)

        elapsed = time.time() - start
        self._log_call(stage, cache_hit, cache_key, elapsed, cached_usage)

        # Stats
        self.stats["calls_total"] += 1
        self.stats["calls_by_stage"][stage] = self.stats["calls_by_stage"].get(stage, 0) + 1
        if cached_usage and isinstance(cached_usage, dict):
            self.stats["usage_tokens_total"] += cached_usage.get("input_tokens", 0) + cached_usage.get("output_tokens", 0)

        return cached_text

    def generate_ir(self, case_id: str, user_problem: Dict[str, Any], device_info: Dict[str, Any],
                    rules_ctx: Dict[str, Any], schema_versions: Dict[str, Any],
                    prompt_name: str = "ir_agent") -> str:
        inputs_hash = stable_hash({"user_problem": user_problem, "device_info": device_info})
        context = {
            "USER_PROBLEM": yaml.safe_dump(user_problem, sort_keys=False, allow_unicode=True),
            "DEVICE_INFO": yaml.safe_dump(device_info, sort_keys=False, allow_unicode=True),
            "case_id": case_id,
        }
        return self._invoke("generate_ir", prompt_name, context, rules_ctx["rules_hash"],
                            schema_versions, inputs_hash)

    def generate_bindings(self, case_id: str, ir_yaml: str, device_info: Dict[str, Any],
                          rules_ctx: Dict[str, Any], schema_versions: Dict[str, Any],
                          prompt_name: str = "binding_agent") -> str:
        inputs_hash = stable_hash({"ir_yaml": ir_yaml, "device_info": device_info})
        context = {
            "IR_YAML": ir_yaml,
            "DEVICE_INFO": yaml.safe_dump(device_info, sort_keys=False, allow_unicode=True),
            "case_id": case_id,
        }
        return self._invoke("generate_bindings", prompt_name, context, rules_ctx["rules_hash"],
                            schema_versions, inputs_hash)

    def repair_ir(self, case_id: str, ir_draft: Dict[str, Any], verifier_errors: Any,
                  rules_ctx: Dict[str, Any], schema_versions: Dict[str, Any],
                  prompt_name: str = "repair_agent") -> str:
        inputs_hash = stable_hash({"ir_draft": ir_draft, "verifier_errors": verifier_errors})
        context = {
            "IR_DRAFT": yaml.safe_dump(ir_draft, sort_keys=False, allow_unicode=True),
            "ERRORS": yaml.safe_dump(verifier_errors, sort_keys=False, allow_unicode=True),
            "case_id": case_id,
        }
        return self._invoke("repair_ir", prompt_name, context, rules_ctx["rules_hash"],
                            schema_versions, inputs_hash)

    def repair_bindings(self, case_id: str, bindings_draft: Dict[str, Any], verifier_errors: Any,
                        rules_ctx: Dict[str, Any], schema_versions: Dict[str, Any],
                        prompt_name: str = "repair_agent") -> str:
        inputs_hash = stable_hash({"bindings_draft": bindings_draft, "verifier_errors": verifier_errors})
        context = {
            "BINDINGS_DRAFT": yaml.safe_dump(bindings_draft, sort_keys=False, allow_unicode=True),
            "ERRORS": yaml.safe_dump(verifier_errors, sort_keys=False, allow_unicode=True),
            "case_id": case_id,
        }
        return self._invoke("repair_bindings", prompt_name, context, rules_ctx["rules_hash"],
                            schema_versions, inputs_hash)
