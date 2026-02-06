#!/usr/bin/env python3
'''Test cases for JSON to AsciiDoc converter.'''

import os
import sys
import unittest

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from glossary_entry import load_glossary, Glossary
from json_to_adoc import render_glossary


class TestJsonToAdoc(unittest.TestCase):
    '''Test JSON to AsciiDoc conversion.'''

    @classmethod
    def setUpClass(cls):
        '''Load test files.'''
        test_dir = os.path.dirname(os.path.abspath(__file__))
        cls.test_json_path = os.path.join(test_dir, 'test1-sample.json')
        cls.expected_adoc_path = os.path.join(test_dir, 'test-from-json.adoc')

        with open(cls.expected_adoc_path, 'r', encoding='utf-8') as f:
            cls.expected_adoc = f.read()

    def test_render_glossary_matches_expected(self):
        '''Test that rendered AsciiDoc matches expected output.'''
        glossary = load_glossary(self.test_json_path)
        actual_adoc = render_glossary(glossary)

        self.assertEqual(
            actual_adoc,
            self.expected_adoc,
            'Rendered AsciiDoc does not match expected output'
        )

    def test_render_glossary_contains_entries(self):
        '''Test that rendered AsciiDoc contains expected entries.'''
        glossary = load_glossary(self.test_json_path)
        adoc_output = render_glossary(glossary)

        # Check for some expected entries
        self.assertIn('A POSTERIORI', adoc_output)
        self.assertIn('CELESTIAL', adoc_output)
        self.assertIn('CONJUGIAL', adoc_output)

    def test_render_glossary_contains_related_entries(self):
        '''Test that rendered AsciiDoc contains related/child entries.'''
        glossary = load_glossary(self.test_json_path)
        adoc_output = render_glossary(glossary)

        # Check for related entries
        self.assertIn('CELESTIAL ANGEL', adoc_output)
        self.assertIn('CELESTIAL HEAVEN', adoc_output)
        self.assertIn('CONJUGIAL LOVE', adoc_output)

    def test_render_glossary_formats_keywords(self):
        '''Test that keyword references are formatted correctly.'''
        glossary = load_glossary(self.test_json_path)
        adoc_output = render_glossary(glossary)

        # astroid has |astroites| in its definition (as _|astroites|_)
        # keyword references are uppercased
        self.assertIn('**ASTROITES**', adoc_output)

    def test_render_glossary_formats_opposites(self):
        '''Test that opposites are rendered correctly.'''
        glossary = load_glossary(self.test_json_path)
        adoc_output = render_glossary(glossary)

        # accede has opposite_slug: "recede"
        self.assertIn('Opp. **RECEDE**', adoc_output)

    def test_render_glossary_formats_italics(self):
        '''Test that italic text is formatted correctly.'''
        glossary = load_glossary(self.test_json_path)
        adoc_output = render_glossary(glossary)

        # astroid has _|astroites|_ in its definition
        # keyword references are uppercased
        self.assertIn('_**ASTROITES**_', adoc_output)

    def test_render_glossary_formats_also_translated(self):
        '''Test that also_translated entries are formatted correctly.'''
        glossary = load_glossary(self.test_json_path)
        adoc_output = render_glossary(glossary)

        # betroth has also_translated: ["affiance"]
        self.assertIn('(also transl. **AFFIANCE**)', adoc_output)

    def test_render_glossary_formats_plural(self):
        '''Test that plural forms are formatted correctly.'''
        glossary = load_glossary(self.test_json_path)
        adoc_output = render_glossary(glossary)

        # arcanum has plural: "arcana"
        self.assertIn('(pl. arcana)', adoc_output)

    def test_render_glossary_formats_pronunciation(self):
        '''Test that pronunciation is formatted correctly.'''
        glossary = load_glossary(self.test_json_path)
        adoc_output = render_glossary(glossary)

        # conjugial has pronunciation: "conju'jul"
        self.assertIn("/conju'jul/", adoc_output)

    def test_render_glossary_has_letter_sections(self):
        '''Test that letter sections are present.'''
        glossary = load_glossary(self.test_json_path)
        adoc_output = render_glossary(glossary)

        # Check for letter section headers
        self.assertIn('== A', adoc_output)
        self.assertIn('== B', adoc_output)
        self.assertIn('== C', adoc_output)


class TestGlossaryEntry(unittest.TestCase):
    '''Test GlossaryEntry and Glossary edge cases.'''

    @classmethod
    def setUpClass(cls):
        '''Load test glossary.'''
        test_dir = os.path.dirname(os.path.abspath(__file__))
        cls.test_json_path = os.path.join(test_dir, 'test1-sample.json')
        cls.glossary = load_glossary(cls.test_json_path)

    def test_has_origin_true(self):
        '''Test has_origin returns True for entry with origin.'''
        entry = self.glossary['a-posteriori']
        self.assertTrue(entry.has_origin())

    def test_has_origin_false(self):
        '''Test has_origin returns False for entry without origin.'''
        entry = self.glossary['abstract']
        self.assertFalse(entry.has_origin())

    def test_has_plural_true(self):
        '''Test has_plural returns True for entry with plural.'''
        entry = self.glossary['arcanum']
        self.assertTrue(entry.has_plural())

    def test_has_plural_false(self):
        '''Test has_plural returns False for entry without plural.'''
        entry = self.glossary['abstract']
        self.assertFalse(entry.has_plural())

    def test_glossary_entries_property(self):
        '''Test glossary entries property returns dict.'''
        entries = self.glossary.entries
        self.assertIsInstance(entries, dict)
        self.assertIn('abstract', entries)

    def test_glossary_getitem_by_slug(self):
        '''Test glossary access by slug.'''
        entry = self.glossary['a-posteriori']
        self.assertEqual(entry.slug, 'a-posteriori')

    def test_glossary_getitem_by_word(self):
        '''Test glossary access by word.'''
        # 'a posteriori' should find 'a-posteriori' entry
        entry = self.glossary['a posteriori']
        self.assertEqual(entry.slug, 'a-posteriori')

    def test_glossary_contains_slug(self):
        '''Test glossary contains check by slug.'''
        self.assertIn('abstract', self.glossary)

    def test_glossary_contains_word(self):
        '''Test glossary contains check by word.'''
        self.assertIn('a posteriori', self.glossary)

    def test_glossary_contains_missing(self):
        '''Test glossary contains check for missing entry.'''
        self.assertNotIn('nonexistent-entry', self.glossary)

    def test_glossary_slugs(self):
        '''Test glossary slugs method.'''
        slugs = self.glossary.slugs()
        self.assertIsInstance(slugs, list)
        self.assertIn('abstract', slugs)
        self.assertIn('celestial', slugs)

    def test_glossary_words(self):
        '''Test glossary words method.'''
        words = self.glossary.words()
        self.assertIsInstance(words, list)
        self.assertIn('abstract', words)
        self.assertIn('celestial', words)

    def test_glossary_from_json_string(self):
        '''Test Glossary.from_json_string class method.'''
        json_string = '''{
            "version": "1.0",
            "entries": {
                "test-word": {
                    "definitions": ["a test definition"]
                }
            }
        }'''
        glossary = Glossary.from_json_string(json_string)
        self.assertEqual(len(glossary), 1)
        self.assertIn('test-word', glossary)


if __name__ == '__main__':
    unittest.main(verbosity=2)
