FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY manage.py ./
COPY config/ ./config/
COPY templates/ ./templates/
COPY news/ ./news/

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--noreload", "--insecure"]
