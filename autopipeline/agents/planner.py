"""Planner Agent - decomposes user problem into IR (Intermediate Representation)"""

from typing import Dict, Any
from datetime import datetime
from autopipeline.agents.prompt_utils import PromptTemplate


class PlannerAgent:
    """Generate IR from user problem and device info using prompt-based reasoning"""

    def __init__(self):
        self.prompt_template = PromptTemplate()

    def generate_ir(self, user_problem: Dict[str, Any], device_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate IR (Intermediate Representation) from user problem

        This is a prompt-only simulation - in real implementation, this would call LLM
        """

        # Build prompt using template
        prompt = self.prompt_template.get_ir_prompt(user_problem, device_info)

        # For now, generate a deterministic IR based on the problem
        # In production, this would be LLM-generated with the prompt
        ir = self._simulate_ir_generation(user_problem, device_info)

        return ir

    def _simulate_ir_generation(self, user_problem: Dict[str, Any], device_info: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate IR generation (placeholder for LLM output)"""

        problem_type = user_problem.get('type', 'monitoring')

        # Generate components based on problem type (renamed from entities)
        components = []
        links = []

        if problem_type == 'monitoring':
            # Sensor -> Processor -> Storage pattern
            components = [
                {
                    "id": "sensor_collector",
                    "type": "data_source",
                    "capabilities": ["sense", "collect"]
                },
                {
                    "id": "data_processor",
                    "type": "processor",
                    "capabilities": ["filter", "aggregate", "analyze"]
                },
                {
                    "id": "storage_service",
                    "type": "storage",
                    "capabilities": ["store", "query"]
                }
            ]

            links = [
                {
                    "id": "link_sensor_to_processor",
                    "from": "sensor_collector",
                    "to": "data_processor",
                    "data_type": "sensor_reading",
                    "frequency": "real-time"
                },
                {
                    "id": "link_processor_to_storage",
                    "from": "data_processor",
                    "to": "storage_service",
                    "data_type": "processed_data",
                    "frequency": "periodic"
                }
            ]

        elif problem_type == 'control':
            # Sensor -> Controller -> Actuator pattern
            components = [
                {
                    "id": "sensor_input",
                    "type": "sensor",
                    "capabilities": ["measure"]
                },
                {
                    "id": "controller",
                    "type": "controller",
                    "capabilities": ["decide", "control"]
                },
                {
                    "id": "actuator_output",
                    "type": "actuator",
                    "capabilities": ["actuate"]
                }
            ]

            links = [
                {
                    "id": "link_sensor_to_controller",
                    "from": "sensor_input",
                    "to": "controller",
                    "data_type": "measurement"
                },
                {
                    "id": "link_controller_to_actuator",
                    "from": "controller",
                    "to": "actuator_output",
                    "data_type": "command"
                }
            ]

        elif problem_type == 'automation':
            # Multi-sensor -> Automation Engine -> Actuators + Notifier + Storage
            # For smart home automation with door sensor, motion sensor, light, notifications
            components = [
                {
                    "id": "door_monitor",
                    "type": "data_source",
                    "capabilities": ["detect_state_change", "binary_sensing"]
                },
                {
                    "id": "motion_detector",
                    "type": "sensor",
                    "capabilities": ["detect_motion", "presence_sensing"]
                },
                {
                    "id": "lighting_controller",
                    "type": "actuator",
                    "capabilities": ["control_light", "dimming"]
                },
                {
                    "id": "automation_engine",
                    "type": "processor",
                    "capabilities": ["rule_eval", "event_routing", "mode_management"]
                },
                {
                    "id": "notification_service",
                    "type": "notification",
                    "capabilities": ["push_alert", "message_delivery"]
                },
                {
                    "id": "data_recorder",
                    "type": "storage",
                    "capabilities": ["store", "query", "time_series"]
                }
            ]

            links = [
                {
                    "id": "link_door_to_engine",
                    "from": "door_monitor",
                    "to": "automation_engine",
                    "data_type": "state_event",
                    "frequency": "event-driven"
                },
                {
                    "id": "link_motion_to_engine",
                    "from": "motion_detector",
                    "to": "automation_engine",
                    "data_type": "motion_event",
                    "frequency": "event-driven"
                },
                {
                    "id": "link_engine_to_light",
                    "from": "automation_engine",
                    "to": "lighting_controller",
                    "data_type": "control_command",
                    "frequency": "on-demand"
                },
                {
                    "id": "link_engine_to_notify",
                    "from": "automation_engine",
                    "to": "notification_service",
                    "data_type": "alert",
                    "frequency": "event-driven"
                },
                {
                    "id": "link_engine_to_storage",
                    "from": "automation_engine",
                    "to": "data_recorder",
                    "data_type": "event_log",
                    "frequency": "periodic"
                }
            ]

        return {
            "components": components,  # Changed from "entities"
            "links": links,
            "logic": {},  # Added logic field
            "metadata": {
                "description": user_problem.get('description', 'Generated IR'),
                "created_at": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
