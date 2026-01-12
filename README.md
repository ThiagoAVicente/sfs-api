# Semantic File Search API (sfs-api)

A local semantic search engine that finds files based on meaning, not just keywords.

---

## Table of contents

- [What is this?](#what-is-this)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Dependencies](#dependencies)
- [How to run](#how-to-run)
  - [Automated setup](#automated-setup)
  - [Manual setup](#manual-setup)
- [Usage Examples](#usage-examples)
  - [Upload a file for indexing](#upload-a-file-for-indexing)
  - [Check indexing status](#check-indexing-status)
  - [Search files](#search-files)
  - [List all files](#list-all-files)
  - [Download a file](#download-a-file)
  - [Delete a file](#delete-a-file)
- [CPU vs GPU](#cpu-vs-gpu)
- [Project Structure](#project-structure)
- [License](#license)

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
- Caddy for reverse proxy

## Dependencies
- Docker
- Docker compose

## How to run

### Automated setup 

```bash
# this will generate all needed information and start the services
./install.sh
```

### Manual setup 

1. **Copy environment file:**
```bash
cp .env.example .env
```

2. **Generate a secure API key:**
```bash
# Generate a random API key (32 characters)
openssl rand -base64 32 | tr '+/' '-_' | tr -d '='
```

3. **Generate MinIO encryption key (for encryption at rest):**
```bash
# Generate a 32-byte key and base64 encode it
openssl rand -base64 32
```

4. **Update `.env` file with your API key, MinIO KMS key, and change the sections with `CHANGE_ME`:**
```bash
# Edit .env and replace:
API_KEY=your-generated-api-key
MINIO_ROOT_USER=your-secure-user
MINIO_ROOT_PASSWORD=your-secure-password
MINIO_KMS_SECRET_KEY=minio-kms:YOUR_BASE64_KEY_HERE
```

5. **Start the services:**
```bash
docker compose up --build
```

The API will be available at `https://localhost`
The endpoints can be accessed at `https://localhost/docs`

**Note:** All endpoints except `/health` and `/` require authentication via the `X-API-Key` header.

## Usage Examples

### Upload a file for indexing
```bash
curl -X POST "https://localhost/index" \
  -H "X-API-Key: your-api-key-here" \
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
curl "https://localhost/index/status/a1b2c3d4" \
  -H "X-API-Key: your-api-key-here"
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
curl -X POST "https://localhost/search" \
  -H "X-API-Key: your-api-key-here" \
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
curl "https://localhost/files/" \
  -H "X-API-Key: your-api-key-here"
```

### Download a file
```bash
curl "https://localhost/files/example.txt" \
  -H "X-API-Key: your-api-key-here" \
  -o downloaded.txt
```

### Delete a file
```bash
curl -X DELETE "https://localhost/index/example.txt" \
  -H "X-API-Key: your-api-key-here"
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
├── conf/             # Configs for services
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

## License

See [LICENSE](LICENSE) file.
