from media_server.archiver.interface.exceptions import ExternalServerError


class PhaidraServerError(ExternalServerError):
    @property
    def external_service_name(self) -> str:
        return 'Phaidra'
