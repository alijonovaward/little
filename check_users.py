from django.contrib.auth import get_user_model
from apps.customer.models import Profile, Phone

User = get_user_model()

def check_users():
    users = User.objects.all().values('username', 'phone', 'is_active', 'is_staff')
    print(f"Total users: {users.count()}")
    for u in users[:5]:
        print(u)
        
    # Check for specific test user
    if User.objects.filter(phone='998901234567').exists():
        print("Test user 998901234567 exists.")
    else:
        print("Test user 998901234567 does NOT exist.")

if __name__ == "__main__":
    check_users()
