import os
import django
from django.contrib.auth import get_user_model

# Настройка окружения (путь к твоему файлу настроек на сервере)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

User = get_user_model()

# Берем данные из переменных окружения Render
username = os.environ.get('ADMIN_USERNAME', 'admin')
password = os.environ.get('ADMIN_PASSWORD', 'admin123')
email = 'admin@example.com'

if not User.objects.filter(username=username).exists():
    print(f"Creating superuser for {username}...")
    User.objects.create_superuser(username=username, email=email, password=password)
    print("Superuser created successfully!")
else:
    print("Superuser already exists.")