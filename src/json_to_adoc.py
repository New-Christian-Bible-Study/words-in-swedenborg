#!/usr/bin/env python3
"""
Export glossary JSON to AsciiDoc format.

Usage:
    python json_to_adoc.py input.json output.adoc
    python json_to_adoc.py input.json  # outputs to stdout
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

from glossary_entry import GlossaryEntry, Glossary, load_glossary, to_slug


def format_text(text: str) -> str:
    """
    Convert text formatting markers to AsciiDoc.

    Markers:
        |word| -> **word** (bold keyword)
        _text_ -> _text_ (italic - same in AsciiDoc)
        _|word|_ -> _**word**_ (italic bold keyword)
    """
    # Handle _|word|_ (italic keyword reference) - convert to bold uppercase
    def italic_keyword_to_bold(match):
        return f'_**{match.group(1).upper()}**_'

    text = re.sub(
        r'_\|([^|]+)\|_',
        italic_keyword_to_bold,
        text
    )

    # Handle |word| (keyword reference) - convert to bold uppercase
    def keyword_to_bold(match):
        return f'**{match.group(1).upper()}**'

    text = re.sub(
        r'\|([^|]+)\|',
        keyword_to_bold,
        text
    )

    return text


def render_entry(
    entry: GlossaryEntry,
    glossary: Optional[Glossary] = None,
    is_related: bool = False
) -> str:
    """Render a single glossary entry to AsciiDoc."""
    lines = []

    # Add anchor for all entries to enable xref cross-references
    lines.append(f'[[{entry.slug}]]')

    # Build the word line with metadata
    word_upper = entry.word.upper()

    # Build metadata parts
    metadata_parts = []
    if entry.plural:
        metadata_parts.append(f'(pl. {entry.plural})')
    if entry.origin:
        if entry.latin_word:
            # Show origin with the specific Latin/Greek word
            metadata_parts.append(f'({entry.origin} _{entry.latin_word.upper()}_)')
        else:
            metadata_parts.append(f'({entry.origin})')
    if entry.part_of_speech:
        metadata_parts.append(f'({entry.part_of_speech})')
    if entry.pronunciation:
        metadata_parts.append(f'/{entry.pronunciation}/')
    # Add flags for archaic_usage/theological_term and new_word (both displayed as [misleading] in book)
    if entry.archaic_usage or entry.theological_term:
        metadata_parts.append('[misleading]')
    if entry.new_word:
        metadata_parts.append('[new word]')

    metadata_str = ' '.join(metadata_parts)

    # Format definitions
    if len(entry.definitions) == 1:
        defn = format_text(entry.definitions[0])
        if metadata_str:
            word_line = f'**{word_upper}** {metadata_str} = {defn}'
        else:
            word_line = f'**{word_upper}** = {defn}'
        lines.append(word_line)
    else:
        # Multiple definitions - numbered list
        if metadata_str:
            word_line = f'**{word_upper}** {metadata_str} ='
        else:
            word_line = f'**{word_upper}** ='
        lines.append(word_line)
        for i, defn in enumerate(entry.definitions, 1):
            lines.append(f'{i}. {format_text(defn)}')

    # Opposite
    if entry.has_opposite():
        opp_entry = glossary.get(entry.opposite_slug) if glossary else None
        opp_word = opp_entry.word if opp_entry else entry.opposite_slug.replace('-', ' ')
        # Add line continuation marker to previous line
        if lines:
            lines[-1] = lines[-1] + ' +'
        lines.append(f'Opp. **{opp_word.upper()}**')

    # Also translated
    if entry.has_also_translated():
        alt_words = ' and '.join(f'**{w.upper()}**' for w in entry.also_translated)
        # Add line continuation marker to previous line
        if lines:
            lines[-1] = lines[-1] + ' +'
        lines.append(f'(also transl. {alt_words})')

    # See also cross-references (using xref for PDF hyperlinks)
    if entry.see_also:
        see_also_refs = []
        for slug in entry.see_also:
            ref_entry = glossary.get(slug) if glossary else None
            ref_word = ref_entry.word if ref_entry else slug.replace('-', ' ')
            see_also_refs.append(f'xref:{slug}[**{ref_word.upper()}**]')
        # Add line continuation marker to previous line
        if lines:
            lines[-1] = lines[-1] + ' +'
        lines.append(f'See also: {", ".join(see_also_refs)}')

    # Related entries (children)
    if glossary:
        children = glossary.children_of(entry.slug)
        if children:
            for child in children:
                child_content = render_entry(child, glossary, is_related=True)
                # Indent child entries with line continuation
                indented_lines = []
                for line in child_content.split('\n'):
                    if line.strip():
                        # Use {nbsp} for non-breaking spaces to preserve indentation in PDF
                        indented_lines.append(f'{{nbsp}}{{nbsp}}{line}')
                # Add line continuation marker to previous line
                if indented_lines and lines:
                    lines[-1] = lines[-1] + ' +'
                lines.extend(indented_lines)

    return '\n'.join(lines)


def render_glossary(glossary: Glossary) -> str:
    """Render the entire glossary to AsciiDoc (definitions only, no header)."""
    lines = []

    # Only render top-level entries; children are rendered nested within parents
    top_level = glossary.top_level_entries()

    # Group entries by first letter for sections
    current_letter = None

    for entry in sorted(top_level, key=lambda e: e.slug):
        first_letter = entry.word[0].upper()

        # Start a new section for each letter
        if first_letter != current_letter:
            if current_letter is not None:
                lines.append('')  # Blank line before new section
            lines.append(f'== {first_letter}')
            lines.append('')
            current_letter = first_letter

        lines.append(render_entry(entry, glossary))
        lines.append('')

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Export glossary JSON to AsciiDoc format'
    )
    parser.add_argument(
        'input',
        help='Input JSON file'
    )
    parser.add_argument(
        'output',
        nargs='?',
        help='Output AsciiDoc file (default: stdout)'
    )

    args = parser.parse_args()

    glossary = load_glossary(args.input)
    adoc_output = render_glossary(glossary)

    if args.output:
        Path(args.output).write_text(adoc_output, encoding='utf-8')
        print(f'Wrote {args.output}', file=sys.stderr)
    else:
        print(adoc_output)


if __name__ == '__main__':
    main()
