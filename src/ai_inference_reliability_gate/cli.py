"""Command-line interface for the reliability gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import evaluate_inference


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate AI inference reliability evidence")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = evaluate_inference(payload["policy"], payload["snapshot"])
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 1 if result["decision"] == "BLOCK" else 0
