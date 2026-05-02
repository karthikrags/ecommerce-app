FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY genproto/ ./
COPY server.py .

RUN addgroup --gid 1000 appgroup && adduser --uid 1000 --gid 1000 --disabled-password appuser
USER appuser

ENV PORT=5050
EXPOSE 5050

CMD ["python", "server.py"]
