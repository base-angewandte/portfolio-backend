from typing import Callable, Set

import django_rq

from portfolio import settings

from ...models import Media


class AsyncMediaHandler:
    queue_name = 'high'

    def __init__(self, media_objects: Set[Media], job: Callable):
        self.media_objects = media_objects
        self.job = job
        self.queue_name = 'high'
        self.queue: django_rq.queues.Queue = django_rq.get_queue(self.queue_name)

    def enqueue(self):
        for media_object in self.media_objects:
            self.queue.enqueue(
                self.job,
                media_object,
                job_id=media_object.get_archive_job_id(),
                failure_ttl=settings.RQ_FAILURE_TTL,
            )
