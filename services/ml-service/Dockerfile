FROM python:3.12-slim
WORKDIR /app
RUN groupadd -r vigil && useradd -r -g vigil vigil
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY artifacts ./artifacts
USER vigil
EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
