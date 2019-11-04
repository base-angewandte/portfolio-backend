from rest_framework.authtoken.models import Token

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create an API user and access token'

    def add_arguments(self, parser):
        parser.add_argument('user_name', nargs='+', type=str)

    def handle(self, *args, **options):
        UserModel = get_user_model()

        for username in options['user_name']:
            user, created = UserModel.objects.get_or_create(username=username)
            if created:
                user.set_unusable_password()
                user.save()

            token = Token.objects.create(user=user)
            self.stdout.write(
                self.style.SUCCESS('Successfully created token for user "{}": {}'.format(user.username, token.key))
            )
