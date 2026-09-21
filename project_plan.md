# AI Customer Support Chatbot, Voice Agent, and Revenue Analytics Dashboard
## End-to-End Development Plan

Domain: E-commerce and Retail Customer Support

---

## 1. Project Overview

This project delivers a full-stack, production-style AI customer support platform for an e-commerce and retail business, combining a retrieval-augmented chatbot, a voice agent, and a revenue and analytics dashboard behind a single professional web application. The public-facing side is a corporate marketing website that presents the product the way a large enterprise would, with a clear login entry point into the authenticated application. The authenticated side gives support agents and business stakeholders two capabilities: a chat and voice assistant that answers customer queries using a retrieval-augmented knowledge base built from a real customer support dataset, and a dashboard that visualizes revenue, orders, customers, and support performance using a real e-commerce transactional dataset. The backend is built with FastAPI and PostgreSQL extended with pgvector for semantic search, embeddings are generated locally using an open-source Hugging Face model, and the language model layer is designed to switch between two free-tier providers, Groq running an open-weight model and Google Gemini, so the system keeps working when one provider's free quota is exhausted. Every component of the stack, from the database to the embeddings model to the LLM providers to the hosting targets, is chosen to be usable at zero cost during development, while the architecture, security practices, and UI quality are built to a standard suitable for a real production deployment.

## 2. Problem Statement

Small and mid-size e-commerce businesses need a customer support system that can answer common order, billing, shipping, refund, and account questions instantly and around the clock, but most teams cannot afford enterprise conversational AI platforms, dedicated vector database infrastructure, or paid LLM API budgets, and they are also unable to demonstrate business value because support tooling is rarely connected to revenue and operational data in a way that shows leadership what the assistant is actually doing for the business. This project addresses that gap by building an assistant that answers customer questions grounded in a real support knowledge base rather than model memory, keeps operating cost near zero by using only free-tier and open-source components with an automatic fallback between two LLM providers and a token minimization strategy, and pairs the assistant with a professional analytics dashboard built on real e-commerce transactional data so the finished system looks, behaves, and reports like something a real retail company would run, not a toy demo.

## 3. Recommended Domain and Datasets

The domain is e-commerce and retail customer support. Two complementary open datasets are used so the demo has both realistic support content and realistic business data behind it. Do not use any paid or license-restricted dataset.

### 3.1 Support knowledge base dataset (for the chatbot and RAG)

Dataset: Bitext Customer Service Tagged Training Dataset for LLM-based Chatbots
Source: Hugging Face, `bitext/Bitext-customer-support-llm-chatbot-training-dataset`
Size: roughly 26,000 to 27,000 rows covering 27 intents across 11 categories such as account management, orders, refunds, shipping, invoices, payments, and subscriptions.
Fields: `instruction` (the customer utterance), `response` (the agent or assistant answer), `category`, `intent`, and tags describing linguistic variation.

How to download:
```bash
pip install datasets
python - <<'PY'
from datasets import load_dataset
ds = load_dataset("bitext/Bitext-customer-support-llm-chatbot-training-dataset")
ds["train"].to_csv("data/raw/support_kb.csv", index=False)
PY
```

How to use it:
- Treat every `instruction`/`response` pair as one knowledge base document.
- Clean and deduplicate, then chunk long responses if needed (most rows are short and need no chunking).
- Generate an embedding for each `response` (and optionally the `instruction`) using the open-source embedding model described in section 4.
- Store the text, metadata (`category`, `intent`), and embedding vector in a PostgreSQL table with a pgvector column.
- At query time, embed the incoming user message, run a similarity search against this table, and pass the top matching entries to the LLM as grounding context. This is the retrieval-augmented generation (RAG) pattern used by the chatbot and voice agent.

### 3.2 Revenue and operations dataset (for the analytics dashboard)

Dataset: Olist Brazilian E-Commerce Public Dataset
Source: Kaggle, `olistbr/brazilian-ecommerce`
Size: roughly 100,000 real, anonymized orders from 2016 to 2018, split across multiple CSV files: orders, order items, order payments, order reviews, customers, products, sellers, and geolocation.

How to download:
```bash
pip install kaggle
# place kaggle.json API token in ~/.kaggle/kaggle.json first (free Kaggle account required)
kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw/olist --unzip
```

How to use it:
- Load the CSV files into PostgreSQL as normalized tables: `orders`, `order_items`, `order_payments`, `order_reviews`, `customers`, `products`, `sellers`.
- Build aggregation queries and materialized views for the dashboard: revenue by day/month, revenue by product category, order volume, average order value, payment method mix, delivery time, and review score distribution.
- Use `order_reviews` (comment text and scores) as an additional, optional source for a "customer sentiment" panel on the dashboard, and optionally as extra grounding content for the chatbot.
- This dataset gives the analytics dashboard real historical trends instead of randomly generated numbers, which is what makes the demo look like a real production system.

### 3.3 Dataset folder structure

```
data/
  raw/
    support_kb.csv
    olist/
      olist_orders_dataset.csv
      olist_order_items_dataset.csv
      olist_order_payments_dataset.csv
      olist_order_reviews_dataset.csv
      olist_customers_dataset.csv
      olist_products_dataset.csv
      olist_sellers_dataset.csv
  processed/
    support_kb_cleaned.parquet
    olist_star_schema/
  embeddings/
    support_kb_embeddings.parquet
  scripts/
    load_support_kb.py
    load_olist.py
    generate_embeddings.py
    build_star_schema.py
```

Provide a `data/README.md` that documents the exact source URLs, license terms of each dataset (Bitext is released under CDLA-Sharing, Olist is released for public research and demo use), and the commands above so any developer can reproduce the data folder from scratch.

## 4. Tech Stack (all free to use)

| Layer | Choice |
|---|---|
| Backend language and framework | Python 3.11, FastAPI |
| Database | PostgreSQL 15+ with the pgvector extension |
| ORM and migrations | SQLAlchemy 2.x, Alembic |
| Caching and rate tracking | Redis (free local or free-tier hosted instance) |
| Embeddings | Open-source Hugging Face model, `BAAI/bge-small-en-v1.5` or `sentence-transformers/all-MiniLM-L6-v2`, run locally via the `sentence-transformers` library, no external API cost |
| Primary LLM provider | Groq API, model `openai/gpt-oss-20b`, free tier |
| Secondary LLM provider | Google Gemini API, model `gemini-2.5-flash`, free tier via Google AI Studio |
| Speech to text | `faster-whisper` (open-source, local inference) |
| Text to speech | `edge-tts` or Coqui TTS (open-source, no API key required) |
| Frontend | React 18 with Vite and TypeScript |
| Styling and components | Tailwind CSS, shadcn/ui |
| Charts | Recharts |
| Auth | JWT access and refresh tokens issued by FastAPI, OAuth2 password flow, bcrypt password hashing, role-based access control |
| Containerization | Docker, Docker Compose |
| Free hosting targets | Render or Railway free tier for the API and PostgreSQL, Vercel or Netlify free tier for the React app |
| CI | GitHub Actions free tier |

Rate limits on the free tiers (subject to change, verify current values in each provider's dashboard before building): Groq allows roughly 30 requests per minute and 1,000 requests per day per model on `openai/gpt-oss-20b`; Gemini's AI Studio free tier for `gemini-2.5-flash` allows roughly 15 requests per minute and 500 requests per day. Because both are limited, the system must never depend on a single provider being available, and it must minimize the number of LLM calls per user interaction. Section 6 (Phase 4) specifies exactly how.

## 5. High-Level Architecture

```
React SPA (public site + authenticated app)
        |
        v  HTTPS / WebSocket
FastAPI backend
  - Auth service (JWT, RBAC)
  - Chat orchestration service
  - Voice pipeline (STT -> chat orchestration -> TTS)
  - Analytics service (aggregation queries over Olist tables)
  - LLM provider router (Groq primary, Gemini fallback)
  - Embedding service (local Hugging Face model)
        |
        v
PostgreSQL + pgvector           Redis
  - users, roles                 - session cache
  - support_kb + embeddings      - semantic response cache
  - olist tables                 - provider quota counters
  - conversations, messages
  - audit_log
```

## 6. Phase-Wise Development Plan

### Phase 0: Environment and Project Scaffolding

- Initialize a monorepo with two top-level folders, `backend/` and `frontend/`, plus the `data/` folder from section 3.3.
- Set up Python 3.11 virtual environment, `pyproject.toml` or `requirements.txt` pinning FastAPI, SQLAlchemy, Alembic, psycopg, pgvector, sentence-transformers, groq, google-generativeai, redis, python-jose, passlib, faster-whisper, edge-tts, pytest.
- Set up the React app with Vite, TypeScript, Tailwind CSS, and shadcn/ui.
- Create `.env.example` for both backend and frontend listing every required variable (database URL, Redis URL, JWT secret, Groq API key, Gemini API key, token expiry settings) with no real secrets committed.
- Set up Docker Compose with three services: `api`, `postgres` (using the `pgvector/pgvector` Docker image), and `redis`.
- Configure pre-commit hooks for linting (ruff or flake8, black, eslint, prettier).
- Initialize Git repository with a sensible `.gitignore` covering `.env`, `data/raw`, `data/processed`, model caches, and `node_modules`.

### Phase 1: Database Design and Data Ingestion

- Design the schema in PostgreSQL:
  - `users(id, email, hashed_password, full_name, role, is_active, created_at)`
  - `roles(id, name)` with values such as `admin`, `agent`, `viewer`
  - `support_kb(id, instruction, response, category, intent, embedding vector(384))`
  - `conversations(id, user_id, channel, started_at, ended_at)`
  - `messages(id, conversation_id, role, content, tokens_used, provider_used, created_at)`
  - Olist star schema tables: `dim_customers`, `dim_products`, `dim_sellers`, `fact_orders`, `fact_order_items`, `fact_payments`, `fact_reviews`
  - `audit_log(id, user_id, action, resource, created_at)`
- Enable the pgvector extension: `CREATE EXTENSION IF NOT EXISTS vector;`
- Write Alembic migrations for every table above, including an HNSW or IVFFlat index on the `embedding` column for fast similarity search.
- Write `scripts/load_support_kb.py` to load and clean the Bitext dataset into `support_kb` (embeddings populated in Phase 4).
- Write `scripts/build_star_schema.py` to load the Olist CSVs, normalize date and currency fields, and populate the star schema tables.
- Add data validation checks (row counts, null checks, foreign key integrity) that run after ingestion and fail loudly if the data looks wrong.

### Phase 2: Backend API Foundation

- Build the FastAPI application with a clean module layout: `app/api/`, `app/core/`, `app/models/`, `app/schemas/`, `app/services/`, `app/db/`.
- Configure settings management with `pydantic-settings` reading from environment variables.
- Add structured logging (JSON logs), a global exception handler, and consistent API error response format.
- Add health check endpoints: `/health` and `/health/db`.
- Add CORS configuration restricted to the known frontend origin.
- Add request rate limiting middleware (for example `slowapi`) to protect both the API and the free LLM quotas from abuse.
- Add OpenAPI documentation via FastAPI's built-in Swagger UI, secured so it is not publicly exposed in production.

### Phase 3: Authentication and Authorization

- Implement signup and login endpoints using OAuth2 password flow.
- Hash passwords with bcrypt via passlib.
- Issue short-lived JWT access tokens and longer-lived refresh tokens; store refresh tokens hashed in the database with revocation support.
- Implement role-based access control with at least three roles: `admin` (full access including analytics and user management), `agent` (chat and voice access, limited analytics), `viewer` (read-only analytics).
- Protect every non-public endpoint with a dependency that validates the JWT and checks the required role.
- Implement password reset flow with time-limited tokens.
- Log every authentication event and every analytics data access into `audit_log`.
- On the frontend, store the access token in memory and the refresh token in an HTTP-only secure cookie, with automatic silent refresh.

### Phase 4: LLM Provider Layer and Token Minimization Strategy

This is the core engineering component of the project and must be built as a clean abstraction, not hardcoded calls scattered through the codebase.

- Build a `LLMProvider` interface with two implementations, `GroqProvider` (model `openai/gpt-oss-20b`) and `GeminiProvider` (model `gemini-2.5-flash`), each exposing the same method signature for a chat completion call.
- Build a `ProviderRouter` that:
  - Tracks remaining quota per provider per minute and per day in Redis.
  - Sends requests to the primary provider (Groq) by default.
  - Automatically switches to the secondary provider (Gemini) when the primary returns a rate limit error or its tracked quota is close to exhausted.
  - Switches back to the primary once its quota window resets.
  - Logs which provider handled each request in the `messages` table for later analysis on the dashboard.
- Implement token minimization so that one end-to-end user interaction uses the fewest possible LLM tokens:
  - Run intent classification locally where possible. Use the embedding similarity search against `support_kb` first; if a high-confidence match is found (similarity above a tuned threshold), return the stored response directly or with light templating, with no LLM call at all.
  - Only call the LLM when the retrieved knowledge base context does not confidently answer the query, or when the response needs to be composed in natural language from multiple retrieved snippets.
  - When the LLM is called, send a compact system prompt, only the top 2 to 3 retrieved knowledge base snippets (not the full corpus), and a trimmed conversation history (last 3 to 4 turns, or a short rolling summary of older turns instead of the raw text).
  - Cap `max_tokens` on every LLM call to the minimum needed for a support answer.
  - Implement a semantic response cache in Redis: before calling the LLM, check if a sufficiently similar question was answered recently, and reuse that answer if so.
  - Track and store token usage per request in the `messages` table so the dashboard can report actual token and provider usage over time.

### Phase 5: Embedding Service and Retrieval-Augmented Chat Engine

- Build an `EmbeddingService` that loads the chosen Hugging Face model once at application startup and exposes an `embed(text) -> vector` method, run on CPU (the chosen models are small enough for CPU inference).
- Write `scripts/generate_embeddings.py` to embed every row of `support_kb` and store the vectors using pgvector.
- Build a `RetrievalService` that embeds an incoming query and performs a cosine similarity search against `support_kb`, returning the top-k matches with their similarity scores.
- Build a `ChatOrchestrationService` that implements the flow: receive message, retrieve context, decide whether an LLM call is needed (per Phase 4 rules), compose the final answer, persist the message and metadata, return the answer.
- Add conversation memory: store each conversation's turns in `messages`, and generate a short rolling summary (itself an inexpensive local operation, not a full LLM call, using simple heuristics or a very small local summarization step) once the history exceeds a configured number of turns.
- Expose REST and WebSocket endpoints: `POST /chat/message` for standard request and response, `WS /chat/stream` for streamed token-by-token responses in the UI.

### Phase 6: Voice Agent

- Add an endpoint that accepts uploaded audio (or a WebSocket audio stream) and runs `faster-whisper` locally to transcribe speech to text.
- Feed the transcribed text into the same `ChatOrchestrationService` used by the text chatbot, so the token minimization and RAG logic in Phase 4 and Phase 5 are fully reused, with no duplicated logic for voice.
- Convert the generated answer to speech using `edge-tts` (or Coqui TTS as an offline alternative) and stream the audio back to the client.
- Build the voice pipeline as a WebSocket flow: client streams microphone audio, server streams back partial transcript, final transcript, text answer, and synthesized audio.
- Add basic voice activity detection on the frontend so audio is only sent while the user is actually speaking, reducing wasted transcription work.

### Phase 7: Frontend, Public Corporate Website

Build a public marketing site that reads like a real enterprise product page, not a demo. Required sections:

- Sticky navigation bar with the product name/logo, links to Product, Solutions, Pricing (can be illustrative), Resources, and a clearly visible Login button in the top right that routes to the authentication screen.
- Hero section: a strong headline about AI-powered customer support and revenue intelligence, a short supporting sentence, a primary call-to-action button ("Request a demo" or "Start free"), and a hero illustration or product screenshot mock.
- Logo strip implying trusted-by companies (use neutral placeholder names, clearly generic, not real company names or logos).
- Feature sections: one block for the AI chatbot and RAG knowledge base, one for the voice agent, one for the analytics and revenue dashboard, each with a short paragraph, an icon, and a supporting image or illustrative screenshot.
- "How it works" section with a 3 to 4 step visual flow.
- Metrics/social proof strip with illustrative stats (for example response time, resolution rate, uptime) clearly presented as product metrics.
- Testimonials section with 2 to 3 illustrative quotes attributed to generic personas and titles (not real people or companies).
- Pricing or plans section (can be simple tiers, illustrative).
- FAQ accordion section.
- Footer with product, company, and legal link columns, and a newsletter signup field.
- Use a cohesive design system: a defined color palette, consistent spacing scale, a professional font pairing (for example a geometric sans for headings and a readable sans or serif for body text), and consistent button and card styles across the whole site. Follow the frontend design guidance available in this environment for spacing, typography, and visual polish rather than default, generic styling.
- All images should be sourced from free stock photo or illustration sources (for example openly licensed placeholder image services or open-source illustration packs) and must be clearly non-copyrighted or self-generated graphics.

### Phase 8: Frontend, Authenticated Application

- Build the login and signup screens matching the same design system as the public site.
- Build an authenticated app shell with a sidebar navigation: Chat, Voice Agent, Dashboard, Conversation History, Settings, and, for admins, User Management.
- Build the chat interface: message list with streaming responses, a visible indicator of which LLM provider answered (useful for demoing the fallback behavior), typing indicators, and a way to rate an answer as helpful or not helpful (store this feedback for future evaluation).
- Build the voice agent interface: a microphone button with recording state, live transcript display, and audio playback of the response, reusing the same conversation thread component as the chat interface where practical.
- Build a conversation history view listing past conversations with search and filtering by date and channel (chat or voice).
- Build a settings page for profile details and password change.
- Build a user management page for admins to view users and change roles.

### Phase 9: Revenue and Analytics Dashboard

- Build backend aggregation endpoints over the Olist star schema, each backed by an efficient SQL query or a materialized view refreshed on a schedule:
  - Revenue over time (daily, weekly, monthly), with period-over-period comparison.
  - Revenue and order count by product category.
  - Average order value trend.
  - Customer growth and repeat purchase rate.
  - Payment method distribution.
  - Average delivery time and on-time delivery rate.
  - Review score distribution and average rating trend.
  - Support-side metrics from the chatbot's own data: conversation volume over time, average resolution without escalation, LLM provider usage split, average tokens per conversation, and average response latency.
- Build the dashboard frontend with a KPI summary row (total revenue, total orders, average order value, active customers) followed by a grid of charts.
- Use Recharts to build professional-looking line charts for trends, bar charts for category comparisons, pie or donut charts for distribution breakdowns, and a data table for a top-products or top-customers list.
- Add global filters (date range, product category) that all charts respond to.
- Add loading skeletons and empty states so the dashboard degrades gracefully while data loads.
- Add CSV export on key tables and charts.
- Ensure every chart has a clear title, axis labels, and legend, matching the polish expected on a real business intelligence product.

### Phase 10: Security Hardening

- Enforce HTTPS in all non-local environments.
- Store all secrets in environment variables, never in source control; document required variables in `.env.example`.
- Validate and sanitize all inputs with Pydantic schemas; reject unexpected fields.
- Apply parameterized queries everywhere through the ORM, no raw string-built SQL.
- Apply rate limiting per user and per IP on authentication and chat endpoints.
- Set secure, HTTP-only, same-site cookies for refresh tokens.
- Apply the principle of least privilege in role-based access control; verify every endpoint against the intended role matrix.
- Add security headers (Content-Security-Policy, X-Frame-Options, X-Content-Type-Options) at the API gateway or reverse proxy layer.
- Add dependency vulnerability scanning to CI (for example `pip-audit` and `npm audit`).
- Add audit logging for authentication events, role changes, and analytics data access.

### Phase 11: Testing

- Backend: unit tests for the provider router and fallback logic, the retrieval service, the token minimization decision logic, and authentication and authorization rules, using pytest.
- Backend: integration tests for the main API flows (signup, login, chat message, voice pipeline, dashboard endpoints) using a test database.
- Frontend: component tests for the chat interface, voice interface, and dashboard charts using a standard React testing library.
- Load a small synthetic load test against the chat endpoint to confirm the provider fallback logic actually triggers when a quota limit is simulated.
- Manual QA checklist covering the full user journey: visit the public site, log in, run a chat conversation, run a voice conversation, view the dashboard, log out.

### Phase 12: Deployment

- Containerize the backend with a production Dockerfile (multi-stage build, non-root user).
- Deploy PostgreSQL and Redis using free-tier hosted instances or the same provider's managed free tier.
- Deploy the FastAPI backend to a free tier of Render or Railway.
- Deploy the React frontend to a free tier of Vercel or Netlify, configured to call the deployed backend URL.
- Set up environment-specific configuration (development, staging, production) with separate `.env` files.
- Set up a GitHub Actions workflow that runs lint and tests on every pull request and deploys on merge to the main branch.
- Document rollback steps and basic monitoring (uptime checks, error logging).

## 7. Documentation Requirements

The repository must include a professional `README.md` at the root with, at minimum, the following sections: project title and one-paragraph summary, architecture diagram or description, tech stack table, prerequisites, local setup instructions (backend, frontend, database, environment variables), how to download and load both datasets, how to run the application locally, how to run tests, deployment instructions, API documentation reference, a note on the LLM provider fallback behavior and how to configure API keys for both providers, project folder structure, and licensing information for the code and for both third-party datasets. The README should be written in clear, professional language throughout, with no casual or unprofessional wording anywhere in the repository's documentation, code comments, or UI copy, and no em dash characters used anywhere in any file.
