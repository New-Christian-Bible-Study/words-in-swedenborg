# Makefile for Words in Swedenborg book conversion
#
# This Makefile tracks dependencies so that changing source files
# automatically triggers rebuilding of dependent targets.

PYTHON := python3

# Source modules
SRC_GLOSSARY := src/glossary_entry.py
SRC_JSON_TO_ADOC := src/json_to_adoc.py
SRC_WORD_LISTS := src/generate_word_lists.py

# Test files
TEST_JSON_TO_ADOC := test/test-json-to-adoc.py
TEST_WORD_LISTS := test/test-generate-word-lists.py
TEST_FIXTURES := test/test1-sample.json test/test-from-json.adoc

# Stamp files for tracking test runs
STAMPS_DIR := .stamps
STAMP_TEST_JSON_TO_ADOC := $(STAMPS_DIR)/test-json-to-adoc
STAMP_TEST_WORD_LISTS := $(STAMPS_DIR)/test-generate-word-lists

# Default target
.PHONY: all
all: book/swedenborg-glossary.adoc test

# Build PDF from master document
.PHONY: pdf
pdf: book/Words_in_Swedenborg.pdf

book/Words_in_Swedenborg.pdf: book/Words_in_Swedenborg.adoc book/swedenborg-glossary.adoc book/front-matter.adoc book/publication-info.adoc book/back-matter.adoc book/cover.png book/new-words.adoc book/archaic-words.adoc book/pdf-theme.yml
	asciidoctor-pdf -o $@ $<

# Build book/swedenborg-glossary.adoc from swedenborg-glossary.json
book/swedenborg-glossary.adoc: swedenborg-glossary.json $(SRC_JSON_TO_ADOC) $(SRC_GLOSSARY)
	$(PYTHON) $(SRC_JSON_TO_ADOC) swedenborg-glossary.json book/swedenborg-glossary.adoc

# Build new-words.adoc and archaic-words.adoc from swedenborg-glossary.json
book/new-words.adoc book/archaic-words.adoc: swedenborg-glossary.json $(SRC_WORD_LISTS) $(SRC_GLOSSARY)
	$(PYTHON) $(SRC_WORD_LISTS) swedenborg-glossary.json book/

# Run all tests
.PHONY: test
test: $(STAMP_TEST_JSON_TO_ADOC) $(STAMP_TEST_WORD_LISTS)

# Create stamps directory
$(STAMPS_DIR):
	mkdir -p $(STAMPS_DIR)

# Test JSON to AsciiDoc conversion
$(STAMP_TEST_JSON_TO_ADOC): $(TEST_JSON_TO_ADOC) $(SRC_JSON_TO_ADOC) $(SRC_GLOSSARY) $(TEST_FIXTURES) | $(STAMPS_DIR)
	$(PYTHON) $(TEST_JSON_TO_ADOC)
	touch $@

# Test generate_word_lists
$(STAMP_TEST_WORD_LISTS): $(TEST_WORD_LISTS) $(SRC_WORD_LISTS) $(SRC_GLOSSARY) $(TEST_FIXTURES) | $(STAMPS_DIR)
	$(PYTHON) $(TEST_WORD_LISTS)
	touch $@

# Code coverage
.PHONY: coverage coverage-html

coverage:
	$(PYTHON) -m coverage run --source=src $(TEST_JSON_TO_ADOC)
	$(PYTHON) -m coverage run --append --source=src $(TEST_WORD_LISTS)
	$(PYTHON) -m coverage report

coverage-html:
	$(PYTHON) -m coverage run --source=src $(TEST_JSON_TO_ADOC)
	$(PYTHON) -m coverage run --append --source=src $(TEST_WORD_LISTS)
	$(PYTHON) -m coverage html
	@echo "Coverage report generated in htmlcov/"

# Clean generated files
.PHONY: clean
clean:
	rm -f book/swedenborg-glossary.adoc
	rm -f book/new-words.adoc
	rm -f book/Words_in_Swedenborg.pdf
	rm -rf $(STAMPS_DIR)
	rm -f .coverage
	rm -rf htmlcov/

# Display help
.PHONY: help
help:
	@echo 'Targets:'
	@echo '  all              - Build book/swedenborg-glossary.adoc and run tests (default)'
	@echo '  pdf              - Generate PDF book (book/Words_in_Swedenborg.pdf)'
	@echo '  book/swedenborg-glossary.adoc  - Generate AsciiDoc from swedenborg-glossary.json'
	@echo '  book/new-words.adoc book/archaic-words.adoc'
	@echo '                   - Generate word list sections from swedenborg-glossary.json'
	@echo '  test             - Run all tests'
	@echo '  coverage         - Run tests with code coverage report'
	@echo '  coverage-html    - Generate HTML coverage report in htmlcov/'
	@echo '  clean            - Remove generated files'
	@echo '  help             - Display this help message'
	@echo ''
	@echo 'Dependencies:'
	@echo '  book/swedenborg-glossary.adoc depends on:'
	@echo '    - swedenborg-glossary.json'
	@echo '    - src/json_to_adoc.py'
	@echo '    - src/glossary_entry.py'
	@echo ''
	@echo '  book/new-words.adoc and book/archaic-words.adoc depend on:'
	@echo '    - swedenborg-glossary.json'
	@echo '    - src/generate_word_lists.py'
	@echo '    - src/glossary_entry.py'
	@echo ''
	@echo '  book/Words_in_Swedenborg.pdf depends on:'
	@echo '    - book/Words_in_Swedenborg.adoc'
	@echo '    - book/swedenborg-glossary.adoc'
	@echo '    - book/new-words.adoc'
	@echo '    - book/archaic-words.adoc'
	@echo '    - book/front-matter.adoc'
	@echo '    - book/publication-info.adoc'
	@echo '    - book/back-matter.adoc'
	@echo '    - book/cover.png'
	@echo '    - book/pdf-theme.yml'
	@echo ''
	@echo '  Tests are re-run when source modules or test fixtures change.'
