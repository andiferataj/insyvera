"""Offline local backup/restore. The restore command refuses non-empty destinations."""
import argparse
from contextlib import closing
import hashlib
import io
import json
import shutil
import sqlite3
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from .config import settings

def backup(target):
    if not settings.database_url.startswith("sqlite"):
        raise ValueError("Use infrastructure/scripts/backup.ps1 for the Compose PostgreSQL stack.")
    target = Path(target).resolve()
    if target.is_relative_to(settings.data_dir.resolve()):
        raise ValueError("Backups must be written outside the data directory.")
    target.parent.mkdir(parents=True, exist_ok=True)
    database_path = settings.database_url.removeprefix("sqlite:///")
    temp = settings.data_dir / "tmp"
    temp.mkdir(exist_ok=True)
    manifest = {}
    with tempfile.TemporaryDirectory(dir=temp) as directory:
        snapshot = Path(directory) / "insyvera.db"
        with closing(sqlite3.connect(database_path)) as source, closing(sqlite3.connect(snapshot)) as copy:
            source.backup(copy)
        with tarfile.open(target, "w:gz") as archive:
            archive.add(snapshot, arcname="insyvera.db")
            manifest["insyvera.db"] = hashlib.sha256(snapshot.read_bytes()).hexdigest()
            for folder in ("objects", "checkpoints"):
                base = settings.data_dir / folder
                if base.exists():
                    for file in sorted(base.rglob("*")):
                        if file.is_file() and not file.is_symlink() and not file.name.endswith(("-wal","-shm")):
                            relative = file.relative_to(settings.data_dir).as_posix()
                            manifest[relative] = hashlib.sha256(file.read_bytes()).hexdigest()
                            archive.add(file, arcname=relative, recursive=False)
            raw = json.dumps({"format":"insyvera-backup-v1","created_at":datetime.now(timezone.utc).isoformat(),
                "files":manifest}).encode()
            info = tarfile.TarInfo("manifest.json")
            info.size = len(raw)
            archive.addfile(info, io.BytesIO(raw))
    return {"path":str(target),"files":len(manifest)}

def restore(source, destination):
    destination = Path(destination).resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Restore only into an empty directory. Existing data is never overwritten.")
    with tarfile.open(source, "r:gz") as archive:
        members = archive.getmembers()
        if any(not m.isfile() or not (destination / m.name).resolve().is_relative_to(destination) for m in members):
            raise ValueError("Backup contains unsafe paths or non-file entries.")
        if sum(m.size for m in members) > 2 * 1024**3:
            raise ValueError("Backup exceeds 2 GB.")
        manifest = json.loads(archive.extractfile("manifest.json").read())
        if manifest["format"] != "insyvera-backup-v1":
            raise ValueError("Unknown backup format.")
        for name, digest in manifest["files"].items():
            raw = archive.extractfile(name).read()
            if hashlib.sha256(raw).hexdigest() != digest:
                raise ValueError("Backup integrity check failed: " + name)
        destination.mkdir(parents=True, exist_ok=True)
        for name in manifest["files"]:
            file = destination / name
            file.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(name) as content, file.open("wb") as output:
                shutil.copyfileobj(content, output)
    return {"directory":str(destination),"files":len(manifest["files"])}

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=["backup","restore"])
    parser.add_argument("path")
    parser.add_argument("--destination")
    args=parser.parse_args()
    if args.action=="restore" and not args.destination:
        parser.error("Restore requires --destination pointing to an empty directory.")
    print(json.dumps(backup(args.path) if args.action=="backup" else restore(args.path,args.destination),indent=2))
