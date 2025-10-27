# Remediated insecure tempfile usage (issue #2)
# Replaced insecure temp file functions with secure alternatives
import tempfile
import os

def write_results1(results):
    # Use mkstemp() instead of mktemp() for secure temp file creation
    fd, filename = tempfile.mkstemp()
    try:
        with os.fdopen(fd, "w") as f:
            f.write(results)
        print("Results written to", filename)
    finally:
        # Ensure cleanup
        try:
            os.unlink(filename)
        except OSError:
            pass

def write_results2(results):
    # Use NamedTemporaryFile instead of os.tempnam()
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        filename = f.name
        f.write(results)
    try:
        print("Results written to", filename)
    finally:
        # Ensure cleanup
        try:
            os.unlink(filename)
        except OSError:
            pass

def write_results3(results):
    # Use mkstemp() instead of os.tmpnam()
    fd, filename = tempfile.mkstemp()
    try:
        with os.fdopen(fd, "w") as f:
            f.write(results)
        print("Results written to", filename)
    finally:
        # Ensure cleanup
        try:
            os.unlink(filename)
        except OSError:
            pass
