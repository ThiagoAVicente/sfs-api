# Semantic File Search Engine

A high-performance **semantic search engine** that allows natural language search across local files (PDFs, text documents, notes, etc.).  
Instead of keyword matching, the system retrieves results based on **semantic similarity** using deep learning embeddings.

The backend is built in **Python** for rapid ML development, while the UI / client layer can be implemented in **C++** for performance-critical usage.

---

## 🚀 Features

- Semantic (meaning-based) search across files
- Works fully offline
- Supports natural language queries
- Fast vector similarity search
- Modular architecture (Python backend + C++ UI)
- Easily extensible to RAG / chat-with-files

---

## 🧠 How It Works

1. Files are ingested from a directory
2. Text is extracted and split into chunks
3. Each chunk is converted into a vector embedding using a deep learning model
4. Embeddings are stored in a vector index
5. User queries are embedded and matched via similarity search
6. Top matching chunks and file references are returned

---

## 🏗️ Architecture


