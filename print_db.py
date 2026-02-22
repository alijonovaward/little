import os

import django
from decouple import config


def main() -> None:
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "config.settings",
    )
    django.setup()

    from django.conf import settings  # noqa: PLC0415

    print(settings.DATABASES.get("default"))


if __name__ == "__main__":
    main()
