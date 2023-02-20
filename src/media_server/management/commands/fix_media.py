from progressbar import progressbar

from django.core.management.base import BaseCommand

from media_server.models import STATUS_NOT_CONVERTED, Media


class Command(BaseCommand):
    help = 'Fix missing media previews'

    def handle(self, *args, **options):
        for m in progressbar(Media.objects.all()):
            data = m.get_data()
            if (
                data.get('mp3', '') is None
                or data.get('thumbnail', '') is None
                or data.get('pdf', '') is None
                or data.get('cover', {}).get('gif', '') is None
                or data.get('cover', {}).get('jpg', '') is None
                or data.get('playlist', '') is None
                or data.get('poster', '') is None
            ):
                Media.objects.filter(id=m.id).update(status=STATUS_NOT_CONVERTED)
                m.media_info_and_convert()
        self.stdout.write(self.style.SUCCESS('Successfully fixed media previews'))
