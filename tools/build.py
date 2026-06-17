#!/usr/bin/env python3
"""Generate the a2-schema SSoT set (v4): GV v0.0.9 + 3 profiles + 3 tiers.

GV is the single source of truth — all def bodies live in GV; profiles/tiers are
pure $ref/selection aggregators. Reads the in-repo GV v0.0.7 + contract v0.1.6,
integrates the signing-primitive closure + biometric/ceremony defs, then adds the
§10 Compliance section (GDPR / EU AI Act / SOC 2 / ISO 27001 / HIPAA / PCI DSS …),
validates, and writes path-aligned artifacts to the repo root (the a2-schema.org
site root): vault/<ver>/schema.json, profiles/<name>/<ver>/schema.json,
tier-configs/<tier>/<ver>/config.json, each + a latest/ alias. File paths mirror
$id URL paths so every $id/$ref resolves on the live domain.

v0.0.9 is purely additive over v0.0.8: every prior def is byte-identical; only new
defs (§10 + ComplianceFrameworkEnum) and new OPTIONAL properties on AIAction /
Instruction / AuditSession are introduced (no existing property is retyped/removed).
"""
import json, re, copy, hashlib, os, glob

# Source schemas live in the dx-platform working repo (GV is built FROM the in-repo
# SSoT). Override with A2_DX_ROOT if cloned elsewhere.
DX = os.environ.get("A2_DX_ROOT", os.path.expanduser("~/Documents/Business/dx-platform"))
# Output root = repo root = the GitHub Pages site root for the a2-schema.org apex
# domain. File paths therefore mirror the $id URL paths (no /schemas/ prefix), so
# every $id / $ref resolves directly once the domain is live.
OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DOMAIN = "https://a2-schema.org/"
GV_ID = DOMAIN + "vault/v0.0.9/schema.json"
SIG_ID = DOMAIN + "profiles/signature/v0.0.2/schema.json"
CT_ID = DOMAIN + "profiles/contract/v0.1.8/schema.json"
COMP_ID = DOMAIN + "profiles/compliance/v0.0.1/schema.json"
TIER_META_ID = DOMAIN + "tier-configs/_meta/v0.1.0/schema.json"   # meta-schema describing tier configs (under tier-configs/)
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
    # BUG FIX: the contract module was authored with ABSOLUTE refs to a long-gone
    # vault version (…/vault/v0.0.6/schema.json#/$defs/X). Once integrated INTO the
    # vault these must be LOCAL refs. Rewrite any absolute a2-schema vault ref to
    # #/$defs/ (the targets are base types that now live in this GV). Do this BEFORE
    # the RENAME so renamed contract types are also caught.
    body = re.sub(r'https://a2-schema\.org/vault/v[0-9.]+/schema\.json#/\$defs/',
                  '#/$defs/', body)
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

# ---- 2b. §3 AI-Audit extensions (PURELY ADDITIVE; no existing property retyped) --
# AIAction already carries humanOverride(bool)/failureReason(str)/humanOverrideBy/At
# plus `unevaluatedProperties:false` + `dependentRequired`. To stay backward
# compatible we ADD new optional properties only (the rich EU-AI-Act human-oversight
# object lives under the new name `humanOversight`, leaving the existing boolean flag
# intact). Every added key is registered in `properties` so `unevaluatedProperties`
# stays satisfiable.
aia = nd["AIAction"]["properties"]
aia["modelName"]    = {"type": "string", "description": "推論モデル名。EU AI Act 透明性。"}
aia["provider"]     = {"type": "string", "description": "モデル提供者。"}
aia["deploymentId"] = {"type": "string", "description": "デプロイ識別子。再現性検証。"}
aia["riskLevel"]    = {"$comment": "EU AI Act リスク分類 ⭐ NEW",
    "enum": ["minimal", "limited", "high", "unacceptable"]}
aia["explainability"] = {"type": "object", "$comment": "EU AI Act Art.13 透明性 ⭐ NEW",
    "properties": {
        "method": {"enum": ["SHAP", "LIME", "attention", "rule-based", "other"]},
        "factors": {"type": "array", "items": {"type": "object", "properties": {
            "feature": {"type": "string"}, "importance": {"type": "number"},
            "direction": {"enum": ["positive", "negative"]}}}},
        "humanReadableExplanation": {"type": "string"}}}
aia["humanOversight"] = {"type": "object",
    "$comment": "EU AI Act Art.14 人的監督の詳細 ⭐ NEW (既存 humanOverride boolean を補完)。",
    "properties": {
        "required": {"type": "boolean"}, "performed": {"type": "boolean"},
        "approverId": {"type": "string"}, "approverIalLevel": {"$ref": "#/$defs/IALLevel"},
        "approvedAt": {"type": "string", "format": "date-time"},
        "decision": {"enum": ["approved", "rejected", "modified"]},
        "modifications": {"type": "object"}, "reasoning": {"type": "string"}}}
aia["dataLineage"] = {"type": "object", "$comment": "入力データ出所追跡 ⭐ NEW",
    "properties": {"sources": {"type": "array", "items": {"type": "object", "properties": {
        "dataId": {"type": "string"},
        "sourceType": {"enum": ["user-input", "database", "external-api", "training-data"]},
        "collectedAt": {"type": "string", "format": "date-time"},
        "consentReceiptId": {"type": "string"}}}}}}

# Instruction: add GDPR legal-basis + IAL + purpose/constraints (new optional props).
ins = nd["Instruction"]["properties"]
ins["issuerIalLevel"] = {"$ref": "#/$defs/IALLevel", "$comment": "⭐ NEW 発行者 IAL。"}
ins["purpose"]        = {"type": "string", "$comment": "⭐ NEW 処理目的。"}
ins["constraints"]    = {"type": "array", "items": {"type": "string"}, "$comment": "⭐ NEW 制約。"}
ins["consentBasis"]   = {"$comment": "⭐ NEW GDPR Art.6 法的根拠",
    "enum": ["consent", "contract", "legal_obligation", "vital_interests",
             "public_task", "legitimate_interests"]}

# AuditSession: widen sessionType with "compliance" + add complianceFrameworks.
ases = nd["AuditSession"]["properties"]
if "compliance" not in ases["sessionType"]["enum"]:
    ases["sessionType"]["enum"].append("compliance")
ases["complianceFrameworks"] = {"type": "array",
    "items": {"$ref": "#/$defs/ComplianceFrameworkEnum"},
    "$comment": "⭐ NEW このセッションに適用される Compliance フレームワーク。"}

# ---- 2c. §10 Compliance (NEW defs) ----------------------------------------------
section("_____S10_COMPLIANCE_____",
    "─── §10 Compliance: GDPR / EU AI Act / SOC 2 / ISO 27001 / HIPAA / PCI DSS / ESG ───")

add("ComplianceFrameworkEnum", {"$comment": "§10. 対応 Compliance フレームワーク。", "enum": [
    "SOC2_TSC", "ISO27001_AnnexA", "ISO27017", "ISO27018", "GDPR", "CCPA", "JP_PIPA",
    "EU_AI_Act", "NIST_AI_RMF", "HIPAA", "PCI_DSS", "NIST_800_53", "NIST_CSF", "FedRAMP",
    "FISC", "JP_3SHO_2GL", "ESG", "TCFD", "CSDDD", "NIS2", "JP_DENSHO", "JP_INVOICE"]})

add("ConsentReceipt", {
    "type": "object",
    "$comment": "§10. GDPR / CCPA / 個人情報保護法 / ESIGN 同意記録。Kantara Consent Receipt v1.1 準拠。",
    "x-a2-sign-target": True, "x-a2-level": "L8",
    "properties": {
        "$tag": {"const": "ConsentReceipt"}, "id": {"$ref": "#/$defs/NodeIdType"},
        "version": {"type": "string", "default": "1.1.0"},
        "receiptType": {"enum": ["data-processing", "esign-disclosure", "marketing",
            "cookie", "biometric", "ai-processing", "third-party-sharing"]},
        "dataSubject": {"type": "object", "properties": {
            "subjectId": {"type": "string"}, "verificationMethod": {"type": "string"},
            "ialLevel": {"$ref": "#/$defs/IALLevel"}}},
        "dataController": {"type": "object", "properties": {
            "organizationId": {"type": "string"}, "name": {"type": "string"},
            "contactEmail": {"type": "string", "format": "email"}, "jurisdiction": {"type": "string"}}},
        "purposes": {"type": "array", "items": {"type": "object", "properties": {
            "purposeCode": {"type": "string"}, "purposeDescription": {"type": "string"},
            "legalBasis": {"enum": ["consent", "contract", "legal_obligation",
                "vital_interests", "public_task", "legitimate_interests"]},
            "retentionPeriod": {"type": "string", "description": "ISO 8601 duration (e.g., P1Y, P30D)"}}}},
        "dataCategories": {"type": "array", "items": {"type": "string"}},
        "thirdPartySharing": {"type": "array", "items": {"type": "object", "properties": {
            "recipientName": {"type": "string"}, "jurisdiction": {"type": "string"},
            "purpose": {"type": "string"}}}},
        "rights": {"type": "array", "items": {
            "enum": ["access", "rectification", "erasure", "portability", "object", "withdraw"]}},
        "withdrawalMethod": {"type": "object", "properties": {
            "url": {"type": "string", "format": "uri"},
            "email": {"type": "string", "format": "email"}, "phone": {"type": "string"}}},
        "consentGivenAt": {"type": "string", "format": "date-time"},
        "consentValidUntil": {"type": "string", "format": "date-time"},
        "consentMethod": {"enum": ["explicit-checkbox", "explicit-signature", "implicit", "biometric"]},
        "evidenceUri": {"type": "string", "format": "uri"},
        "$signature": {"$ref": "#/$defs/SignatureBundle"}, "$hashChain": {"$ref": "#/$defs/HashChain"}},
    "required": ["$tag", "id", "receiptType", "dataSubject", "dataController", "purposes", "consentGivenAt"]})

add("ComplianceLog", {
    "type": "object",
    "$comment": "§10. 汎用 Compliance 統制実施ログ。SOC 2 / ISO 27001 / HIPAA / PCI DSS の自動証拠収集。",
    "x-a2-sign-target": True, "x-a2-level": "L7",
    "properties": {
        "$tag": {"const": "ComplianceLog"}, "id": {"$ref": "#/$defs/NodeIdType"},
        "controlIds": {"type": "array", "items": {"type": "string"},
            "description": "適用統制ID (例: SOC2.CC6.1, ISO27001.A.9.1, GDPR.Art32)"},
        "framework": {"type": "array", "items": {"$ref": "#/$defs/ComplianceFrameworkEnum"}},
        "controlType": {"enum": ["preventive", "detective", "corrective", "compensating"]},
        "evidence": {"type": "object", "description": "統制実施の証拠データ (フリーフォーム)"},
        "result": {"enum": ["compliant", "non-compliant", "partial", "not-applicable"]},
        "severity": {"enum": ["info", "low", "medium", "high", "critical"]},
        "collectionMethod": {"enum": ["automatic", "semi-automatic", "manual"]},
        "remediationActions": {"type": "array", "items": {"type": "object", "properties": {
            "action": {"type": "string"}, "performedAt": {"type": "string", "format": "date-time"},
            "performerId": {"type": "string"}, "result": {"type": "string"}}}},
        "timestamp": {"type": "string", "format": "date-time"},
        "$signature": {"$ref": "#/$defs/SignatureBundle"}, "$hashChain": {"$ref": "#/$defs/HashChain"}},
    "required": ["$tag", "id", "controlIds", "framework", "timestamp"]})

add("DataLineage", {
    "type": "object", "$comment": "§10. データ出所追跡。GDPR / EU AI Act 対応。",
    "x-a2-level": "L7",
    "properties": {
        "$tag": {"const": "DataLineage"}, "id": {"$ref": "#/$defs/NodeIdType"},
        "dataId": {"type": "string"},
        "sources": {"type": "array", "items": {"type": "object", "properties": {
            "sourceType": {"enum": ["user-input", "database", "external-api",
                "training-data", "ai-generated", "third-party"]},
            "sourceId": {"type": "string"}, "collectedAt": {"type": "string", "format": "date-time"},
            "consentReceiptId": {"type": "string"},
            "transformations": {"type": "array", "items": {"type": "string"}}}}},
        "$signature": {"$ref": "#/$defs/SignatureBundle"}, "$hashChain": {"$ref": "#/$defs/HashChain"}},
    "required": ["$tag", "id"]})

add("PIIDetection", {
    "type": "object", "$comment": "§10. 個人情報 (PII) 検出記録。GDPR / 個人情報保護法対応。",
    "x-a2-level": "L7",
    "properties": {
        "$tag": {"const": "PIIDetection"}, "id": {"$ref": "#/$defs/NodeIdType"},
        "documentId": {"type": "string"},
        "detections": {"type": "array", "items": {"type": "object", "properties": {
            "piiType": {"enum": ["name", "email", "phone", "address", "national-id",
                "passport", "drivers-license", "credit-card", "bank-account",
                "health-data", "biometric", "genetic", "location", "ip-address"]},
            "location": {"type": "string", "description": "Document path or coordinates"},
            "confidence": {"$ref": "#/$defs/ConfidenceType"},
            "maskingApplied": {"type": "boolean"}}}},
        "detectedAt": {"type": "string", "format": "date-time"},
        "$signature": {"$ref": "#/$defs/SignatureBundle"}},
    "required": ["$tag", "id"]})

add("DataSubjectRequest", {
    "type": "object", "$comment": "§10. データ主体権利行使要求 (GDPR Art 15-22)。RTBF 対応。",
    "x-a2-sign-target": True, "x-a2-level": "L7",
    "properties": {
        "$tag": {"const": "DataSubjectRequest"}, "id": {"$ref": "#/$defs/NodeIdType"},
        "requestType": {"enum": ["access", "rectification", "erasure", "restrict",
            "portability", "object"]},
        "subjectId": {"type": "string"}, "verificationMethod": {"type": "string"},
        "ialLevel": {"$ref": "#/$defs/IALLevel"},
        "requestedAt": {"type": "string", "format": "date-time"},
        "responseDeadline": {"type": "string", "format": "date-time", "description": "GDPR 1ヶ月以内"},
        "status": {"enum": ["pending", "in-progress", "completed", "rejected", "extended"]},
        "completedAt": {"type": "string", "format": "date-time"},
        "rejectionReason": {"type": "string"},
        "$signature": {"$ref": "#/$defs/SignatureBundle"}, "$hashChain": {"$ref": "#/$defs/HashChain"}},
    "required": ["$tag", "id", "requestType", "subjectId"]})

add("IncidentReport", {
    "type": "object",
    "$comment": "§10. セキュリティインシデント記録。NIS2 24h通報 / GDPR Art 33 (72h通報) 対応。",
    "x-a2-sign-target": True, "x-a2-level": "L7",
    "properties": {
        "$tag": {"const": "IncidentReport"}, "id": {"$ref": "#/$defs/NodeIdType"},
        "incidentType": {"enum": ["data-breach", "system-compromise", "ddos",
            "ransomware", "insider-threat", "other"]},
        "severity": {"enum": ["low", "medium", "high", "critical"]},
        "detectedAt": {"type": "string", "format": "date-time"},
        "discoveredAt": {"type": "string", "format": "date-time"},
        "containedAt": {"type": "string", "format": "date-time"},
        "affectedDataSubjects": {"type": "integer"},
        "affectedDataTypes": {"type": "array", "items": {"type": "string"}},
        "notifications": {"type": "array", "items": {"type": "object", "properties": {
            "recipient": {"enum": ["authority", "data-subjects", "public"]},
            "sentAt": {"type": "string", "format": "date-time"}, "method": {"type": "string"}}}},
        "remediation": {"type": "string"},
        "$signature": {"$ref": "#/$defs/SignatureBundle"}, "$hashChain": {"$ref": "#/$defs/HashChain"}},
    "required": ["$tag", "id", "incidentType", "severity"]})

add("AccessControlEvent", {
    "type": "object", "$comment": "§10. アクセス制御イベント。SOC 2 CC6.x / ISO 27001 A.9.x 対応。",
    "x-a2-level": "L7",
    "properties": {
        "$tag": {"const": "AccessControlEvent"}, "id": {"$ref": "#/$defs/NodeIdType"},
        "eventType": {"enum": ["login-success", "login-failure", "logout", "session-timeout",
            "permission-granted", "permission-denied", "role-assigned", "role-revoked",
            "privilege-escalation", "data-access", "data-modification", "data-deletion"]},
        "actorId": {"type": "string"}, "resourceId": {"type": "string"},
        "ialLevel": {"$ref": "#/$defs/IALLevel"}, "aalLevel": {"$ref": "#/$defs/AALLevel"},
        "ipAddress": {"type": "string"}, "userAgent": {"type": "string"},
        "deviceFingerprint": {"type": "string"}, "geolocation": {"type": "string"},
        "result": {"enum": ["allowed", "denied", "error"]},
        "denialReason": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "$signature": {"$ref": "#/$defs/SignatureBundle"}, "$hashChain": {"$ref": "#/$defs/HashChain"}},
    "required": ["$tag", "id", "eventType", "timestamp"]})

add("GovernanceAttestation", {
    "type": "object", "$comment": "§10. ガバナンス・ESG 証明。TCFD / CSDDD / 上場企業ESG開示対応。",
    "x-a2-sign-target": True, "x-a2-level": "L8",
    "properties": {
        "$tag": {"const": "GovernanceAttestation"}, "id": {"$ref": "#/$defs/NodeIdType"},
        "attestationType": {"enum": ["esg", "tcfd", "csddd", "csr", "human-rights-dd"]},
        "reportingPeriod": {"type": "object", "properties": {
            "start": {"type": "string", "format": "date"}, "end": {"type": "string", "format": "date"}}},
        "metrics": {"type": "object"},
        "attestor": {"type": "object", "properties": {
            "organizationId": {"type": "string"}, "officerName": {"type": "string"},
            "ialLevel": {"$ref": "#/$defs/IALLevel"}}},
        "attestedAt": {"type": "string", "format": "date-time"},
        "$signature": {"$ref": "#/$defs/SignatureBundle"}, "$hashChain": {"$ref": "#/$defs/HashChain"}},
    "required": ["$tag", "id", "attestationType"]})

# ---- 3. GV v0.0.9 document ------------------------------------------------------
gv8 = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": GV_ID,
    "title": "Grand Vault v0.0.9 — SSoT with Compliance Extensions",
    "version": "0.0.9",
    "description": "SSoT with §10 Compliance extensions (GDPR / EU AI Act / SOC 2 / ISO 27001 / HIPAA / PCI DSS / ESG). Purely additive over v0.0.8. All other schemas $ref defs here. Sections §1–§10; scalable to 2500+ DocTypes.",
    "license": "Apache-2.0",
    "x-a2-role": "ssot",
    "x-a2-deprecation-policy": "Defs marked x-a2-deprecated remain available for 2 minor versions before removal.",
    "$defs": nd,
}
if "x-a2-input" in gv: gv8["x-a2-input"] = gv["x-a2-input"]

# ---- 4. validation --------------------------------------------------------------
def all_local_ref_names(doc): return set(re.findall(r'#/\$defs/([A-Za-z0-9_]+)', json.dumps(doc)))
missing = sorted(r for r in all_local_ref_names(gv8) if r not in nd)
# GV must be self-contained: it may reference ONLY itself, via LOCAL #/$defs refs.
# Any absolute a2-schema URL ref inside GV is a bug (e.g. stale vault/v0.0.6 refs
# carried in from the contract module). Flag them so they can never ship silently.
abs_self_refs = sorted(set(re.findall(r'"\$ref":\s*"(https://a2-schema\.org/[^"]+)"', json.dumps(gv8))))
print(f"GV v0.0.9 defs: {len(nd)}  (was {len(gd)})  | integrated closure: {len(closure)}")
print(f"dangling #/$defs refs in GV: {missing or 'NONE ✓'}")
print(f"absolute a2-schema refs inside GV (must be 0): {abs_self_refs or 'NONE ✓'}")
assert not abs_self_refs, f"GV contains absolute self-refs (should be local): {abs_self_refs}"
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
    "title": "Signature Profile v0.0.2", "version": "0.0.2",
    "description": "Profile selecting signature-related defs from Grand Vault v0.0.9. NO own def bodies — pure $ref aggregator.",
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
    "title": "Contract Profile v0.1.8", "version": "0.1.8",
    "description": "Profile selecting contract-related defs from Grand Vault v0.0.9. References Signature Profile + contract primitives. Adds ContractConsentReceipt (ESIGN disclosure).",
    "license": "Apache-2.0", "x-a2-role": "profile", "x-a2-base-schema": GV_ID,
    "x-a2-depends-on": ["signature-profile-v0.0.2"],
    "$defs": {
        "ContractRoot": {"type": "object", "properties": {
            "$tag": {"const": "Contract"}, "id": {"$ref": GVREF + "NodeIdType"},
            "parties": {"type": "array", "items": {"$ref": GVREF + "ContractParty"}},
            "clauses": {"type": "array", "items": {"$ref": GVREF + "ContractClause"}},
            "signingCeremony": {"$ref": GVREF + "ContractSigningCeremony"},
            "$signature": {"$ref": SIG_ID + "#/$defs/SignatureNode"},
            "$hashChain": {"$ref": GVREF + "HashChain"}}},
        "ContractConsentReceipt": {
            "$comment": "Contract-specific ConsentReceipt (ESIGN disclosure). Composes GV ConsentReceipt.",
            "allOf": [{"$ref": GVREF + "ConsentReceipt"}],
            "properties": {
                "contractId": {"type": "string"},
                "esIgnDisclosure": {"$ref": GVREF + "ConsentToESign"}}}},
    "x-a2-included-defs": ["ContractParty", "ContractClause", "ConsentToESign", "USESIGNCompliance",
        "SignatoryBlock", "SigningCeremonyEvidence", "RedlineAction", "RedlineActionEnum",
        "PartySignatureStateEnum", "ContractSigningCeremony", "HandwrittenContractSignature",
        "ConsentReceipt"],
}
comp_profile = {
    "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": COMP_ID,
    "title": "Compliance Profile v0.0.1", "version": "0.0.1",
    "description": "Profile selecting compliance-related defs from Grand Vault v0.0.9. References §10 Compliance + §3 AI Audit. NO own def bodies — pure $ref aggregator.",
    "license": "Apache-2.0", "x-a2-role": "profile", "x-a2-base-schema": GV_ID,
    "$defs": {"ComplianceEvent": {"oneOf": [
        {"$ref": GVREF + "ComplianceLog"}, {"$ref": GVREF + "AccessControlEvent"},
        {"$ref": GVREF + "ConsentReceipt"}, {"$ref": GVREF + "DataSubjectRequest"},
        {"$ref": GVREF + "IncidentReport"}, {"$ref": GVREF + "PIIDetection"},
        {"$ref": GVREF + "GovernanceAttestation"}, {"$ref": GVREF + "AIAction"}]}},
    "x-a2-included-defs": ["ComplianceLog", "ComplianceFrameworkEnum", "ConsentReceipt", "DataLineage",
        "DataSubjectRequest", "IncidentReport", "AccessControlEvent", "PIIDetection",
        "GovernanceAttestation", "AIAction", "Instruction", "AuditSession"],
}

# profile $ref + included-defs must resolve to GV defs
def check_profile(p):
    bad = [r for r in re.findall(re.escape(GVREF) + r'([A-Za-z0-9_]+)', json.dumps(p)) if r not in nd]
    bad += [d for d in p.get("x-a2-included-defs", []) if d not in nd]
    return sorted(set(bad))
print("signature-profile unresolved:", check_profile(sig_profile) or "NONE ✓")
print("contract-profile  unresolved:", check_profile(ct_profile) or "NONE ✓")
print("compliance-profile unresolved:", check_profile(comp_profile) or "NONE ✓")

# ---- 6. tiers / tier-config meta: NOT published (decision 2026-06-17) -----------
# Tier configs are INTERNAL build manifests: they select GV defs per app/doctype AND
# carry app-specific UI/look metadata (x-a2-ui, per-property meta, the seed for
# $formDesign). They are NOT part of the public schema vocabulary, so this publisher
# does NOT generate or emit any tier config or tier-config meta-schema.
# Public surface = Grand Vault + profiles ONLY. Tier sources live in dx-platform
# (xml/ichiriXML/tier_configs/). See docs/schema-architecture.md §8.

# ---- 7. write (path-aligned: file path == $id URL path; site root = repo root) ---
def id_to_path(schema_id):
    assert schema_id.startswith(DOMAIN), schema_id
    return os.path.join(OUT, schema_id[len(DOMAIN):])   # strip domain -> repo-root-relative
def latest_path(rel_or_id_path):
    parts = rel_or_id_path.split(os.sep); parts[-2] = "latest"; return os.sep.join(parts)
def w(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print("wrote", os.path.relpath(path, OUT), f"({os.path.getsize(path)} bytes)")

# canonical, immutable, version-pinned artifacts at their $id paths + a `latest` alias.
# Public surface = Grand Vault + profiles ONLY (no tiers — see §6 above).
# The `latest` copy is byte-identical (its internal $id still names the real version —
# `latest` is a convenience mirror, never a distinct identity).
for obj in (gv8, sig_profile, ct_profile, comp_profile):
    p = id_to_path(obj["$id"])
    w(p, obj)
    w(latest_path(p), obj)

# ---- 8. migrate frozen legacy versions into the path-aligned layout --------------
# Older published files were flat (schemas/<name>-vNN.json). Relocate each to its $id
# path so its URL resolves; tiers also get $id + a resolvable $schema. Content of
# schema bodies is preserved byte-for-byte (frozen versions stay immutable).
LEGACY = os.path.join(OUT, "schemas")
def migrate_legacy():
    if not os.path.isdir(LEGACY): return
    for root, _, files in os.walk(LEGACY):
        for fn in files:
            if not fn.endswith(".json"): continue
            src = os.path.join(root, fn)
            doc = json.load(open(src, encoding="utf-8"))
            if doc.get("kind") == "tier-config":          # legacy tier → new layout + fixes
                t, v = doc.get("tier"), doc.get("version")
                doc["$schema"] = TIER_META_ID
                doc["$id"] = f"{DOMAIN}tier-configs/{t}/v{v}/config.json"
                dst = id_to_path(doc["$id"])
            elif isinstance(doc.get("$id"), str) and doc["$id"].startswith(DOMAIN):
                dst = id_to_path(doc["$id"])
            else:
                print("  ⚠ legacy file has no a2-schema $id, leaving in place:", fn); continue
            if os.path.abspath(dst) == os.path.abspath(src): continue
            if os.path.exists(dst):    # build already wrote this version — its output wins
                continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "w", encoding="utf-8") as f:
                json.dump(doc, f, ensure_ascii=False, indent=2)
            print("migrated legacy", fn, "->", os.path.relpath(dst, OUT))
migrate_legacy()

# ---- 9. normalize: a vault file must reference ONLY itself, via LOCAL refs --------
# Fixes the stale absolute vault/v0.0.6 refs that the contract module carried into
# every GV build (incl. the frozen v0.0.8). Idempotent: rewrites absolute a2-schema
# vault refs -> #/$defs/ in any vault/**/schema.json, then asserts none remain.
def normalize_vault_self_refs():
    for f in glob.glob(os.path.join(OUT, "vault", "**", "schema.json"), recursive=True):
        txt = open(f, encoding="utf-8").read()
        fixed = re.sub(r'https://a2-schema\.org/vault/v[0-9.]+/schema\.json#/\$defs/',
                       '#/$defs/', txt)
        if fixed != txt:
            open(f, "w", encoding="utf-8").write(fixed)
            print("normalized self-refs in", os.path.relpath(f, OUT))
        leftover = re.findall(r'"\$ref":\s*"(https://a2-schema\.org/vault/[^"]+)"', fixed)
        assert not leftover, f"{f} still has absolute vault refs: {leftover[:2]}"
normalize_vault_self_refs()

print("\nGV_HASH =", GV_HASH)
print("NOTE: after a clean run, delete the now-empty legacy schemas/ dir (one-time).")
