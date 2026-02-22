import os
import django

from decouple import config


def _setup_django() -> None:
    database_url = config("DATABASE_URL", default=None)
    if not database_url:
        raise SystemExit(
            "DATABASE_URL is required. Set it in your environment (or a local .env file) before running this script."
        )

    os.environ.setdefault("DATABASE_URL", database_url)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()


_setup_django()

from apps.customer.models import User, Profile, B2BApplication
from apps.product.models import Phone, Ticket, Good

def verify_server_data():
    print("--- SERVER DATA VERIFICATION (NEON DB) ---")
    
    # 1. Check Superuser
    try:
        superadmin = User.objects.get(username='superadmin')
        print(f"✅ Superuser 'superadmin' exists. Is staff: {superadmin.is_staff}")
    except User.DoesNotExist:
        print("❌ Superuser 'superadmin' not found!")

    # 2. Check Tables
    print(f"Users count: {User.objects.count()}")
    print(f"B2B Applications count: {B2BApplication.objects.count()}")
    print(f"Products (Phones) count: {Phone.objects.count()}")

    print("\n--- B2B LOGIC VERIFICATION ---")
    # Simulate a B2B application if not exists or check current ones
    apps = B2BApplication.objects.all()
    if apps.exists():
        for app in apps:
            print(f"App by {app.user.username}: Status={app.status}, Is B2B after: {app.user.is_b2b}")
    else:
        print("No B2B applications found to verify automation.")

if __name__ == "__main__":
    verify_server_data()
