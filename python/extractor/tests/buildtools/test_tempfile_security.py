"""
Test secure temporary file handling in the Python extractor.

Security tests for issue #2: Verify that temporary files and directories
are properly cleaned up to prevent resource leaks and potential security issues.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import shutil

from buildtools.install import Venv
from buildtools import auto_install
from buildtools.semmle import requirements


class TestVenvCleanup(unittest.TestCase):
    """Test that Venv class properly cleans up temporary directories."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary workspace directory for testing
        self.test_workspace = tempfile.mkdtemp(prefix="test-workspace-")
        self.original_workspace = os.environ.get("LGTM_WORKSPACE")
        os.environ["LGTM_WORKSPACE"] = self.test_workspace

    def tearDown(self):
        """Clean up test environment."""
        if self.original_workspace:
            os.environ["LGTM_WORKSPACE"] = self.original_workspace
        else:
            os.environ.pop("LGTM_WORKSPACE", None)
        
        # Clean up test workspace
        if os.path.exists(self.test_workspace):
            shutil.rmtree(self.test_workspace)

    def test_venv_cleanup_method(self):
        """Test that Venv.cleanup() removes the temporary directory."""
        venv_path = os.path.join(self.test_workspace, "test-venv")
        venv = Venv(venv_path, 3)
        
        # Verify empty_folder was created
        self.assertTrue(os.path.exists(venv.empty_folder))
        empty_folder_path = venv.empty_folder
        
        # Call cleanup
        venv.cleanup()
        
        # Verify directory was removed
        self.assertFalse(os.path.exists(empty_folder_path))
        
    def test_venv_cleanup_idempotent(self):
        """Test that cleanup() can be called multiple times safely."""
        venv_path = os.path.join(self.test_workspace, "test-venv")
        venv = Venv(venv_path, 3)
        
        empty_folder_path = venv.empty_folder
        
        # Call cleanup multiple times
        venv.cleanup()
        venv.cleanup()
        venv.cleanup()
        
        # Verify directory was removed and no error occurred
        self.assertFalse(os.path.exists(empty_folder_path))
        
    def test_venv_context_manager(self):
        """Test that Venv works as a context manager and cleans up."""
        venv_path = os.path.join(self.test_workspace, "test-venv")
        
        with Venv(venv_path, 3) as venv:
            empty_folder_path = venv.empty_folder
            self.assertTrue(os.path.exists(empty_folder_path))
        
        # After exiting context, directory should be cleaned up
        self.assertFalse(os.path.exists(empty_folder_path))
        
    def test_venv_context_manager_with_exception(self):
        """Test that Venv cleans up even when exception occurs."""
        venv_path = os.path.join(self.test_workspace, "test-venv")
        empty_folder_path = None
        
        try:
            with Venv(venv_path, 3) as venv:
                empty_folder_path = venv.empty_folder
                self.assertTrue(os.path.exists(empty_folder_path))
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected exception
        
        # Even with exception, directory should be cleaned up
        self.assertFalse(os.path.exists(empty_folder_path))

    def test_venv_destructor_cleanup(self):
        """Test that Venv.__del__() cleans up the temporary directory."""
        venv_path = os.path.join(self.test_workspace, "test-venv")
        venv = Venv(venv_path, 3)
        empty_folder_path = venv.empty_folder
        
        self.assertTrue(os.path.exists(empty_folder_path))
        
        # Delete the object, triggering __del__
        del venv
        
        # Directory should be cleaned up
        # Note: __del__ is not guaranteed to run immediately, but in practice it should
        import gc
        gc.collect()  # Force garbage collection
        
        # Give it a moment for cleanup to occur
        self.assertFalse(os.path.exists(empty_folder_path))


class TestAutoInstallCleanup(unittest.TestCase):
    """Test that auto_install.pip_install properly cleans up temp files."""

    @patch('buildtools.auto_install.requirements.save_to_file')
    @patch.object(Venv, 'upgrade_pip')
    @patch.object(Venv, 'pip')
    def test_pip_install_cleanup_on_success(self, mock_pip, mock_upgrade, mock_save):
        """Test that temp file is cleaned up on successful installation."""
        # Setup mock - use secure NamedTemporaryFile instead of deprecated mktemp
        with tempfile.NamedTemporaryFile(suffix=".txt", mode='w', delete=False) as f:
            temp_file = f.name
            f.write("test")
        mock_save.return_value = temp_file
        
        # Create a mock requirement
        from packaging.requirements import Requirement
        req = Requirement("requests>=2.0.0")
        
        # Create mock venv
        with patch.dict(os.environ, {"LGTM_WORKSPACE": tempfile.gettempdir()}):
            # Note: mkdtemp() is secure (unlike deprecated mktemp()).
            # It creates directories with mode 0700 and unpredictable names.
            venv = Venv(tempfile.mkdtemp(), 3)
            
            try:
                # Call pip_install
                auto_install.pip_install(req, venv)
                
                # Verify temp file was cleaned up
                self.assertFalse(os.path.exists(temp_file))
            finally:
                venv.cleanup()

    @patch('buildtools.auto_install.requirements.save_to_file')
    @patch.object(Venv, 'upgrade_pip')
    @patch.object(Venv, 'pip')
    def test_pip_install_cleanup_on_exception(self, mock_pip, mock_upgrade, mock_save):
        """Test that temp file is cleaned up even when exception occurs."""
        # Setup mock to raise exception - use secure NamedTemporaryFile instead of deprecated mktemp
        with tempfile.NamedTemporaryFile(suffix=".txt", mode='w', delete=False) as f:
            temp_file = f.name
            f.write("test")
        mock_save.return_value = temp_file
        mock_pip.side_effect = Exception("Installation failed")
        
        # Create a mock requirement
        from packaging.requirements import Requirement
        req = Requirement("requests>=2.0.0")
        
        # Create mock venv
        with patch.dict(os.environ, {"LGTM_WORKSPACE": tempfile.gettempdir()}):
            # Note: mkdtemp() is secure (unlike deprecated mktemp()).
            # It creates directories with mode 0700 and unpredictable names.
            venv = Venv(tempfile.mkdtemp(), 3)
            
            try:
                # Call pip_install, expecting it to raise
                with self.assertRaises(Exception):
                    auto_install.pip_install(req, venv)
                
                # Verify temp file was still cleaned up despite exception
                self.assertFalse(os.path.exists(temp_file))
            finally:
                venv.cleanup()


class TestRequirementsSaveToFile(unittest.TestCase):
    """Test that requirements.save_to_file creates secure temp files."""

    def test_save_to_file_creates_secure_file(self):
        """Test that save_to_file creates a file with secure permissions."""
        from packaging.requirements import Requirement
        reqs = [Requirement("requests>=2.0.0"), Requirement("urllib3>=1.0")]
        
        temp_file = requirements.save_to_file(reqs)
        
        try:
            # Verify file exists
            self.assertTrue(os.path.exists(temp_file))
            
            # Verify file has secure permissions (Unix only)
            if os.name != 'nt':  # Not Windows
                stat_info = os.stat(temp_file)
                mode = stat_info.st_mode
                # File should be readable/writable only by owner (0600)
                # tempfile.NamedTemporaryFile creates files with mode 0600
                self.assertEqual(mode & 0o777, 0o600)
            
            # Verify content
            with open(temp_file, 'r') as f:
                content = f.read()
                self.assertIn("requests>=2.0.0", content)
                self.assertIn("urllib3>=1.0", content)
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_save_to_file_unpredictable_name(self):
        """Test that save_to_file creates files with unpredictable names."""
        from packaging.requirements import Requirement
        reqs = [Requirement("requests>=2.0.0")]
        
        # Create multiple temp files
        temp_files = []
        try:
            for _ in range(5):
                temp_file = requirements.save_to_file(reqs)
                temp_files.append(temp_file)
            
            # Verify all names are unique and contain the prefix
            self.assertEqual(len(temp_files), len(set(temp_files)))
            for temp_file in temp_files:
                basename = os.path.basename(temp_file)
                self.assertTrue(basename.startswith("semmle-requirements"))
                self.assertTrue(basename.endswith(".txt"))
        finally:
            # Clean up all temp files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)


if __name__ == '__main__':
    unittest.main()
