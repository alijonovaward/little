import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from apps.customer.models import Profile

User = get_user_model()

def create_test_user():
    username = "frontend_tester"
    password = "password123"
    phone_number = "+998901234567"

    user, created = User.objects.get_or_create(username=username)
    user.set_password(password)
    user.is_wholesaler = True
    user.is_approved = True
    user.is_b2b = True
    user.save()

    # Create or update profile
    profile, p_created = Profile.objects.get_or_create(origin=user)
    profile.full_name = "Frontend Tester"
    profile.phone_number = phone_number
    profile.save()

    print("-" * 30)
    print("TEST USER READY")
    print("-" * 30)
    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"Phone:    {phone_number}")
    print("-" * 30)
    print("Permissions:")
    print(f"  is_wholesaler: {user.is_wholesaler}")
    print(f"  is_approved:   {user.is_approved}")
    print(f"  is_b2b:        {user.is_b2b}")
    print("-" * 30)

if __name__ == "__main__":
    create_test_user()
