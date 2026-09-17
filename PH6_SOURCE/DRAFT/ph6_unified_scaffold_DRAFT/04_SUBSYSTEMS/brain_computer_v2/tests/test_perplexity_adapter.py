import unittest
from brain_computer_v2.brain_computer_v2 import BrainComputerV2
from brain_computer_v2.perplexity_adapter import PerplexityAdapter

FAKE_RESPONSE = {
    "id": "resp_test_001",
    "model": "sonar",
    "choices": [
        {
            "message": {
                "content": "Neo4j bulk import is intended for large initial graph loads.",
                "citations": [
                    "https://neo4j.com/docs/operations-manual/current/import/"
                ]
            }
        }
    ]
}

class PerplexityAdapterTests(unittest.TestCase):
    def test_ingest_chat_response_creates_output_metadata_and_citation_nodes(self):
        brain = BrainComputerV2()
        adapter = PerplexityAdapter(brain, api_key='pplx-test-key')
        result = adapter.ingest_chat_response(
            prompt='Test prompt',
            response=FAKE_RESPONSE,
            retrieval_tags=['test']
        )
        self.assertEqual(result['citation_count'], 1)
        self.assertTrue(any(n['classification'] == 'OUTPUT' for n in brain.nodes))
        self.assertTrue(any(n['classification'] == 'CONTEXT' and 'raw_response' in n['content'] for n in brain.nodes))
        self.assertTrue(any(e['relation'] == 'REFERENCES' for e in brain.edges))
        self.assertTrue(any(l['event'] == 'PERPLEXITY_RESPONSE_INGESTED' for l in brain.ledger))

if __name__ == '__main__':
    unittest.main()
