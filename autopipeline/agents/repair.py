"""Repair Agent - delegates IR/Bindings repair to LLMClient"""

from typing import Dict, Any
import yaml
from autopipeline.llm.llm_client import LLMClient


class RepairAgent:
    """Repair IR or Bindings based on validation errors using LLM client"""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.max_repair_attempts = 3

    def repair_ir(self, ir_data: Dict[str, Any], error_message: str, device_info: Dict[str, Any],
                  rules_ctx: Dict[str, Any], schema_versions: Dict[str, Any]) -> Dict[str, Any]:
        repaired_yaml = self.llm.repair_ir(
            case_id=rules_ctx.get("case_id", ""),
            ir_draft=ir_data,
            verifier_errors={"error": error_message},
            rules_ctx=rules_ctx,
            schema_versions=schema_versions,
            prompt_name="repair_agent"
        )
        repaired = yaml.safe_load(repaired_yaml)
        if not isinstance(repaired, dict):
            raise ValueError("RepairAgent expected YAML mapping for IR, got non-dict content")
        return repaired

    def repair_bindings(self, bindings_data: Dict[str, Any], error_message: str,
                       ir_data: Dict[str, Any], device_info: Dict[str, Any],
                       rules_ctx: Dict[str, Any], schema_versions: Dict[str, Any]) -> Dict[str, Any]:
        repaired_yaml = self.llm.repair_bindings(
            case_id=rules_ctx.get("case_id", ""),
            bindings_draft=bindings_data,
            verifier_errors={"error": error_message},
            rules_ctx=rules_ctx,
            schema_versions=schema_versions,
            prompt_name="repair_agent"
        )
        repaired = yaml.safe_load(repaired_yaml)
        if not isinstance(repaired, dict):
            raise ValueError("RepairAgent expected YAML mapping for bindings, got non-dict content")
        return repaired
