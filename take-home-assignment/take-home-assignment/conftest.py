import os
import sys

# config.py reads GFW_API_TOKEN at import time -- tests never call the
# real API, but need a value present so the import doesn't blow up.
os.environ.setdefault("GFW_API_TOKEN", "test-token-not-real")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
