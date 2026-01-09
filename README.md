# Semantic File Search

A local semantic search engine that finds files based on meaning, not just keywords.

## What is this?

Search your files using natural language. Instead of exact keyword matching, this tool understands what you're looking for.

## Installation

Requires Python 3.13+

```bash
# Clone the repo
git clone https://codeberg.org/yourusername/semantic-file-search.git
cd semantic-file-search

# Install uv (if you don't have it)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# For development (includes pytest, safety, bandit)
uv sync --extra dev
```
## License

See [LICENSE](LICENSE) file.
