from .brain_computer_v2 import BrainComputerV2

def export_neo4j_csv(state_path, nodes_path, relationships_path):
    brain = BrainComputerV2(state=state_path)
    return brain.export_neo4j(nodes_path, relationships_path)
