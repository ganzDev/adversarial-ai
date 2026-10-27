FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/ ./agents/
COPY environment/ ./environment/
COPY security/ ./security/

EXPOSE 8000

CMD ["uvicorn", "environment.api:app", "--host", "0.0.0.0", "--port", "8000"]
