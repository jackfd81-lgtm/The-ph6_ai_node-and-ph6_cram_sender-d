"""
ph6_l2_expand.lmpq_proposed

Lane: 2
Authority: ZERO
Status: PROPOSED — not ratified.

New LMPQ-001 token/continuity design work (RLT, PLT, AHT, Life CRAM
"BCV2" bundles, SoSo-JEDI single-token adapter). Kept entirely separate
from ph6_l2_expand.token_types / token_policy / schemas, which remain
locked to exactly {RT, VDT, VLT} by
ph6_l2_expand/tests/test_token_classes_locked.py and
ph6_l2_expand/tests/test_soso_tokens_not_lane1.py. Nothing in this
package may be added to TOKEN_TYPES or ALLOWED_TOKEN_TYPES without a
separate, explicit operator ratification.

See PH6_SOURCE/DRAFT/PH6-LMPQ-001-PROPOSED-SPEC-v0.1.md for the design
record.
"""
