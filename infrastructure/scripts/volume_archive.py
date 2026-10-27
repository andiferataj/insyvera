import sys
import tarfile
from pathlib import Path

action, source, target = sys.argv[1:]
source, target = Path(source), Path(target)
if action == "backup":
    with tarfile.open(target, "w") as archive:
        if source.exists():
            archive.add(source, arcname="checkpoints")
    print(target)
else:
    raise SystemExit("Only backup is supported by this helper. Restore manually to an empty, stopped stack.")
