FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY examples ./examples
RUN pip install --no-cache-dir .
ENTRYPOINT ["python", "-m", "ai_inference_reliability_gate"]
CMD ["--input", "examples/inference-snapshot.json"]
