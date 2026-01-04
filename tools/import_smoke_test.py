"""Minimal import smoke test to catch circular/absent exports."""


def main():
    import sys
    sys.path.append(".")
    imports = [
        "autopipeline",
        "autopipeline.llm.llm_client",
        "autopipeline.eval.evaluate_artifacts",
        "autopipeline.eval.validators_registry",
        "autopipeline.catalog.catalog_utils",
    ]
    for path in imports:
        __import__(path)
        print(f"Imported {path} OK")


if __name__ == "__main__":
    main()
