import typing
from collections import defaultdict
from typing import Dict, List, Optional, Union

from core.models import Entry
from media_server.archiver.implementations.phaidra.metadata.default.datatranslation import (
    BfNoteTranslator,
    GenericSkosConceptTranslator,
    GenericStaticPersonTranslator,
    PhaidraMetaDataTranslator,
    create_person_object,
)
from media_server.archiver.implementations.phaidra.metadata.mappings.contributormapping import (
    BidirectionalConceptsMapper,
    extract_phaidra_role_code,
)
from media_server.archiver.interface.exceptions import InternalValidationError


class ResponsiveGenericSkosConceptTranslator(GenericSkosConceptTranslator):
    """Implement basic error feedback."""

    def translate_errors(self, errors: Optional[Union[List[Dict], Dict]]) -> Dict:
        if not errors:
            return {}
        translated_errors = {}
        translated_errors = self.set_nested(
            keys=[self.entry_attribute, *self.json_keys],
            value=errors,
            target=translated_errors,
        )
        return translated_errors


class ResponsiveBfNoteTranslator(BfNoteTranslator):
    def translate_errors(self, errors: Union[List[str], Dict]) -> Dict[str, List[str]]:
        if errors.__class__ is list:
            return {'texts': errors}
        else:
            super().translate_errors(errors)


class ResponsiveGenericStaticPersonTranslator(GenericStaticPersonTranslator):
    """Implement basic error feedback."""

    def translate_errors(self, errors: Union[Dict, List]) -> Dict:
        """Since all of this errors are on schema level, we just to add the top
        keys.

        :param errors:
        :return:
        """
        if not errors:
            return {}
        return {'data': {self.primary_level_data_key: errors}}


class PhaidraThesisMetaDataTranslator(PhaidraMetaDataTranslator):

    def __init__(self):
        super().__init__()

        self.data_with_dynamic_structure = defaultdict(list)

        self._key_translator_mapping['role:aut'] = ResponsiveGenericStaticPersonTranslator(
            primary_level_data_key='authors',
            role_uri='http://base.uni-ak.ac.at/portfolio/vocabulary/author',
        )

        self._key_translator_mapping['dcterms:language'] = ResponsiveGenericSkosConceptTranslator(
            'data',
            [
                'language',
            ],
            raise_on_not_found_error=False,
        )

        self._key_translator_mapping['bf:note'] = ResponsiveBfNoteTranslator()

    def _translate_errors_with_dynamic_structure(
        self, errors: Dict, contributor_role_mapping: 'BidirectionalConceptsMapper'
    ):
        """

        :param errors:
        :param contributor_role_mapping
        :return:
        """

        dynamic_errors = {}

        for concept_mapping in contributor_role_mapping.concept_mappings.values():
            for phaidra_role in concept_mapping.owl_sameAs:
                if 'loc.gov' not in phaidra_role:
                    continue
                phaidra_role_code = extract_phaidra_role_code(phaidra_role)
                if phaidra_role_code in errors:
                    dynamic_errors[phaidra_role_code] = errors[phaidra_role_code]

        if dynamic_errors:
            raise InternalValidationError(str(dynamic_errors))
        else:
            return {}

    def _merge(self, data_with_static_structure: dict, data_with_dynamic_structure: dict):
        for key, value in data_with_dynamic_structure.items():
            if key not in data_with_static_structure:
                data_with_static_structure[key] = value
            elif data_with_static_structure[key].__class__ is list and value.__class__ is list:
                data_with_static_structure[key] += value
            else:
                pass  # All we do right now
        return data_with_static_structure

    def _get_data_with_dynamic_structure(
        self, model: 'Entry', contributor_role_mapping: 'BidirectionalConceptsMapper'
    ) -> Dict:
        self._extract_data_with_dynamic_structure(model, contributor_role_mapping)
        # add keys in mapping aka must-use to data:
        for concept_mapping in contributor_role_mapping.concept_mappings.values():
            for phaidra_role_code in self.yield_phaidra_role_codes(concept_mapping.owl_sameAs):
                if phaidra_role_code not in self.data_with_dynamic_structure:
                    self.data_with_dynamic_structure[phaidra_role_code] = []
        return self.data_with_dynamic_structure

    def translate_errors(self, errors: Optional[Dict], mapping: 'BidirectionalConceptsMapper') -> Dict:
        errors = self._extract_from_container(errors)
        static_errors = self._translate_errors(errors)
        dynamic_errors = self._translate_errors_with_dynamic_structure(errors, mapping)
        all_errors = self._merge(static_errors, dynamic_errors)
        return self._filter_errors(all_errors)

    def translate_data(self, model: 'Entry', mapping: 'BidirectionalConceptsMapper') -> Dict:
        static_data = self._translate_data(model)
        dynamic_data = self._get_data_with_dynamic_structure(model, mapping)
        all_data = self._merge(static_data, dynamic_data)
        return self._wrap_in_container(all_data)

    def _extract_data_with_dynamic_structure(self, model: 'Entry',
                                             contributor_role_mapping: 'BidirectionalConceptsMapper'
                                             ) -> Dict[str, List]:
        if (model.data is None) or ('contributors' not in model.data):
            return self.data_with_dynamic_structure
        contributors: List[Dict] = model.data['contributors']
        for contributor in contributors:
            if 'roles' not in contributor:
                continue
            for role in contributor['roles']:
                if 'source' not in role:
                    continue
                phaidra_roles = contributor_role_mapping.get_owl_sameAs_from_uri(role['source'])
                for phaidra_role_code in self.yield_phaidra_role_codes(phaidra_roles):
                    person_object = create_person_object(
                            name=contributor['label'],
                            source=role['source'] if 'source' in role else None,
                        )
                    if person_object not in self.data_with_dynamic_structure[phaidra_role_code]:
                        self.data_with_dynamic_structure[phaidra_role_code].append(person_object)

        return self.data_with_dynamic_structure

    def yield_phaidra_role_codes(self, phaidra_roles: typing.Iterable[str]) -> typing.Generator[str, None, None]:
        for phaidra_role in phaidra_roles:
            if 'loc.gov' not in phaidra_role:
                continue
            yield extract_phaidra_role_code(phaidra_role)
