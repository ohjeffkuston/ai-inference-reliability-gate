import unittest

from ai_inference_reliability_gate.engine import evaluate_inference


def fixture():
    policy = {
        "policy_version": "2026-10-20", "max_error_rate_pct": 1.0,
        "max_p95_ttft_ms": 800, "max_p95_e2e_ms": 4000,
        "min_tokens_per_second": 35, "max_gpu_utilization_pct": 90,
        "max_gpu_memory_pct": 92, "max_queue_depth": 50,
        "max_cost_per_1k_tokens_usd": 0.025, "min_request_count": 1000,
        "require_fallback": True,
    }
    snapshot = {
        "service": "support-assistant-v3", "window_minutes": 60,
        "request_count": 2500, "error_rate_pct": 0.4, "p95_ttft_ms": 620,
        "p95_e2e_ms": 3200, "tokens_per_second": 48,
        "gpu_utilization_pct": 76, "gpu_memory_pct": 81, "queue_depth": 18,
        "cost_per_1k_tokens_usd": 0.019, "fallback_healthy": True,
        "telemetry_complete": True,
    }
    return policy, snapshot


class GateTests(unittest.TestCase):
    def test_passes_healthy_snapshot(self):
        p, s = fixture(); self.assertEqual(evaluate_inference(p, s)["decision"], "PASS")

    def test_blocks_error_rate_breach(self):
        p, s = fixture(); s["error_rate_pct"] = 1.1
        self.assertIn("ERROR_RATE_SLO_BREACH", evaluate_inference(p, s)["blocking_reason_codes"])

    def test_blocks_ttft_breach(self):
        p, s = fixture(); s["p95_ttft_ms"] = 801
        self.assertEqual(evaluate_inference(p, s)["decision"], "BLOCK")

    def test_blocks_low_throughput(self):
        p, s = fixture(); s["tokens_per_second"] = 20
        self.assertIn("THROUGHPUT_SLO_BREACH", evaluate_inference(p, s)["blocking_reason_codes"])

    def test_blocks_unhealthy_fallback(self):
        p, s = fixture(); s["fallback_healthy"] = False
        self.assertIn("FALLBACK_UNHEALTHY", evaluate_inference(p, s)["blocking_reason_codes"])

    def test_warns_capacity_headroom(self):
        p, s = fixture(); s["gpu_utilization_pct"] = 95
        self.assertEqual(evaluate_inference(p, s)["decision"], "WARN")

    def test_warns_cost_budget(self):
        p, s = fixture(); s["cost_per_1k_tokens_usd"] = 0.03
        self.assertIn("UNIT_COST_BUDGET_EXCEEDED", evaluate_inference(p, s)["warning_reason_codes"])

    def test_block_takes_precedence_over_warning(self):
        p, s = fixture(); s["p95_e2e_ms"] = 5000; s["queue_depth"] = 70
        self.assertEqual(evaluate_inference(p, s)["decision"], "BLOCK")

    def test_deterministic_fingerprint(self):
        p, s = fixture(); self.assertEqual(evaluate_inference(p, s), evaluate_inference(p, s))

    def test_invalid_percentage_fails_closed(self):
        p, s = fixture(); s["gpu_memory_pct"] = 101
        with self.assertRaises(ValueError): evaluate_inference(p, s)


if __name__ == "__main__":
    unittest.main()
