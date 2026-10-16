import fnmatch
import os
import shutil
import unicodedata
import uuid
import zipfile
from datetime import datetime
from pathlib import Path

from .config import APP_DIR, TRASH_DIR, TRASH_INDEX

CATEGORIES = {
    "Images": {"jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "heic", "tiff", "ico"},
    "Documents": {"pdf", "doc", "docx", "txt", "odt", "rtf", "xls", "xlsx", "ppt", "pptx", "csv", "md"},
    "Vidéos": {"mp4", "mkv", "avi", "mov", "wmv", "webm", "flv", "mpeg"},
    "Musique": {"mp3", "wav", "flac", "aac", "ogg", "m4a", "wma"},
    "Archives": {"zip", "rar", "7z", "tar", "gz", "bz2"},
    "Programmes": {"exe", "msi", "apk", "bat"},
}
ALL_EXT = set().union(*CATEGORIES.values())
TYPE_WORDS = {}


def _tw(words, exts):
    for w in words.split():
        TYPE_WORDS[w] = set(exts)


_tw("image images photo photos picture pictures", CATEGORIES["Images"])
_tw("document documents", CATEGORIES["Documents"])
_tw("video videos film films", CATEGORIES["Vidéos"])
_tw("musique musiques son sons audio audios chanson chansons", CATEGORIES["Musique"])
_tw("archive archives", CATEGORIES["Archives"])
_tw("programme programmes installateur installateurs logiciel logiciels", CATEGORIES["Programmes"])
_tw("word", {"doc", "docx"})
_tw("excel", {"xls", "xlsx"})
_tw("powerpoint", {"ppt", "pptx"})
_tw("texte textes", {"txt"})


def _nchar(c):
    d = unicodedata.normalize("NFD", c)
    return d[0].lower() if d else c


def norm(s):
    return "".join(_nchar(c) for c in s)


def ext_of(name):
    return os.path.splitext(name)[1].lower().lstrip(".")


def category_of(name):
    e = ext_of(name)
    for cat, exts in CATEGORIES.items():
        if e in exts:
            return cat
    return "Autres"


def fmt_size(n):
    for unit in ("o", "Ko", "Mo", "Go", "To"):
        if n < 1024 or unit == "To":
            return f"{n:.0f} o" if unit == "o" else f"{n:.1f} {unit}"
        n /= 1024


def is_hidden(entry):
    if entry.name.startswith("."):
        return True
    try:
        attrs = getattr(entry.stat(follow_symlinks=False), "st_file_attributes", 0)
        return bool(attrs & 0x6)
    except OSError:
        return False


def unique_path(folder, name, is_dir=False):
    cand = os.path.join(folder, name)
    if not os.path.exists(cand):
        return cand
    base, ext = (name, "") if is_dir else os.path.splitext(name)
    i = 1
    while True:
        cand = os.path.join(folder, f"{base} ({i}){ext}")
        if not os.path.exists(cand):
            return cand
        i += 1


def is_inside(child, parent):
    try:
        parent = os.path.abspath(parent)
        return os.path.commonpath([os.path.abspath(child), parent]) == parent
    except ValueError:
        return False


def copy_items(paths, dest):
    done, errs = 0, []
    for p in paths:
        name = os.path.basename(p)
        try:
            isdir = os.path.isdir(p)
            if isdir and is_inside(dest, p):
                errs.append(f"Impossible de copier « {name} » dans lui-même.")
                continue
            target = unique_path(dest, name, isdir)
            if isdir:
                shutil.copytree(p, target)
            else:
                shutil.copy2(p, target)
            done += 1
        except OSError as e:
            errs.append(f"{name} : {e}")
    return done, errs


def move_items(paths, dest):
    done, errs = 0, []
    for p in paths:
        name = os.path.basename(p)
        try:
            isdir = os.path.isdir(p)
            if isdir and is_inside(dest, p):
                errs.append(f"Impossible de déplacer « {name} » dans lui-même.")
                continue
            if os.path.abspath(os.path.dirname(p)) == os.path.abspath(dest):
                errs.append(f"« {name} » est déjà dans ce dossier.")
                continue
            shutil.move(p, unique_path(dest, name, isdir))
            done += 1
        except (OSError, shutil.Error) as e:
            errs.append(f"{name} : {e}")
    return done, errs


def zip_items(paths, zip_path):
    zip_abs = os.path.abspath(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            parent = os.path.dirname(os.path.abspath(p))
            if os.path.isdir(p):
                for root, _dirs, files in os.walk(p):
                    z.write(root, os.path.relpath(root, parent))
                    for f in files:
                        full = os.path.join(root, f)
                        if os.path.abspath(full) != zip_abs:
                            z.write(full, os.path.relpath(full, parent))
            elif os.path.abspath(p) != zip_abs:
                z.write(p, os.path.basename(p))


class Trash:
    def __init__(self):
        APP_DIR.mkdir(parents=True, exist_ok=True)
        TRASH_DIR.mkdir(parents=True, exist_ok=True)
        self.items = []
        try:
            with open(TRASH_INDEX, encoding="utf-8") as f:
                data = json.load(f)
            self.items = [i for i in data if (TRASH_DIR / i["id"]).exists()]
        except (OSError, ValueError, KeyError, TypeError):
            self.items = []

    def _save(self):
        with open(TRASH_INDEX, "w", encoding="utf-8") as f:
            json.dump(self.items, f, ensure_ascii=False, indent=1)

    def add(self, path):
        path = os.path.abspath(path)
        uid = uuid.uuid4().hex
        folder = TRASH_DIR / uid
        folder.mkdir(parents=True)
        name = os.path.basename(path)
        is_dir = os.path.isdir(path)
        size = 0 if is_dir else os.path.getsize(path)
        try:
            shutil.move(path, str(folder / name))
        except Exception:
            shutil.rmtree(folder, ignore_errors=True)
            raise
        self.items.append({
            "id": uid, "name": name, "original": path,
            "deleted": datetime.now().isoformat(timespec="seconds"),
            "is_dir": is_dir, "size": size,
        })
        self._save()

    def add_many(self, paths):
        done, errs = 0, []
        for p in paths:
            try:
                self.add(p)
                done += 1
            except Exception as e:  # noqa: BLE001
                errs.append(f"{os.path.basename(p)} : {e}")
        return done, errs

    def get(self, uid):
        return next((i for i in self.items if i["id"] == uid), None)

    def restore(self, uid):
        it = self.get(uid)
        if not it:
            raise OSError("élément introuvable dans la corbeille")
        src = TRASH_DIR / uid / it["name"]
        target_dir = os.path.dirname(it["original"])
        os.makedirs(target_dir, exist_ok=True)
        dest = unique_path(target_dir, it["name"], it["is_dir"])
        shutil.move(str(src), dest)
        shutil.rmtree(TRASH_DIR / uid, ignore_errors=True)
        self.items.remove(it)
        self._save()
        return dest

    def purge(self, uid):
        it = self.get(uid)
        if it:
            shutil.rmtree(TRASH_DIR / uid, ignore_errors=True)
            self.items.remove(it)
            self._save()

    def empty(self):
        for it in list(self.items):
            self.purge(it["id"])
