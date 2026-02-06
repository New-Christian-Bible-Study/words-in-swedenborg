"""
Module for modeling and loading glossary entries from Words in Swedenborg.

Provides the GlossaryEntry class and functions to load entries from JSON.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import jsonschema

# Path to the JSON schema file (in project root, one level up from src/)
SCHEMA_PATH = Path(__file__).parent.parent / 'swedenborg-glossary.schema.json'

def to_slug(word):
    '''Convert a word to a slug for use as a JSON key.

    A "slug" is a URL-friendly identifier derived from the word: lowercase with
    spaces replaced by hyphens (e.g., "a posteriori" -> "a-posteriori"). Slugs
    serve as unique keys in the JSON entries object for fast lookup.
    '''
    return word.lower().strip().replace(' ', '-')


def slug_to_word(slug):
    '''Convert a slug back to a word (replace hyphens with spaces).'''
    return slug.replace('-', ' ')


@dataclass
class GlossaryEntry:
    """
    Represents a keyword-definitions entry from the glossary.

    Attributes:
        word: The term being defined (lowercase)
        slug: The slugified key for this entry (e.g., 'a-posteriori')
        definitions: List of definition strings
        origin: Language of origin (L., Gr., Heb., Fr.)
        part_of_speech: Part of speech (n., adj., adv., v., prep., conj.)
        pronunciation: Pronunciation guide
        plural: Plural form of the word
        archaic_usage: Reason why word is used in an older sense that differs from modern usage (or None)
        theological_term: Reason why Swedenborg gives this word a specific doctrinal meaning (or None)
        new_word: True if this is a new word not in standard English dictionaries
        opposite_slug: Slug of antonym entry (if exists in glossary)
        also_translated: Alternative translation words
        see_also: List of slugs for related entries (cross-references)
        parent: Slug of parent entry (for related/sub-entries)
    """
    word: str
    slug: str
    definitions: list[str]
    origin: Optional[str] = None
    latin_word: Optional[str] = None
    part_of_speech: Optional[str] = None
    pronunciation: Optional[str] = None
    plural: Optional[str] = None
    archaic_usage: Optional[str] = None
    theological_term: Optional[str] = None
    new_word: bool = False
    opposite_slug: Optional[str] = None
    also_translated: list[str] = field(default_factory=list)
    see_also: list[str] = field(default_factory=list)
    parent: Optional[str] = None

    @classmethod
    def from_dict(cls, slug: str, data: dict) -> 'GlossaryEntry':
        """Create a GlossaryEntry from a dictionary (parsed JSON).

        The word field is optional - if not present, it's derived from the slug
        by replacing hyphens with spaces.
        """
        # Derive word from slug if not explicitly provided
        word = data.get('word', slug_to_word(slug))

        return cls(
            word=word,
            slug=slug,
            definitions=data['definitions'],
            origin=data.get('origin'),
            latin_word=data.get('latin_word'),
            part_of_speech=data.get('part_of_speech'),
            pronunciation=data.get('pronunciation'),
            plural=data.get('plural'),
            archaic_usage=data.get('archaic_usage'),
            theological_term=data.get('theological_term'),
            new_word=data.get('new_word', False),
            opposite_slug=data.get('opposite_slug'),
            also_translated=data.get('also_translated', []),
            see_also=data.get('see_also', []),
            parent=data.get('parent')
        )

    def has_origin(self) -> bool:
        """Check if entry has a language of origin."""
        return self.origin is not None

    def has_plural(self) -> bool:
        """Check if entry has a plural form."""
        return self.plural is not None

    def has_opposite(self) -> bool:
        """Check if entry has an antonym."""
        return self.opposite_slug is not None

    def has_parent(self) -> bool:
        """Check if entry has a parent (is a related/sub-entry)."""
        return self.parent is not None

    def has_also_translated(self) -> bool:
        """Check if entry has alternative translations."""
        return len(self.also_translated) > 0


def _load_schema() -> dict:
    """Load the JSON schema from file."""
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_glossary_data(data: dict, schema: dict = None):
    """
    Validate glossary data against the JSON schema.

    Args:
        data: Full glossary dict with metadata and entries
        schema: Optional schema dict; if not provided, loads from SCHEMA_PATH

    Raises:
        jsonschema.ValidationError: If data doesn't match schema
    """
    if schema is None:
        schema = _load_schema()
    jsonschema.validate(instance=data, schema=schema)


class Glossary:
    """
    A collection of glossary entries.

    Provides methods for loading, accessing, and iterating over entries.
    Entries are stored flat (no nesting) with parent references for hierarchy.
    """

    def __init__(self, entries: dict[str, GlossaryEntry] = None):
        self._entries = entries or {}
        self._by_word: dict[str, GlossaryEntry] = {}
        self._children: dict[str, list[str]] = {}  # parent_slug -> [child_slugs]
        self._build_indexes()

    def _build_indexes(self):
        """Build lookup indexes for quick access."""
        for slug, entry in self._entries.items():
            self._by_word[entry.word.lower()] = entry
            if entry.parent:
                if entry.parent not in self._children:
                    self._children[entry.parent] = []
                self._children[entry.parent].append(slug)

    @classmethod
    def from_json_file(cls, path: str | Path, validate: bool = True) -> 'Glossary':
        """
        Load glossary from a JSON file.

        Args:
            path: Path to the JSON file
            validate: Whether to validate against the schema (default: True)

        Raises:
            jsonschema.ValidationError: If validation is enabled and data is invalid
        """
        path = Path(path)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if validate:
            validate_glossary_data(data)
        entries = {slug: GlossaryEntry.from_dict(slug, item) for slug, item in data['entries'].items()}
        return cls(entries)

    @classmethod
    def from_json_string(cls, json_string: str, validate: bool = True) -> 'Glossary':
        """
        Load glossary from a JSON string.

        Args:
            json_string: JSON string containing glossary data
            validate: Whether to validate against the schema (default: True)

        Raises:
            jsonschema.ValidationError: If validation is enabled and data is invalid
        """
        data = json.loads(json_string)
        if validate:
            validate_glossary_data(data)
        entries = {slug: GlossaryEntry.from_dict(slug, item) for slug, item in data['entries'].items()}
        return cls(entries)

    @property
    def entries(self) -> dict[str, GlossaryEntry]:
        """Return the entries dict mapping slugs to entries."""
        return self._entries

    def top_level_entries(self) -> list[GlossaryEntry]:
        """Return entries that have no parent (sorted by slug)."""
        return [e for e in self._entries.values() if not e.has_parent()]

    def children_of(self, slug: str) -> list[GlossaryEntry]:
        """Return child entries of a given parent slug."""
        child_slugs = self._children.get(slug, [])
        return [self._entries[s] for s in child_slugs]

    def __len__(self) -> int:
        """Return the total number of entries."""
        return len(self._entries)

    def __iter__(self):
        """Iterate over all entries (sorted by slug)."""
        return iter(sorted(self._entries.values(), key=lambda e: e.slug))

    def __getitem__(self, key: str) -> GlossaryEntry:
        """
        Get an entry by slug or word.

        Args:
            key: Slug (e.g., 'a-posteriori') or word (e.g., 'a posteriori')

        Returns:
            The matching GlossaryEntry

        Raises:
            KeyError: If not found
        """
        # Try slug first
        if key in self._entries:
            return self._entries[key]
        # Try word
        word_key = key.lower()
        if word_key in self._by_word:
            return self._by_word[word_key]
        # Try converting word to slug
        slug = to_slug(key)
        if slug in self._entries:
            return self._entries[slug]
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        """Check if a slug or word exists in the glossary."""
        if key in self._entries:
            return True
        word_key = key.lower()
        if word_key in self._by_word:
            return True
        slug = to_slug(key)
        return slug in self._entries

    def get(self, key: str, default=None) -> Optional[GlossaryEntry]:
        """Get an entry by slug or word, returning default if not found."""
        try:
            return self[key]
        except KeyError:
            return default

    def slugs(self) -> list[str]:
        """Return list of all slugs."""
        return list(self._entries.keys())

    def words(self) -> list[str]:
        """Return list of all words."""
        return [e.word for e in self._entries.values()]


def load_glossary(path: str | Path = 'swedenborg-glossary.json', validate: bool = True) -> Glossary:
    """
    Convenience function to load a glossary from a JSON file.

    Args:
        path: Path to the JSON file (default: 'swedenborg-glossary.json')
        validate: Whether to validate against the schema (default: True)

    Returns:
        A Glossary instance containing all entries

    Raises:
        jsonschema.ValidationError: If validation is enabled and data is invalid
    """
    return Glossary.from_json_file(path, validate=validate)
