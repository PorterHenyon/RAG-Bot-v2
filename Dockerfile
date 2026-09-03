# Lightweight ticket tracker — no ML/RAG dependencies
FROM python:3.11-slim

WORKDIR /app

COPY requirements-tracker.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-tracker.txt

COPY ticket_tracker.py .

CMD ["python", "-u", "ticket_tracker.py"]
