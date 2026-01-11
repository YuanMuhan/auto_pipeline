"""LLM-based incremental patch for bindings."""

from typing import List, Dict, Any
import textwrap


def llm_patch_bindings(llm_client, previous_text: str, failure_hints: List[Dict[str, Any]],
                       skeleton: Dict[str, Any], case_id: str, rules_ctx: Dict[str, Any], schema_versions: Dict[str, Any],
                       attempt: int = 1) -> str:
    """
    Build a repair prompt and call LLM provider to patch bindings.
    """
    hints_lines = []
    for h in failure_hints or []:
        hints_lines.append(f"- error={h.get('code')} path={h.get('path')} missing={h.get('missing')} message={h.get('message')}")
    hints_text = "\n".join(hints_lines)
    prompt = textwrap.dedent(f"""
    You are fixing a bindings YAML. Only patch the missing fields mentioned.
    Keep existing content unchanged unless required to fix the errors.
    Output full YAML only, no explanations.

    Failure hints:
    {hints_text}

    Previous bindings (YAML):
    {previous_text}

    Minimal skeleton (for reference):
    {skeleton}
    """)
    # Use repair_bindings interface if available; fallback to generate_bindings with repair prompt
    repaired_text = llm_client.repair_bindings(
        case_id=case_id,
        bindings_draft=previous_text,
        verifier_errors=hints_lines,
        rules_ctx=rules_ctx,
        schema_versions=schema_versions,
        prompt_name="repair_agent",
    )
    return repaired_text
