from re import match

from progressbar import progressbar

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.models import Entry
from media_server.models import Media
from showroom_connector import sync


class Command(BaseCommand):
    help = 'Push one or all entries to a showroom instance'

    def add_arguments(self, parser):
        parser.add_argument(
            'id', type=str, nargs='*', help='The ShortUUID of an entry to push (will be ignored when using --all'
        )
        parser.add_argument('--all', action='store_true', help='Use this to push all published entries to Showroom')
        parser.add_argument('-l', '--limit', type=int, help='An optional limit to the numbers entries that are pushed')
        parser.add_argument(
            '-o', '--offset', type=int, help='An optional offset to first entry in the result set to be pushed'
        )

    def handle(self, *args, **options):
        if None in [settings.SHOWROOM_API_BASE, settings.SHOWROOM_API_KEY, settings.SHOWROOM_REPO_ID]:
            raise CommandError('A showroom config parameter is missing in .env! Cannot push anything.')

        if not options['all'] and not options['id']:
            raise CommandError(
                'You have to provide at least one id. Use the --all flag, if you want to push all entries.'
            )

        for entry_id in options['id']:
            if len(entry_id) != 22 or not match(r'^[0-9a-zA-Z]{22}$', entry_id):
                raise CommandError(f'This does not look like a valid ShortUUID: {entry_id}')

        # Now fetch our entries
        if options['all']:
            entries = Entry.objects.filter(published=True)
            if not entries:
                self.stdout.write(self.style.WARNING('Your portfolio does not contain any published entries'))
                return
        else:
            entries = Entry.objects.filter(pk__in=options['id'], published=True)
            if not entries:
                self.stdout.write(self.style.WARNING('No published entries found with provided IDs'))
                return

        limit = None
        offset = None
        # limited = True
        if options['limit']:
            if options['limit'] <= 0:
                raise CommandError('limit has to be a positive integer')
            limit = options['limit']
        if options['offset']:
            if options['offset'] <= 0:
                raise CommandError('offset has to be a positive integer')
            offset = options['offset']
        if offset and limit is None:
            entries = entries[offset:]
            # limited = True
        elif limit and offset is None:
            entries = entries[0:limit]
            # limited = True
        elif limit and offset:
            entries = entries[offset : limit + offset]
            # limited = True

        created = []
        updated = []
        not_pushed = []
        for entry in progressbar(entries):
            result = {}
            try:
                result = sync.push_entry(entry)
            except (sync.ShowroomAuthenticationError, sync.ShowroomUndefinedError) as e:
                raise CommandError(e) from e
            except sync.ShowroomError as e:
                not_pushed.append(entry.id)
                self.stdout.write(self.style.WARNING(e))

            # so far Showroom does only allow single entry POSTs, but the response
            # format is already tailored towards multi entry POSTs. therefore
            # we extract the created/updated as if we would submit multiple
            # entries and extend our aggregated lists
            result_created = result.get('created')
            if result_created:
                created.extend([(entry['id'], entry['showroom_id']) for entry in result_created])
            result_updated = result.get('updated')
            if result_updated:
                updated.extend([(entry['id'], entry['showroom_id']) for entry in result_updated])

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
        for entry in progressbar(entries):
            media = Media.objects.filter(entry_id=entry.id, published=True)
            for medium in media:
                result = {}
                try:
                    result = sync.push_medium(medium)
                except (sync.ShowroomAuthenticationError, sync.ShowroomUndefinedError) as e:
                    raise CommandError(e) from e
                except sync.ShowroomError as e:
                    media_not_pushed.append(entry.id)
                    self.stdout.write(self.style.WARNING(e))

                # so far Showroom does only allow single media POSTs, but the response
                # format is already tailored towards multi entry POSTs. therefore
                # we extract the created/updated as if we would submit multiple
                # entries and extend our aggregated lists
                result_created = result.get('created')
                if result_created:
                    media_created.extend([(m['id'], m['showroom_id']) for m in result_created])
                result_updated = result.get('updated')
                if result_updated:
                    media_updated.extend([(m['id'], m['showroom_id']) for m in result_updated])

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
        for entry in progressbar(entries):
            result = {}
            try:
                result = sync.push_relations(entry)
            except (sync.ShowroomAuthenticationError, sync.ShowroomUndefinedError) as e:
                raise CommandError(e) from e
            except sync.ShowroomError as e:
                relations_not_pushed.append(entry.id)
                self.stdout.write(self.style.WARNING(e))

            created = result.get('created')
            if created:
                relations_created.extend((entry.id, entry_id) for entry_id in created)
            not_found = result.get('not_found')
            if not_found:
                relations_not_pushed.extend((entry.id, entry_id) for entry_id in not_found)

        self.stdout.write(self.style.SUCCESS(f'Successfully pushed {len(relations_created)} relations.'))
        if len(relations_not_pushed) > 0:
            self.stdout.write(self.style.WARNING(f'Could not push {len(relations_not_pushed)} relations:'))
            self.stdout.write(str(relations_not_pushed))
