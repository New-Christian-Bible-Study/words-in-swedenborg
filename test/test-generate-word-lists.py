#!/usr/bin/env python3
'''Test cases for generate_word_lists module.'''

import os
import sys
import unittest

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from glossary_entry import load_glossary
from generate_word_lists import (
    get_new_words,
    get_flagged_words,
    format_new_words,
    format_archaic_words,
    generate_new_words_adoc,
    generate_archaic_words_adoc,
)


class TestGetWords(unittest.TestCase):
    '''Test word extraction functions.'''

    @classmethod
    def setUpClass(cls):
        '''Load test glossary.'''
        test_dir = os.path.dirname(os.path.abspath(__file__))
        cls.test_json_path = os.path.join(test_dir, 'test1-sample.json')
        cls.glossary = load_glossary(cls.test_json_path)

    def test_get_new_words(self):
        '''Test extracting new words from glossary.'''
        words = get_new_words(self.glossary)
        # test1-sample.json has conjugial and conjugial-adj marked as new_word
        self.assertIn('CONJUGIAL', words)
        self.assertEqual(len(words), 1)  # Both entries have same word, should dedupe

    def test_get_flagged_words(self):
        '''Test extracting flagged words (archaic_usage or theological_term) from glossary.'''
        words = get_flagged_words(self.glossary)
        # test1-sample.json has accidental, sensuous, save marked as archaic_usage
        # and charity marked as theological_term
        self.assertIn('ACCIDENTAL', words)
        self.assertIn('SENSUOUS', words)
        self.assertIn('SAVE', words)
        self.assertIn('CHARITY', words)
        self.assertEqual(len(words), 4)

    def test_get_new_words_returns_sorted(self):
        '''Test that new words are returned sorted.'''
        words = get_new_words(self.glossary)
        self.assertEqual(words, sorted(words))

    def test_get_flagged_words_returns_sorted(self):
        '''Test that flagged words are returned sorted.'''
        words = get_flagged_words(self.glossary)
        self.assertEqual(words, sorted(words))


class TestFormatWords(unittest.TestCase):
    '''Test word formatting functions.'''

    def test_format_new_words(self):
        '''Test formatting new words with double-space separation.'''
        words = ['ALPHA', 'BETA', 'GAMMA']
        result = format_new_words(words)
        self.assertEqual(result, 'ALPHA  BETA  GAMMA')

    def test_format_new_words_single(self):
        '''Test formatting single new word.'''
        words = ['CONJUGIAL']
        result = format_new_words(words)
        self.assertEqual(result, 'CONJUGIAL')

    def test_format_new_words_empty(self):
        '''Test formatting empty list.'''
        result = format_new_words([])
        self.assertEqual(result, '')

    def test_format_archaic_words(self):
        '''Test formatting archaic words as table.'''
        words = ['ACCIDENTAL', 'SAVE', 'SENSUOUS']
        result = format_archaic_words(words)
        self.assertIn('[cols="1,1,1,1", frame=none, grid=none]', result)
        self.assertIn('|===', result)
        self.assertIn('ACCIDENTAL', result)
        self.assertIn('SAVE', result)
        self.assertIn('SENSUOUS', result)

    def test_format_archaic_words_empty(self):
        '''Test formatting empty archaic words list.'''
        result = format_archaic_words([])
        self.assertEqual(result, '')

    def test_format_archaic_words_pads_row(self):
        '''Test that incomplete rows are padded.'''
        words = ['ONE', 'TWO']  # Less than 4 columns
        result = format_archaic_words(words)
        # Should have padded cells
        lines = result.split('\n')
        data_line = [l for l in lines if l.startswith('|') and '===' not in l][0]
        # Count pipes - should have 4 cells
        self.assertEqual(data_line.count('|'), 4)


class TestGenerateAdoc(unittest.TestCase):
    '''Test full AsciiDoc generation functions.'''

    @classmethod
    def setUpClass(cls):
        '''Load test glossary.'''
        test_dir = os.path.dirname(os.path.abspath(__file__))
        cls.test_json_path = os.path.join(test_dir, 'test1-sample.json')
        cls.glossary = load_glossary(cls.test_json_path)

    def test_generate_new_words_adoc(self):
        '''Test generating new-words.adoc content.'''
        result = generate_new_words_adoc(self.glossary)
        self.assertIn('== New Words', result)
        self.assertIn('CONJUGIAL', result)
        self.assertTrue(result.endswith('\n'))

    def test_generate_archaic_words_adoc(self):
        '''Test generating archaic-words.adoc content.'''
        result = generate_archaic_words_adoc(self.glossary)
        self.assertIn('== Misleading Words', result)  # Book title stays as "Misleading Words"
        self.assertIn('ACCIDENTAL', result)
        self.assertIn('SENSUOUS', result)
        self.assertIn('SAVE', result)
        self.assertIn('CHARITY', result)  # theological_term also included
        self.assertTrue(result.endswith('\n'))

    def test_generate_new_words_adoc_has_header(self):
        '''Test that new words adoc has explanatory header.'''
        result = generate_new_words_adoc(self.glossary)
        self.assertIn('more than a dozen new words', result)

    def test_generate_archaic_words_adoc_has_header(self):
        '''Test that archaic words adoc has explanatory header.'''
        result = generate_archaic_words_adoc(self.glossary)
        self.assertIn('different meaning than the average reader would expect', result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
