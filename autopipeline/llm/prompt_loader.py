from pathlib import Path
from typing import Dict, Any
import yaml
from autopipeline.llm.hash_utils import text_hash


class PromptLoader:
    """Load prompt templates from prompts/ and render with a simple format map."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def load(self, prompt_name: str) -> str:
        prompt_path = self.base_dir / f"{prompt_name}.txt"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")

    def render(self, prompt_name: str, context: Dict[str, Any]) -> Dict[str, str]:
        template = self.load(prompt_name)
        rendered_context = yaml.safe_dump(context, sort_keys=False, allow_unicode=True)
        rendered = f"{template}\n\n# Context\n{rendered_context}"
        return {
            "template": template,
            "template_hash": text_hash(template),
            "rendered": rendered,
            "rendered_hash": text_hash(rendered),
        }
