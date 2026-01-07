import yaml
from autopipeline.normalize.bindings_normalizer import normalize_bindings


def test_normalizer_generates_stubs():
    ir = {"app_name": "app", "version": "1.0", "components": [{"id": "c1"}, {"id": "c2"}]}
    raw = {"transports": []}  # missing component_bindings
    norm, actions = normalize_bindings(raw, ir, {}, gate_mode="core")
    assert norm.get("component_bindings")
    assert any(cb.get("is_stub") for cb in norm["component_bindings"])
    # Should be valid YAML output
    yaml.safe_dump(norm)
