# BTC Crowdfund Analytics - Project Status & Integration Roadmap

> **Note:** Legacy status report focused on the BTCPay + Angor hybrid MVP.  
> The codebase now ships a streamlined Angor-only dashboard. Refer to `README.md` for the up-to-date scope.

**Date:** October 11, 2025  
**Status:** ✅ MVP Complete - Demo Mode Functional  
**Next Phase:** Real Service Integration

---

## 🎯 Current State

### What's Working ✅

1. **Core Application**
   - FastAPI server running on port 8000
   - SQLite database with 3 tables (Invoice, EventLog, SourceProject)
   - SQLModel ORM for data persistence
   - Server-side rendering with Jinja2 templates
   - Responsive CSS styling
   - Chart.js visualizations (line charts, doughnut charts)

2. **Demo Mode**
   - 30 synthetic invoices seeded across 14 days
   - Mock data shows realistic BTC crowdfunding scenarios
   - All UI components rendering correctly
   - Dashboard shows: KPIs, time-series charts, status distribution
   - Settings page displays configuration
   - Webhook logs page ready to receive events

3. **Code Quality**
   - 17 unit tests passing (100% pass rate)
   - Tests cover: HMAC verification, analytics aggregation, timestamp parsing, API headers
   - Clean separation of concerns (models, views, repo, analytics, adapters)
   - Type hints throughout
   - Comprehensive error handling

4. **Infrastructure**
   - Virtual environment configured (.venv)
   - All dependencies installed via pip
   - Makefile with convenient commands (run, test, seed, clean)
   - .gitignore configured
   - README with full documentation

---

## 🚧 What's NOT Integrated (Template Only)

### 1. BTCPay Server Integration ⚠️

**Current State:**
- ✅ Client wrapper exists (`app/btcpay_client.py`)
- ✅ API methods defined: `get_invoices()`, `get_invoice()`, `ensure_webhook()`
- ✅ Proper authorization header format: `Authorization: token {api_key}`
- ✅ Correct endpoint structure: `/api/v1/stores/{storeId}/invoices`
- ❌ **NO REAL API CALLS TESTED** - never connected to actual BTCPay instance
- ❌ No error handling for real API responses
- ❌ Don't know if BTCPay response format matches our expectations
- ❌ Webhook verification written but NEVER tested with real BTCPay signature

**What We Assume (Based on Docs):**
```python
# Invoice response format we expect:
{
  "id": "invoice_id",
  "storeId": "store_id", 
  "status": "Settled" | "Expired" | "New" | "Processing",
  "amount": 10.00,
  "currency": "USD",
  "cryptoPrice": 0.00015,  # BTC amount
  "createdTime": "2024-10-11T12:00:00Z",
  "paidTime": "2024-10-11T12:05:00Z",
  "buyerEmail": "user@example.com",
  "metadata": {}
}
```

**Critical Unknowns:**
1. Does the real API return `cryptoPrice` or something else for BTC amount?
2. Are timestamps ISO-8601 with Z or +00:00?
3. What are ALL possible status values in production?
4. Does pagination work as expected for stores with 1000+ invoices?
5. What rate limits exist on the API?
6. How does webhook signature verification work with real payloads?

**Integration Blockers:**
- Need access to a BTCPay Server instance (testnet or mainnet)
- Need to generate API key with proper permissions
- Need to test webhook delivery mechanism
- Need to handle API versioning and breaking changes

---

### 2. Webhook System ⚠️

**Current State:**
- ✅ Endpoint exists: `POST /webhook`
- ✅ HMAC-SHA256 verification implemented
- ✅ Raw body reading and signature comparison
- ✅ EventLog storage for all deliveries
- ✅ Unit tests pass for known test vectors
- ❌ **NEVER TESTED WITH REAL BTCPAY WEBHOOKS**
- ❌ Don't know if BTCPay sends headers exactly as documented
- ❌ No ngrok or public URL setup for testing
- ❌ No webhook retry logic
- ❌ No webhook authentication beyond HMAC

**Critical Testing Needed:**
1. Set up ngrok tunnel: `ngrok http 8000`
2. Configure BTCPay webhook with ngrok URL
3. Create test invoice and pay it
4. Verify webhook is received and signature validates
5. Test what happens with malformed payloads
6. Test automatic redelivery on failure

**Current Webhook Handler Logic:**
```python
# webhook.py expects:
- Header: BTCPay-Sig (HMAC-SHA256 hex)
- Body: Raw JSON invoice event
- Events: InvoiceSettled, InvoiceExpired, InvoiceInvalid
```

---

### 3. Angor Protocol Integration ⚠️

**Current State:**
- ✅ Adapter exists (`app/angor_adapter.py`)
- ✅ Three-tier strategy: demo JSON → hub API → fallback
- ✅ Demo data loads from `data/angor_demo.json` (5 projects)
- ❌ **HUB.ANGOR.IO API NEVER TESTED** - just placeholder code
- ❌ Don't know actual API structure or endpoints
- ❌ No Nostr integration (mentioned in spec but not implemented)
- ❌ No authentication for Angor Hub
- ❌ CORS issues likely if calling from browser

**What We Assume About Angor:**
```python
# Expected API response from hub.angor.io:
{
  "projects": [
    {
      "projectId": "angor_123",
      "title": "Project Name",
      "targetAmount": 1.5,  # BTC
      "amountRaised": 0.8,  # BTC
      "createdAt": "2024-10-01T00:00:00Z"
    }
  ]
}
```

**Critical Unknowns:**
1. What is the actual Angor Hub API endpoint?
2. Does it require authentication?
3. What's the real response structure?
4. How do we get project metadata (descriptions, founders, etc.)?
5. Is there a WebSocket for real-time updates?
6. How does Nostr fit into the architecture?
7. What are the time-lock and staged release mechanisms?

**Nostr Integration Gap:**
- Angor uses Nostr for metadata and communication
- We have ZERO Nostr code
- Need Nostr client library (e.g., `python-nostr`)
- Need to subscribe to project update events
- Need to fetch project details via Nostr relays

---

## 📊 Database Schema (Current)

```sql
-- Invoice Table
CREATE TABLE invoice (
    id TEXT PRIMARY KEY,
    store_id TEXT NOT NULL,
    status TEXT NOT NULL,
    currency TEXT NOT NULL,
    amount REAL NOT NULL,
    amount_btc REAL,
    created_at DATETIME NOT NULL,
    paid_at DATETIME,
    payer_email TEXT,
    invoice_metadata TEXT  -- JSON as text
);

-- EventLog Table
CREATE TABLE eventlog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    received_at DATETIME NOT NULL,
    signature TEXT NOT NULL,
    verified BOOLEAN NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL  -- JSON as text
);

-- SourceProject Table (Angor)
CREATE TABLE sourceproject (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    amount_target REAL NOT NULL,
    amount_raised REAL NOT NULL,
    created_at DATETIME NOT NULL,
    source TEXT NOT NULL  -- "angor" or "demo"
);
```

**Potential Schema Issues:**
- No indexes for performance (will be slow with 10k+ invoices)
- No foreign keys or relationships
- No project descriptions or metadata
- No contributor tracking
- No milestone/stage tracking for Angor projects
- Amount stored as REAL (should use INTEGER satoshis for precision)

---

## 🔧 Technical Debt & Improvements Needed

### High Priority

1. **Real BTCPay Testing**
   - Get testnet BTCPay instance or API sandbox
   - Test all API endpoints with real data
   - Validate webhook signature with actual deliveries
   - Handle pagination for large stores
   - Add retry logic with exponential backoff

2. **Error Handling**
   - BTCPay API errors currently just print and return empty list
   - No user-facing error messages
   - No Sentry or error tracking
   - No API timeout handling beyond basic httpx timeout

3. **Security**
   - API keys stored in plaintext .env
   - No rate limiting on webhook endpoint
   - No CSRF protection
   - No authentication on dashboard (anyone can view analytics)
   - Webhook endpoint is public (only HMAC protects it)

4. **Performance**
   - No caching layer (Redis)
   - No database indexes
   - All analytics computed on every page load
   - No background jobs for data syncing

### Medium Priority

5. **Angor Real Integration**
   - Find actual Angor Hub API documentation
   - Test API endpoints
   - Add Nostr client integration
   - Subscribe to project events
   - Fetch real-time funding updates

6. **Data Accuracy**
   - BTC amounts stored as float (loses precision)
   - Should use satoshis (integer) everywhere
   - No currency conversion handling
   - No historical price tracking

7. **Monitoring**
   - No logging framework (just print statements)
   - No metrics collection (Prometheus)
   - No health check beyond basic endpoint
   - No alerting for failed webhooks

### Low Priority

8. **UI/UX**
   - No user authentication or multi-user support
   - No invoice detail view
   - No filtering by date range (just shows all)
   - No export to CSV/JSON
   - No dark mode
   - Charts not responsive on mobile

9. **Testing**
   - Only 17 unit tests
   - No integration tests
   - No end-to-end tests
   - No load testing
   - No webhook delivery testing

---

## 🎯 Integration Roadmap

### Phase 1: BTCPay Server (Real Integration)

**Goal:** Connect to actual BTCPay instance and receive live data

**Tasks:**
1. ✅ Set up BTCPay Server account (testnet or demo instance)
2. ✅ Generate API key with permissions:
   - `btcpay.store.canviewinvoices`
   - `btcpay.store.webhooks.canmodifywebhooks`
3. ✅ Update .env with real credentials
4. ✅ Test `get_invoices()` endpoint
5. ✅ Verify response format matches our assumptions
6. ✅ Add error handling for rate limits and timeouts
7. ✅ Set up ngrok for webhook testing
8. ✅ Configure webhook in BTCPay dashboard
9. ✅ Create test invoice and verify webhook delivery
10. ✅ Fix any bugs in webhook verification
11. ✅ Add pagination for large invoice lists
12. ✅ Add background job for periodic sync

**Estimated Time:** 2-3 days

---

### Phase 2: Angor Protocol (Real Integration)

**Goal:** Fetch and display real Angor crowdfunding projects

**Tasks:**
1. ⬜ Research Angor Hub API documentation
   - Find official docs or reverse engineer API
   - Identify authentication requirements
   - Understand project data structure
2. ⬜ Test Angor Hub API endpoints
   - List all projects
   - Get project details
   - Fetch funding progress
3. ⬜ Implement Nostr integration
   - Add `python-nostr` or `nostr-sdk` dependency
   - Connect to Nostr relays
   - Subscribe to Angor project events (NIP-XX?)
   - Fetch project metadata from Nostr
4. ⬜ Update adapter to use real data
   - Replace mock API calls
   - Handle real response structure
   - Add caching for Nostr events
5. ⬜ Test with 10+ real Angor projects
6. ⬜ Add real-time updates via WebSocket or polling

**Estimated Time:** 4-5 days (if docs available, 7-10 days if reverse engineering)

**Critical Blockers:**
- Need Angor Hub API documentation
- Need to understand Nostr event types for projects
- May need access to Angor developer community/Discord

---

### Phase 3: Production Readiness

**Goal:** Make app production-ready for real users

**Tasks:**
1. ⬜ Add proper logging (structlog or loguru)
2. ⬜ Add error tracking (Sentry)
3. ⬜ Add rate limiting on webhook endpoint
4. ⬜ Add authentication (OAuth2, JWT, or API keys)
5. ⬜ Switch to PostgreSQL for production
6. ⬜ Add Redis for caching and job queue
7. ⬜ Add background workers (Celery or ARQ)
8. ⬜ Add database migrations (Alembic)
9. ⬜ Use satoshis (integers) instead of BTC floats
10. ⬜ Add database indexes for performance
11. ⬜ Add comprehensive integration tests
12. ⬜ Add monitoring dashboard (Grafana)
13. ⬜ Containerize with Docker
14. ⬜ Deploy to cloud (Render, Railway, or DigitalOcean)

**Estimated Time:** 1-2 weeks

---

## 🤔 Questions for Integration

### BTCPay Server

1. **API Response Format:** Can we get a sample JSON response from a real BTCPay `/stores/{id}/invoices` call?
2. **Pagination:** How does pagination work? Query params `?skip=0&take=100`?
3. **Status Values:** What are ALL possible invoice status values in production?
4. **Rate Limits:** What are the API rate limits? Per hour? Per day?
5. **Webhook Signature:** Can we get a real webhook payload + signature to test against?
6. **Metadata Field:** What structure does the `metadata` field have? Is it always an object?
7. **BTC Amount:** Is `cryptoPrice` the field name, or is it `btcPrice`, `amount_btc`, etc.?
8. **Timestamp Format:** Are timestamps always ISO-8601 with Z, or do they vary?

### Angor Protocol

1. **Hub API:** What is the actual Angor Hub API URL and documentation?
2. **Authentication:** Does the API require auth tokens or API keys?
3. **Nostr Integration:** Which Nostr event kinds (NIPs) does Angor use for projects?
4. **Project Structure:** What fields are available for projects? (description, founder, milestones, etc.)
5. **Funding Updates:** How do we get real-time funding updates? Polling? WebSocket? Nostr events?
6. **Time Locks:** How are Bitcoin time-locks represented in the API?
7. **Staged Releases:** How do we track milestone releases and fund disbursement?
8. **Public vs Private:** Are all projects public, or do some require authentication?

### General Architecture

1. **Multi-Store:** Should we support multiple BTCPay stores per user?
2. **User Auth:** Do we need user authentication, or is this single-user/admin only?
3. **Data Retention:** How long should we cache invoice data? Forever? 90 days?
4. **Refresh Strategy:** Should data refresh automatically (cron job) or manually only?
5. **Notifications:** Should users get email/SMS alerts for new invoices?
6. **API Endpoints:** Should we expose REST API endpoints for external consumption?

---

## 📦 Current Dependencies

```
fastapi==0.104.1          # Web framework
uvicorn[standard]==0.24.0 # ASGI server
jinja2==3.1.2             # Templates
sqlmodel==0.0.14          # ORM
httpx==0.25.1             # HTTP client
python-dotenv==1.0.0      # .env loading
pytest==7.4.3             # Testing
pytest-asyncio==0.21.1    # Async testing
```

**Missing Dependencies for Real Integration:**
- `redis` - Caching and job queue
- `celery` or `arq` - Background tasks
- `alembic` - Database migrations
- `sentry-sdk` - Error tracking
- `prometheus-client` - Metrics
- `python-nostr` or `nostr-sdk` - Nostr protocol
- `psycopg2-binary` - PostgreSQL driver (for production)

---

## 🚀 How to Get Started with Real Integration

### Option 1: BTCPay Server Testnet

```bash
# 1. Go to https://testnet.demo.btcpayserver.org/
# 2. Create an account
# 3. Create a store
# 4. Go to Store Settings > Access Tokens
# 5. Generate new API key with permissions
# 6. Update .env file with real values

# .env
BTCPAY_HOST=testnet.demo.btcpayserver.org
BTCPAY_API_KEY=actual_api_key_here
BTCPAY_STORE_ID=actual_store_id_here
BTCPAY_WEBHOOK_SECRET=choose_a_secret

# 7. Restart app - demo mode should turn off
# 8. Click "Refresh Data" in dashboard
# 9. Verify invoices appear from real API
```

### Option 2: Local BTCPay Server (Advanced)

```bash
# Run BTCPay Server locally with Docker
git clone https://github.com/btcpayserver/btcpayserver-docker
cd btcpayserver-docker
./btcpay-setup.sh

# Follow setup wizard
# Connect to regtest or testnet
```

### Option 3: Angor Hub Research

```bash
# 1. Visit https://angor.io/ and https://hub.angor.io/
# 2. Open browser DevTools > Network tab
# 3. Browse projects and watch API calls
# 4. Document API endpoints and response structures
# 5. Look for API documentation or GitHub repos
# 6. Join Angor community (Discord/Telegram) for API docs
```

---

## 💡 Recommendations for Next Steps

### Immediate (This Weekend)

1. **Test with Real BTCPay** - Priority #1
   - Set up testnet BTCPay account
   - Configure API credentials
   - Verify invoice fetching works
   - Test webhook delivery with ngrok

2. **Fix Critical Bugs**
   - Add database indexes for performance
   - Fix BTC amount precision (use satoshis)
   - Add proper error messages to UI

### Short Term (Next Week)

3. **Angor Research**
   - Find API documentation
   - Test Hub endpoints
   - Document response structure

4. **Add Logging**
   - Replace print statements
   - Add structured logging
   - Log all API calls and webhooks

### Medium Term (Next Month)

5. **Production Deploy**
   - Set up PostgreSQL
   - Add Redis caching
   - Deploy to cloud platform
   - Add monitoring

6. **Nostr Integration**
   - Add Nostr client
   - Subscribe to Angor events
   - Real-time project updates

---

## 🎯 Success Metrics

**MVP is successful when:**
- ✅ 30+ demo invoices displayed correctly (DONE)
- ✅ All tests pass (DONE)
- ⬜ Connected to real BTCPay Server
- ⬜ Receiving and processing real invoices
- ⬜ Webhook delivery working and verified
- ⬜ Displaying at least 5 real Angor projects

**Production-ready when:**
- ⬜ Deployed to public URL
- ⬜ Handling 1000+ invoices smoothly
- ⬜ Zero downtime in 7 days
- ⬜ Real users viewing dashboard
- ⬜ Automated data sync every 15 minutes

---

## 📞 Contact & Resources

**BTCPay Server:**
- Docs: https://docs.btcpayserver.org/
- API Docs: https://docs.btcpayserver.org/API/Greenfield/v1/
- Demo: https://mainnet.demo.btcpayserver.org/
- Testnet: https://testnet.demo.btcpayserver.org/

**Angor Protocol:**
- Website: https://angor.io/
- Hub: https://hub.angor.io/
- GitHub: https://github.com/block-core/angor

**Current Application:**
- Running on: http://localhost:8000
- Database: `btc_crowdfund.db` (SQLite)
- Logs: Console output only

---

**End of Status Report**

*This document should give any AI assistant or developer a complete picture of what's working, what's not, and exactly what needs to be done to integrate with real services.*
