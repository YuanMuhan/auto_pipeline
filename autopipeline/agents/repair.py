"""Repair Agent - delegates IR/Bindings repair to LLMClient"""

from typing import Dict, Any
import yaml
from autopipeline.llm.llm_client import LLMClient
from autopipeline.llm.decode import decode_payload, minimal_ir_check, minimal_bindings_check, LLMOutputFormatError, populate_ir_defaults


class RepairAgent:
    """Repair IR or Bindings based on validation errors using LLM client"""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.max_repair_attempts = 3

    def repair_ir(self, ir_data: Dict[str, Any], error_message: str, device_info: Dict[str, Any],
                  rules_ctx: Dict[str, Any], schema_versions: Dict[str, Any], attempt: int = 1) -> Dict[str, Any]:
        repaired_yaml = self.llm.repair_ir(
            case_id=rules_ctx.get("case_id", ""),
            ir_draft=ir_data,
            verifier_errors={"error": error_message},
            rules_ctx=rules_ctx,
            schema_versions=schema_versions,
            prompt_name="repair_agent",
            attempt=attempt
        )
        repaired, _ = decode_payload(repaired_yaml, expected="yaml", stage="repair_ir", attempt=attempt,
                                     output_dir=str(self.llm._raw_dir(rules_ctx.get("case_id", "unknown"))))
        repaired = populate_ir_defaults(repaired, case_id=rules_ctx.get("case_id", ""),
                                        plan_data=ir_data, user_problem=None, fallback=ir_data)
        if not minimal_ir_check(repaired):
            raise LLMOutputFormatError("Repaired IR missing required top-level fields",
                                       stage="repair_ir", attempt=attempt)
        return repaired

    def repair_bindings(self, bindings_data: Dict[str, Any], error_message: str,
                       ir_data: Dict[str, Any], device_info: Dict[str, Any],
                       rules_ctx: Dict[str, Any], schema_versions: Dict[str, Any], attempt: int = 1) -> Dict[str, Any]:
        repaired_yaml = self.llm.repair_bindings(
            case_id=rules_ctx.get("case_id", ""),
            bindings_draft=bindings_data,
            verifier_errors={"error": error_message},
            rules_ctx=rules_ctx,
            schema_versions=schema_versions,
            prompt_name="repair_agent",
            attempt=attempt
        )
        repaired, _ = decode_payload(repaired_yaml, expected="yaml", stage="repair_bindings", attempt=attempt,
                                     output_dir=str(self.llm._raw_dir(rules_ctx.get("case_id", "unknown"))))
        if not minimal_bindings_check(repaired):
            raise LLMOutputFormatError("Repaired bindings missing required fields",
                                       stage="repair_bindings", attempt=attempt)
        return repaired
