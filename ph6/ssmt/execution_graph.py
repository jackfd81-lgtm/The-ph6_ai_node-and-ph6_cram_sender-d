EXECUTION_GRAPH = [
    ["S4"],          # identity first
    ["S1", "S7"],    # active + intake
    ["S2", "S3"],    # context + summary
    ["S5", "S6"],    # history + latent
    ["S8"],          # drift after context
    ["S9"],          # future acquisition last
]

FORBIDDEN_EDGES = [
    ("S1", "CRAM_WRITE"),
    ("S8", "PASS"),
    ("S9", "DROP"),
]
