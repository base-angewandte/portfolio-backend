from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Hashable, List, Optional, Union

from media_server.archiver.interface.exceptions import InternalValidationError

if TYPE_CHECKING:
    from django.db.models import Model


class AbstractDataTranslator(ABC):
    @abstractmethod
    def translate_data(self, model: 'Model') -> Union[Dict, List]:
        pass

    @abstractmethod
    def translate_errors(self, errors: Optional[Dict]) -> Dict:
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


class AbstractUserUnrelatedDataTranslator(AbstractDataTranslator, ABC):
    """Some validation errors are not due to user input, but to internal data
    problems.

    Do not throw Translated Validation Errors on Validation fails, but
    raise InternalValidationError
    """

    def translate_errors(self, errors: Optional[Union[List[Dict], Dict]]) -> Union[List[Dict], Dict]:
        """None of these errors will be shown to the user."""
        if errors.__class__ is list:
            if any([len(error) > 0 for error in errors]):
                raise InternalValidationError(str(errors))
            else:
                return [{} for error in errors]
        elif errors.__class__ is dict:
            if len(errors):
                raise InternalValidationError(str(errors))
            else:
                return {}
        else:
            raise NotImplementedError(f'Can not handle error translation for type {errors.__class__}')
