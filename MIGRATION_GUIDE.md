# Migration Guide: New JSON Response Format

## Overview

The application has been updated to return structured JSON responses instead of plain text query strings. This guide explains the changes and how to migrate.

## What Changed

### Before (Old Format)
```json
{
  "original_query": "Senior software engineer in Hyderabad",
  "formatted_query": "site:ashbyhq.com (\"senior software engineer\" OR \"software developer\") (Hyderabad)",
  "metadata": { ... }
}
```

### After (New Format)
```json
{
  "original_query": "Senior software engineer in Hyderabad last 1 week",
  "query_string": "(\"senior software engineer\" OR \"senior developer\" OR \"senior sde\") after:2025-12-18 before:2025-12-25",
  "locations": ["Hyderabad", "Bangalore"],
  "duration": {
    "from": "18/12/2025",
    "to": "25/12/2025"
  },
  "metadata": { ... }
}
```

## Key Changes

1. **`formatted_query` → `query_string`**: The field name has changed
2. **New `locations` field**: Array of extracted locations
3. **New `duration` field**: Object with `from` and `to` dates (DD/MM/YYYY format)
4. **Query format changed**:
   - Removed `site:ashbyhq.com` prefix
   - Added `after:YYYY-MM-DD before:YYYY-MM-DD` date filters

## Database Migration

Run the Alembic migration to add new columns:

```bash
# Apply the migration
alembic upgrade head

# To rollback if needed
alembic downgrade -1
```

The migration:
- Adds `query_string`, `locations`, `duration_from`, `duration_to` columns
- Migrates existing data from `formatted_query` to `query_string`
- Makes `formatted_query` nullable for backwards compatibility

## API Changes

### Response Schema

The `FormattedQueryResponse` now includes:

```python
class FormattedQueryResponse(BaseModel):
    original_query: str
    query_string: str              # New: replaces formatted_query
    locations: List[str]            # New: extracted locations
    duration: DurationSchema        # New: date range
    metadata: Optional[dict]
```

### Duration Schema

```python
class DurationSchema(BaseModel):
    from_date: str  # Alias: "from" - DD/MM/YYYY format
    to_date: str    # Alias: "to" - DD/MM/YYYY format
```

## Code Migration Examples

### Client Code (Before)
```python
response = requests.post("/format-query", json={"query": "..."})
query = response.json()["formatted_query"]
print(query)
```

### Client Code (After)
```python
response = requests.post("/format-query", json={"query": "..."})
data = response.json()
query_string = data["query_string"]
locations = data["locations"]
duration = data["duration"]

print(f"Query: {query_string}")
print(f"Locations: {', '.join(locations)}")
print(f"From: {duration['from']} To: {duration['to']}")
```

## Backwards Compatibility

The database migration preserves the old `formatted_query` column, so existing data remains accessible. However, the API response format has changed and clients must update to use the new structure.

## Testing

Updated tests are included in [tests/test_api.py](tests/test_api.py). Run tests to verify:

```bash
pytest tests/test_api.py -v
```

## OpenAI Prompt Changes

The system prompt now:
- Instructs the model to return JSON instead of plain text
- Parses time-based filters ("last 1 week", "last 2 days", etc.)
- Returns structured data with locations and duration
- Uses `response_format={"type": "json_object"}` for guaranteed JSON output

## Questions?

If you encounter any issues during migration, please check:
1. Database migration completed successfully
2. All required fields are present in responses
3. Client code updated to use new field names
