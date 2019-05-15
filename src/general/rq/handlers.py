import logging

logger = logging.getLogger(__name__)


def exception_handler(job, *exc_info):
    logger.error('Error while processing RQ job %s (%s)', job.id, job.func_name, exc_info=exc_info)
