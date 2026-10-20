"""Deterministic SLO, capacity, and cost evaluation for AI inference."""

from __future__ import annotations

import hashlib
import json
from typing import Any


REQUIRED_POLICY = {
    "max_error_rate_pct", "max_p95_ttft_ms", "max_p95_e2e_ms",
    "min_tokens_per_second", "max_gpu_utilization_pct",
    "max_gpu_memory_pct", "max_queue_depth",
    "max_cost_per_1k_tokens_usd", "min_request_count", "require_fallback",
}
REQUIRED_SNAPSHOT = {
    "service", "window_minutes", "request_count", "error_rate_pct",
    "p95_ttft_ms", "p95_e2e_ms", "tokens_per_second",
    "gpu_utilization_pct", "gpu_memory_pct", "queue_depth",
    "cost_per_1k_tokens_usd", "fallback_healthy", "telemetry_complete",
}


def _fingerprint(value: Any) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _validate(policy: dict[str, Any], snapshot: dict[str, Any]) -> None:
    missing_policy = sorted(REQUIRED_POLICY - policy.keys())
    missing_snapshot = sorted(REQUIRED_SNAPSHOT - snapshot.keys())
    if missing_policy:
        raise ValueError(f"missing policy fields: {', '.join(missing_policy)}")
    if missing_snapshot:
        raise ValueError(f"missing snapshot fields: {', '.join(missing_snapshot)}")
    if snapshot["window_minutes"] <= 0 or snapshot["request_count"] < 0:
        raise ValueError("window_minutes must be positive and request_count non-negative")
    for field in ("error_rate_pct", "gpu_utilization_pct", "gpu_memory_pct"):
        if not 0 <= snapshot[field] <= 100:
            raise ValueError(f"{field} must be between 0 and 100")
    for field in (
        "p95_ttft_ms", "p95_e2e_ms", "tokens_per_second", "queue_depth",
        "cost_per_1k_tokens_usd",
    ):
        if snapshot[field] < 0:
            raise ValueError(f"{field} must be non-negative")


def evaluate_inference(policy: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    """Return PASS, WARN, or BLOCK with explainable evidence and actions."""
    _validate(policy, snapshot)
    blocking: list[str] = []
    warnings: list[str] = []
    actions: list[str] = []

    if not snapshot["telemetry_complete"]:
        blocking.append("TELEMETRY_INCOMPLETE")
        actions.append("Restore required metrics before promotion or scaling changes.")
    if snapshot["error_rate_pct"] > policy["max_error_rate_pct"]:
        blocking.append("ERROR_RATE_SLO_BREACH")
        actions.append("Hold rollout and inspect model server, gateway, and dependency errors.")
    if snapshot["p95_ttft_ms"] > policy["max_p95_ttft_ms"]:
        blocking.append("TTFT_SLO_BREACH")
        actions.append("Inspect queueing, cold starts, batching, and accelerator saturation.")
    if snapshot["p95_e2e_ms"] > policy["max_p95_e2e_ms"]:
        blocking.append("E2E_LATENCY_SLO_BREACH")
        actions.append("Trace preprocessing, inference, and downstream response stages.")
    if snapshot["tokens_per_second"] < policy["min_tokens_per_second"]:
        blocking.append("THROUGHPUT_SLO_BREACH")
        actions.append("Review model size, quantization, batch policy, and serving runtime.")
    if policy["require_fallback"] and not snapshot["fallback_healthy"]:
        blocking.append("FALLBACK_UNHEALTHY")
        actions.append("Restore and test the fallback route before production promotion.")

    if snapshot["gpu_utilization_pct"] > policy["max_gpu_utilization_pct"]:
        warnings.append("GPU_UTILIZATION_HEADROOM_LOW")
        actions.append("Add capacity or tune autoscaling before demand increases.")
    if snapshot["gpu_memory_pct"] > policy["max_gpu_memory_pct"]:
        warnings.append("GPU_MEMORY_HEADROOM_LOW")
        actions.append("Review model placement, memory fragmentation, and replica sizing.")
    if snapshot["queue_depth"] > policy["max_queue_depth"]:
        warnings.append("QUEUE_DEPTH_HIGH")
        actions.append("Tune concurrency, batching, and queue-aware autoscaling.")
    if snapshot["cost_per_1k_tokens_usd"] > policy["max_cost_per_1k_tokens_usd"]:
        warnings.append("UNIT_COST_BUDGET_EXCEEDED")
        actions.append("Compare accelerator mix, utilization, caching, and model routing policy.")
    if snapshot["request_count"] < policy["min_request_count"]:
        warnings.append("SAMPLE_SIZE_LOW")
        actions.append("Collect a larger representative window before final promotion.")

    decision = "BLOCK" if blocking else "WARN" if warnings else "PASS"
    ratios = {
        "error_rate": round(snapshot["error_rate_pct"] / policy["max_error_rate_pct"], 3),
        "ttft": round(snapshot["p95_ttft_ms"] / policy["max_p95_ttft_ms"], 3),
        "e2e_latency": round(snapshot["p95_e2e_ms"] / policy["max_p95_e2e_ms"], 3),
        "gpu_utilization": round(snapshot["gpu_utilization_pct"] / policy["max_gpu_utilization_pct"], 3),
        "gpu_memory": round(snapshot["gpu_memory_pct"] / policy["max_gpu_memory_pct"], 3),
        "queue_depth": round(snapshot["queue_depth"] / policy["max_queue_depth"], 3),
        "unit_cost": round(snapshot["cost_per_1k_tokens_usd"] / policy["max_cost_per_1k_tokens_usd"], 3),
    }
    result = {
        "service": snapshot["service"],
        "decision": decision,
        "blocking_reason_codes": sorted(set(blocking)),
        "warning_reason_codes": sorted(set(warnings)),
        "recommended_actions": sorted(set(actions)),
        "threshold_ratios": ratios,
        "window_minutes": snapshot["window_minutes"],
        "request_count": snapshot["request_count"],
        "policy_version": policy.get("policy_version", "unversioned"),
    }
    result["evidence_fingerprint"] = _fingerprint({"policy": policy, "snapshot": snapshot, "result": result})
    return result
