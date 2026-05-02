FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy generated proto files and service code
COPY genproto/ ./
COPY server.py .

RUN addgroup --gid 1000 appgroup && adduser --uid 1000 --gid 1000 --disabled-password appuser
USER appuser

ENV PORT=7000
EXPOSE 7000

CMD ["python", "server.py"]
