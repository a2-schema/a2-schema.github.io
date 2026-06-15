#!/usr/bin/env python3
"""Generate the a2-schema SSoT set (v3): GV v0.0.8 + 2 profiles + 2 tiers.

GV is the single source of truth — all def bodies live in GV; profiles/tiers are
pure $ref/selection aggregators. Reads the in-repo GV v0.0.7 + contract v0.1.6,
integrates the signing-primitive closure + new biometric/ceremony defs, validates,
and writes to ~/Documents/Business/a2-schema.github.io/schemas/.
"""
import json, re, copy, hashlib, os

# Source schemas live in the dx-platform working repo (GV is built FROM the in-repo
# SSoT). Override with A2_DX_ROOT if cloned elsewhere.
DX = os.environ.get("A2_DX_ROOT", os.path.expanduser("~/Documents/Business/dx-platform"))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "schemas")
OUT = os.path.abspath(OUT)
GV_ID = "https://a2-schema.org/vault/v0.0.8/schema.json"
SIG_ID = "https://a2-schema.org/profiles/signature/v0.0.1/schema.json"
CT_ID = "https://a2-schema.org/profiles/contract/v0.1.7/schema.json"
GVREF = GV_ID + "#/$defs/"

gv = json.load(open(f"{DX}/xml/ichiriXML/a2_grand_vault_v_00_00_07.schema.json"))
ct = json.load(open(f"{DX}/xml/ichiriXML/a2-schema_module_schema/contract/a2_contract_module_v_00_01_06.schema.json"))
gd, cd = gv["$defs"], ct["$defs"]

# ---- 1. contract signing-primitive closure -------------------------------------
SEEDS = ["Party", "Clause", "ConsentToESign", "USESIGNCompliance", "SignatoryBlock",
         "Redline", "RedlineActionEnum", "PartySignatureStateEnum", "SigningCeremonyEvidence"]
def local_refs(o): return set(re.findall(r'#/\$defs/([A-Za-z0-9_]+)', json.dumps(o)))
closure, stack = set(), list(SEEDS)
while stack:
    n = stack.pop()
    if n in closure or n not in cd: continue
    closure.add(n)
    stack += [r for r in local_refs(cd[n]) if r in cd]

RENAME = {"Party": "ContractParty", "Clause": "ContractClause", "Redline": "RedlineAction"}
def integrate_contract(name):
    body = json.dumps(cd[name])
    for old, new in RENAME.items():
        body = body.replace(f'"#/$defs/{old}"', f'"#/$defs/{new}"')
    return json.loads(body)

# ---- 2. build GV v0.0.8 $defs ---------------------------------------------------
nd = copy.deepcopy(gd)  # start from GV v0.0.7

def add(name, body): nd[name] = body
def section(key, text): nd[key] = {"description": text, "x-a2-section": True}

# §1 SignedAt / SignedBy (prompt lists them as defs; GV had them only as HashChain props)
add("SignedAt", {"type": "string", "format": "date-time", "$comment": "§1 ISO-8601 time a node was signed."})
add("SignedBy", {"type": "string", "$comment": "§1 signer identity (URI/URN)."})

# §4 SignatureBundle
section("_____S4_SIGNATURE_PRIMITIVES_____", "─── §4 Signature Primitives (ML-DSA, RSA, JAdES, Bundle) ───")
add("SignatureBundle", {
    "type": "object", "$comment": "§4. Bundle of parallel signatures (ML-DSA + RSA + handwritten).",
    "x-a2-sign-target": True,
    "properties": {
        "$tag": {"const": "SignatureBundle"}, "id": {"$ref": "#/$defs/NodeIdType"},
        "signatures": {"type": "array", "items": {"oneOf": [
            {"$ref": "#/$defs/BlockSignature"}, {"$ref": "#/$defs/HandwrittenSignature"},
            {"$ref": "#/$defs/BiometricCapture"}]}},
        "primaryAlgorithm": {"$ref": "#/$defs/MLDSAAlgorithmEnum"}},
    "required": ["$tag", "signatures"]})

# §5 Biometric
section("_____S5_BIOMETRIC_____", "─── §5 Biometric (ISO/IEC 19794-7 handwriting + generic) ───")
add("BiometricTypeEnum", {"type": "string", "enum": ["handwriting", "fingerprint", "voiceprint", "facial", "iris", "vein"]})
add("HandwrittenSignature", {
    "type": "object",
    "$comment": "ISO/IEC 19794-7:2021 準拠 手書き署名 — 筆圧・速度・軌跡・傾き全データ。a2-Sign 含む全 DocType で使用可能。",
    "x-a2-sign-target": True, "x-a2-iso-standard": "ISO/IEC 19794-7:2021", "x-a2-level": "L9",
    "properties": {
        "$tag": {"const": "HandwrittenSignature"}, "id": {"$ref": "#/$defs/NodeIdType"},
        "isoStandard": {"type": "string", "const": "ISO/IEC 19794-7:2021"},
        "signerId": {"type": "string"}, "capturedAt": {"type": "string", "format": "date-time"},
        "biometricData": {"type": "object", "properties": {
            "strokes": {"type": "array", "items": {"type": "object", "properties": {
                "points": {"type": "array", "items": {"type": "object", "properties": {
                    "x": {"type": "number"}, "y": {"type": "number"},
                    "t": {"type": "number", "description": "ms from start"},
                    "pressure": {"type": "number", "minimum": 0, "maximum": 1},
                    "tiltX": {"type": "number"}, "tiltY": {"type": "number"},
                    "azimuth": {"type": "number"}, "altitude": {"type": "number"}},
                    "required": ["x", "y", "t"]}},
                "startTime": {"type": "string", "format": "date-time"},
                "endTime": {"type": "string", "format": "date-time"}}}},
            "totalDuration": {"type": "number"}, "avgVelocity": {"type": "number"},
            "maxVelocity": {"type": "number"}, "avgPressure": {"type": "number"},
            "strokeCount": {"type": "integer"}}},
        "deviceInfo": {"type": "object", "properties": {
            "deviceModel": {"type": "string"}, "manufacturer": {"type": "string"},
            "samplingRate": {"type": "number"}, "pressureLevels": {"type": "integer"},
            "spatialResolution": {"type": "string"}, "calibrationDate": {"type": "string", "format": "date-time"}}},
        "renderedImage": {"type": "object", "properties": {
            "format": {"enum": ["png", "svg"]}, "data": {"type": "string", "contentEncoding": "base64"},
            "width": {"type": "integer"}, "height": {"type": "integer"}}},
        "$signature": {"$ref": "#/$defs/SignatureBundle"}, "$hashChain": {"$ref": "#/$defs/HashChain"}},
    "required": ["$tag", "id", "isoStandard", "signerId", "capturedAt", "biometricData"]})
add("BiometricCapture", {
    "type": "object", "$comment": "§5. Generic biometric capture.",
    "properties": {
        "$tag": {"const": "BiometricCapture"}, "id": {"$ref": "#/$defs/NodeIdType"},
        "captureType": {"$ref": "#/$defs/BiometricTypeEnum"}, "isoStandard": {"type": "string"},
        "capturedAt": {"type": "string", "format": "date-time"},
        "data": {"type": "string", "contentEncoding": "base64"},
        "qualityScore": {"type": "number", "minimum": 0, "maximum": 1},
        "$signature": {"$ref": "#/$defs/SignatureBundle"}},
    "required": ["$tag", "captureType"]})

# §6 SigningCeremony
section("_____S6_SIGNING_CEREMONY_____", "─── §6 SigningCeremony (generic, all DocTypes) ───")
add("IALLevel", {"type": "string", "enum": ["IAL1", "IAL2", "IAL3"]})
add("AALLevel", {"type": "string", "enum": ["AAL1", "AAL2", "AAL3"]})
add("FALLevel", {"type": "string", "enum": ["FAL1", "FAL2", "FAL3"]})
add("CeremonyTypeEnum", {"type": "string", "enum": ["contract", "consent", "authorization",
    "attestation", "delegation", "will", "medical-consent", "regulatory-filing"]})
add("CeremonyParticipant", {"type": "object", "properties": {
    "actorId": {"type": "string"}, "role": {"type": "string"},
    "signedAt": {"$ref": "#/$defs/SignedAt"}, "ialLevel": {"$ref": "#/$defs/IALLevel"},
    "aalLevel": {"$ref": "#/$defs/AALLevel"}, "falLevel": {"$ref": "#/$defs/FALLevel"}}})
add("SigningCeremony", {
    "type": "object", "$comment": "§6. 汎用署名儀式 — 全 DocType で再利用可能。",
    "x-a2-sign-target": True, "x-a2-level": "L8",
    "properties": {
        "$tag": {"const": "SigningCeremony"}, "id": {"$ref": "#/$defs/NodeIdType"},
        "ceremonyType": {"$ref": "#/$defs/CeremonyTypeEnum"},
        "participants": {"type": "array", "items": {"$ref": "#/$defs/CeremonyParticipant"}},
        "startedAt": {"type": "string", "format": "date-time"},
        "completedAt": {"type": "string", "format": "date-time"},
        "location": {"type": "object", "properties": {
            "ipAddress": {"type": "string"}, "geolocation": {"type": "string"}, "deviceInfo": {"type": "string"}}},
        "$signature": {"$ref": "#/$defs/SignatureBundle"}, "$hashChain": {"$ref": "#/$defs/HashChain"}},
    "required": ["$tag", "id", "ceremonyType", "participants"]})

# §8 Contract Primitives (integrate the 22-def closure, renamed seeds)
section("_____S8_CONTRACT_PRIMITIVES_____", "─── §8 Contract Primitives (integrated from contract module) ───")
for name in sorted(closure):
    nd[RENAME.get(name, name)] = integrate_contract(name)
add("ContractSigningCeremony", {
    "type": "object", "$comment": "§8. Contract signing ceremony — extends SigningCeremony.",
    "allOf": [{"$ref": "#/$defs/SigningCeremony"}],
    "properties": {
        "$tag": {"const": "ContractSigningCeremony"}, "contractId": {"type": "string"},
        "jurisdiction": {"type": "string"},
        "applicableLaw": {"type": "string", "enum": ["US ESIGN", "JP 電子署名法", "EU eIDAS", "UNCITRAL"]},
        "esIgnConsent": {"$ref": "#/$defs/ConsentToESign"}}})
add("HandwrittenContractSignature", {
    "type": "object", "$comment": "§8. Contract wrapper around HandwrittenSignature.",
    "properties": {
        "$tag": {"const": "HandwrittenContractSignature"},
        "handwriting": {"$ref": "#/$defs/HandwrittenSignature"},
        "clauseId": {"type": "string"}, "agreementText": {"type": "string"}}})

# §9 reserved
section("_____S9_FUTURE_DOC_TYPES_____", "─── §9 Reserved for future modules (Medical, Robot, Life …) ───")

# ---- 3. GV v0.0.8 document ------------------------------------------------------
gv8 = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": GV_ID,
    "title": "Grand Vault v0.0.8 — Single Source of Truth",
    "version": "0.0.8",
    "description": "The complete, authoritative def repository for a2-schema. All other schemas $ref defs here. Sections §1–§9; scalable to 2500+ DocTypes.",
    "license": "Apache-2.0",
    "x-a2-role": "ssot",
    "x-a2-deprecation-policy": "Defs marked x-a2-deprecated remain available for 2 minor versions before removal.",
    "$defs": nd,
}
if "x-a2-input" in gv: gv8["x-a2-input"] = gv["x-a2-input"]

# ---- 4. validation --------------------------------------------------------------
def all_local_ref_names(doc): return set(re.findall(r'#/\$defs/([A-Za-z0-9_]+)', json.dumps(doc)))
missing = sorted(r for r in all_local_ref_names(gv8) if r not in nd)
dupes = "none (dict keys unique)"
print(f"GV v0.0.8 defs: {len(nd)}  (was {len(gd)})  | integrated closure: {len(closure)}")
print(f"dangling #/$defs refs in GV: {missing or 'NONE ✓'}")
try:
    from jsonschema import Draft202012Validator
    Draft202012Validator.check_schema(gv8)
    print("draft 2020-12 metaschema: VALID ✓")
except Exception as e:
    print("metaschema ERROR:", str(e)[:200])

GV_HASH = "sha256:" + hashlib.sha256(json.dumps(gv8, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

# ---- 5. profiles ----------------------------------------------------------------
sig_profile = {
    "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": SIG_ID,
    "title": "Signature Profile v0.0.1", "version": "0.0.1",
    "description": "Profile selecting signature-related defs from Grand Vault. NO own def bodies — pure $ref aggregator.",
    "license": "Apache-2.0", "x-a2-role": "profile", "x-a2-base-schema": GV_ID,
    "$defs": {"SignatureNode": {"oneOf": [
        {"$ref": GVREF + "BlockSignature"}, {"$ref": GVREF + "HandwrittenSignature"},
        {"$ref": GVREF + "BiometricCapture"}, {"$ref": GVREF + "SignatureBundle"}]}},
    "x-a2-included-defs": ["MLDSAAlgorithmEnum", "SignatureAlgorithmType", "LegacySignatureAlgEnum",
        "JAdESProfileEnum", "JAdESEtsiUEntry", "JAdESSigTst", "JAdESTstVD", "JAdESRVals", "JAdESXVals",
        "JCSCanonicalizationEnum", "JWSProtectedHeaderDecoded", "BlockSignature", "SignatureBundle",
        "HandwrittenSignature", "BiometricCapture", "BiometricTypeEnum"],
}
ct_profile = {
    "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": CT_ID,
    "title": "Contract Profile v0.1.7", "version": "0.1.7",
    "description": "Profile selecting contract-related defs from Grand Vault. References Signature Profile + contract primitives.",
    "license": "Apache-2.0", "x-a2-role": "profile", "x-a2-base-schema": GV_ID,
    "x-a2-depends-on": ["signature-profile-v0.0.1"],
    "$defs": {"ContractRoot": {"type": "object", "properties": {
        "$tag": {"const": "Contract"}, "id": {"$ref": GVREF + "NodeIdType"},
        "parties": {"type": "array", "items": {"$ref": GVREF + "ContractParty"}},
        "clauses": {"type": "array", "items": {"$ref": GVREF + "ContractClause"}},
        "signingCeremony": {"$ref": GVREF + "ContractSigningCeremony"},
        "$signature": {"$ref": SIG_ID + "#/$defs/SignatureNode"},
        "$hashChain": {"$ref": GVREF + "HashChain"}}}},
    "x-a2-included-defs": ["ContractParty", "ContractClause", "ConsentToESign", "USESIGNCompliance",
        "SignatoryBlock", "SigningCeremonyEvidence", "RedlineAction", "RedlineActionEnum",
        "PartySignatureStateEnum", "ContractSigningCeremony", "HandwrittenContractSignature"],
}

# profile $ref + included-defs must resolve to GV defs
def check_profile(p):
    bad = [r for r in re.findall(re.escape(GVREF) + r'([A-Za-z0-9_]+)', json.dumps(p)) if r not in nd]
    bad += [d for d in p.get("x-a2-included-defs", []) if d not in nd]
    return sorted(set(bad))
print("signature-profile unresolved:", check_profile(sig_profile) or "NONE ✓")
print("contract-profile unresolved:", check_profile(ct_profile) or "NONE ✓")

# ---- 6. tiers -------------------------------------------------------------------
SIGN_TIER_DEFS = ["A2Envelope", "Root", "Header", "NodeIdType", "SemanticType", "SemanticBlock",
    "Value", "ExternalPayload", "HashChain", "BlockHashChain", "AIAction", "Instruction", "AuditSession",
    "MLDSAAlgorithmEnum", "SignatureAlgorithmType", "BlockSignature", "SignatureBundle", "JAdESProfileEnum",
    "JCSCanonicalizationEnum", "JWSProtectedHeaderDecoded", "HandwrittenSignature", "BiometricCapture",
    "BiometricTypeEnum", "SigningCeremony", "CeremonyParticipant", "CeremonyTypeEnum", "IALLevel", "AALLevel",
    "FALLevel", "ContractParty", "ContractClause", "ConsentToESign", "USESIGNCompliance", "SignatoryBlock",
    "RedlineAction", "ContractSigningCeremony", "HandwrittenContractSignature"]
def tier(name, version, defs, profiles, desc):
    miss = [d for d in defs if d not in nd]
    print(f"tier {name}: {len(defs)} defs, missing-from-GV: {miss or 'NONE ✓'}")
    return {"$schema": "https://a2-schema.org/tier-config/v0.1.0", "kind": "tier-config",
        "tier": name, "version": version, "x-strip-mode": "selection", "description": desc,
        "imports": {"main": GV_ID}, "profiles": profiles,
        "baseSchemas": {"main": {"schemaHash": GV_HASH, "lastSyncedAt": "2026-06-15T00:00:00Z"}},
        "defs": {d: {"selected": True} for d in defs}}

a2sign_tier = tier("a2-sign", "0.0.1", SIGN_TIER_DEFS, [SIG_ID, CT_ID],
    "Tier config for the a2-Sign electronic-signature app: GV (SSoT) + signature & contract profiles + handwritten signature.")

# a2-doc: carry the in-repo doc_a2 tier's selected defs + new biometric/ceremony
doc_src = json.load(open(f"{DX}/xml/ichiriXML/tier_configs/tier_doc_a2.master.json"))
doc_selected = [k for k, v in (doc_src.get("defs") or {}).items() if isinstance(v, dict) and v.get("selected")]
doc_defs = sorted(set(doc_selected) | {"HandwrittenSignature", "BiometricCapture", "SigningCeremony", "SignatureBundle"})
doc_defs = [d for d in doc_defs if d in nd]  # only real GV defs
a2doc_tier = tier("a2-doc", "0.0.3", doc_defs, [SIG_ID],
    "General-purpose document tier (not contract-specific). Updated for SSoT v0.0.8.")

# ---- 7. write -------------------------------------------------------------------
os.makedirs(f"{OUT}/profiles", exist_ok=True)
os.makedirs(f"{OUT}/tier-configs", exist_ok=True)
def w(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print("wrote", path, f"({os.path.getsize(path)} bytes)")
w(f"{OUT}/a2-grand-vault-v00.00.08.json", gv8)
w(f"{OUT}/profiles/a2-signature-profile-v00.00.01.json", sig_profile)
w(f"{OUT}/profiles/a2-contract-profile-v00.01.07.json", ct_profile)
w(f"{OUT}/tier-configs/a2-sign-v00.00.01.json", a2sign_tier)
w(f"{OUT}/tier-configs/a2-doc-v00.00.03.json", a2doc_tier)
print("\nGV_HASH =", GV_HASH)
