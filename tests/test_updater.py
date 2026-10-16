import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from orphe_gest.updater import (
    UpdateError,
    download_verified_executable,
    fetch_latest_release,
)


class FakeResponse(io.BytesIO):
    def __init__(self, content, headers=None):
        super().__init__(content)
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def release_payload(tag_name="v1.1.0"):
    return json.dumps({
        "tag_name": tag_name,
        "html_url":
            "https://github.com/orphericgcd-lab/ORPHE-GESTIONNAIRE/releases/tag/v1.1.0",
        "draft": False,
        "prerelease": False,
        "assets": [
            {
                "name": "ORPHE-GEST.exe",
                "browser_download_url":
                    "https://github.com/orphericgcd-lab/ORPHE-GESTIONNAIRE/releases/download/"
                    "v1.1.0/ORPHE-GEST.exe",
            },
            {
                "name": "ORPHE-GEST.exe.sha256",
                "browser_download_url":
                    "https://github.com/orphericgcd-lab/ORPHE-GESTIONNAIRE/releases/download/"
                    "v1.1.0/ORPHE-GEST.exe.sha256",
            },
        ],
    }).encode("utf-8")


class UpdateCheckerTests(unittest.TestCase):
    @patch("orphe_gest.updater._request")
    def test_finds_new_release_and_assets(self, request):
        request.return_value = FakeResponse(release_payload())

        result = fetch_latest_release("orphericgcd-lab/ORPHE-GESTIONNAIRE", "1.0.0")

        self.assertEqual(result.version, "1.1.0")
        self.assertIn("/ORPHE-GEST.exe", result.executable_url)
        self.assertIn("/ORPHE-GEST.exe.sha256", result.checksum_url)

    @patch("orphe_gest.updater._request")
    def test_current_release_returns_no_update(self, request):
        request.return_value = FakeResponse(release_payload("v1.0.0"))

        self.assertIsNone(fetch_latest_release("orphericgcd-lab/ORPHE-GESTIONNAIRE", "1.0.0"))

    @patch("orphe_gest.updater._request")
    def test_rejects_release_asset_from_another_host(self, request):
        payload = json.loads(release_payload())
        payload["assets"][0]["browser_download_url"] = "https://example.com/ORPHE-GEST.exe"
        request.return_value = FakeResponse(json.dumps(payload).encode("utf-8"))

        with self.assertRaises(UpdateError):
            fetch_latest_release("orphericgcd-lab/ORPHE-GESTIONNAIRE", "1.0.0")

    @patch("orphe_gest.updater._request")
    def test_download_keeps_file_when_checksum_matches(self, request):
        executable = b"verified ORPHE-GEST release"
        digest = hashlib.sha256(executable).hexdigest()
        request.side_effect = [
            FakeResponse(digest.encode("ascii")),
            FakeResponse(executable, {"Content-Length": str(len(executable))}),
        ]

        class Release:
            checksum_url = (
                "https://github.com/orphericgcd-lab/ORPHE-GESTIONNAIRE/releases/download/"
                "v1.1.0/ORPHE-GEST.exe.sha256")
            executable_url = (
                "https://github.com/orphericgcd-lab/ORPHE-GESTIONNAIRE/releases/download/"
                "v1.1.0/ORPHE-GEST.exe")

        with tempfile.TemporaryDirectory() as directory:
            downloaded, actual_digest = download_verified_executable(Release(), directory)

            self.assertEqual(downloaded.read_bytes(), executable)
            self.assertEqual(actual_digest, digest)

    @patch("orphe_gest.updater._request")
    def test_bad_checksum_removes_temporary_download(self, request):
        executable = b"tampered ORPHE-GEST release"
        request.side_effect = [
            FakeResponse(("0" * 64).encode("ascii")),
            FakeResponse(executable),
        ]

        class Release:
            checksum_url = (
                "https://github.com/orphericgcd-lab/ORPHE-GESTIONNAIRE/releases/download/"
                "v1.1.0/ORPHE-GEST.exe.sha256")
            executable_url = (
                "https://github.com/orphericgcd-lab/ORPHE-GESTIONNAIRE/releases/download/"
                "v1.1.0/ORPHE-GEST.exe")

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(UpdateError, "SHA-256"):
                download_verified_executable(Release(), directory)
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
