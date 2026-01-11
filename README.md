# Semantic File Search API (sfs-api)

A local semantic search engine that finds files based on meaning, not just keywords.

## What is this?

Search your files using natural language. Instead of exact keyword matching, this tool understands what you're looking for.

**This is a personal learning project.** I built it to learn about:
- Vector databases and embeddings
- Object storage
- Caching

## Features

- Upload and index text files
- Semantic search using sentence transformers
- Asynchronous processing with background workers
- Rate limiting on endpoints

## Tech Stack

- Python 
- Vector search with Qdrant
- Object storage via MinIO
- Redis and arq for caching and background jobs
- Docker & Docker Compose for infrastructure

## Dependencies
- Docker
- Docker compose

## How to run

```bash
cp .env.example .env
docker compose up --build
```

The API will be available at `http://localhost:8000`
The endpoints can be accessed at `http://localhost:8000/docs`

## Usage Examples

### Upload a file for indexing
```bash
curl -X POST "http://localhost:8000/index" \
  -F "file=@/path/to/your/file.txt"
```

Response:
```json
{
  "job_id": "a1b2c3d4"
}
```

### Check indexing status
```bash
curl "http://localhost:8000/index/status/a1b2c3d4"
```

Response:
```json
{
  "job_id": "a1b2c3d4",
  "status": "complete"
}
```

### Search files
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "what is machine learning?", "limit": 5}'
```

Response:
```json
{
  "query": "what is machine learning?",
  "results": [
    {
      "score": 0.85,
      "payload": {
        "file_path": "ml_intro.txt",
        "text": "Machine learning is a subset of artificial intelligence...",
        "start": 0,
        "end": 100
      }
    }
  ],
  "count": 1
}
```

### List all files
```bash
curl "http://localhost:8000/files/"
```

### Download a file
```bash
curl "http://localhost:8000/files/example.txt" -o downloaded.txt
```

### Delete a file
```bash
curl -X DELETE "http://localhost:8000/index/example.txt"
```

## CPU vs GPU

By default, this project runs on **CPU** because I don't have a good GPU.

To use GPU instead, edit `pyproject.toml` and remove the torch CPU configuration:

```toml
### remove to use gpu version
[tool.uv]
extra-index-url = ["https://download.pytorch.org/whl/cpu"]  # <- DELETE THIS
index-strategy = "unsafe-best-match"
###
```

Then reinstall torch with CUDA support.

## Project Structure

```
src/
├── clients/          # Database and storage clients (Qdrant, Minio, Redis)
├── config/           # Configuration and settings
├── embeddings/       # Text embedding generation
├── indexer/          # File reading and chunking
├── models/           # Pydantic models for requests/responses
├── routers/          # FastAPI route handlers (upload, search, files)
├── search/           # Search logic
├── utils/            # Utility functions
└── worker/           # Background job processing (arq)
```

## Missing Features

This project is missing important security features:

- **No authentication** - Anyone can upload, search, and delete files
- **No encryption** - Files are stored in plain text
- **No input validation** beyond basic Pydantic models

## License

See [LICENSE](LICENSE) file.
