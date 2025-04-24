FROM python:3.11-slim

# Установка необходимых системных пакетов, включая GraphViz
RUN apt-get update && apt-get install -y graphviz && apt-get clean && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY . .

# Открытие порта
EXPOSE 8000

# Запуск Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "lost_and_found.wsgi:application"]