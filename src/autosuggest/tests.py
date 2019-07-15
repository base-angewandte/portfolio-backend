import logging

from django.test import TestCase

from .views import fetch_responses

logging.basicConfig(level=logging.ERROR)


class AutoSuggestTestCase(TestCase):
    """
    tests based on current settings configured.
    TODO:
    very repetitive, make it better with decorators
    """
    def test_empty_contributors_all(self):
        res = fetch_responses('', ('VIAF_PERSON', 'GND_PERSON', 'GND_INSTITUTION'))
        assert(len(res))
        # exactly what is expected in this case?
        return

    def test_contributors_gnd_person(self):
        res = fetch_responses('Johann Wolfgang von Goethe', ('GND_PERSON',))
        assert(any(rec['source'] == 'http://d-nb.info/gnd/118540238' for rec in res))

        return

    def test_contributors_gnd_person(self):
        res = fetch_responses('Goethe-Institut München', ('GND_INSTITUTION',))
        assert(any(rec['source'] == 'http://d-nb.info/gnd/10068828-7' for rec in res))
        return

    def test_contributors_viaf(self):
        res = fetch_responses('Goethe', ('VIAF_PERSON',))
        assert(any(rec['source'] == 'http://www.viaf.org/viaf/24602065' for rec in res))
        return

    def test_places_gnd(self):
        res = fetch_responses('Wien', ('GND_PLACE',))
        assert(any(rec['source'] == 'http://d-nb.info/gnd/4066009-6' for rec in res))

        return

    def test_viaf_corporate(self):
        res = fetch_responses('Universität Wien', ('VIAF_INSTITUTION',))
        assert(any(rec['source'] == 'http://www.viaf.org/viaf/131901031' for rec in res))

        return

    def test_places_geonames(self):
        res = fetch_responses('Wien', ('GEONAMES_PLACE',))
        assert(any(rec['source'] == 'http://api.geonames.org/get?username=***REMOVED***&geonameId=2761369' for rec in res))

        return

    def test_empty_places_all(self):
        res = fetch_responses('', ('GEONAMES_PLACE',))
        assert(len(res))
        return

    def test_empty_keywords(self):
        res = fetch_responses('', ('VOC_KEYWORDS',))
        assert(len(res) == 0)
        return

    def test_keywords(self):
        res = fetch_responses('aerodyna', ('VOC_KEYWORDS',))
        assert(any(rec['source'] == 'http://base.uni-ak.ac.at/portfolio/disciplines/103001' for rec in res))
        return

    def test_empty_roles(self):
        res = fetch_responses('', ('VOC_ROLES',))
        assert(len(res))
        return

    def test_roles(self):
        res = fetch_responses('archite', ('VOC_ROLES',))
        assert(any(rec['source'] == 'http://base.uni-ak.ac.at/portfolio/vocabulary/architecture' for rec in res))
        return

    def test_empty_formats(self):
        res = fetch_responses('', ('VOC_FORMATS',))
        assert(len(res))
        return

    def test_formats(self):
        res = fetch_responses('og', ('VOC_FORMATS',))
        assert(any(rec['source'] == 'http://base.uni-ak.ac.at/portfolio/vocabulary/ogg' for rec in res))
        return

    def test_empty_materials(self):
        res = fetch_responses('', ('VOC_MATERIALS',))
        assert(len(res))
        return

    def test_materials(self):
        res = fetch_responses('pap', ('VOC_MATERIALS',))
        assert(any(rec['source'] == 'http://base.uni-ak.ac.at/portfolio/vocabulary/paper' for rec in res))
        return

    def test_empty_languages(self):
        res = fetch_responses('', ('VOC_LANGUAGES',))
        assert(len(res) == 0)
        return

    def test_languages(self):
        res = fetch_responses('ge', ('VOC_LANGUAGES',))
        assert(any(rec['source'] == 'http://base.uni-ak.ac.at/portfolio/languages/de' for rec in res))
        return

    def test_empty_texttypes(self):
        res = fetch_responses('', ('VOC_TEXTTYPES',))
        assert(len(res))
        return

    def test_texttypes(self):
        res = fetch_responses('abs', ('VOC_TEXTTYPES',))
        assert any(rec['source'] == 'http://base.uni-ak.ac.at/portfolio/vocabulary/abstract' for rec in res)
        return

    def test_all_labels(self):
        VOC_SOURCES = ('VOC_LANGUAGES', 'VOC_MATERIALS', 'VOC_FORMATS', 'VOC_ROLES', 'VOC_KEYWORDS', 'VOC_TEXTTYPES')
        for voc_source in VOC_SOURCES:
            res = fetch_responses('a', (voc_source,))
            assert len(res) > 0, '{} is empty'.format(voc_source)
            for rec in res:
                assert 'label' in rec, '{}: no prefLabels'.format(voc_source)
                assert 'en' in rec.get('prefLabels')
                assert 'de' in rec.get('prefLabels')

        return

    def test_pelias(self):
        res = fetch_responses('wien', ('PELIAS',))
        assert any(rec['label'] == 'Vienna, Austria' for rec in res)
        return
