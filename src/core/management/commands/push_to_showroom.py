from re import match

import requests

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.models import Entry


class Command(BaseCommand):
    help = 'Push one or all entries to a showroom instance'

    def add_arguments(self, parser):
        parser.add_argument(
            'id', type=str, nargs='*', help='The ShortUUID of an entry to push (will be ignored when using --all'
        )
        parser.add_argument('--all', action='store_true', help='Use this to push all published entries to Showroom')

    def handle(self, *args, **options):
        if None in [settings.SHOWROOM_API_BASE, settings.SHOWROOM_API_KEY, settings.SHOWROOM_REPO_ID]:
            raise CommandError('A showroom config parameter is missing in .env! Cannot push anything.')

        if not options['all'] and not options['id']:
            raise CommandError(
                'You have to provide at least one id. Use the --all flag, if you want to push all entries.'
            )

        for id in options['id']:
            if len(id) != 22 or not match(r'^[0-9a-zA-Z]{22}$', id):
                raise CommandError(f'This does not look like a valid ShortUUID: {id}')

        # TODO: should we also check for duplicated ids? or just push them twice/several times?

        # Now fetch our entries
        if options['all']:
            entries = Entry.objects.all()
        else:
            entries = Entry.objects.filter(pk__in=options['id'])

        created = []
        updated = []
        not_pushed = []
        for entry in entries:
            data = {
                'source_repo_entry_id': entry.id,
                'source_repo': settings.SHOWROOM_REPO_ID,
                'source_repo_owner_id': str(entry.owner),
                'data': {
                    'title': entry.title,
                    'subtitle': entry.subtitle,
                    'type': entry.type,
                    'keywords': entry.keywords,
                    'texts': entry.texts,
                    'data': entry.data,
                },
            }

            headers = {
                'X-Api-Client': str(settings.SHOWROOM_REPO_ID),
                'X-Api-Key': settings.SHOWROOM_API_KEY,
            }
            r = requests.post(settings.SHOWROOM_API_BASE + 'activities/', json=data, headers=headers)

            if r.status_code == 403:
                raise CommandError(f'Authentication failed: {r.text}')

            elif r.status_code == 400:
                not_pushed.append(entry.id)
                self.stdout.write(self.style.WARNING(f'Entry {entry.id} could not be pushed: 400: {r.text}'))

            # according to the api spec the only other option is a 201 response when the entry was pushed
            # but we should also check for anything unexpected to happen
            elif r.status_code == 201:
                # so far Showroom does only allow single entry POSTs, but the response
                # format is already tailored towards multi entry POSTs. therefore
                # we extract the created/updated as if we would submit multiple
                # entries and extend our aggregated lists
                result = r.json()
                if result_created := result.get('created'):
                    created.extend([(entry['id'], entry['showroom_id']) for entry in result_created])
                if result_updated := result.get('updated'):
                    updated.extend([(entry['id'], entry['showroom_id']) for entry in result_updated])
            else:
                raise CommandError(f'Ouch! Something unexpected happened: {r.status_code} {r.text}')

        self.stdout.write(self.style.SUCCESS(f'Successfully pushed {len(created)+len(updated)} entries:'))
        self.stdout.write(f'Created: {len(created)}')
        self.stdout.write(f'Updated: {len(updated)}')
        if len(not_pushed) > 0:
            self.stdout.write(self.style.WARNING(f'Could not push {len(not_pushed)} entries:'))
            self.stdout.write(str(not_pushed))
