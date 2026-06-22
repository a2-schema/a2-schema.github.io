# a2-schema.github.io

**AI Auditable JSON Schema for the Trust Era**

🌐 [a2-schema.org](https://a2-schema.org) | 📜 [Apache 2.0](LICENSE)

---

## What is a2-schema?

**a2-schema** is a JSON Schema framework designed for **AI auditability** in the post-quantum, regulated AI era.

The **"a2"** stands for **AI Auditable** — every data node, transition, and AI decision is cryptographically verifiable, tamper-evident, and ready for regulatory audit (EU AI Act, NIST AI RMF, etc.).

---

## Why a2-schema?

Modern AI systems generate decisions, contracts, and records that must be:

- ✅ **Verifiable** — Who created this? When? With what AI?
- ✅ **Tamper-evident** — Has it been altered since creation?
- ✅ **Quantum-resistant** — Will it remain trustworthy in 20+ years?
- ✅ **AI-auditable** — Can regulators audit every AI action?

a2-schema makes all of this possible through a unified structured data standard.

---

## Core Features

### 🔗 3-Tier HashChain
- Document-level chain (overall history)
- Entity-level chain (per-clause, per-record)
- Log-level chain (granular events, AI actions)

### ✍️ Multi-Algorithm Signatures
- **ML-DSA-65** (FIPS 204) — quantum-resistant
- **RSA-3072** — current legal compatibility
- **ECDSA P-256** — DPoP / token binding

### 🤖 AI Action Logging
- Every AI decision recorded with `$signature`
- Human override tracking
- Failure reason attribution
- EU AI Act compliance built-in

### 🏛️ Regulatory Ready
- IAL3 / AAL3 / FAL3 (NIST SP 800-63-3)
- eIDAS QES compatible
- Japanese 電子署名法 / 電子帳簿保存法

---

## Architecture (SSoT)

a2-schema follows a **Single Source of Truth** architecture — every def is defined
exactly once, in the Grand Vault. Everything else references it.

```
Grand Vault (SSoT)        all def definitions (§1–§10)
   ↓ $ref only
Profiles                  Signature, Contract, Compliance, … (pure $ref aggregators)
   ↓ aggregate
Tier Configs              a2-sign, a2-doc, a2-compliance, … (per-App def selection)
   ↓ filter
Applications              a2-Sign App, a2-Doc App, a2-Compliance App, …
```

Dependency is strictly one-way (Profiles/Tiers → Grand Vault); the Vault references
nothing outside itself (only **local** `#/$defs` refs). New document types are added by
extending a Vault section and adding a profile — never by duplicating defs.

### Versioning & URLs (convention for all future schemas)

Each published artifact is **immutable per version** and served at a URL whose path **mirrors its
`$id`**, so every `$id`/`$ref` resolves directly at the domain root:

- **Vault**: `https://a2-schema.org/vault/v<MAJOR.MINOR.PATCH>/schema.json`
- **Profile**: `https://a2-schema.org/profiles/<name>/v<ver>/schema.json`
- **`latest` alias** (e.g. `…/vault/latest/schema.json`) is a byte-copy of the newest version for
  humans/tools; its internal `$id` still names the real version. Profiles always pin an **exact**
  version in their `$ref`s — never `latest`.

**Rules (full spec: dx-platform `docs/schema-architecture.md` §8):**
- File path == `$id` path (no `/schemas/` prefix; ends in `schema.json`). Version in the **path**.
- **Immutable**: never change a published version's bytes — ship a new version. PATCH = additive/
  back-compat; MAJOR = breaking. A generated/derived schema gets its **own** `$id`, never the vault's.
- **Public surface = Grand Vault + profiles only.** **Tier configs, modules, generated tiered schemas
  and `$formDesign` are NOT published** — they are internal build inputs/outputs (tier configs also
  carry app-specific UI/look metadata). The deployable per-doctype schema is generated and embedded in
  apps, not exposed as a public `$id`.

## Schemas

| Type | Schema | Version | Role |
|---|---|---|---|
| **SSoT** | [Grand Vault](vault/v0.0.12/schema.json) | v0.0.12 | **Lean** SSoT of shared/universal types (Common, HashChain, AI Audit, OperationLog, **Signature (multi-party `$signatures`)**, Biometric, SigningCeremony, Contract primitives, ConsentReceipt, ComplianceFrameworkEnum). Domain defs live in profiles. |
| Profile | [Signature](profiles/signature/v0.0.3/schema.json) | v0.0.3 | Signature use cases (ML-DSA, RSA, JAdES, Handwritten ISO 19794-7) — pure aggregator |
| Profile | [Contract](profiles/contract/v0.1.9/schema.json) | v0.1.9 | Legal contracts (US ESIGN, JP 電子署名法, EU eIDAS) — pure aggregator |
| Profile | [Compliance](profiles/compliance/v0.0.2/schema.json) | v0.0.2 | Compliance (GDPR, EU AI Act, SOC 2, ISO 27001, …) — **body-owning** (owns §10 entity defs; GV-lean) |
| Profile | [Delegation](profiles/delegation/v0.0.2/schema.json) | v0.0.2 | Power-of-attorney / delegation — **body-owning** |

> **v0.0.12 (patch over v0.0.11):** the **A2Envelope** DOCUMENT signature slot is now **`$signatures`**
> (array of `BlockSignature`) for **multi-party signing** (甲乙…) — every party signs the same canonical
> body (the array is excluded from the payload), single-signer = length 1; `BlockSignature` gains an
> optional informative `signer` (email / party / identityAssurance / signedAt). The **per-block**
> single-author `$signature` on every other def is **unchanged**. Profiles stay pinned to GV **v0.0.10**.
> **v0.0.11 (additive over v0.0.10):** + `OperationLog` — the universal per-operation audit record
> (actor + IAL/AAL/FAL + result, signable/hash-chained; `operation` is a free string).
> **v0.0.10 = GV-lean:** compliance §10 entity defs moved OUT of GV into the body-owning compliance
> profile; only shared `ConsentReceipt` + `ComplianceFrameworkEnum` remain in GV (GV 135→128 defs).
> Prior versions (GV [v0.0.8](vault/v0.0.8/schema.json)/[v0.0.9](vault/v0.0.9/schema.json)/[v0.0.10](vault/v0.0.10/schema.json)/[v0.0.11](vault/v0.0.11/schema.json), signature v0.0.1–2, contract v0.1.7–8, compliance v0.0.1, delegation v0.0.1) remain for `$ref` stability.

## Tier configs — not published

Per-app **tier configs** (a2-sign, a2-doc, a2-compliance, …) are **internal build manifests**, not
part of this public registry. They select GV defs per app/doctype and also carry app-specific UI/look
metadata (the seed for the document `$formDesign`), which is not public vocabulary. The deployable
per-doctype schema is *generated* from a tier (self-contained, its own `$id`) and embedded in the
consuming app — it is not exposed here. Tier sources live in the private dx-platform repo
(`xml/ichiriXML/tier_configs/`). See dx-platform `docs/schema-architecture.md` §5, §8.

## Compliance Frameworks Supported (§10)

SOC 2 Type II · ISO 27001 / 27017 / 27018 · GDPR / CCPA / 個人情報保護法 · EU AI Act ·
NIST AI RMF / 800-53 / CSF · HIPAA / PCI DSS · FedRAMP / FISC / 3省2ガイドライン ·
ESG / TCFD / CSDDD / NIS2 · 電子帳簿保存法 / インボイス制度

§10 defs: `ConsentReceipt` (Kantara Consent Receipt v1.1) · `ComplianceLog` ·
`DataSubjectRequest` (GDPR Art 15-22 / RTBF) · `IncidentReport` (NIS2 24h / GDPR 72h) ·
`AccessControlEvent` (SOC 2 CC6 / ISO 27001 A.9) · `PIIDetection` · `DataLineage` ·
`GovernanceAttestation` (ESG/TCFD/CSDDD). §3 `AIAction` gains EU-AI-Act
`riskLevel` / `explainability` / `humanOversight` / `dataLineage`.

### Scalability

The design supports **2500+ document types** through Vault section expansion (§1–§50+),
profile-based composition (no duplication), and tier-config filtering (App-specific).
More modules coming: Healthcare, Robotics, Life, KnowledgeOS.

---

## Quick Example

```json
{
  "$tag": "Contract",
  "id": "doc_abc123",
  "$signature": {
    "algorithm": "ML-DSA-65",
    "value": "base64...",
    "keyId": "..."
  },
  "$hashChain": {
    "current": "sha256:...",
    "previous": "sha256:...",
    "level": "document"
  },
  "clauses": [
    {
      "$tag": "Clause",
      "$signature": { ... },
      "$hashChain": { ... },
      "auditLog": [
        {
          "$tag": "AIAction",
          "actor": "ai-agent-v2.3",
          "action": "review",
          "humanOverride": false,
          "$signature": { ... }
        }
      ]
    }
  ]
}
```

→ **Every node is independently signed and chained**

---

## Use Cases

| Industry | Application |
|---|---|
| 📝 Legal | Contracts, delegations, e-signatures |
| 🏥 Healthcare | EHR audit, AI diagnosis tracking |
| 🤖 Robotics | Robot action attestation |
| 🏦 Finance | KYC/AML trails, transaction proofs |
| 🌐 AI Agents | Inter-agent commerce, delegation |

---

## Roadmap

- [x] Grand Vault SSoT v0.0.8 (§1–§9)
- [x] Grand Vault SSoT v0.0.9 (§1–§10, +Compliance — 120 defs)
- [x] Signature Profile v0.0.2 (incl. Handwritten ISO 19794-7)
- [x] Contract Profile v0.1.8
- [x] Compliance Profile v0.0.1 (GDPR / EU AI Act / SOC 2 / ISO 27001 / HIPAA / PCI DSS)
- [x] Tier Configs: a2-sign, a2-doc, a2-compliance
- [ ] Healthcare Module
- [ ] AI Agent Module
- [ ] SDK (TypeScript, Rust, Python)
- [ ] Validator with Lisp-based rule engine
- [ ] W3C / IETF standardization proposal

---

## License

Licensed under the **Apache License 2.0** — see [LICENSE](LICENSE)

---

## Contributing

a2-schema is an open initiative. Issues, discussions, and PRs welcome.

---

## Citation

```
a2-schema: AI Auditable JSON Schema
Ichiri / a2-schema project, 2026
https://a2-schema.org
```

---

**Powered by trust. Auditable by design. Quantum-ready by default.**
