FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY genproto/ ./
COPY app.py .
COPY templates/ templates/

RUN addgroup --gid 1000 appgroup && adduser --uid 1000 --gid 1000 --disabled-password appuser
USER appuser

ENV PORT=8080
ENV FLASK_ENV=production
EXPOSE 8080

CMD ["python", "app.py"]
