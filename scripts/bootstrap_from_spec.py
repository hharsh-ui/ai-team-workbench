"""Create every file embedded in the specification document.

  python scripts/bootstrap_from_spec.py WORKBENCH_SPEC.md --target .
  python scripts/bootstrap_from_spec.py WORKBENCH_SPEC.md --target ./my-workbench --list

A file block in the spec is a line '#### File: `relative/path`' followed by a fence of
five backticks. Files that already exist with the same content are skipped; a different
existing file stops the run unless you pass --force.
"""

import argparse
from pathlib import Path, PurePosixPath
import re
import sys

HEADING = re.compile(r"^#### File: `([^`]+)`\s*$")
FENCE = "`````"


def extract(text: str) -> list[tuple[str, str]]:
    lines = text.splitlines()
    files, index = [], 0
    while index < len(lines):
        match = HEADING.match(lines[index])
        index += 1
        if not match:
            continue
        while index < len(lines) and not lines[index].strip():
            index += 1
        if index >= len(lines) or not lines[index].startswith(FENCE):
            raise ValueError(f"File block {match.group(1)} has no opening fence of five backticks.")
        index += 1
        body = []
        while index < len(lines) and lines[index] != FENCE:
            body.append(lines[index])
            index += 1
        if index >= len(lines):
            raise ValueError(f"File block {match.group(1)} has no closing fence.")
        index += 1
        files.append((match.group(1), "\n".join(body) + "\n"))
    return files


def safe_path(target: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or re.match(r"^[A-Za-z]:", relative):
        raise ValueError(f"Refusing unsafe path: {relative}")
    return target.joinpath(*pure.parts)


def same_content(path: Path, content: str) -> bool:
    return path.read_bytes().replace(b"\r\n", b"\n") == content.encode("utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("spec")
    parser.add_argument("--target", required=True)
    parser.add_argument("--force", action="store_true", help="Overwrite existing files whose content differs")
    parser.add_argument("--list", action="store_true", help="Only list the files")
    args = parser.parse_args(argv)
    files = extract(Path(args.spec).read_text(encoding="utf-8"))
    target = Path(args.target).resolve()
    if args.list:
        print("\n".join(path for path, _ in files))
        print(f"{len(files)} files")
        return 0
    conflicts = [path for path, content in files
                 if safe_path(target, path).exists() and not same_content(safe_path(target, path), content)]
    if conflicts and not args.force:
        print("These files already exist with different content; nothing was written. Use --force to overwrite:\n  "
              + "\n  ".join(conflicts))
        return 1
    written = 0
    for relative, content in files:
        path = safe_path(target, relative)
        if path.exists() and same_content(path, content):
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        written += 1
    print(f"Wrote {written} files under {target} ({len(files) - written} already up to date)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
