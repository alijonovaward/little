import csv
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from your_app.models import Profile

User = get_user_model()


class Command(BaseCommand):
    help = "Import users from CSV"

    def handle(self, *args, **kwargs):
        with open('auth_user.csv', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                username = row['username']

                if User.objects.filter(username=username).exists():
                    print(f"{username} already exists")
                    continue

                user = User.objects.create(
                    username=username,
                    password=row['password'],  # HASH 그대로
                    is_superuser=row['is_superuser'] == 't',
                    is_staff=row['is_staff'] == 't',
                    is_active=row['is_active'] == 't',
                    date_joined=row['date_joined']
                )

                Profile.objects.create(
                    origin=user,
                    full_name="",
                    phone_number=username,  # telefon username ichida
                )

                print(f"{username} imported successfully")
