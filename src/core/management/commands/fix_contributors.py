import requests
from progressbar import progressbar

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.models import Entry


class Command(BaseCommand):
    help = 'Fix invalid contributors'

    def handle(self, *args, **options):
        if None in (
            settings.USER_PREFERENCES_API_BASE,
            settings.USER_PREFERENCES_API_KEY,
        ):
            raise CommandError('A config parameter is missing in .env! Cannot run command.')

        for e in progressbar(Entry.objects.all()):
            if e.data and e.data.get('contributors'):
                need_to_save = False
                contributors = e.data['contributors']
                for idx, contributor in enumerate(contributors):
                    if not contributor.get('label'):
                        r = requests.get(
                            settings.USER_PREFERENCES_API_BASE + f'users/{e.owner.username}/',
                            headers={'X-Api-Key': settings.USER_PREFERENCES_API_KEY},
                        )
                        if r.status_code == 200:
                            need_to_save = True
                            response = r.json()
                            e.data['contributors'][idx]['label'] = response.get('name')
                            e.data['contributors'][idx]['source'] = e.owner.username
                        else:
                            self.stdout.write(
                                self.style.WARNING(f'Could not fetch user information for {e.owner.username}')
                            )
                if need_to_save:
                    e.save()
        self.stdout.write(self.style.SUCCESS('Successfully fixed contributors'))
