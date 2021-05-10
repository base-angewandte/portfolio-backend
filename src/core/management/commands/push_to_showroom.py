from re import match

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

        print(entries)
        self.stdout.write(self.style.SUCCESS('Successfully pushed entries:'))
        # TODO: output number of new and updated entries
