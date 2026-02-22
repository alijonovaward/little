from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.customer.models import Profile

class Command(BaseCommand):
    help = 'Creates a superuser with username user1 and password admin123'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'user1'
        email = 'user1@example.com'
        password = 'admin123'

        # Delete existing if any to ensure fresh start
        User.objects.filter(username=username).delete()

        # Create superuser
        user = User.objects.create_superuser(username, email, password)
        
        # Ensure Profile exists
        Profile.objects.get_or_create(
            origin=user,
            defaults={
                'full_name': 'Admin User',
                'phone_number': '+998001112233'
            }
        )

        self.stdout.write(self.style.SUCCESS(f'Successfully created superuser "{username}" with password "{password}"'))
