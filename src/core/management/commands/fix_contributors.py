import requests
from progressbar import progressbar
from titlecase import titlecase

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.models import Entry
from core.skosmos import get_preflabel


class Command(BaseCommand):
    help = 'Fix invalid contributors'

    def handle(self, *args, **options):
        if None in (
            settings.USER_PREFERENCES_API_BASE,
            settings.USER_PREFERENCES_API_KEY,
        ):
            raise CommandError(
                'A config parameter is missing in .env! Cannot run command.'
            )

        for e in progressbar(Entry.objects.all()):
            if e.data and e.data.get('contributors'):
                need_to_save = False
                contributors = e.data['contributors']
                for idx, contributor in enumerate(contributors):
                    if not contributor.get('label'):
                        r = requests.get(
                            settings.USER_PREFERENCES_API_BASE
                            + f'users/{e.owner.username}/',
                            headers={'X-Api-Key': settings.USER_PREFERENCES_API_KEY},
                            timeout=settings.REQUESTS_TIMEOUT,
                        )
                        if r.status_code == 200:
                            need_to_save = True
                            response = r.json()
                            e.data['contributors'][idx]['label'] = response.get('name')
                            e.data['contributors'][idx]['source'] = e.owner.username
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Could not fetch user information for {e.owner.username}'
                                )
                            )
                    roles = contributor.get('roles', [])
                    for role_idx, role in enumerate(roles):
                        if not role.get('label'):
                            if role.get('source'):
                                need_to_save = True
                                _graph, concept = role['source'].rsplit('/', 1)
                                e.data['contributors'][idx]['roles'][role_idx][
                                    'label'
                                ] = {
                                    'de': get_preflabel(concept, lang='de'),
                                    'en': titlecase(get_preflabel(concept, lang='en')),
                                }
                        if role.get('label'):
                            label_titlecase = titlecase(
                                e.data['contributors'][idx]['roles'][role_idx]['label'][
                                    'en'
                                ]
                            )
                            if (
                                label_titlecase
                                != e.data['contributors'][idx]['roles'][role_idx][
                                    'label'
                                ]['en']
                            ):
                                need_to_save = True
                                e.data['contributors'][idx]['roles'][role_idx]['label'][
                                    'en'
                                ] = label_titlecase
                if need_to_save:
                    e.save()
        self.stdout.write(self.style.SUCCESS('Successfully fixed contributors'))
