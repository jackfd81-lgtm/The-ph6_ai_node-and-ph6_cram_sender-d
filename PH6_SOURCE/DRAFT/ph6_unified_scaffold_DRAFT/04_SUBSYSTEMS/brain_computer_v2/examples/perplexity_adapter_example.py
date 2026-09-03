import json
from brain_computer_v2.brain_computer_v2 import BrainComputerV2
from brain_computer_v2.perplexity_adapter import PerplexityAdapter

brain = BrainComputerV2(state='output/brain_computer_v2_kernel_ingest_state_final.json')
adapter = PerplexityAdapter(brain)

# Requires PPLX_API_KEY in environment.
# result = adapter.research(
#     prompt='Summarize the latest relevant update for Neo4j bulk import performance.',
#     retrieval_tags=['neo4j', 'research']
# )
# print(json.dumps(result['ingest_result'], indent=2))

print(json.dumps({
    'status': 'adapter ready',
    'chat_url': adapter.chat_url,
    'model': adapter.model,
    'brain_status': brain.status()
}, indent=2))
