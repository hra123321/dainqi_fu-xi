import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.security import find_committed_secrets, require_api_key


def test_api_key_validation():
    for invalid in ("", "your-api-key", "abc"):
        try:
            require_api_key(invalid)
        except RuntimeError as error:
            if invalid:
                assert invalid not in str(error)
        else:
            raise AssertionError("invalid API key should be rejected")

    assert require_api_key("sk-" + "a" * 24).startswith("sk-")


def test_git_tracked_files_contain_no_key_shaped_secret():
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    tracked = [
        ROOT / item.decode("utf-8")
        for item in result.stdout.split(b"\0")
        if item
    ]
    assert find_committed_secrets(tracked) == []


if __name__ == "__main__":
    test_api_key_validation()
    test_git_tracked_files_contain_no_key_shaped_secret()
    print("PASS: test_security")
