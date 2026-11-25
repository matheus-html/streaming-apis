FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN pip install --no-cache-dir "locust>=2.32,<3" grpcio grpcio-tools
ENTRYPOINT ["locust"]