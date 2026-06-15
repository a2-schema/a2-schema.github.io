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

## Schemas

| Schema | Version | Purpose |
|---|---|---|
| [Grand Vault](schemas/a2-grand-vault-v00.00.03.json) | v0.0.3 | Foundation: Identity, AI Audit, Trust |
| [Contract Module](schemas/a2-contract-module-v00.01.00.json) | v0.1.0 | Legal contracts with full audit |

More modules coming: Healthcare, Robotics, KnowledgeOS

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

- [x] Grand Vault Schema v0.0.3
- [x] Contract Module v0.1.0
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
