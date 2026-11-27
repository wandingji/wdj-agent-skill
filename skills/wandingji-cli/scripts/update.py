"""Check, defer, or install a confirmed Wandingji CLI skill release."""

import argparse
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
from tempfile import NamedTemporaryFile, TemporaryDirectory
from time import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZIP_DEFLATED, ZipFile


NAME = "wandingji-cli"
REPO = "wandingji/wdj-agent-skill"
MANIFEST = f"https://raw.githubusercontent.com/{REPO}/main/releases/{NAME}.json"
STATE = Path.home() / ".config" / "wandingji" / "skill-update.json"
SKILL = Path(__file__).resolve().parents[1]
DAY = 24 * 60 * 60
MAX_BYTES = 20 * 1024 * 1024
VERSION = re.compile(r"(?:0|[1-9][0-9]{0,5})(?:\.(?:0|[1-9][0-9]{0,5})){2}")


def version_tuple(value):
    if not isinstance(value, str) or not VERSION.fullmatch(value):
        raise ValueError("invalid stable version")
    return tuple(map(int, value.split(".")))


def version_from_skill(data):
    opening, metadata, _ = data.decode("utf-8").split("---", 2)
    if opening or not re.search(r"(?m)^name:\s*wandingji-cli\s*$", metadata):
        raise ValueError("unexpected skill")
    field = re.search(r"""(?m)^version:[ \t]*["']?([0-9.]+)["']?[ \t]*$""", metadata)
    if not field:
        raise ValueError("missing skill version")
    version = field.group(1)
    version_tuple(version)
    return version


def fetch(url, limit):
    request = Request(url, headers={"User-Agent": "wandingji-skill-update"})
    with urlopen(request, timeout=4) as response:
        final = urlsplit(response.geturl())
        if final.scheme != "https" or final.hostname != urlsplit(url).hostname:
            raise ValueError("invalid update host")
        body = response.read(limit + 1)
    if len(body) > limit:
        raise ValueError("update response too large")
    return body


def release_meta(data):
    if not isinstance(data, dict):
        raise ValueError("invalid release")
    version_tuple(data.get("version"))
    revision = data.get("revision")
    if not isinstance(revision, str) or not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("invalid release revision")
    return {"version": data["version"], "revision": revision}


def load_state():
    try:
        data = json.loads(STATE.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_state(data):
    STATE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with NamedTemporaryFile(mode="w", dir=STATE.parent, delete=False) as staged:
        json.dump(data, staged)
        path = Path(staged.name)
    try:
        os.replace(path, STATE)
    finally:
        path.unlink(missing_ok=True)


def check(current, state, force):
    now = int(time())
    checked = state.get("checked_at")
    if not force and type(checked) is int and 0 <= now - checked < DAY:
        release = state.get("latest")
    else:
        try:
            release = release_meta(json.loads(fetch(MANIFEST, 8192)))
        except (OSError, ValueError):
            release = None
        state.update(checked_at=now, latest=release)
        try:
            save_state(state)
        except OSError:
            pass
    if release is None:
        return {"status": "unavailable", "current": current}
    latest = release_meta(release)["version"]
    if version_tuple(latest) <= version_tuple(current):
        status = "up_to_date"
    elif not force and (state.get("skipped") == latest or (
        state.get("snoozed") == latest and isinstance(state.get("until"), int) and state["until"] > now
    )):
        status = "snoozed"
    else:
        status = "update_available"
    return {"status": status, "current": current, "latest": latest}


def read_release_files(release):
    revision = release["revision"]
    archive = fetch(f"https://codeload.github.com/{REPO}/zip/{revision}", MAX_BYTES)
    prefix = f"wdj-agent-skill-{revision}/skills/{NAME}/"
    files = {}
    total = 0
    with ZipFile(io.BytesIO(archive)) as bundle:
        for entry in bundle.infolist():
            if entry.is_dir() or not entry.filename.startswith(prefix):
                continue
            relative = entry.filename.removeprefix(prefix)
            path = PurePosixPath(relative)
            if (path.is_absolute() or path.as_posix() != relative or ".." in path.parts
                    or "\\" in relative or ":" in relative or relative.startswith(".")
                    or relative in files or stat.S_ISLNK(entry.external_attr >> 16)):
                raise ValueError("invalid ZIP entry")
            total += entry.file_size
            if total > MAX_BYTES or len(files) >= 100:
                raise ValueError("update archive too large")
            files[relative] = bundle.read(entry)
    if version_from_skill(files.get("SKILL.md", b"")) != release["version"] or "scripts/update.py" not in files:
        raise ValueError("release does not match the approved skill")
    return files


def local_install():
    candidates = [Path.home() / ".workbuddy" / "skills" / NAME]
    candidates.extend(Path.cwd() / directory / "skills" / NAME for directory in (".workbuddy", ".codebuddy"))
    return any(path == SKILL and path.resolve() == SKILL for path in candidates)


def install_update(files, release):
    version = release["version"]
    if local_install():
        with TemporaryDirectory(prefix=".wandingji-update-", dir=SKILL.parent) as temporary:
            temporary = Path(temporary)
            next_skill = temporary / "next"
            for name, content in files.items():
                file = next_skill / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(content)
            backup_root = STATE.parent / "skill-backups"
            backup_root.mkdir(parents=True, exist_ok=True)
            backup = backup_root / f"{NAME}-{int(time()*1000)}"
            shutil.copytree(SKILL, backup, symlinks=True)
            previous = temporary / "previous"
            os.replace(SKILL, previous)
            try:
                os.replace(next_skill, SKILL)
            except OSError:
                os.replace(previous, SKILL)
                raise
        return {"status": "updated", "version": version, "backup": str(backup)}
    directory = STATE.parent / "skill-downloads"
    directory.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(prefix=f"{NAME}-{version}-", suffix=".zip", dir=directory, delete=False) as output:
        with ZipFile(output, "w", compression=ZIP_DEFLATED) as bundle:
            for name, content in files.items():
                bundle.writestr(f"{NAME}/{name}", content)
    return {"status": "ready_to_import", "version": version, "path": output.name}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("check").add_argument("--force", action="store_true")
    for action in ("later", "skip", "update"):
        actions.add_parser(action).add_argument("version")
    args = parser.parse_args()
    try:
        current = version_from_skill((SKILL / "SKILL.md").read_bytes())
        state = load_state()
        if args.action == "check":
            result = check(current, state, args.force)
        else:
            if version_tuple(args.version) <= version_tuple(current):
                raise ValueError("version is not newer")
            if args.action == "later":
                state.update(snoozed=args.version, until=int(time()) + DAY)
                save_state(state)
                result = {"status": "snoozed", "version": args.version}
            elif args.action == "skip":
                state["skipped"] = args.version
                save_state(state)
                result = {"status": "skipped", "version": args.version}
            else:
                release = release_meta(json.loads(fetch(MANIFEST, 8192)))
                if release["version"] != args.version:
                    raise ValueError("latest version changed; ask the user again")
                result = install_update(read_release_files(release), release)
    except (BadZipFile, OSError, ValueError) as exc:
        print(json.dumps({"status": "unavailable", "error": type(exc).__name__}))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
