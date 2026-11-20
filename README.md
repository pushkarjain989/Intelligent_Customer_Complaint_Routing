# 🎯 AutoRoute AI: Intelligent Customer Complaint Routing & Automated Response System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.0+-61DAFB.svg)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-8.0+-646CFF.svg)](https://vitejs.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An end-to-end AI-powered customer complaint classification, sentiment analysis, routing, and automated resolution system. AutoRoute AI processes incoming customer tickets across multiple channels, automatically categorizes them, detects urgency & sentiment, assigns them to appropriate department queues, and generates context-aware, empathetic auto-responses.

---

## 🌟 Key Features

- **Automated NLP Classification**: Semantic intent routing using `Sentence-Transformers` (`all-MiniLM-L6-v2`) and keyword TF-IDF/embeddings.
- **Sentiment & Urgency Scoring**: Real-time sentiment polarity detection using VADER & rule-based escalation scoring.
- **Intelligent Response Generation**: Generates customized, empathetic email/chat templates addressing specific customer pain points.
- **Multi-Domain Pretrained Datasets**: Includes test datasets for Banking & Fintech, E-Commerce, Telecom/ISP, and Airlines.
- **Interactive Web Dashboard**: Modern React 19 + Vite dashboard featuring queue management, priority badges, analytics, and instant testing.
- **Production-Ready FastAPI Server**: Fast asynchronous REST API with automatic Swagger UI (`/docs`) and ReDoc (`/redoc`).

---

## 🏗️ Architecture

```
                                  Incoming Customer Complaint
                                              │
                                              ▼
                             ┌─────────────────────────────────┐
                             │    NLP Processing Pipeline      │
                             │  - Cleaning & Normalization     │
                             │  - Sentence Embeddings          │
                             │  - VADER Sentiment Analysis     │
                             │  - Urgency & Severity Score     │
                             └────────────────┬────────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
         ┌──────────────────────────┐                   ┌───────────────────────────┐
         │     Smart Routing        │                   │    AI Auto-Responder      │
         │  - Department Assignment │                   │  - Context-Aware Replies  │
         │  - Priority Level        │                   │  - Dynamic Placeholders   │
         │  - SLA & Escalation Tag  │                   │  - Empathy Tone Matching  │
         └────────────┬─────────────┘                   └─────────────┬─────────────┘
                      │                                               │
                      └───────────────────────┬───────────────────────┘
                                              ▼
                             ┌─────────────────────────────────┐
                             │ React 19 Web Dashboard & API    │
                             │  - Live Ticket Management       │
                             │  - Batch CSV Ingestion & Sim    │
                             │  - Analytics & Reports          │
                             └─────────────────────────────────┘
```

---

## 📁 Repository Structure

```
.
├── backend/
│   ├── main.py                 # FastAPI application server and routes
│   ├── nlp_pipeline.py         # NLP classification, sentiment analysis & routing
│   ├── schemas.py              # Pydantic data schemas
│   ├── templates.py            # AI automated response templates
│   ├── data/                   # Prepackaged test and sample datasets
│   └── model_store/            # Serialized pipeline state & artifacts
├── frontend/
│   ├── src/                    # React UI components, views, and styles
│   ├── package.json            # Node dependencies and scripts
│   └── vite.config.js          # Vite build configuration
├── test_datasets/              # Specialized domain CSV test files
├── archive (3)/                # Baseline Twitter/Customer dataset
├── create_test_datasets.py     # Script to generate synthetic benchmark data
├── test_pipeline.py            # Unit tests for the NLP pipeline
├── test_system_e2e.py          # End-to-end integration tests
├── requirements.txt            # Python dependencies
└── run.py                      # One-click startup script
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10 or higher
- Node.js 18+ & npm (for frontend customization, or run pre-bundled)
- Git

### 2. Clone the Repository
```bash
git clone https://github.com/pushkarjain989/Intelligent_Customer_Complaint_Routing.git
cd Intelligent_Customer_Complaint_Routing
```

### 3. Backend Setup
Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

Install backend dependencies:
```bash
pip install -r requirements.txt
```

### 4. Frontend Setup (Optional for Development)
```bash
cd frontend
npm install
npm run build
cd ..
```

### 5. Launch the System
Run the unified entrypoint:
```bash
python run.py
```

Access the application:
- 🌐 **Web Dashboard**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- 📖 **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 📑 **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🧪 Testing

Run unit and integration tests:
```bash
# Test the NLP Pipeline
python test_pipeline.py

# Run End-to-End System Tests
python test_system_e2e.py
```

---

## 📊 Datasets Note

To keep the repository lightweight and adhere to GitHub's file limits, large raw CSV datasets (>100MB) are excluded via `.gitignore`. Sample benchmark datasets for multiple industries (Fintech, Telecom, E-commerce, Aviation) are included under `test_datasets/` and `backend/data/`.

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
