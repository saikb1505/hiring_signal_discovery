# Job Search Query Formatter API

A FastAPI application that converts natural language job search queries into optimized Google search queries using OpenAI.

## Example

**Input:**
```
Senior software engineer in Hyderabad last 1 week
```

**Output:**
```json
{
  "query_string": "('senior software engineer' OR 'senior developer' OR 'senior sde') after:2025-12-18 before:2025-12-25",
  "locations": ["Hyderabad", "Bangalore"],
  "duration": {
    "from": "18/12/2025",
    "to": "25/12/2025"
  }
}
```

## Setup

1. Clone and install dependencies:
```bash
git clone <repository-url>
cd hsd
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

3. Run the server:
```bash
# Development mode with auto-reload
python main.py

# Or use uvicorn directly
uvicorn main:app --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### POST /format-query

Format a natural language job search query.

```bash
curl -X POST "http://localhost:8000/format-query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Senior software engineer in Hyderabad with Ruby on rails"}'
```

### GET /health

Health check endpoint.

### GET /

API information and available endpoints.

## Interactive Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration

Environment variables (see [.env.example](.env.example)):

- `OPENAI_API_KEY` - OpenAI API key (required)
- `OPENAI_MODEL` - Model to use (default: gpt-4o-mini)
- `ENVIRONMENT` - development or production
- `LOG_LEVEL` - Logging level (default: INFO)
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8000)

## Testing

```bash
pytest
pytest --cov=app
```

## Project Structure

```
hsd/
├── app/
│   ├── api/              # API routes and handlers
│   ├── core/             # Configuration and logging
│   ├── models/           # Pydantic schemas
│   └── services/         # Business logic (OpenAI integration)
├── tests/                # Test suite
├── main.py               # Application entry point
└── requirements.txt      # Dependencies
```

## License

MIT
