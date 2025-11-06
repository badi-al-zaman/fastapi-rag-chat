import hashlib

def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file for change detection."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""): # avoids reading the whole file into memory.
            h.update(chunk)
    return h.hexdigest()