#!/usr/bin/env python3
"""
Security tests for bulk_generate_mad.py to validate subprocess security improvements.

These tests ensure that:
1. Language validation works correctly
2. Extractor options validation works correctly
3. Invalid inputs are rejected to prevent command injection
"""

import unittest
import sys
import pathlib

# Add the directory to the path so we can import the module
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import bulk_generate_mad


class TestLanguageValidation(unittest.TestCase):
    """Test cases for language validation."""

    def test_valid_languages(self):
        """Test that all valid languages are accepted."""
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
        for language in valid_languages:
            try:
                bulk_generate_mad.validate_language(language)
            except ValueError:
                self.fail(f"Valid language '{language}' was rejected")

    def test_invalid_language(self):
        """Test that invalid languages are rejected."""
        invalid_languages = [
            "invalid",
            "shell",
            "bash",
            "perl",
            '"; rm -rf /',
        ]
        for language in invalid_languages:
            with self.assertRaises(
                ValueError, msg=f"Invalid language '{language}' was accepted"
            ):
                bulk_generate_mad.validate_language(language)


class TestExtractorOptionsValidation(unittest.TestCase):
    """Test cases for extractor options validation."""

    def test_valid_extractor_options(self):
        """Test that valid extractor options are accepted."""
        valid_options = [
            ["--option1", "--option2"],
            ["--verbose"],
            ["--timeout=100"],
            [],  # Empty list should be valid
        ]
        for options in valid_options:
            try:
                bulk_generate_mad.validate_extractor_options(options)
            except ValueError:
                self.fail(f"Valid extractor options {options} were rejected")

    def test_dangerous_characters_rejected(self):
        """Test that extractor options with dangerous characters are rejected."""
        dangerous_options = [
            ["; rm -rf /"],
            ["| cat /etc/passwd"],
            ["&& malicious_command"],
            ["`whoami`"],
            ["$(malicious)"],
            ["test;malicious"],
            ["test|other"],
            ["test&background"],
            ["test<input"],
            ["test>output"],
            ["test\\escape"],
            ["test'quote"],
            ['test"doublequote'],
            ["test\nmalicious"],
            ["test{brace}"],
            ["test[bracket]"],
            ["test(paren)"],
        ]
        for options in dangerous_options:
            with self.assertRaises(
                ValueError,
                msg=f"Dangerous extractor option {options} was accepted",
            ):
                bulk_generate_mad.validate_extractor_options(options)

    def test_non_string_options_rejected(self):
        """Test that non-string options are rejected."""
        invalid_options = [
            [123],
            [None],
            [{"key": "value"}],
            [["nested", "list"]],
        ]
        for options in invalid_options:
            with self.assertRaises(
                ValueError, msg=f"Non-string option {options} was accepted"
            ):
                bulk_generate_mad.validate_extractor_options(options)


class TestSubprocessSecurity(unittest.TestCase):
    """Test cases to ensure subprocess calls are secure."""

    def test_valid_languages_constant_exists(self):
        """Test that VALID_LANGUAGES constant is defined and contains expected languages."""
        self.assertIn("VALID_LANGUAGES", dir(bulk_generate_mad))
        self.assertIsInstance(bulk_generate_mad.VALID_LANGUAGES, set)
        # Check for a few expected languages
        expected = {"python", "java", "javascript", "go", "rust"}
        self.assertTrue(
            expected.issubset(bulk_generate_mad.VALID_LANGUAGES),
            f"Expected languages {expected} not found in VALID_LANGUAGES",
        )


if __name__ == "__main__":
    unittest.main()
