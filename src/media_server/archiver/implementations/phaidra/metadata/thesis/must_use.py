"""This portfolio roles must be present as their skosmos sameAs form in the
phaidra data."""
from __future__ import annotations

from dataclasses import dataclass

from media_server.archiver.messages.validation.thesis import MISSING_SUPERVISOR


@dataclass
class CustomFieldDirective:
    """Used by media_server.archiver.implementations.phaidra.metadata.thesis.sc
    hemas._create_dynamic_phaidra_meta_data_schema to add behavior to he
    schema."""

    missing_message: str


DEFAULT_DYNAMIC_ROLES: dict[str, CustomFieldDirective] = {
    'http://base.uni-ak.ac.at/portfolio/vocabulary/supervisor': CustomFieldDirective(
        missing_message=MISSING_SUPERVISOR,
    ),
}
