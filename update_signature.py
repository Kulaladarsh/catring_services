import sys
sys.path.append('.')
from backend.db import dishes_collection

# Mark all dishes as signaturez
result = dishes_collection.update_many(
    {},
    {'$set': {'is_signature': True}}
)
print(f'Marked {result.modified_count} dishes as signature')
