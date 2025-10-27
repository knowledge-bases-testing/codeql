# Remediated insecure tempfile usage (issue #2)
# Replaced tempfile.mktemp() with tempfile.mkstemp() for secure temp file creation
import tempfile
import os

def write_results(results):
    # Use mkstemp() which atomically creates the file with secure permissions
    fd, filename = tempfile.mkstemp()
    try:
        # Write using the file descriptor for atomic operation
        with os.fdopen(fd, "w") as f:
            f.write(results)
        print("Results written to", filename)
    finally:
        # Ensure cleanup of temp file
        try:
            os.unlink(filename)
        except OSError:
            pass
