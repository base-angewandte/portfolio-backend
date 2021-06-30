from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Hashable, List, Optional

if TYPE_CHECKING:
    from django.db.models import Model


class AbstractDataTranslator(ABC):
    @abstractmethod
    def translate_data(self, model: 'Model') -> dict:
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
