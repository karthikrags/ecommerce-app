FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY locustfile.py .

RUN groupadd -g 1000 appgroup && useradd -u 1000 -g appgroup -M appuser
USER appuser

ENV FRONTEND_ADDR=http://frontend:80
ENV USERS=10
ENV RATE=1

CMD ["locust", "--headless", \
     "--host", "http://frontend:80", \
     "--users", "10", \
     "--spawn-rate", "1", \
     "-f", "locustfile.py"]
