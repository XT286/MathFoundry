FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml /app/
COPY mathfoundry /app/mathfoundry
COPY scripts /app/scripts
COPY queries /app/queries
COPY eval /app/eval

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

EXPOSE 8000
CMD ["uvicorn", "mathfoundry.app:app", "--host", "0.0.0.0", "--port", "8000"]
