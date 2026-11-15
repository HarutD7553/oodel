import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Create or update the staff account configured for the baker portal.'

    def handle(self, *args, **options):
        username = os.environ.get('BAKER_USERNAME', '').strip()
        password = os.environ.get('BAKER_PASSWORD', '')
        if not username and not password:
            self.stdout.write(self.style.WARNING('BAKER_USERNAME and BAKER_PASSWORD are not set; skipping staff setup.'))
            return
        if not username or not password:
            raise CommandError('BAKER_USERNAME and BAKER_PASSWORD must both be set.')

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(username=username)
        user.is_staff = True
        user.is_active = True
        user.set_password(password)
        user.save()
        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{action} baker staff account {username!r}.'))
