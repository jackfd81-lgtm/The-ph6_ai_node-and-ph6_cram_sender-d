# PH6 Authority Mode Hierarchy

**Schema:** ph6.governance.authority_mode_hierarchy.v1  
**Status:** PROPOSED — prototype-ready governance  
**Proposed by:** claude-code-lane2 | **Ratified by:** null  
**AI contribution:** `{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-06-06T00:00:00Z","ratified_by":null}`

---

## 1. Authority Level Table

| Level | Name | Description |
|-------|------|-------------|
| 0 | Reality | Physical world; what actually happened |
| 1 | Legal / Courtroom Authority | Court of law; evidentiary rules (FRE 702, chain of custody) |
| 2 | Scientific Discipline Authority | Validated scientific method; peer review; publication standards |
| 2A | Experimental Authority | Active experiment inside scientific mode; may revise under scientific rules |
| 3 | PSEUDO Deterministic Authority | PH6 deterministic measurement gate; PASS / DROP only |
| 4 | CRAM Evidence Memory Authority | PH6 preserved evidence packets and audit chain |
| 5 | SoSo Continuity / Advisory Sub-Authority | Continuity mapping, drift tracking, context advisory |
| 6 | Tokens / Virtual Tokens / Topology | Lineage, versioning, topology, reference structures |
| 7 | AI Learning / Explanation Layer | Advisory interpretation; explanation only; Authority ZERO |

Higher level number = lower authority. Level 0 is ultimate. Level 7 is advisory only.

---

## 2. Mode Definitions

### LEGAL Mode

```
Trigger:    Litigation, law enforcement, court proceedings, formal legal review
Governs:    Chain of custody, operator identity, method validation,
            evidence admissibility, FRE 702 compliance
Override:   Overrides all other modes
Constraint: Evidence must be traceable to CRAM chain and PSEUDO verdicts
```

### SCIENTIFIC Mode

```
Trigger:    Published method, calibrated instrument, ISO/IEC 17025 context
Governs:    Method validation, calibration records, uncertainty quantification,
            reproducibility, error rate documentation
Override:   Overrides Experimental and Theoretical modes
Constraint: Method must be documented; results must be reproducible;
            uncertainty must be declared
```

### EXPERIMENTAL Authority (sub-mode of Scientific)

```
Trigger:    Active prototype, R&D, unvalidated method under investigation
Governs:    Prototype development, exploratory measurement, design iteration
Override:   May revise methods under Scientific Mode rules
Constraint: Results are preliminary; must not be presented as validated
            without completing Scientific Mode validation cycle
```

### THEORETICAL Mode

```
Trigger:    Modeling, simulation, AI advisory, posit generation
Governs:    Hypotheses, predictions, AI explanations, posit records
Override:   May NOT override Legal, Scientific, Experimental, CRAM, or PSEUDO
Constraint: Theory must be labeled; may not enter evidence chain without
            PSEUDO validation or operator ratification
```

---

## 3. Override Rules

```
Legal Mode is highest.
Scientific Mode governs validated method, calibration, reproducibility, uncertainty.
Experimental Authority exists inside Scientific Mode.
Theoretical Mode is lowest and may never override Legal, Scientific,
  Experimental, CRAM, or PSEUDO authority.
CRAM is the evidence memory authority.
PSEUDO is the deterministic decision authority.
SoSo is advisory continuity sub-authority only.
Tokens are lineage/topology/reference structures, not primary authority.
AI is advisory learner/interpreter only.
```

---

## 4. Mode Interaction Table

| Source Mode | May Override | May Not Override |
|-------------|-------------|-----------------|
| Legal | All | — |
| Scientific | Experimental, Theoretical | Legal |
| Experimental | Theoretical | Legal, Scientific |
| Theoretical | — | Legal, Scientific, Experimental, CRAM, PSEUDO |
| PSEUDO (L3) | Tokens, AI | CRAM, Legal, Scientific |
| CRAM (L4) | Tokens, AI | PSEUDO verdicts, Legal, Scientific |
| SoSo (L5) | Tokens, AI | PSEUDO, CRAM, Legal, Scientific |
| AI (L7) | Its own prior explanations | Everything else |

---

## 5. Non-Negotiable Rules

```
1. AI output is always Level 7 (advisory) regardless of confidence.
2. AI may not promote its own output to CRAM evidence.
3. AI may not issue PASS or DROP verdicts.
4. SoSo advisory may disagree with PSEUDO — PSEUDO remains controlling.
5. Theoretical posits must not enter the evidence chain without PSEUDO validation.
6. Legal Mode cannot be waived by operator; it activates when proceedings begin.
7. Experimental results presented as final evidence require Scientific Mode
   validation first.
```

---

## 6. Authority in Practice

### Example: AI suggests DROP on a frame

```
AI produces advisory output suggesting a frame should be DROP.
→ Level 7 (Theoretical).
→ Cannot override PSEUDO Level 3 verdict.
→ If PSEUDO has already issued PASS, PSEUDO verdict stands.
→ DISSENT_TOKEN created.
→ Operator review required.
→ AI suggestion remains in record as advisory annotation only.
```

### Example: SoSo continuity map disagrees with PSEUDO gate

```
SoSo (Level 5) maps a drift that suggests prior PSEUDO gate was too lenient.
→ SoSo is advisory sub-authority.
→ PSEUDO verdict is not revised retroactively.
→ DISSENT_TOKEN created.
→ Future PSEUDO gate may be updated by operator based on SoSo input.
→ Past verdicts remain unchanged.
```

### Example: Operator in Legal Mode

```
Legal proceedings begin.
→ Legal Mode activates.
→ Chain of custody check required.
→ All AI advisory outputs labeled explicitly as secondary advisory.
→ PSEUDO verdict + CRAM chain are the primary evidence candidates.
→ Courtroom Readiness matrix reviewed.
```

---

*Lane-2 advisory document. No authority changes. Operator ratification required.*
