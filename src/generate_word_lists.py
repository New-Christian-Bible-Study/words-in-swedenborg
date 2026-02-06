#!/usr/bin/env python3
"""
Generate new-words.adoc and archaic-words.adoc from swedenborg-glossary.json.

Extracts entries marked with new_word=true, archaic_usage=true, or
theological_term=true and generates AsciiDoc files with formatted word lists
for inclusion in the book.

Usage:
    python generate_word_lists.py swedenborg-glossary.json book/
"""

import argparse
import sys
from pathlib import Path

from glossary_entry import Glossary, load_glossary


# Header text for new words section
NEW_WORDS_HEADER = '''== New Words

There are more than a dozen new words in Swedenborg's Writings, many of them appearing only a few times or in one particular translation. There are five that are frequently used:

// Generated from swedenborg-glossary.json - do not edit below this line
'''

# Header text for archaic words section (displayed as "Misleading Words" in book)
ARCHAIC_WORDS_HEADER = '''== Misleading Words

There are many words that have a different meaning than the average reader would expect. Here are some of them:

// Generated from swedenborg-glossary.json - do not edit below this line
'''


def get_new_words(glossary: Glossary) -> list[str]:
    """Extract words marked as new_word from the glossary."""
    words = []
    for entry in glossary:
        if entry.new_word:
            words.append(entry.word.upper())
    return sorted(set(words))


def get_flagged_words(glossary: Glossary) -> list[str]:
    """Extract words marked as archaic_usage or theological_term from the glossary."""
    words = []
    for entry in glossary:
        if entry.archaic_usage or entry.theological_term:
            words.append(entry.word.upper())
    return sorted(set(words))


def format_new_words(words: list[str]) -> str:
    """Format new words as a single line with double-space separation."""
    return '  '.join(words)


def format_archaic_words(words: list[str], columns: int = 4) -> str:
    """Format archaic usage words as an AsciiDoc table with specified columns."""
    if not words:
        return ''

    lines = ['[cols="1,1,1,1", frame=none, grid=none]', '|===']

    # Build rows with specified number of columns
    for i in range(0, len(words), columns):
        row_words = words[i:i + columns]
        # Pad row if needed
        while len(row_words) < columns:
            row_words.append('')
        row = '|' + ' |'.join(row_words)
        lines.append(row)

    lines.append('|===')
    return '\n'.join(lines)


def generate_new_words_adoc(glossary: Glossary) -> str:
    """Generate the complete new-words.adoc content."""
    words = get_new_words(glossary)
    formatted = format_new_words(words)
    return NEW_WORDS_HEADER + formatted + '\n'


def generate_archaic_words_adoc(glossary: Glossary) -> str:
    """Generate the complete archaic-words.adoc content."""
    words = get_flagged_words(glossary)
    formatted = format_archaic_words(words)
    return ARCHAIC_WORDS_HEADER + formatted + '\n'


def main():
    parser = argparse.ArgumentParser(
        description='Generate new-words.adoc and archaic-words.adoc from swedenborg-glossary.json'
    )
    parser.add_argument(
        'input',
        help='Input JSON file (swedenborg-glossary.json)'
    )
    parser.add_argument(
        'output_dir',
        help='Output directory for generated .adoc files (e.g., book/)'
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.is_dir():
        print(f'Error: {args.output_dir} is not a directory', file=sys.stderr)
        sys.exit(1)

    glossary = load_glossary(args.input)

    # Generate new-words.adoc
    new_words_path = output_dir / 'new-words.adoc'
    new_words_content = generate_new_words_adoc(glossary)
    new_words_path.write_text(new_words_content, encoding='utf-8')
    print(f'Wrote {new_words_path}', file=sys.stderr)

    # Generate archaic-words.adoc
    archaic_words_path = output_dir / 'archaic-words.adoc'
    archaic_words_content = generate_archaic_words_adoc(glossary)
    archaic_words_path.write_text(archaic_words_content, encoding='utf-8')
    print(f'Wrote {archaic_words_path}', file=sys.stderr)


if __name__ == '__main__':
    main()
