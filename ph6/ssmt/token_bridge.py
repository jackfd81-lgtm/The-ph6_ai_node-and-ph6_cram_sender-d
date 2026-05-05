from .constants import TOK_READ_ROOT
import os


class TokenBridge:
    """
    Read-only bridge from TOK-1.0 into SSMT.
    SSMT may consume token references.
    It may not promote tokens into evidence.
    """

    def __init__(self, root: str = TOK_READ_ROOT):
        self._root = root

    def read_token(self, tok_ref: str) -> dict:
        path = os.path.join(self._root, tok_ref.lstrip("tok://"))
        if not os.path.exists(path):
            return {"ref": tok_ref, "status": "not_found"}
        with open(path) as f:
            import json
            return json.load(f)

    def is_writable(self) -> bool:
        return False
