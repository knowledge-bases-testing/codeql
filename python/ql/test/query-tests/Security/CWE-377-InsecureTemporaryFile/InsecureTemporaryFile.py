from tempfile import NamedTemporaryFile

def write_results1(results):
    with NamedTemporaryFile(mode="w+", delete=False) as f:
        f.write(results)
    print("Results written to", f.name)

def write_results2(results):
    with NamedTemporaryFile(mode="w+", delete=False) as f:
        f.write(results)
    print("Results written to", f.name)

def write_results3(results):
    with NamedTemporaryFile(mode="w+", delete=False) as f:
        f.write(results)
    print("Results written to", f.name)
