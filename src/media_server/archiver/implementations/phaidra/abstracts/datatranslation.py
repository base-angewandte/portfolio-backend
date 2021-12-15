from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Hashable, List, Optional, Union

from media_server.archiver.interface.exceptions import InternalValidationError

if TYPE_CHECKING:
    from django.db.models import Model
    from media_server.archiver.implementations.phaidra.metadata.mappings.contributormapping import \
        BidirectionalConceptsMapper


class AbstractDataTranslator(ABC):
    @abstractmethod
    def translate_data(self, model: 'Model') -> Union[Dict, List]:
        """
        Extract and translate data from a django model to phaidra's data model
        """
        pass

    @abstractmethod
    def translate_errors(self, errors: Optional[Dict]) -> Dict:
        """
        Translate error schema validation messages to portfolio's data schema, so that the user can adjust the data

        :param errors: 
        :return: 
        """
        if (errors is None) or len(errors) == 0:
            return {}

    def set_nested(self, keys: List[Hashable], value: Any, target: Dict) -> Dict:
        if len(keys) == 0:
            return target
        sub_target = target
        last_key = keys.pop()
        for key in keys:
            if key not in sub_target:
                sub_target[key] = {}
            sub_target = sub_target[key]
        sub_target[last_key] = value
        return target
    
    
class AbstractConceptMappingDataTranslator(AbstractDataTranslator, ABC):
    """
    Use a concept mapper to extend translation capabilities.
    """
    mapping: 'BidirectionalConceptsMapper'

    def __init__(self, mapping: 'BidirectionalConceptsMapper'):
        self.mapping = mapping


class AbstractUserUnrelatedDataTranslator(AbstractDataTranslator, ABC):
    """Some validation errors are not due to user input, but to internal data
    problems.

    Do not throw Translated Validation Errors on Validation fails, but
    raise InternalValidationError
    """

    def translate_errors(self, errors: Optional[Union[List[Dict], Dict]]) -> Union[Dict[int, Dict], Dict[str, List]]:
        """None of these errors will be shown to the user."""
        if len(errors):
            raise InternalValidationError(str(errors))
        else:
            return {}
