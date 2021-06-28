import unittest

from media_server.archiver.interface.datatranslation import DictCommand, ListCommand, TranslationCommand, Translator


class TranslatorTestCase(unittest.TestCase):
    def test_dict_to_static_list_and_reversed(self):
        source = {
            'a': 'A',
            'b': 'B',
        }
        target = {'any': ['A', 'B']}

        translator = Translator(
            [
                TranslationCommand(
                    getter_commands=[
                        DictCommand(access_key='a'),
                    ],
                    setter_commands=[DictCommand(access_key='any'), ListCommand(access_key=None)],
                ),
                TranslationCommand(
                    getter_commands=[
                        DictCommand(access_key='b'),
                    ],
                    setter_commands=[DictCommand(access_key='any'), ListCommand(access_key=None)],
                ),
            ]
        )

        self.assertEqual(translator.translate(source, from_source_to_target=True), target)
        self.assertEqual(translator.translate(target, from_source_to_target=False), source)

    def test_required(self):
        nothing_here = {}
        translator = Translator(
            [
                TranslationCommand(
                    getter_commands=[DictCommand(access_key='not existing')],
                    setter_commands=[DictCommand(access_key='also not existing')],
                    required=True,
                    required_in_reverse=True,
                )
            ]
        )

        self.assertRaises(KeyError, lambda: translator.translate(nothing_here))
        self.assertRaises(KeyError, lambda: translator.translate(nothing_here, from_source_to_target=False))

    def test_not_required(self):
        some_data = {'some-key': 'some-value'}
        translator = Translator(
            [
                TranslationCommand(
                    getter_commands=[DictCommand(access_key='not existing')],
                    setter_commands=[DictCommand(access_key='also not existing')],
                    required=False,
                    required_in_reverse=False,
                ),
                TranslationCommand(
                    getter_commands=[DictCommand(access_key='some-key')],
                    setter_commands=[DictCommand(access_key='some-key')],
                    required=True,
                    required_in_reverse=True,
                ),
            ]
        )

        self.assertEqual(translator.translate(source=some_data, from_source_to_target=True), some_data)
        self.assertEqual(translator.translate(source=some_data, from_source_to_target=False), some_data)

    def test_required_one_way(self):
        example_source_data = {'a': {'b': 'abc'}}
        example_target_data = {'b': {'a': 'abc'}}

        translator = Translator(
            [
                TranslationCommand(
                    getter_commands=[DictCommand(access_key='not existing')],
                    setter_commands=[DictCommand(access_key='also not existing')],
                    required=True,
                    required_in_reverse=False,
                ),
                TranslationCommand(
                    getter_commands=[
                        DictCommand(access_key='a'),
                        DictCommand(access_key='b'),
                    ],
                    setter_commands=[
                        DictCommand(access_key='b'),
                        DictCommand(access_key='a'),
                    ],
                    required=True,
                    required_in_reverse=True,
                ),
            ]
        )

        self.assertRaises(KeyError, lambda: translator.translate(example_source_data, from_source_to_target=True))
        self.assertEqual(translator.translate(example_target_data, from_source_to_target=False), example_source_data)
