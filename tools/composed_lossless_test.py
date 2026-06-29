#!/usr/bin/env python3
"""LOSSLESS test — does Composed (GV v0.0.13 + Contract profile v0.1.10) reproduce the
OLD GV v0.0.12 *content* exactly, def-by-def, BYTE level (not just names)?

Definition of lossless here: EVERY $def in GV v0.0.12 must appear in the composed schema
with a BYTE-IDENTICAL body (canonical JSON). Extra defs in composed (e.g. SignatureNode,
ContractRoot) are ADDITIONS, not losses — reported but allowed.

Composed is reconstructed the way a2-sign composes it in memory:
  composed.$defs = GV0.0.13.$defs
                 + { localize(body) for each Contract-profile $def }   # cross-refs → local
                 + SignatureNode (synthesized from the GV signature types)

Exit 0 only if NOTHING in GV0.0.12 is missing or changed. Exit 1 otherwise (prints the
exact missing / changed defs). Run: python3 tools/composed_lossless_test.py
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GV12 = os.path.join(ROOT, "vault/v0.0.12/schema.json")
GV13 = os.path.join(ROOT, "vault/v0.0.13/schema.json")
CT = os.path.join(ROOT, "profiles/contract/v0.1.10/schema.json")

_ANY_DEFS_REF = re.compile(r'"\$ref":\s*"[^"]*#/\$defs/([A-Za-z0-9_]+)"')
_SIG_TYPES = ("BlockSignature", "HandwrittenSignature", "BiometricCapture", "SignatureBundle")


def defs(path):
    s = json.load(open(path, encoding="utf-8"))
    return s.get("$defs", s.get("definitions", {}))


def localize(obj):
    return json.loads(_ANY_DEFS_REF.sub(lambda m: '"$ref": "#/$defs/%s"' % m.group(1), json.dumps(obj)))


def canon(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)


def build_composed():
    gd = defs(GV13)
    composed = dict(gd)
    cd = defs(CT)
    if any(t in gd for t in _SIG_TYPES):
        composed["SignatureNode"] = {"oneOf": [{"$ref": "#/$defs/%s" % t} for t in _SIG_TYPES if t in gd]}
    for name, body in cd.items():
        composed[name] = localize(body)
    return composed


def main():
    g12 = defs(GV12)
    composed = build_composed()

    missing, changed = [], []
    for name, body in g12.items():
        if name not in composed:
            missing.append(name)
        elif canon(composed[name]) != canon(body):
            changed.append(name)

    additions = sorted(set(composed) - set(g12))

    print(f"GV0.0.12 defs: {len(g12)} | composed defs: {len(composed)}")
    print(f"additions in composed (allowed): {additions}")
    print(f"\n[LOSS] GV0.0.12 defs MISSING from composed ({len(missing)}): {sorted(missing) or 'NONE'}")
    print(f"[LOSS] GV0.0.12 defs whose BODY CHANGED ({len(changed)}): {sorted(changed) or 'NONE'}")

    for name in sorted(changed):
        print(f"\n--- DIFF: {name} ---")
        a, b = canon(g12[name]), canon(composed[name])
        print(f"  GV0.0.12 : {a[:300]}")
        print(f"  composed : {b[:300]}")

    ok = not missing and not changed
    print(f"\n{'PASS ✓ — composed reproduces GV0.0.12 byte-for-byte (lossless)' if ok else 'FAIL ✗ — NOT lossless (see above)'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
