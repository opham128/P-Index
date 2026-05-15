import sys
import json
from api.framework.api import wos_search

data = wos_search("AU=(\"Michel Tuan Pham\")", limit=1)
print(json.dumps(data, indent=2))
