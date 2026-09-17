export interface BrainNodeV2 {
  id: string;
  type: string;
  label: string;
  classification: string;
  content: string;
  sequence: number;
  created_at: string;
  active: boolean;
  retrieval_tags: string[];
}

export interface BrainEdgeV2 {
  from: string;
  to: string;
  relation: string;
}

export interface LedgerEventV2 {
  event: string;
  target: string;
  reason: string;
  timestamp?: string;
}
