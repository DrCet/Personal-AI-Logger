# 🚀 Personal AI Logger (Free & Open-Source)

A system to log conversations, thoughts, and coding patterns for future AI training.  
Built entirely with **free, open-source tools**.

## 📌 Tech Stack (All Free & Open-Source)

| Component        | Tool Used            | Why? |
|-----------------|----------------------|------|
| **Backend**     | FastAPI (Python)      | Free, lightweight, async support |
| **Speech-to-Text** | OpenAI Whisper (Local) | Runs locally, no API cost |
| **Database**    | PostgreSQL + SQLite   | Open-source, scalable |
| **Vector Storage** | ChromaDB            | Free local storage for embeddings |
| **Hosting**     | Local / Fly.io / Railway.app | Free tiers available |
| **Deployment**  | GitHub Actions + Docker | Free CI/CD setup |

---

## ⚡ Workflow 

1️⃣ **User Logs Data**  
   - **Text Input** → Sent via FastAPI  
   - **Audio Input** → Transcribed using **local Whisper model**  

2️⃣ **Processing & Storage**  
   - **Text logs** → Stored in **PostgreSQL/SQLite**  
   - **Vectorized logs** → Stored in **ChromaDB**  

3️⃣ **Search & Retrieval**  
   - **Keyword search** → PostgreSQL query  
   - **Semantic search** → ChromaDB’s vector search  

4️⃣ **Access & Deployment**  
   - **FastAPI runs locally or on free hosting**  
   - **Data stored locally or in a free PostgreSQL cloud instance**  

---

Remember to activate venv and install all dependencies
Remember to install vosk model and unzip it in vosk_model directory