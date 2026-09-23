"""Pin every declared ``>=`` floor to exactly that version, as pip constraints.

usage: minimum_constraints.py <output> <requirements file>...

The minimum-versions CI job installs with the result as a constraints file, so
each floor this project declares is a version the suite has actually run on --
not a number nobody has installed since it was written. Exact pins (``==``)
are left to the requirement files themselves; a floor in a comment is ignored.
"""
import pathlib
import re
import sys

FLOOR = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*>=\s*([0-9][^\s,;#]*)\s*(#.*)?$")

output, *sources = sys.argv[1:]
pins = []
for source in sources:
    for line in pathlib.Path(source).read_text(encoding="utf-8").splitlines():
        match = FLOOR.match(line)
        if match:
            pins.append(f"{match.group(1)}=={match.group(2)}")
if not pins:
    raise SystemExit(f"no '>=' floors found in {sources}")
pathlib.Path(output).write_text("".join(pin + "\n" for pin in pins), encoding="utf-8")
print("\n".join(pins))
