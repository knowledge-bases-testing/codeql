# Secure Temporary File Handling

## Overview

This document describes the secure temporary file handling practices implemented in the Python extractor, addressing security issue #2.

## Security Best Practices

### Why Secure Temporary File Handling Matters

Insecure temporary file handling can lead to several security vulnerabilities:

1. **Race Conditions**: Using deprecated `tempfile.mktemp()` creates predictable filenames that attackers can exploit
2. **Information Disclosure**: Temporary files with improper permissions can leak sensitive data
3. **Resource Exhaustion**: Failure to clean up temporary files/directories leads to disk space exhaustion
4. **Denial of Service**: Accumulated temporary files can degrade system performance

### Secure APIs Used

The Python extractor uses only secure temporary file APIs:

1. **`tempfile.mkdtemp()`**: Creates a directory with secure permissions (mode 0700)
   - Generates unpredictable directory names
   - Returns the directory path
   - Caller is responsible for cleanup

2. **`tempfile.NamedTemporaryFile()`**: Creates a file with secure permissions (mode 0600)
   - Generates unpredictable file names
   - Can auto-delete on close (when `delete=True`)
   - When `delete=False`, caller must clean up

### Implementation Details

#### 1. Venv Class (buildtools/install.py)

**Issue**: Created temporary directory `empty_folder` with `mkdtemp()` but never cleaned it up.

**Solution**:
- Added `cleanup()` method to explicitly remove the temporary directory
- Implemented context manager protocol (`__enter__`, `__exit__`) for automatic cleanup
- Added `__del__` destructor as a fallback (note: not guaranteed to run)
- Added `_cleaned_up` flag to make cleanup idempotent

**Usage Examples**:

```python
# Recommended: Use as context manager
with Venv(path, version) as venv:
    venv.create()
    venv.pip(["install", "requests"])
# Automatic cleanup when exiting context

# Alternative: Explicit cleanup
venv = Venv(path, version)
try:
    venv.create()
    venv.pip(["install", "requests"])
finally:
    venv.cleanup()
```

#### 2. pip_install Function (buildtools/auto_install.py)

**Issue**: Temporary requirements file could leak if exception occurred during pip installation.

**Solution**:
- Wrapped pip installation in `try/finally` block
- Ensures `os.remove(tmp)` is always called, even on exception

**Code Pattern**:

```python
def pip_install(req, venv, dependencies=True, wheel=True):
    tmp = requirements.save_to_file([req])
    try:
        # ... pip installation logic ...
        venv.pip(args)
    finally:
        # Always clean up, even on exception
        os.remove(tmp)
```

#### 3. save_to_file Function (buildtools/semmle/requirements.py)

**Status**: Already secure, enhanced documentation.

**Security Features**:
- Uses `tempfile.NamedTemporaryFile()` with `delete=False`
- Creates file with mode 0600 (owner read/write only)
- Generates unpredictable filename
- Documented caller responsibility for cleanup

## Testing

Comprehensive security tests in `tests/buildtools/test_tempfile_security.py`:

### TestVenvCleanup
- `test_venv_cleanup_method`: Verifies `cleanup()` removes directory
- `test_venv_cleanup_idempotent`: Ensures cleanup can be called multiple times safely
- `test_venv_context_manager`: Tests context manager cleanup
- `test_venv_context_manager_with_exception`: Verifies cleanup on exception
- `test_venv_destructor_cleanup`: Tests `__del__` fallback

### TestAutoInstallCleanup
- `test_pip_install_cleanup_on_success`: Verifies cleanup on successful install
- `test_pip_install_cleanup_on_exception`: Ensures cleanup when exception occurs

### TestRequirementsSaveToFile
- `test_save_to_file_creates_secure_file`: Checks file permissions (0600 on Unix)
- `test_save_to_file_unpredictable_name`: Verifies unpredictable filenames

## References

- [Python tempfile documentation](https://docs.python.org/3/library/tempfile.html)
- [CWE-377: Insecure Temporary File](https://cwe.mitre.org/data/definitions/377.html)
- [CWE-459: Incomplete Cleanup](https://cwe.mitre.org/data/definitions/459.html)
- Security Issue #2: Refactor to eliminate insecure tempfile usage

## Migration Guide

If you're adding new code that uses temporary files:

### DO ✅

```python
# Use mkdtemp for directories
import tempfile
import shutil

temp_dir = tempfile.mkdtemp(prefix="myprefix-")
try:
    # ... use temp_dir ...
    pass
finally:
    shutil.rmtree(temp_dir)

# Use NamedTemporaryFile for files
with tempfile.NamedTemporaryFile(mode='w', delete=True) as f:
    f.write("data")
    f.flush()
    # ... use f.name ...
# Automatic cleanup

# Or if you need the file after closing:
import os
temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
try:
    temp_file.write("data")
    temp_file.close()
    # ... use temp_file.name ...
finally:
    os.remove(temp_file.name)
```

### DON'T ❌

```python
# NEVER use mktemp() - it's insecure and deprecated
import tempfile
temp_name = tempfile.mktemp()  # ❌ INSECURE!

# NEVER create predictable temp file names
temp_file = "/tmp/myapp_temp.txt"  # ❌ INSECURE!

# NEVER forget to clean up
temp_dir = tempfile.mkdtemp()
# ... use it ...
# ❌ Missing cleanup! Always use try/finally or context manager
```

## Maintenance

When modifying code that uses temporary files:

1. **Always verify cleanup**: Use try/finally or context managers
2. **Test exception paths**: Ensure cleanup happens even on errors
3. **Document ownership**: Clearly indicate who is responsible for cleanup
4. **Prefer context managers**: They're more robust than manual cleanup
5. **Check permissions**: Temporary files should have restrictive permissions

## Audit Checklist

Use this checklist when reviewing code that handles temporary files:

- [ ] Uses secure APIs (`mkdtemp`, `mkstemp`, `NamedTemporaryFile`)
- [ ] Never uses deprecated `mktemp()`
- [ ] Never uses predictable filenames
- [ ] Has explicit cleanup code (try/finally or context manager)
- [ ] Cleanup happens even on exceptions
- [ ] Documented who is responsible for cleanup
- [ ] Has tests covering cleanup behavior
- [ ] Has tests covering exception paths
- [ ] File permissions are restrictive (0600 for files, 0700 for dirs)
