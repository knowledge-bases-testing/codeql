#!/usr/bin/env python3
"""
Tests for bulk_generate_mad.py security enhancements.
"""

import pytest
from bulk_generate_mad import validate_language, validate_extractor_options


class TestLanguageValidation:
    """Test cases for language parameter validation."""

    def test_valid_languages(self):
        """Test that valid CodeQL languages are accepted."""
        valid_languages = [
            "cpp",
            "csharp",
            "go",
            "java",
            "javascript",
            "python",
            "ruby",
            "rust",
            "swift",
        ]
        for lang in valid_languages:
            # Should not raise ValueError
            validate_language(lang)

    def test_invalid_language_with_special_chars(self):
        """Test that languages with special characters are rejected."""
        invalid_languages = [
            "python; rm -rf /",
            "cpp && echo hacked",
            "java | cat /etc/passwd",
            "rust`whoami`",
            "go$(id)",
        ]
        for lang in invalid_languages:
            with pytest.raises(ValueError, match="Invalid language"):
                validate_language(lang)

    def test_invalid_language_empty(self):
        """Test that empty language is rejected."""
        with pytest.raises(ValueError, match="Invalid language"):
            validate_language("")

    def test_invalid_language_unknown(self):
        """Test that unknown languages are rejected."""
        with pytest.raises(ValueError, match="Invalid language"):
            validate_language("cobol")


class TestExtractorOptionsValidation:
    """Test cases for extractor_options validation."""

    def test_valid_extractor_options(self):
        """Test that valid extractor options are accepted."""
        valid_options = [
            ["key=value"],
            ["option1=value1", "option2=value2"],
            ["flag-name=true"],
            ["config_option=123"],
            ["MixedCase=Value"],
            [],  # Empty list is valid
        ]
        for options in valid_options:
            # Should not raise ValueError
            validate_extractor_options(options)

    def test_invalid_extractor_options_with_special_chars(self):
        """Test that extractor options with special characters are rejected."""
        invalid_options = [
            ["key; rm -rf /"],
            ["option && echo hacked"],
            ["flag|cat /etc/passwd"],
            ["config`whoami`"],
            ["value$(id)"],
            ["key=value; echo hacked"],
            ["key=value\nmalicious"],
        ]
        for options in invalid_options:
            with pytest.raises(ValueError, match="Invalid extractor option"):
                validate_extractor_options(options)

    def test_invalid_extractor_options_not_list(self):
        """Test that non-list extractor options are rejected."""
        with pytest.raises(ValueError, match="must be a list"):
            validate_extractor_options("not-a-list")

    def test_invalid_extractor_options_non_string_elements(self):
        """Test that extractor options with non-string elements are rejected."""
        with pytest.raises(ValueError, match="must contain only strings"):
            validate_extractor_options(["valid", 123, "also-valid"])

    def test_valid_extractor_options_with_dots_and_slashes(self):
        """Test that extractor options with dots and forward slashes are accepted."""
        valid_options = [
            ["path=/some/path"],
            ["version=1.2.3"],
            ["url=https://example.com"],
            ["file.name=value"],
        ]
        for options in valid_options:
            # Should not raise ValueError
            validate_extractor_options(options)
