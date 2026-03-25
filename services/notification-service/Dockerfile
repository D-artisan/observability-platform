FROM python:3.11-slim
WORKDIR /app
COPY shared /app/shared
COPY notification-service/main.py .
RUN pip install --no-cache-dir -r shared/requirements-common.txt
ENV PYTHONPATH="/app/shared:${PYTHONPATH}"
EXPOSE 8082
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8082", "--log-level", "info"]