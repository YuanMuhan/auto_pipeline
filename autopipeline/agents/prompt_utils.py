"""Prompt template utilities"""

import os
from pathlib import Path
from typing import Dict, Any
import json
import yaml


class PromptTemplate:
    """Load and fill prompt templates"""

    def __init__(self):
        self.prompts_dir = Path(__file__).parent.parent.parent / "prompts"

    def load_template(self, template_name: str) -> str:
        """Load a prompt template file"""
        template_path = self.prompts_dir / "P0" / f"{template_name}.txt"
        legacy_path = self.prompts_dir / f"{template_name}.txt"
        if template_path.exists():
            path = template_path
        elif legacy_path.exists():
            path = legacy_path
        else:
            raise FileNotFoundError(f"Prompt template not found: {template_path}")

        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def fill_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Fill template with variables"""
        result = template
        for key, value in variables.items():
            placeholder = "{{" + key + "}}"

            # Convert value to string representation
            if isinstance(value, (dict, list)):
                value_str = yaml.dump(value, default_flow_style=False, allow_unicode=True)
            else:
                value_str = str(value)

            result = result.replace(placeholder, value_str)

        return result

    def get_ir_prompt(self, user_problem: Dict[str, Any], device_info: Dict[str, Any]) -> str:
        """Get filled IR agent prompt"""
        template = self.load_template("ir_agent")
        return self.fill_template(template, {
            "USER_PROBLEM": user_problem,
            "DEVICE_INFO": device_info
        })

    def get_binding_prompt(self, ir_data: Dict[str, Any], device_info: Dict[str, Any]) -> str:
        """Get filled binding agent prompt"""
        template = self.load_template("binding_agent")

        # Extract available endpoints
        available_endpoints = []
        for device in device_info.get('devices', []):
            device_id = device.get('id', '')
            interfaces = device.get('interfaces', {})
            endpoints = interfaces.get('endpoints', [])
            for ep in endpoints:
                available_endpoints.append({
                    'device': device_id,
                    'address': ep.get('address', ''),
                    'protocol': ep.get('protocol', 'unknown')
                })

        return self.fill_template(template, {
            "IR": ir_data,
            "DEVICE_INFO": device_info,
            "AVAILABLE_ENDPOINTS": available_endpoints
        })

    def get_repair_prompt(self, artifact_type: str, current_artifact: Dict[str, Any],
                         error_message: str, ir_data: Dict[str, Any],
                         device_info: Dict[str, Any]) -> str:
        """Get filled repair agent prompt"""
        template = self.load_template("repair_agent")
        return self.fill_template(template, {
            "ARTIFACT_TYPE": artifact_type,
            "CURRENT_ARTIFACT": current_artifact,
            "ERROR_MESSAGE": error_message,
            "IR": ir_data if ir_data else {},
            "DEVICE_INFO": device_info
        })
