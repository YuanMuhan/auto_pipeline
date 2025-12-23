"""IR Agent - generates IR from plan and user problem"""

from typing import Dict, Any, List
from datetime import datetime
import yaml
from autopipeline.llm.llm_client import LLMClient


class IRAgent:
    """Generate IR (Intermediate Representation) from plan + user problem + device info"""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def generate_ir(self, plan_data: Dict[str, Any], user_problem: Dict[str, Any],
                    device_info: Dict[str, Any], rules_ctx: Dict[str, Any],
                    schema_versions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate IR from plan and user problem.

        Uses LLM client; returns parsed IR dict.
        """
        ir_yaml = self.llm.generate_ir(
            case_id=rules_ctx.get("case_id", ""),
            user_problem=user_problem,
            device_info=device_info,
            rules_ctx=rules_ctx,
            schema_versions=schema_versions,
            prompt_name="ir_agent"
        )
        return yaml.safe_load(ir_yaml)

    def _simulate_ir_generation(self, plan_data: Dict[str, Any], user_problem: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic IR generation based on plan outlines or user problem type"""
        problem_type = plan_data.get("problem_type") or user_problem.get("type", "monitoring")

        components_outline: List[Dict[str, Any]] = plan_data.get("components_outline") or []
        links_outline: List[Dict[str, Any]] = plan_data.get("links_outline") or []

        # If plan provides outlines, use them; otherwise fall back to defaults
        if not components_outline or not links_outline:
            components_outline, links_outline = self._default_topology(problem_type)

        ir_components = []
        for comp in components_outline:
            ir_components.append({
                "id": comp.get("id"),
                "type": comp.get("type"),
                "capabilities": comp.get("capabilities", []),
                "metadata": comp.get("metadata", {}),
            })

        ir_links = []
        for link in links_outline:
            ir_links.append({
                "id": link.get("id"),
                "from": link.get("from"),
                "to": link.get("to"),
                "data_type": link.get("data_type", "data"),
                "frequency": link.get("frequency", "event-driven"),
                "contract": link.get("contract", {}),
            })

        return {
            "app_name": plan_data.get("app_name", f"{problem_type}_app"),
            "description": plan_data.get("description", user_problem.get("description", "")),
            "version": plan_data.get("version", "1.0"),
            "schemas": plan_data.get("schemas", []),
            "components": ir_components,
            "links": ir_links,
            "policies": plan_data.get("policies", []),
            "logic": {},
            "metadata": {
                "description": user_problem.get('description', 'Generated IR'),
                "created_at": datetime.now().isoformat(),
                "version": plan_data.get("version", "1.0")
            }
        }

    def _default_topology(self, problem_type: str):
        """Fallback topology when plan does not provide outlines"""
        if problem_type == "automation":
            components = [
                {"id": "door_monitor", "type": "data_source", "capabilities": ["detect_state_change", "binary_sensing"]},
                {"id": "motion_detector", "type": "sensor", "capabilities": ["detect_motion", "presence_sensing"]},
                {"id": "lighting_controller", "type": "actuator", "capabilities": ["control_light", "dimming"]},
                {"id": "automation_engine", "type": "processor", "capabilities": ["rule_eval", "event_routing", "mode_management"]},
                {"id": "notification_service", "type": "notification", "capabilities": ["push_alert", "message_delivery"]},
                {"id": "data_recorder", "type": "storage", "capabilities": ["store", "query", "time_series"]},
            ]
            links = [
                {"id": "link_door_to_engine", "from": "door_monitor", "to": "automation_engine",
                 "data_type": "state_event", "frequency": "event-driven"},
                {"id": "link_motion_to_engine", "from": "motion_detector", "to": "automation_engine",
                 "data_type": "motion_event", "frequency": "event-driven"},
                {"id": "link_engine_to_light", "from": "automation_engine", "to": "lighting_controller",
                 "data_type": "control_command", "frequency": "on-demand"},
                {"id": "link_engine_to_notify", "from": "automation_engine", "to": "notification_service",
                 "data_type": "alert", "frequency": "event-driven"},
                {"id": "link_engine_to_storage", "from": "automation_engine", "to": "data_recorder",
                 "data_type": "event_log", "frequency": "periodic"},
            ]
        elif problem_type == "control":
            components = [
                {"id": "sensor_input", "type": "sensor", "capabilities": ["measure"]},
                {"id": "controller", "type": "controller", "capabilities": ["decide", "control"]},
                {"id": "actuator_output", "type": "actuator", "capabilities": ["actuate"]},
            ]
            links = [
                {"id": "link_sensor_to_controller", "from": "sensor_input", "to": "controller",
                 "data_type": "measurement"},
                {"id": "link_controller_to_actuator", "from": "controller", "to": "actuator_output",
                 "data_type": "command"},
            ]
        else:  # monitoring and default
            components = [
                {"id": "sensor_collector", "type": "data_source", "capabilities": ["sense", "collect"]},
                {"id": "data_processor", "type": "processor", "capabilities": ["filter", "aggregate", "analyze"]},
                {"id": "storage_service", "type": "storage", "capabilities": ["store", "query"]},
            ]
            links = [
                {"id": "link_sensor_to_processor", "from": "sensor_collector", "to": "data_processor",
                 "data_type": "sensor_reading", "frequency": "real-time"},
                {"id": "link_processor_to_storage", "from": "data_processor", "to": "storage_service",
                 "data_type": "processed_data", "frequency": "periodic"},
            ]
        return components, links
