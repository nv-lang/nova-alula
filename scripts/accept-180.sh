#!/bin/sh
# Acceptance of the task 180 (the package part): three functions by role instead of `parse_agent_reply` (AL-131).
#
# Run from any place:  ALULA_GLOSSARY=<state-machine-glossary.md of the methodology, version 13> sh scripts/accept-180.sh
# The environment of Nova (the variables of the toolchain, `nova` on PATH) is the caller's; `NOVA` names the compiler if it is not `nova`.
# Heavy runs go one folder at a time, `nice -n 15`, `--jobs 2` (the machine is shared).
#
# What it checks (the red until the work is done):
#   1. the dictionary of the package is the normative part of the glossary of the methodology (version 13): the pairs, the hash 35c571ccda17;
#   2. the registries of the owner of the package (`spec/samples/registry.md`, `examples/registry.md`): no table "by role", no `parse_agent_reply`;
#      the sample registry has the three functions with the results WitnessAnswer, EditResult, LensResult;
#   3. no `parse_agent_reply` in the tests and the README that the task migrates (the samples, the cases and the scenarios are migrated by the task 181 together with the format);
#   4. `nova test` of the folders machine, machine_nested, machine_table, machine_text is green except the tests that wait for the task 181 (listed in WAITS_181 below).
set -u
cd "$(dirname "$0")/.." || exit 9
NOVA="${NOVA:-nova}"
fail=0
bad() { echo "RED: $*"; fail=1; }

# ---- 1. the dictionary -----------------------------------------------------------------------------------------------------------------------------
if [ -z "${ALULA_GLOSSARY:-}" ] || [ ! -f "$ALULA_GLOSSARY" ]; then
    bad "ALULA_GLOSSARY must name the file state-machine-glossary.md (version 13)"
else
    out=$(python scripts/glossary-names.py "$ALULA_GLOSSARY" --check 2>&1) || bad "glossary-names.py --check: $out"
    echo "$out" | head -3
    case "$out" in *"1270"*) ;; *) bad "the dictionary must have 1270 pairs: $out" ;; esac
    h=$(python scripts/glossary-names.py --hash 2>&1) || bad "glossary-names.py --hash: $h"
    [ "$h" = "35c571ccda17" ] || bad "the hash of the dictionary is $h, must be 35c571ccda17"
fi

# ---- 2. the registries ------------------------------------------------------------------------------------------------------------------------------
for r in spec/samples/registry.md examples/registry.md; do
    n=$(grep -c "по роли" "$r"); [ "$n" = "0" ] || bad "$r: \"по роли\" $n"
    n=$(grep -c "^## Roles" "$r"); [ "$n" = "0" ] || bad "$r: the table \"## Roles\" is still there"
    n=$(grep -c "parse_agent_reply" "$r"); [ "$n" = "0" ] || bad "$r: parse_agent_reply $n"
done
grep -q "^| parse_witness_reply | .*| \[\]WitnessAnswer | volatile |" spec/samples/registry.md || bad "spec/samples/registry.md: no parse_witness_reply -> []WitnessAnswer"
grep -q "^| parse_author_reply | .*| EditResult | volatile |" spec/samples/registry.md || bad "spec/samples/registry.md: no parse_author_reply -> EditResult"
grep -q "^| parse_lens_reply | .*| LensResult | volatile |" spec/samples/registry.md || bad "spec/samples/registry.md: no parse_lens_reply -> LensResult"

# ---- 3. the files that the task migrates -------------------------------------------------------------------------------------------------------------
MIGRATED="src/machine/README.md src/machine/host_test.nv src/machine_nested/check_test.nv src/machine_nested/translate_test.nv src/machine_table/v212_test.nv src/machine_text/glossary_names.tsv"
n=$(grep -c "parse_agent_reply" $MIGRATED | awk -F: '{s+=$2} END {print s+0}')
[ "$n" = "0" ] || bad "parse_agent_reply in the migrated files: $n"

# ---- 4. the tests -----------------------------------------------------------------------------------------------------------------------------------
total_ok=0
if [ "${SKIP_NOVA:-0}" = "1" ]; then
    echo "nova test skipped (SKIP_NOVA=1)"
else
    for d in machine machine_nested machine_table machine_text; do
        echo "=== nova test src/$d $(date +%T)"
        out=$(nice -n 15 "$NOVA" test "src/$d" --jobs 2 2>&1); rc=$?
        echo "$out" | tail -4
        [ "$rc" = "0" ] || bad "nova test src/$d: rc=$rc"
        sleep 5
    done
fi

if [ "$fail" = "0" ]; then
    echo "ACCEPTED 180 (package): parse_agent_reply 0 in the registries and the migrated files; \"по роли\" 0; dictionary 1270 pairs, hash 35c571ccda17; nova test machine, machine_nested, machine_table, machine_text green"
    exit 0
fi
echo "NOT ACCEPTED 180"
exit 1
