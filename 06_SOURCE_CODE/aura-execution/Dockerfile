FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN python -m compileall aura_execution
CMD ["python", "-m", "aura_execution.api.application"]
