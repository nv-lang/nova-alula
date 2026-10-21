# -*- coding: utf-8 -*-
"""Table of names of the translator of tables: Russian name -> English name from the dictionary of the methodology.

Usage: python scripts/glossary-names.py <state-machine-glossary.md> > src/machine_text/names.tsv

The dictionary (`state-machines/state-machine-glossary.md` of unitcraft/ai-dev-methodology, read only) keeps its names in tables of
section 2 (`| `ru` | `en` | ...`) and, for the data of the machines (2.10), in bullet lines (`ru` -> `en`). The output is one line
`kind<TAB>ru<TAB>en` per name, sorted by the Russian name; `#` lines are the header. Two English names for one Russian name
stop the script when they are in one kind of names; different kinds may differ (a datum `расход` is `transport_usage`, the field `расход` is
`usage`, section 2.15) and the translator asks for the kind it needs.
"""
import re
import sys

KINDS = {
    "2.2": "type", "2.3": "case", "2.4": "state", "2.5": "event", "2.6": "effect", "2.7": "method",
    "2.8": "function", "2.9": "field", "2.10": "data", "2.11": "constant", "2.12": "variable",
}


def main(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    version = ""
    for line in lines[:6]:
        m = re.search(r"Версия словаря: (\d+)", line)
        if m:
            version = m.group(1)
    section = None
    names = {}
    for line in lines:
        m = re.match(r"^###? (\d+\.\d+)\.", line)
        if m:
            section = m.group(1)
            continue
        if section not in KINDS:
            continue
        kind = KINDS[section]
        row = re.match(r"^\| `([^`]+)` \| `([^`]*)` \|", line)
        pairs = []
        if row:
            pairs.append((row.group(1), row.group(2)))
        elif section == "2.10":
            pairs.extend(re.findall(r"`([^`]+)` → `([^`]+)`", line))
        for ru, en in pairs:
            if "${" in ru or " " in ru and section != "2.4":
                continue
            key = (kind, ru)
            if key in names and names[key] != en:
                sys.exit("two English names for %s (%s): %s and %s" % (ru, kind, names[key], en))
            names[key] = en
    print("# Names of the dictionary of the methodology (state-machine-glossary.md, version %s), kind, Russian, English." % version)
    print("# Made by scripts/glossary-names.py; do not edit by hand (names of the format and of the product: names_format.tsv).")
    for (kind, ru) in sorted(names, key=lambda k: (k[1], k[0])):
        print("%s	%s	%s" % (kind, ru, names[(kind, ru)]))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
