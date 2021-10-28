from re import match

import requests

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.models import Entry
from media_server.models import AUDIO_TYPE, DOCUMENT_TYPE, IMAGE_TYPE, VIDEO_TYPE, Media


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

        # Now fetch our entries
        if options['all']:
            entries = Entry.objects.all()
            if not entries:
                self.stdout.write(self.style.WARNING('Your portfolio does not contain any entries'))
                return
        else:
            entries = Entry.objects.filter(pk__in=options['id'])
            if not entries:
                self.stdout.write(self.style.WARNING('No entries found with provided IDs'))
                return

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
                result_created = result.get('created')
                if result_created:
                    created.extend([(entry['id'], entry['showroom_id']) for entry in result_created])
                result_updated = result.get('updated')
                if result_updated:
                    updated.extend([(entry['id'], entry['showroom_id']) for entry in result_updated])
            else:
                raise CommandError(f'Ouch! Something unexpected happened: {r.status_code} {r.text}')

        self.stdout.write(self.style.SUCCESS(f'Successfully pushed {len(created)+len(updated)} entries:'))
        self.stdout.write(f'Created: {len(created)}')
        self.stdout.write(f'Updated: {len(updated)}')
        if len(not_pushed) > 0:
            self.stdout.write(self.style.WARNING(f'Could not push {len(not_pushed)} entries:'))
            self.stdout.write(str(not_pushed))

        self.stdout.write('Now pushing all related published media')
        media_created = []
        media_updated = []
        media_not_pushed = []
        for entry in entries:
            media = Media.objects.filter(entry_id=entry.id, published=True)
            for medium in media:
                medium_data = medium.get_data()
                data = {
                    'file': medium.file.url,
                    'type': medium.type,
                    'mime_type': medium.mime_type,
                    'exif': medium.exif,
                    'license': medium.license,
                    'source_repo_media_id': medium.id,
                    'source_repo_entry_id': entry.id,
                    'specifics': {},
                }
                if medium.type == IMAGE_TYPE:
                    data['specifics'] = {
                        'previews': medium_data.get('previews'),
                        'thumbnail': medium_data.get('thumbnail'),
                    }
                elif medium.type == AUDIO_TYPE:
                    data['specifics'] = {
                        'duration': medium_data['metadata'].get('Duration'),
                        'mp3': medium_data.get('mp3'),
                    }
                elif medium.type == VIDEO_TYPE:
                    data['specifics'] = {
                        'cover': medium_data.get('cover'),
                        'playlist': medium_data.get('playlist'),
                    }
                elif medium.type == DOCUMENT_TYPE:
                    data['specifics'] = {
                        'cover': medium_data.get('cover'),
                        'pdf': medium_data.get('pdf'),
                        'thumbnail': medium_data.get('thumbnail'),
                    }

                headers = {
                    'X-Api-Client': str(settings.SHOWROOM_REPO_ID),
                    'X-Api-Key': settings.SHOWROOM_API_KEY,
                }
                r = requests.post(settings.SHOWROOM_API_BASE + 'media/', json=data, headers=headers)

                if r.status_code == 403:
                    raise CommandError(f'Authentication failed: {r.text}')

                elif r.status_code == 400:
                    media_not_pushed.append(medium.id)
                    self.stdout.write(self.style.WARNING(f'Medium {medium.id} could not be pushed: 400: {r.text}'))

                # according to the api spec the only other option is a 201 response when the entry was pushed
                # but we should also check for anything unexpected to happen
                elif r.status_code == 201:
                    # so far Showroom does only allow single media POSTs, but the response
                    # format is already tailored towards multi entry POSTs. therefore
                    # we extract the created/updated as if we would submit multiple
                    # entries and extend our aggregated lists
                    result = r.json()
                    result_created = result.get('created')
                    if result_created:
                        media_created.extend([(m['id'], m['showroom_id']) for m in result_created])
                    result_updated = result.get('updated')
                    if result_updated:
                        media_updated.extend([(m['id'], m['showroom_id']) for m in result_updated])
                else:
                    raise CommandError(f'Ouch! Something unexpected happened: {r.status_code} {r.text}')

        media_pushed = len(media_created) + len(media_updated)
        self.stdout.write(self.style.SUCCESS(f'Successfully pushed {media_pushed} media:'))
        self.stdout.write(f'Created: {len(media_created)}')
        self.stdout.write(f'Updated: {len(media_updated)}')
        if len(media_not_pushed) > 0:
            self.stdout.write(self.style.WARNING(f'Could not push {len(media_not_pushed)} media:'))
            self.stdout.write(str(media_not_pushed))

        self.stdout.write('Now pushing entry relations')
        relations_created = []
        relations_not_pushed = []
        for entry in entries:
            data = {'related_to': []}
            for related_entry in entry.relations.all():
                data['related_to'].append(related_entry.id)
            headers = {
                'X-Api-Client': str(settings.SHOWROOM_REPO_ID),
                'X-Api-Key': settings.SHOWROOM_API_KEY,
            }
            path = f'activities/{entry.id}/relations/'
            r = requests.post(settings.SHOWROOM_API_BASE + path, json=data, headers=headers)

            if r.status_code == 403:
                raise CommandError(f'Authentication failed: {r.text}')

            elif r.status_code == 404 or r.status_code == 400:
                relations_not_pushed.extend([(entry.id, r) for r in data['related_to']])
                self.stdout.write(
                    self.style.WARNING(f'Relations from {entry.id} could not be pushed: {r.status_code}: {r.text}')
                )

            # according to the api spec the only other option is a 201 response
            # when the relationship was successfully added
            # but we should also check for anything unexpected to happen
            elif r.status_code == 201:
                result = r.json()
                created = result.get('created')
                if created:
                    relations_created.extend((entry.id, id) for id in created)
                not_found = result.get('not_found')
                if not_found:
                    relations_not_pushed.extend((entry.id, id) for id in not_found)
            else:
                raise CommandError(f'Ouch! Something unexpected happened: {r.status_code} {r.text}')

        self.stdout.write(self.style.SUCCESS(f'Successfully pushed {len(relations_created)} relations.'))
        if len(relations_not_pushed) > 0:
            self.stdout.write(self.style.WARNING(f'Could not push {len(relations_not_pushed)} relations:'))
            self.stdout.write(str(relations_not_pushed))
