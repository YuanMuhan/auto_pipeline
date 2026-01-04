from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from autopipeline.llm.hash_utils import text_hash


class PromptLoader:
    """Load prompt templates from prompts/ and render with a simple format map."""

    def __init__(self, base_dir: Path, tier: str = "P0"):
        self.base_dir = base_dir
        self.tier = tier

    def load(self, prompt_name: str) -> str:
        tier_path = self.base_dir / self.tier / f"{prompt_name}.txt"
        fallback_path = self.base_dir / "P0" / f"{prompt_name}.txt"
        legacy_path = self.base_dir / f"{prompt_name}.txt"
        if tier_path.exists():
            return tier_path.read_text(encoding="utf-8")
        if fallback_path.exists():
            return fallback_path.read_text(encoding="utf-8")
        if legacy_path.exists():
            return legacy_path.read_text(encoding="utf-8")
        raise FileNotFoundError(f"Prompt template not found for tier {self.tier}: {tier_path}")

    def render(self, prompt_name: str, context: Dict[str, Any], injections: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        template = self.load(prompt_name)
        rendered_template = template
        if injections:
            for key, val in injections.items():
                rendered_template = rendered_template.replace(f"{{{{{key}}}}}", val)
        rendered_context = yaml.safe_dump(context, sort_keys=False, allow_unicode=True)
        rendered = f"{rendered_template}\n\n# Context\n{rendered_context}"
        return {
            "template": template,
            "template_hash": text_hash(template),
            "rendered": rendered,
            "rendered_hash": text_hash(rendered),
        }
