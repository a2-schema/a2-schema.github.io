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

### Versioning & URLs

Each artifact is **immutable per version** and served at a URL whose path mirrors its
`$id`, so every `$id`/`$ref` resolves directly:

- Vault: `https://a2-schema.org/vault/v0.0.9/schema.json`
- Profile: `https://a2-schema.org/profiles/<name>/<ver>/schema.json`
- Tier config: `https://a2-schema.org/tier-configs/<tier>/<ver>/config.json` (a build manifest, **not** an instance schema; described by the [tier-config meta-schema](tier-config/v0.1.0/schema.json))
- **`latest` alias** (e.g. `…/vault/latest/schema.json`) mirrors the newest version for humans/tools; profiles and tiers always pin an **exact** version in their `$ref`s.

## Schemas

| Type | Schema | Version | Role |
|---|---|---|---|
| **SSoT** | [Grand Vault](vault/v0.0.9/schema.json) | v0.0.9 | All def definitions (§1–§10): Common, HashChain, AI Audit, Signature, Biometric, SigningCeremony, Document, Contract, **Compliance** |
| Profile | [Signature](profiles/signature/v0.0.2/schema.json) | v0.0.2 | Signature use cases (ML-DSA, RSA, JAdES, Handwritten ISO 19794-7) |
| Profile | [Contract](profiles/contract/v0.1.8/schema.json) | v0.1.8 | Legal contracts (US ESIGN, JP 電子署名法, EU eIDAS) |
| Profile | [Compliance](profiles/compliance/v0.0.1/schema.json) | v0.0.1 | **NEW** — Compliance aggregator (GDPR, EU AI Act, SOC 2, ISO 27001, …) |

> Prior versions ([Grand Vault v0.0.8](vault/v0.0.8/schema.json), [Signature v0.0.1](profiles/signature/v0.0.1/schema.json), [Contract v0.1.7](profiles/contract/v0.1.7/schema.json)) remain published for `$ref` stability. v0.0.9 is **purely additive** over v0.0.8.

## Tier Configurations (App Profiles)

| Tier | Version | Use Case |
|---|---|---|
| [a2-sign](tier-configs/a2-sign/v0.0.2/config.json) | v0.0.2 | Electronic signature application |
| [a2-doc](tier-configs/a2-doc/v0.0.4/config.json) | v0.0.4 | General document processing |
| [a2-compliance](tier-configs/a2-compliance/v0.0.1/config.json) | v0.0.1 | **NEW** — Compliance management (automated evidence, audit trail) |

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
