# AI Inference Reliability Gate — Deployment and Learning Guide

To: ohjeffkuston@yahoo.ca

## Project purpose

This project demonstrates how Cloud, DevOps, SRE, and Platform Engineering practices apply to production AI inference. It evaluates user-visible inference quality, accelerator capacity, unit cost, and fallback readiness through a deterministic policy gate.

## What you built

The Python engine accepts a versioned policy and a fixed telemetry snapshot. It returns `PASS`, `WARN`, or `BLOCK`, plus reason codes, recommended actions, threshold ratios, and a stable evidence fingerprint. It makes no network or production changes.

## Deploy and run

```bash
git clone https://github.com/ohjeffkuston/ai-inference-reliability-gate
cd ai-inference-reliability-gate
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python -m ai_inference_reliability_gate --input examples/inference-snapshot.json
```

Docker:

```bash
docker build -t ai-inference-reliability-gate .
docker run --rm ai-inference-reliability-gate
```

## File guide

- `engine.py`: validation, policy comparison, decisions, actions, and fingerprinting.
- `cli.py`: JSON input/output wrapper and CI-friendly exit status.
- `tests/test_engine.py`: healthy, breach, capacity, cost, precedence, determinism, and invalid-input cases.
- `examples/inference-snapshot.json`: safe sample policy and telemetry.
- `.github/workflows/ci.yml`: repeatable GitHub Actions validation.
- `Dockerfile`: portable runtime packaging.
- `n8n/`: inactive manual-trigger integration template.
- `docs/architecture.png`: minimal architecture visual for GitHub and publishing.

## Production adaptation

1. Define separate SLO policies for interactive, batch, embedding, and agent workloads.
2. Query Prometheus, OpenTelemetry, or cloud monitoring through a read-only identity.
3. Create a fixed, traceable evidence window.
4. Run the gate in CI/CD or an internal developer platform.
5. Send WARN/BLOCK results to change approval.
6. Keep scaling and deployment credentials in a different service.
7. Test fallback capacity rather than trusting a health check.

## Interview positioning

Explain that conventional HTTP availability does not fully describe AI inference quality. Discuss TTFT, generation throughput, queueing, GPU memory, unit economics, and fallback behavior. Emphasize that the policy gate is deterministic because authorization should be explainable, while AI assistance can remain downstream for investigation and summarization.

Good interview questions to prepare:

1. Why is time to first token different from end-to-end latency?
2. When should high GPU utilization warn rather than block?
3. How would you collect trustworthy evidence from Kubernetes?
4. How would you set SLOs for batch versus interactive inference?
5. Why are production credentials kept outside the gate?
6. How would you validate a fallback under load?

## Extensions

- Prometheus query adapter with read-only authentication
- OpenTelemetry traces for stage-level latency
- Kubernetes HPA/KEDA recommendation output without automatic mutation
- Model-version and canary cohort comparison
- Multi-region fallback evidence
- Cost attribution by tenant and model route
