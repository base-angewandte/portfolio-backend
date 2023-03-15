import django_rq
from rest_framework.test import APITestCase
from rq.exceptions import NoSuchJobError
from rq.job import Job
from rq.suspension import resume, suspend

from django.core.files.uploadedfile import SimpleUploadedFile

from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import ModelProvider
from media_server.models import Media


class DeleteMediaJobs(APITestCase):
    """If an media item is deleted, the corresponding jobs should be stopped as
    well."""

    def setUp(self) -> None:
        self.model_provider = ModelProvider()
        self.entry = self.model_provider.get_entry()
        self.connection = django_rq.get_connection()
        suspend(self.connection)  # So we can manually run them sync
        self.client.login(username=self.model_provider.username, password=self.model_provider.peeword)
        response = self.client.post(
            path='/api/v1/media/',
            data={
                'file': SimpleUploadedFile('example.txt', b'example text'),
                'entry': self.entry.id,
                'published': True,
                'license': """{
                            "label": {"de": "urheberrechtlich geschützt", "en": "Copyright"},
                            "source": "http://base.uni-ak.ac.at/portfolio/licenses/copyright"
                        }""",
            },
        )
        media_id = response.data
        self.job_id = Media(pk=media_id).get_job_id()

    def delete_entry(self):
        return self.client.delete(f'/api/v1/entry/{self.entry.id}/')

    def test_before_job(self):
        """
        The job should be deleted
        :return:
        """
        self.delete_entry()
        self.assertRaises(NoSuchJobError, lambda: Job.fetch(self.job_id, connection=self.connection))

    def test_after_job(self):
        resume(connection=self.connection)
        django_rq.get_worker().work(burst=True)
        self.delete_entry()
        self.assertRaises(NoSuchJobError, lambda: Job.fetch(self.job_id, connection=self.connection))
