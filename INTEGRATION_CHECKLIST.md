# Quick Integration Checklist

## 🎯 To Integrate Real BTCPay Server (30 minutes)

### Step 1: Get BTCPay Access
- [ ] Go to https://testnet.demo.btcpayserver.org/
- [ ] Create account and store
- [ ] Generate API key with these permissions:
  - `btcpay.store.canviewinvoices`
  - `btcpay.store.webhooks.canmodifywebhooks`

### Step 2: Configure Application
```bash
# Edit .env file
BTCPAY_HOST=testnet.demo.btcpayserver.org
BTCPAY_API_KEY=<your_actual_key>
BTCPAY_STORE_ID=<your_store_id>
BTCPAY_WEBHOOK_SECRET=<choose_random_string>
```

### Step 3: Test Connection
```bash
# Restart server
pkill -f uvicorn
source .venv/bin/activate && uvicorn app.main:app --reload

# Visit http://localhost:8000
# Yellow "Demo Mode" banner should disappear
# Click "Refresh Data" button
# Should fetch real invoices (if any exist)
```

### Step 4: Test Webhooks
```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com/

# Start ngrok tunnel
ngrok http 8000

# Copy the https URL (e.g., https://abc123.ngrok.io)
# Go to BTCPay Store Settings > Webhooks
# Add webhook:
#   URL: https://abc123.ngrok.io/webhook
#   Secret: <same as .env BTCPAY_WEBHOOK_SECRET>
#   Events: InvoiceSettled, InvoiceExpired, InvoiceInvalid

# Create test invoice in BTCPay and pay it
# Check /logs page for webhook delivery
```

---

## 🔍 To Research Angor Integration (1-2 hours)

### Investigation Tasks
- [ ] Visit https://hub.angor.io/
- [ ] Open Browser DevTools > Network tab
- [ ] Click around projects and capture API calls
- [ ] Document endpoints found (e.g., `/api/projects`)
- [ ] Look for GitHub repos: https://github.com/block-core/angor
- [ ] Check for API documentation
- [ ] Join Angor community (Discord/Telegram) if exists

### Expected Findings
Document in `ANGOR_API_NOTES.md`:
- Base API URL
- Authentication method (if any)
- Project list endpoint
- Project detail endpoint
- Response structure
- Rate limits
- Nostr relay information

---

## 🐛 Known Issues to Fix

### High Priority
1. **BTC Precision Loss**
   - Currently storing BTC as float (loses precision)
   - Should convert to satoshis (integer) everywhere
   - Fix in: `models.py`, `analytics.py`, `seed_demo.py`

2. **No Database Indexes**
   - Will be slow with 1000+ invoices
   - Add indexes on: `invoice.created_at`, `invoice.status`, `invoice.store_id`

3. **Error Handling**
   - API failures just print and return empty list
   - Should show error banner in UI
   - Should log to file, not just console

### Medium Priority
4. **No Pagination**
   - `get_invoices()` fetches all invoices at once
   - Will timeout with large stores
   - Add pagination parameters

5. **No Caching**
   - Recomputes analytics on every page load
   - Add Redis caching layer

---

## 📊 Test Real Integration

### BTCPay API Tests
```python
# Add to tests/test_btcpay_integration.py
import pytest
from app.btcpay_client import btcpay_client

@pytest.mark.asyncio
async def test_real_api_connection():
    """Test actual BTCPay API call."""
    invoices = await btcpay_client.get_invoices(days=7)
    assert isinstance(invoices, list)
    if invoices:
        assert 'id' in invoices[0]
        assert 'status' in invoices[0]

# Run with: pytest tests/test_btcpay_integration.py -v
```

### Webhook Tests
```bash
# Test webhook signature with real example
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -H "BTCPay-Sig: <get_from_real_delivery>" \
  -d '<paste_real_webhook_payload>'

# Check /logs page to verify verification status
```

---

## 🚀 Quick Wins for Weekend

### Easy Improvements (1-2 hours each)

1. **Add Favicon**
```bash
# Download Bitcoin logo
# Save as static/favicon.ico
# Add to base.html: <link rel="icon" href="/static/favicon.ico">
```

2. **Add Loading States**
```javascript
// In index.html, show "Loading..." during refresh
document.querySelector('form[action="/refresh"]').addEventListener('submit', function() {
    this.querySelector('button').textContent = '⏳ Loading...';
});
```

3. **Add Invoice Detail Page**
```python
# In views.py
@router.get("/invoice/{invoice_id}", response_class=HTMLResponse)
async def invoice_detail(invoice_id: str, session: Session = Depends(get_session)):
    invoice = session.get(Invoice, invoice_id)
    return templates.TemplateResponse("invoice_detail.html", {
        "request": request,
        "invoice": invoice
    })
```

4. **Add CSV Export**
```python
# In views.py
@router.get("/export/csv")
async def export_csv(session: Session = Depends(get_session)):
    invoices = get_all_invoices(session)
    # Use pandas or csv module to generate CSV
    return Response(content=csv_content, media_type="text/csv")
```

5. **Add Date Range Filter**
```html
<!-- In index.html -->
<form method="get">
    <input type="date" name="start_date">
    <input type="date" name="end_date">
    <button type="submit">Filter</button>
</form>
```

---

## 🔐 Security Improvements Needed

Before going to production:

- [ ] Add rate limiting on webhook endpoint (use `slowapi`)
- [ ] Add HTTPS/SSL certificate (required for webhooks)
- [ ] Add authentication to dashboard (OAuth2 or simple password)
- [ ] Validate all webhook payload fields before processing
- [ ] Add CSRF protection for forms
- [ ] Use environment variable for database password (if switching to PostgreSQL)
- [ ] Add Content Security Policy headers
- [ ] Sanitize all user inputs (email addresses, etc.)

---

## 📝 Documentation Gaps

Still need to document:

- [ ] How to deploy to production (Docker, Railway, Render, etc.)
- [ ] How to backup and restore database
- [ ] How to migrate from SQLite to PostgreSQL
- [ ] How to add new analytics metrics
- [ ] How to troubleshoot common webhook issues
- [ ] API documentation (if exposing endpoints)

---

## 🎓 Learning Resources

### BTCPay Server
- Official Docs: https://docs.btcpayserver.org/
- API Explorer: https://docs.btcpayserver.org/API/Greenfield/v1/
- Video Tutorials: https://www.youtube.com/c/BTCPayServer

### Angor Protocol
- Website: https://angor.io/
- GitHub: https://github.com/block-core/angor
- (Need to find community Discord/Telegram)

### Nostr Protocol
- NIPs (Nostr Implementation Possibilities): https://github.com/nostr-protocol/nips
- Python Client: https://github.com/jeffthibault/python-nostr

---

## ✅ Current Status Summary

**Working:**
- ✅ FastAPI app running
- ✅ SQLite database with seeded data
- ✅ Dashboard with charts
- ✅ All 17 tests passing
- ✅ Demo mode fully functional

**Not Working:**
- ❌ No real BTCPay connection
- ❌ No real webhook testing
- ❌ No real Angor integration
- ❌ No Nostr client

**Next Action:**
🎯 **Set up BTCPay testnet account and test real API connection**

---

Copy the `PROJECT_STATUS.md` file to share with ChatGPT or other AI assistants for detailed improvement suggestions!
