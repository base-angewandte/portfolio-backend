from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING

import django_rq
from rq.job import Job

from portfolio import settings

if TYPE_CHECKING:
    from ..implementations.phaidra.media.archiver import MediaArchiver


class AsyncMediaHandler:
    run_at: datetime | None = None
    queue_name = 'high'
    enqueued_jobs: list[Job]

    def __init__(self, media_archivers: set[MediaArchiver], job: Callable, run_at: datetime | None = None):
        self.media_archivers = media_archivers
        self.job = job
        self.queue: django_rq.queues.Queue = django_rq.get_queue(self.queue_name)
        self.enqueued_jobs = []
        if run_at:
            self.run_at = run_at

    def enqueue(self):
        for media_archiver in self.media_archivers:
            args = [self.run_at, self.job, media_archiver] if self.run_at else [self.job, media_archiver]
            kwargs = {
                'job_id': media_archiver.media_object.get_archive_job_id(),
                'failure_ttl': settings.RQ_FAILURE_TTL,
            }
            function = self.queue.enqueue_at if self.run_at else self.queue.enqueue
            self.enqueued_jobs.append((function(*args, **kwargs), function, args, kwargs))
