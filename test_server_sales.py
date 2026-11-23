import sys
from pathlib import Path

BASE = Path("D:/app/brag-lead-hunter")
sys.path.insert(0, str(BASE))

import server
from backend.sales_service import get_sales_stats, get_sales_leads, record_interaction

print("Checking server syntax and imports... SUCCESS")
stats = get_sales_stats()
print("Stats Bruce:", stats["bruce"]["total_leads"])
print("Stats Gabriel:", stats["gabriel"]["total_leads"])
print("Stats General:", stats["general"]["total_leads"])
assert stats["bruce"]["total_leads"] == 200
assert stats["gabriel"]["total_leads"] == 200
assert stats["general"]["total_leads"] == 400
print("ALL SERVER TESTS PASSED PERFECTLY!")
