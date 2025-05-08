FROM python:3.9.22-bullseye AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

FROM python:3.9.22-slim-bullseye

WORKDIR /app

COPY --from=builder /usr/local /usr/local

COPY --from=builder /app /app

EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]