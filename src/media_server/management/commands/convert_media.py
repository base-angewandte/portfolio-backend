from re import match

from progressbar import progressbar

from django.core.management.base import BaseCommand, CommandError

from media_server.models import STATUS_NOT_CONVERTED, Media


class Command(BaseCommand):
    help = 'Convert media'

    def add_arguments(self, parser):
        parser.add_argument(
            'media_id',
            type=str,
            nargs='*',
            help='The ShortUUID of the media that should be converted',
        )

    def handle(self, *args, **options):

        if not options['media_id']:
            raise CommandError('You have to provide at least one media_id.')

        for media_id in options['media_id']:
            if len(media_id) != 22 or not match(r'^[0-9a-zA-Z]{22}$', media_id):
                raise CommandError(f'This does not look like a valid ShortUUID: {media_id}')

        for m in progressbar(Media.objects.filter(id__in=options['media_id'])):
            Media.objects.filter(id=m.id).update(status=STATUS_NOT_CONVERTED)
            m.media_info_and_convert()

        self.stdout.write(self.style.SUCCESS('Successfully converted media'))
