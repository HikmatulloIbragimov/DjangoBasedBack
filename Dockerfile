# Dockerfile
FROM python:3.11

# Установка рабочей директории
WORKDIR /app

# Копируем весь проект внутрь контейнера
COPY . .

# Устанавливаем зависимости
RUN pip install --upgrade pip && pip install -r requirements.txt

# Статические файлы (если надо)
# RUN python manage.py collectstatic --noinput

# Запуск gunicorn по умолчанию
CMD ["gunicorn", "bek.wsgi:application", "--bind", "0.0.0.0:8000"]
