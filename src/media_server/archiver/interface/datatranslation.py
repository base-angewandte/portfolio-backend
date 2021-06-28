"""Utilities to transform a data structure to another."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from itertools import zip_longest
from typing import Any, Dict, Hashable, List, Optional, Union

"""
Commands, to define data structures
"""


@dataclass
class AbstractCommand(ABC):
    access_key: Any = None
    use_in_from_source_to_target: bool = True
    use_in_from_target_to_source: bool = True

    @abstractmethod
    def get(self, container: Any) -> Any:
        """Get value from container.

        :param container:
        :return:
        """
        pass

    @abstractmethod
    def set(self, container: Union[List, Dict, object], value: Any) -> Any:
        """Set value in container and return container.

        :param container:
        :param value:
        :return:
        """
        pass

    @abstractmethod
    def create_container(self, value: Optional[Any] = None) -> Union[Dict, List, object]:
        pass

    @abstractmethod
    def index_exists(self, container: Union[List, Dict, object]) -> bool:
        """Check if the index of the command is contained in a container.

        :param container:
        :return:
        """
        pass


@dataclass
class DictCommand(AbstractCommand):
    access_key: Hashable = 0

    def get(self, container: Dict) -> Any:
        return container[self.access_key]

    def set(self, container: Dict, value: Any) -> dict:
        container[self.access_key] = value
        return container

    def create_container(self, value: Optional[Any] = None) -> dict:
        return {self.access_key: value}

    def index_exists(self, container: Dict) -> bool:
        return self.access_key in container


@dataclass
class ListCommand(AbstractCommand):
    access_key: Optional[Union[int, slice]] = slice(None)

    def get(self, container: List) -> Any:
        return container[self.access_key] if self.access_key else container.pop(0)

    def set(self, container: List, value: Any) -> List:
        container.append(value)
        return container

    def create_container(self, value: Optional[Any] = None) -> List:
        return [] if value is None else [value]

    def index_exists(self, container: List) -> bool:
        try:
            # it does have an effect. It throws an error sometimes :-)
            # noinspection PyStatementEffect
            container[self.access_key]
            return True
        except (IndexError, TypeError):
            return False


@dataclass
class AttributeCommand(AbstractCommand):
    access_key: str = ''

    class DummyClass:
        pass

        def as_dict(self):
            return {
                attribute: value.as_dict() if value.__class__ is self.__class__ else value
                for attribute, value in self.__dict__.items()
            }

    def get(self, container: object) -> Any:
        return getattr(container, self.access_key)

    def set(self, container: object, value: Any) -> object:
        setattr(container, self.access_key, value)
        return container

    def create_container(self, value: Optional[Any] = None) -> object:
        dummy_object = self.DummyClass()
        return self.set(dummy_object, value)

    def index_exists(self, container: object) -> bool:
        return hasattr(container, self.access_key)


@dataclass
class TranslationCommand:
    getter_commands: List[AbstractCommand]
    setter_commands: List[AbstractCommand]
    required: bool = True
    """raise error if data not found"""
    required_in_reverse: bool = True
    """raise error if data not found backwards"""


class Translator:
    """Build an object, that can translate one data structure to another."""

    translator_commands: List[TranslationCommand]

    __data_wrapper_key__ = 'data_wrapper'
    """
    Wrap the data in a mutable dict for reference
    """

    def __init__(self, translator_commands: List[TranslationCommand]):
        self.translator_commands = translator_commands

    def translate(self, source: Any, from_source_to_target: bool = True) -> Any:
        target = {self.__data_wrapper_key__: None}
        """
        To pass an mutable object down the chain, without caring, if the desired target object is mutable or not (and a
        copy or an reference)
        """

        for translation_command in self.translator_commands:
            if from_source_to_target:
                getter_commands = translation_command.getter_commands
                setter_commands = translation_command.setter_commands
            else:
                getter_commands = translation_command.setter_commands
                setter_commands = translation_command.getter_commands
            setter_commands: List[AbstractCommand] = [
                DictCommand(access_key=self.__data_wrapper_key__),
            ] + setter_commands

            setter_commands = self._filter_commands_by_direction(setter_commands, from_source_to_target)
            getter_commands = self._filter_commands_by_direction(getter_commands, from_source_to_target)

            """
            Again for the mutable dict wrapper
            """
            try:
                source_value = self._get_value(source, getter_commands)
                self._set_value_from_chain(source_value, target, setter_commands)
            except (IndexError, KeyError, AttributeError, TypeError) as error:
                if (translation_command.required and from_source_to_target) or (
                    translation_command.required_in_reverse and not from_source_to_target
                ):
                    raise error

        return target[self.__data_wrapper_key__]

    # noinspection PyMethodMayBeStatic
    def _get_value(self, source: Any, commands: List[AbstractCommand]) -> Any:
        for command in commands:
            source = command.get(source)
        return source

    def _set_value_from_chain(self, source_value: Any, target: Union[dict, list, object], setter_commands) -> None:
        next_level_commands = setter_commands[1:]
        two_level_commands = zip_longest(setter_commands, next_level_commands)
        level_1_command: AbstractCommand
        level_2_command: Optional[AbstractCommand]
        for level_1_command, level_2_command in two_level_commands:
            if level_2_command is None:
                """Finish line.

                No more levels to create or access
                """
                self._set_value(level_1_command, target, source_value)
                return
            elif level_1_command.get(target) is None:
                """Level has not been created yet."""
                self._create_level(level_1_command, level_2_command, target)
            else:
                """Level has been created and becomes extended."""
                self._extend_level(level_1_command, level_2_command, target)
            target = self._get_next_level(level_1_command, target)

    # noinspection PyMethodMayBeStatic
    def _set_value(self, command: AbstractCommand, target: Union[List, Dict, object], value: Any):
        command.set(target, value)

    # noinspection PyMethodMayBeStatic
    def _create_level(
        self, level_1_command: AbstractCommand, level_2_command: AbstractCommand, target: Union[Dict, List, object]
    ) -> None:
        level_1_command.set(target, level_2_command.create_container(value=None))

    # noinspection PyMethodMayBeStatic
    def _extend_level(
        self, level_1_command: AbstractCommand, level_2_command: AbstractCommand, target: Union[Dict, List, object]
    ) -> None:
        if level_2_command.__class__ is ListCommand:
            """Non need to add a key."""
            return
        target = level_1_command.get(target)
        if not level_2_command.index_exists(target):
            level_2_command.set(container=target, value=None)

    # noinspection PyMethodMayBeStatic
    def _get_next_level(
        self, level_1_command: AbstractCommand, target: Union[Dict, List, object]
    ) -> Union[Dict, List, object]:
        return level_1_command.get(target)

    # noinspection PyMethodMayBeStatic
    def _filter_commands_by_direction(
        self, commands: List[AbstractCommand], from_source_to_target: bool
    ) -> List[AbstractCommand]:
        return [
            command
            for command in commands
            if (command.use_in_from_source_to_target and from_source_to_target)
            or (command.use_in_from_target_to_source and not from_source_to_target)
        ]
