"""Planner Agent - produces pre-IR plan artifacts"""

from typing import Dict, Any
from datetime import datetime
from autopipeline.agents.prompt_utils import PromptTemplate


class PlannerAgent:
    """Generate a high-level plan from user problem and device info"""

    def __init__(self):
        self.prompt_template = PromptTemplate()

    def generate_plan(self, user_problem: Dict[str, Any], device_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a planning artifact (pre-IR) from user problem.

        This is a prompt-only simulation - in real implementation, this would call LLM.
        """

        # Build prompt using template (placeholder for LLM call)
        _ = self.prompt_template.get_ir_prompt(user_problem, device_info)

        # Deterministic plan generation
        plan = self._simulate_plan_generation(user_problem, device_info)

        return plan

    def _simulate_plan_generation(self, user_problem: Dict[str, Any], device_info: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate plan generation (placeholder for LLM output)"""

        problem_type = user_problem.get('type', 'monitoring')
        description = user_problem.get('description', '')
        requirements = user_problem.get('requirements', [])
        constraints = user_problem.get('constraints', {})

        # High-level component/link hints (purely logical) based on problem type
        components = []
        links = []

        if problem_type == 'monitoring':
            # Sensor -> Processor -> Storage pattern
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

        elif problem_type == 'control':
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

        elif problem_type == 'automation':
            # Smart-home style automation
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

        else:
            components = [
                {"id": "starter", "type": "source", "capabilities": ["emit"]},
                {"id": "sink", "type": "sink", "capabilities": ["communicate"]},
            ]
            links = [
                {"id": "link_default", "from": "starter", "to": "sink", "data_type": "message"},
            ]

        return {
            "app_name": f"{problem_type}_app",
            "description": description,
            "version": "0.1.0",
            "problem_type": problem_type,
            "requirements": requirements,
            "constraints": constraints,
            "components_outline": components,
            "links_outline": links,
            "notes": "Deterministic planner output (pre-IR)",
            "generated_at": datetime.now().isoformat(),
        }
