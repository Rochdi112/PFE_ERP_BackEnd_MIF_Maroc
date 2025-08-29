FROM python:3.11
WORKDIR /app
COPY . .
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1
RUN pip install --no-cache-dir -r requirements.txt
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
