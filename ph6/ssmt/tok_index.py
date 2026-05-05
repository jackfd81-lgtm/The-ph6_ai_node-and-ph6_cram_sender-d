import json
import os
from .constants import TOK_READ_ROOT


class TOKIndex:
    def __init__(self, root: str = TOK_READ_ROOT):
        self.root = root

    def refs_for_cram(self, cram_ref: str) -> list[str]:
        refs = []

        if not os.path.isdir(self.root):
            return refs

        for name in os.listdir(self.root):
            if not name.endswith(".json"):
                continue

            path = os.path.join(self.root, name)

            try:
                with open(path, "r", encoding="utf-8") as f:
                    obj = json.load(f)

                if obj.get("cram_ref") == cram_ref:
                    refs.append(
                        f"tok://{obj.get('token_type', 'UNKNOWN')}"
                        f"/{obj.get('token_id', name)}"
                    )

            except Exception:
                continue

        return refs
