# PH6 Standards Crosswalk

**Schema:** ph6.governance.standards_crosswalk.v1  
**Proposed by:** claude-code-lane2 | **Ratified by:** null  
**Authority:** ZERO — advisory alignment document only  

PH6 is not claiming conformance to any of the standards listed below. This crosswalk maps PH6 internal concepts to professional equivalents to support communication, future audit readiness, and external review.

---

## Concept Mapping

| PH6 Concept | Professional Equivalent | Standard Reference |
|-------------|------------------------|-------------------|
| CRAM | Evidence preservation container / forensic acquisition image | NIST SP 800-86, SWGDE |
| Canon hash (BLAKE2b-256) | Integrity digest / cryptographic evidence seal | NIST SP 800-86, SP 800-101 Rev. 1 |
| PSEUDO deterministic measurement | Validated measurement method / deterministic test procedure | ISO/IEC 17025, NIST AI RMF 1.0 |
| SoSo / Lane-2 advisory | Expert advisory / non-authoritative analysis layer | NIST AI RMF 1.0, FRE 702 |
| Token topology (RT/VDT/VLT/AVLT) | Evidence metadata / acquisition environment log | NIST SP 800-86, SWGDE |
| Governance drift scan | Policy/configuration compliance check | NIST SP 800-53 Rev. 5, SP 800-218 SSDF |
| Replay MATCH | Reproducibility check / hash verification | ISO/IEC 17025, NIST SP 800-86 |
| Restore point | Change-control rollback / configuration baseline | NIST SP 800-53 Rev. 5 CM, SP 800-218 SSDF |
| Test registry | Controlled method catalog / SOP index | ISO/IEC 17025 |
| PH6 Desktop cockpit | Operator interface — not authority engine | NIST AI RMF 1.0, CISA Secure by Design |
| CRAM-A (PASS store) | Write-once forensic archive | NIST SP 800-86, SWGDE |
| Audit event chain (audit.jsonl) | Tamper-evident chain-of-custody log | NIST SP 800-53 Rev. 5 AU |

---

## Referenced Standards

### NIST SP 800-86
*Guide to Integrating Forensic Techniques into Incident Response*  
Forensic evidence lifecycle: preparation → collection/acquisition → examination → analysis → reporting. PH6 CRAM, hash chains, and chain-of-custody logs should be interpretable in these terms.

### NIST SP 800-101 Rev. 1
*Guidelines on Mobile Device Forensics*  
Validation, preservation, acquisition, examination, analysis, and reporting of digital information. PH6 sensor evidence packets should mirror this structure.

### SWGDE Best Practices for Digital Evidence Collection
Maintaining digital evidence integrity during collection. PH6's hash-authenticated write paths, .blake2b markers, and atomic write contract are the implementation of this principle.

### ISO/IEC 17025
*General requirements for the competence of testing and calibration laboratories*  
Validated methods, calibration records, uncertainty statements, reproducibility. PH6 is not an accredited lab, but the architecture should support future validation evidence in these terms.

### NIST AI RMF 1.0
*Artificial Intelligence Risk Management Framework*  
Trustworthy AI: valid, reliable, safe, secure, accountable, transparent, explainable. PH6's Lane-2 advisory boundary and explicit authority labeling implement the explainability and accountability requirements. Advisory output must be distinguishable from deterministic measurement.

### NIST SP 800-218 (SSDF)
*Secure Software Development Framework Version 1.1*  
Secure development: version control, review, reproducible builds, dependency records, vulnerability tracking, change approval. PH6 governance scan and commit gate are implementations of this.

### NIST SP 800-53 Rev. 5
*Security and Privacy Controls for Information Systems*  
PH6 borrows: Audit and Accountability (AU), Configuration Management (CM), System Integrity (SI), Supply Chain Risk Management (SR). The governance scan, commit gate, and audit chain are direct implementations.

### Federal Rule of Evidence 702
*Testimony by Expert Witnesses*  
Expert opinion must be based on sufficient facts, reliable methods, and reliable application of those methods. For PH6 output to be FRE 702-compatible: the device must be able to explain what was measured, how it was measured, what method was used, what the error rate is, how the system was validated, and where interpretation begins. The Lane-1/Lane-2 boundary directly implements this separation.

### CISA Secure by Design
Security responsibility built into product design. Desktop authority boundary, preflight checks, and restore points are implementations of this principle at the interface layer.

---

## Storage Doctrine

**Git is the prototype source/version-control layer. It is not the final production evidence-storage authority.**

| Storage Type | Role |
|---|---|
| Internal SSD/NVMe | Local primary evidence/device storage |
| External USB SSD/NVMe | Backup, export, field evidence storage |
| Cloud storage | Remote archive, sync, disaster recovery |
| Git | Prototype source control; optional metadata/version layer |
| CRAM storage | PH6 evidence preservation layer (authority) |
| Object storage (future) | Scalable evidence/artifact backend |
| Offline archive | Courtroom/evidence retention package |

Evidence authority comes from: CRAM chain, artifact manifests, hashes, replay records, operator logs, storage manifests, and chain-of-custody records.

Git answers: *what code was running at this commit.* CRAM answers: *what was measured and preserved.*

Production PH6 must support storage backends independent of Git. Git may record metadata (script hash, git HEAD) as context, but is not a required evidence link.

---

## Alignment Gaps (Prototype Stage)

| Gap | Impact | Future Action |
|----|--------|--------------|
| No formal calibration records | Cannot claim ISO/IEC 17025 compliance | Add calibration state to method validation records |
| No operator identity chain | FRE 702 chain-of-custody weakened | Add operator ID to run manifests |
| No formal uncertainty quantification | ISO/IEC 17025 requires uncertainty statements | Define measurement uncertainty per sensor/method |
| No SBOM | Supply chain risk not formally tracked | Add Syft/Trivy later |
| No time authority (GPS/PPS) | Forensic timestamp trust limited to NTP | Add chrony or GPS later |

---

*Lane-2 advisory document. No authority changes. Operator ratification required before this is considered authoritative.*
