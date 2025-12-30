from dataclasses import dataclass
from typing import Any, Dict, Optional


class ErrorCode:
    E_SCHEMA_UP = "E_SCHEMA_UP"
    E_SCHEMA_DI = "E_SCHEMA_DI"
    E_SCHEMA_IR = "E_SCHEMA_IR"
    E_SCHEMA_BIND = "E_SCHEMA_BIND"
    E_INPUT_INVALID = "E_INPUT_INVALID"
    E_CATALOG_COMPONENT = "E_CATALOG_COMPONENT"
    E_ENDPOINT_TYPE = "E_ENDPOINT_TYPE"
    E_ENDPOINT_MISSING_FIELDS = "E_ENDPOINT_MISSING_FIELDS"
    E_BOUNDARY = "E_BOUNDARY"
    E_COVERAGE = "E_COVERAGE"
    E_ENDPOINT_CHECK = "E_ENDPOINT_CHECK"
    E_PLACEMENT_INVALID = "E_PLACEMENT_INVALID"
    E_RUNTIME_COMPOSE_CONFIG = "E_RUNTIME_COMPOSE_CONFIG"
    E_RUNTIME_BUILD = "E_RUNTIME_BUILD"
    E_RUNTIME_HEALTH = "E_RUNTIME_HEALTH"
    E_LLM_API_ERROR = "E_LLM_API_ERROR"
    E_LLM_OUTPUT_FORMAT = "E_LLM_OUTPUT_FORMAT"
    E_LLM_OUTPUT_INVALID = "E_LLM_OUTPUT_INVALID"
    E_CHECKER_FAIL = "E_CHECKER_FAIL"
    E_UNKNOWN = "E_UNKNOWN"


@dataclass
class FailureRecord:
    code: str
    stage: str
    checker: str
    message: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "code": self.code,
            "stage": self.stage,
            "checker": self.checker,
            "message": self.message,
        }
        if self.details:
            data["details"] = self.details
        return data


def failure(code: str, stage: str, checker: str, message: str, details: Optional[Dict[str, Any]] = None) -> FailureRecord:
    """Helper to quickly build FailureRecord instances."""
    return FailureRecord(code=code, stage=stage, checker=checker, message=message, details=details or {})
