import hashlib
import json
import os
import re
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from .version import GITHUB_REPOSITORY

_MAX_API_RESPONSE = 2 * 1024 * 1024
_MAX_CHECKSUM_RESPONSE = 256
_MAX_EXE_SIZE = 512 * 1024 * 1024
_DOWNLOAD_CHUNK_SIZE = 1024 * 1024
_VERSION_PATTERN = re.compile(r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
_CHECKSUM_PATTERN = re.compile(r"^([0-9a-fA-F]{64})(?:\s+\*?ORPHE-GEST\.exe)?\s*$")


class UpdateError(RuntimeError):
    pass


@dataclass(frozen=True)
class UpdateRelease:
    version: str
    tag_name: str
    page_url: str
    executable_url: str
    checksum_url: str


def _version_tuple(value):
    match = _VERSION_PATTERN.fullmatch(value)
    if match is None:
        raise UpdateError(f"Version GitHub invalide : {value!r}")
    return tuple(int(part) for part in match.groups())


def _read_limited(response, limit, description):
    data = response.read(limit + 1)
    if len(data) > limit:
        raise UpdateError(f"La réponse {description} dépasse la taille autorisée.")
    return data


def _release_asset_url(value, owner, repository):
    if not isinstance(value, str):
        raise UpdateError("GitHub n’a pas fourni l’adresse d’un fichier de mise à jour.")
    parsed = urlparse(value)
    expected_prefix = f"/{owner}/{repository}/releases/download/"
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com" \
            or not parsed.path.startswith(expected_prefix):
        raise UpdateError("GitHub a retourné une adresse d’archive inattendue.")
    return value


def _request(url):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "ORPHE-GEST-Updater",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    return urllib.request.urlopen(request, timeout=20)


def fetch_latest_release(repository=GITHUB_REPOSITORY, current_version="0.0.0"):
    match = re.fullmatch(r"([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", repository)
    if match is None:
        raise UpdateError("Le dépôt GitHub configuré est invalide.")
    owner, name = match.groups()
    current = _version_tuple(current_version)
    url = f"https://api.github.com/repos/{owner}/{name}/releases/latest"

    try:
        with _request(url) as response:
            payload = json.loads(_read_limited(response, _MAX_API_RESPONSE, "des informations de version"))
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise UpdateError(
                "Aucune version publique n’est encore disponible sur GitHub. "
                "Le dépôt doit être créé et une première release publiée.") from error
        raise UpdateError(f"GitHub n’a pas pu fournir les versions ({error.code}).") from error
    except urllib.error.URLError as error:
        raise UpdateError(f"Impossible de joindre GitHub : {error.reason}") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise UpdateError("GitHub a retourné des informations de version invalides.") from error

    if not isinstance(payload, dict) or payload.get("draft") or payload.get("prerelease"):
        raise UpdateError("La dernière release publique est invalide.")
    tag_name = payload.get("tag_name")
    if not isinstance(tag_name, str):
        raise UpdateError("La release ne contient pas de numéro de version.")
    release_version = _version_tuple(tag_name.removeprefix("v"))
    if release_version <= current:
        return None

    assets = payload.get("assets")
    if not isinstance(assets, list):
        raise UpdateError("La release ne contient pas la liste de ses fichiers.")
    by_name = {
        asset.get("name"): asset
        for asset in assets
        if isinstance(asset, dict) and isinstance(asset.get("name"), str)
    }
    executable = by_name.get("ORPHE-GEST.exe")
    checksum = by_name.get("ORPHE-GEST.exe.sha256")
    if not isinstance(executable, dict) or not isinstance(checksum, dict):
        raise UpdateError("La release ne contient pas l’exécutable et son empreinte SHA-256.")
    page_url = payload.get("html_url")
    expected_page_prefix = f"https://github.com/{owner}/{name}/releases/tag/"
    if not isinstance(page_url, str) or not page_url.startswith(expected_page_prefix):
        raise UpdateError("L’adresse de la release GitHub est invalide.")

    return UpdateRelease(
        version=".".join(str(part) for part in release_version),
        tag_name=tag_name,
        page_url=page_url,
        executable_url=_release_asset_url(executable.get("browser_download_url", ""), owner, name),
        checksum_url=_release_asset_url(checksum.get("browser_download_url", ""), owner, name),
    )


def download_verified_executable(release, directory=None):
    temporary_path = None
    keep_temporary_file = False
    try:
        with _request(release.checksum_url) as response:
            checksum_data = _read_limited(response, _MAX_CHECKSUM_RESPONSE, "de l’empreinte SHA-256")
        checksum_text = checksum_data.decode("ascii").strip()
        checksum_match = _CHECKSUM_PATTERN.fullmatch(checksum_text)
        if checksum_match is None:
            raise UpdateError("Le fichier d’empreinte SHA-256 de la release est invalide.")
        expected_digest = checksum_match.group(1).lower()

        file_descriptor, temporary_path = tempfile.mkstemp(
            prefix="orphe-gest-update-", suffix=".exe", dir=directory)
        digest = hashlib.sha256()
        size = 0
        with os.fdopen(file_descriptor, "wb") as destination:
            with _request(release.executable_url) as response:
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > _MAX_EXE_SIZE:
                    raise UpdateError("La taille de l’exécutable dépasse la limite autorisée.")
                while True:
                    chunk = response.read(_DOWNLOAD_CHUNK_SIZE)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > _MAX_EXE_SIZE:
                        raise UpdateError("La taille de l’exécutable dépasse la limite autorisée.")
                    destination.write(chunk)
                    digest.update(chunk)

        if size == 0:
            raise UpdateError("GitHub a fourni un exécutable vide.")
        if digest.hexdigest() != expected_digest:
            raise UpdateError("L’empreinte SHA-256 est incorrecte; la mise à jour a été refusée.")
        keep_temporary_file = True
        return Path(temporary_path), expected_digest
    except urllib.error.HTTPError as error:
        raise UpdateError(f"GitHub n’a pas pu télécharger la mise à jour ({error.code}).") from error
    except urllib.error.URLError as error:
        raise UpdateError(f"Impossible de télécharger la mise à jour : {error.reason}") from error
    except (OSError, ValueError, UnicodeDecodeError) as error:
        if isinstance(error, UpdateError):
            raise
        raise UpdateError(f"Le téléchargement de la mise à jour a échoué : {error}") from error
    except UpdateError:
        raise
    finally:
        if not keep_temporary_file and temporary_path and os.path.exists(temporary_path):
            try:
                os.remove(temporary_path)
            except OSError as error:
                raise UpdateError(
                    f"Impossible de supprimer le téléchargement temporaire : {error}") from error
