import random
from .models import Profile


def generate_otp():
    return random.randint(1000, 9999)
