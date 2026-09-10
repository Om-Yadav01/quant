import hashlib
import os
import tarfile
import urllib.request


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD_DIR = os.path.join(PROJECT_ROOT, "data", "downloads")
TRACE_DIR = os.path.join(PROJECT_ROOT, "data", "alibaba_trace")
ARCHIVE_PATH = os.path.join(DOWNLOAD_DIR, "batch_task.tar.gz")
EXPECTED_SHA256 = "7c4b32361bd1ec2083647a8f52a6854a03bc125ca5c202652316c499fbf978c6"
URL = "http://aliopentrace.oss-cn-beijing.aliyuncs.com/v2018Traces/batch_task.tar.gz"


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        print(f"[download] Archive already exists: {path}")
        return

    print(f"[download] Fetching {url}")
    with urllib.request.urlopen(url, timeout=60) as response:
        total = int(response.headers.get("Content-Length") or 0)
        read = 0
        with open(path, "wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
                read += len(chunk)
                if total:
                    print(f"\r[download] {read / total:6.1%}", end="")
    print()


def main():
    _download(URL, ARCHIVE_PATH)

    actual_sha = _sha256(ARCHIVE_PATH)
    if actual_sha != EXPECTED_SHA256:
        raise RuntimeError(
            f"Checksum mismatch for {ARCHIVE_PATH}: {actual_sha} != {EXPECTED_SHA256}"
        )
    print(f"[download] SHA256 verified: {actual_sha}")

    os.makedirs(TRACE_DIR, exist_ok=True)
    with tarfile.open(ARCHIVE_PATH, "r:gz") as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        if names != ["batch_task.csv"]:
            raise RuntimeError(f"Unexpected archive contents: {names}")
        archive.extractall(TRACE_DIR, members=members)
    csv_path = os.path.join(TRACE_DIR, "batch_task.csv")
    print(f"[download] Extracted: {csv_path}")


if __name__ == "__main__":
    main()
