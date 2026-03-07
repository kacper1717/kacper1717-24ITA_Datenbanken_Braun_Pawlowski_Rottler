FROM python:3.12-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ---------- Test stage ----------
FROM base AS test
RUN pip install --no-cache-dir pytest
RUN pytest -q

# ---------- Runtime stage ----------
FROM base AS runtime
EXPOSE 5000
CMD ["python", "app.py"]