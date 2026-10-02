# Backend Flow :

backend/
├── app/
│ ├── main.py
│ ├── core/
│ │ ├── config.py # pydantic Settings
│ │ ├── security.py # JWT, password hashing
│ │ ├── deps.py # get_current_user, get_db
│ │ └── logging.py
│ ├── api/
│ │ ├── v1/
│ │ │ ├── auth.py # POST /auth/register, /login
│ │ │ ├── documents.py # POST /documents, GET /documents/{id}
│ │ │ ├── jobs.py # GET /jobs/{id}, GET /jobs/{id}/stream (SSE)
│ │ │ ├── query.py # POST /documents/{id}/query
│ │ │ └── feedback.py
│ ├── models/ # SQLAlchemy ORM
│ ├── schemas/ # Pydantic v2
│ ├── services/
│ │ ├── storage.py # S3 client wrapper
│ │ ├── parser.py # PDF/DOCX → text + page map
│ │ ├── chunker.py # semantic + page-aware
│ │ ├── embedder.py # Gemini text-embedding-004
│ │ ├── vector_store.py # Qdrant client
│ │ ├── retriever.py # hybrid (dense + BM25) + RRF
│ │ ├── reranker.py # cross-encoder or Gemini rerank
│ │ ├── llm.py # Gemini wrapper w/ retry + schema
│ │ ├── validator.py # citation check + refusal enforcement
│ │ └── trust.py # trust score computation
│ ├── workers/
│ │ ├── celery_app.py
│ │ ├── ingest_tasks.py
│ │ ├── query_tasks.py
│ │ └── outbox_publisher.py
│ └── prompts/
│ ├── system_qa.txt
│ ├── system_contract.txt
│ └── system_finance.txt
├── alembic/
├── tests/
└── Dockerfile

# Frontend Flow :

frontend/
├── app/
│ ├── (auth)/login/page.tsx
│ ├── (auth)/register/page.tsx
│ ├── dashboard/page.tsx # document list
│ ├── doc/[id]/page.tsx # 3-panel viewer
│ └── layout.tsx
├── components/
│ ├── upload/DropZone.tsx
│ ├── upload/ProgressStream.tsx # SSE consumer
│ ├── viewer/DocPanel.tsx # PDF.js or react-pdf
│ ├── viewer/PageThumbnails.tsx
│ ├── viewer/HighlightLayer.tsx # highlights cited ranges
│ ├── chat/QueryInput.tsx
│ ├── chat/AnswerCard.tsx # answer + citations + trust bar
│ ├── chat/CitationChip.tsx # click → scroll+highlight
│ └── ui/\*
├── lib/
│ ├── api.ts # typed fetch wrapper
│ ├── sse.ts # EventSource helper
│ └── store.ts # zustand: current doc, highlights
└── middleware.ts # auth guard

# Key Interactions

┌──────────────┬────────────────────────┬──────────────────────┐
│ Thumbnails │ PDF / text viewer │ Q&A panel │
│ (page list) │ with highlight layer │ ┌──────────────┐ │
│ │ │ │ AnswerCard │ │
│ ● p.1 │ ┌─────────────────┐ │ │ [1] p.4 │ │
│ ● p.2 │ │ ...contract... │ │ │ [2] p.7 │ │
│ ● p.3 ◄─────┼───┤ highlighted │ │ │ trust ▓▓▓░ │ │
│ │ └─────────────────┘ │ └──────────────┘ │
│ │ │ [Ask a question…] │
└──────────────┴────────────────────────┴──────────────────────┘
