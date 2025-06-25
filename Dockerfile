FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
# Додаємо всі потрібні бібліотеки для Pillow
RUN apt-get update && apt-get install -y gcc libpq-dev zlib1g-dev libjpeg-dev libpng-dev

RUN pip install --no-cache-dir -r requirements.txt

# Ensure alembic and other pip-installed scripts are in PATH
ENV PATH="/root/.local/bin:$PATH"

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]