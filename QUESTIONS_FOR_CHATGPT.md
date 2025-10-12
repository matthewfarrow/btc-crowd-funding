# Questions to Ask ChatGPT for System Improvements

> **Context:** These prompts were written for the previous BTCPay + Angor version of the project.  
> Revise them if you want guidance for the current Angor-only dashboard.

## 📋 Copy this entire message to ChatGPT:

---

I have a Bitcoin crowdfunding analytics dashboard built with FastAPI, SQLite, and Chart.js. It's designed to pull data from BTCPay Server and display Angor protocol projects. Currently it works in demo mode with synthetic data, but I haven't integrated the real services yet.

**Full technical details in:** [Attach PROJECT_STATUS.md file]

### My Specific Questions:

## 1. BTCPay Server Integration

**Context:** I have a client wrapper with methods like `get_invoices()` and `ensure_webhook()`, but I've never tested with a real BTCPay instance.

**Questions:**
- What's the best way to test BTCPay API integration safely without real money? (testnet vs regtest vs demo.btcpayserver.org)
- Are there any gotchas with BTCPay's webhook signature verification that commonly trip people up?
- How should I handle pagination for stores with thousands of invoices? What's the recommended batch size?
- What error codes/responses should I expect from the Greenfield API, and how should I handle each?
- Is there a sandbox or mock BTCPay server for development/testing?

## 2. Angor Protocol & Nostr

**Context:** Angor is a decentralized crowdfunding protocol using Bitcoin + Nostr. I have placeholder code but no actual integration.

**Questions:**
- Where can I find the official Angor Hub API documentation? (I couldn't find it on angor.io)
- What Nostr NIPs (event kinds) does Angor use for project metadata?
- Which Nostr relays should I connect to for Angor data?
- Should I use `python-nostr` or is there a better library for Nostr integration?
- How do I fetch real-time funding updates for Angor projects?
- What's the best architecture: poll the Hub API, subscribe to Nostr events, or both?

## 3. Data Modeling & Precision

**Current Issue:** I'm storing Bitcoin amounts as SQLite REAL (float), which loses precision.

**Questions:**
- Should I store everything in satoshis (integers) and convert for display?
- What's the standard practice for storing BTC amounts in databases?
- Should I track historical BTC/USD exchange rates for analytics?
- How do I handle different cryptocurrencies if BTCPay supports multiple?

## 4. Webhook Reliability

**Current Setup:** Single webhook endpoint with HMAC verification, stores all deliveries in EventLog table.

**Questions:**
- How do I handle webhook failures and retries gracefully?
- Should I implement idempotency keys to prevent duplicate processing?
- What's the best way to test webhook delivery locally? (ngrok vs localtunnel vs something else?)
- Should I add a queue (like Redis + Celery) for processing webhooks asynchronously?
- How do I detect and alert on missed webhooks?

## 5. Architecture & Scalability

**Current:** Single FastAPI app, SQLite database, no caching, synchronous API calls.

**Questions:**
- At what point should I switch from SQLite to PostgreSQL?
- Should I add Redis caching now or wait until I have performance issues?
- Are my analytics functions efficient, or will they be slow with 10k+ invoices? (See `analytics.py`)
- Should I move data fetching to background jobs (Celery/ARQ) or keep it synchronous?
- What's the recommended architecture for a production Bitcoin analytics dashboard?

## 6. Security & Production Readiness

**Current:** No authentication, API keys in .env, public webhook endpoint.

**Questions:**
- What authentication method should I use for the dashboard? (OAuth2, JWT, simple password)
- Are there any Bitcoin-specific security concerns I should know about?
- How do I securely store BTCPay API keys in production? (environment variables, secrets manager, etc.)
- Should I add rate limiting on the webhook endpoint? If so, how?
- What monitoring/alerting should I set up for a Bitcoin app in production?

## 7. Testing Strategy

**Current:** 17 unit tests, no integration tests, never tested with real services.

**Questions:**
- How do I test webhook signature verification without a real BTCPay instance?
- Should I mock the BTCPay API or use a real testnet instance for integration tests?
- What are the most important integration tests to write first?
- How do I test Nostr event subscriptions in CI/CD?

## 8. Immediate Next Steps

**Given my current state (working demo, zero real integrations), what should I prioritize?**

Rank these in order:
- A) Get BTCPay testnet working and verify invoice fetching
- B) Set up webhook testing with ngrok
- C) Research Angor API and document endpoints
- D) Switch to satoshis and fix precision issues
- E) Add database indexes and optimize queries
- F) Add error handling and logging
- G) Deploy to production with demo data
- H) Add user authentication

## 9. Angor-Specific Architecture

**Given that Angor uses:**
- Bitcoin for actual funds (with time-locks)
- Nostr for project metadata and communication
- Decentralized architecture (no central server)

**Questions:**
- Should my app be a Nostr client that subscribes to events, or should I poll a centralized hub?
- How do I verify that project funding amounts are accurate (since it's decentralized)?
- What happens if the Angor Hub goes offline? How do I get data directly from the blockchain + Nostr?
- Are there any existing Python SDKs or libraries for Angor integration?

## 10. Comparison to Existing Solutions

**Questions:**
- Are there any open-source Bitcoin crowdfunding analytics tools I should study?
- How do existing BTCPay Server dashboards handle data aggregation and analytics?
- What features do popular crowdfunding platforms (Kickstarter, Geyser, Tallycoin) have that I'm missing?
- Is my approach (cache invoices locally + analyze) the right pattern, or should I query BTCPay on-demand?

---

## Additional Context You Might Need:

**Tech Stack:**
- Python 3.11
- FastAPI 0.104.1
- SQLModel (SQLAlchemy + Pydantic)
- SQLite database
- Jinja2 templates
- Chart.js for visualizations
- httpx for HTTP requests

**Current Files:**
- `app/btcpay_client.py` - BTCPay API wrapper
- `app/webhook.py` - Webhook handler with HMAC verification
- `app/angor_adapter.py` - Angor integration (placeholder)
- `app/analytics.py` - Aggregation functions
- `app/models.py` - Database models (Invoice, EventLog, SourceProject)

**Running Application:**
- Dashboard at http://localhost:8000
- 30 demo invoices seeded
- All tests passing
- Demo mode working perfectly

**What I Need:**
Specific, actionable advice on:
1. How to integrate BTCPay Server (step-by-step)
2. How to integrate Angor + Nostr (where to start)
3. What to improve before going to production
4. Common pitfalls to avoid with Bitcoin/Lightning applications

---

Please provide detailed recommendations with code examples where relevant. Focus on practical, implementable solutions over theoretical discussions.

Thank you!
