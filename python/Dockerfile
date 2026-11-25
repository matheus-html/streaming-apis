FROM python:3.12-slim
ARG MODULE
ENV MODULE=${MODULE} PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements-core.txt requirements-${MODULE}.txt ./
RUN pip install --no-cache-dir -r requirements-core.txt -r requirements-${MODULE}.txt
COPY core ./core
COPY ${MODULE} ./${MODULE}
CMD ["sh", "-c", "exec python -m ${MODULE}.servidor"]