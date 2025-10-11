# 🔄 Switching from Demo Mode to Real Data

## Current Problem
Your app is running in **DEMO MODE** with fake data because no BTCPay Server is configured.

## The Solution
You need to configure BTCPay Server credentials in a `.env` file.

---

## 🚀 Quick Start - Three Options

### Option 1: Run the Interactive Setup Wizard (Recommended)

```bash
# Run the setup wizard
python3 setup_btcpay.py
```

The wizard will:
- ✅ Guide you through the setup process
- ✅ Help you create API keys
- ✅ Generate secure webhook secrets
- ✅ Create your `.env` file automatically

---

### Option 2: Manual Setup (If You Already Have Credentials)

1. **Copy the example file:**
```bash
cp .env.example .env
```

2. **Edit the `.env` file:**
```bash
nano .env
# or
code .env
```

3. **Fill in your credentials:**
```env
BTCPAY_HOST=your-btcpay-server.com
BTCPAY_API_KEY=your_api_key_from_btcpay
BTCPAY_STORE_ID=your_store_id_here
BTCPAY_WEBHOOK_SECRET=create_a_random_secret_here
```

4. **Restart the app:**
```bash
pkill -f uvicorn
uvicorn app.main:app --reload
```

---

### Option 3: Use BTCPay Demo Server (For Testing)

If you don't have your own BTCPay Server, you can test with the public demo:

```bash
# Create .env file
cat > .env << 'EOF'
BTCPAY_HOST=mainnet.demo.btcpayserver.org
BTCPAY_API_KEY=YOUR_DEMO_API_KEY
BTCPAY_STORE_ID=YOUR_DEMO_STORE_ID
BTCPAY_WEBHOOK_SECRET=demo_webhook_secret_123
ANGOR_ENABLE=false
DATABASE_URL=sqlite:///./btc_crowdfund.db
EOF
```

**To get demo credentials:**
1. Go to: https://mainnet.demo.btcpayserver.org/
2. Create a test account
3. Create a store
4. Generate an API key (Account → API Keys)
5. Copy your Store ID from the URL

---

## 📋 What You Need from BTCPay Server

### 1. BTCPay Host
The domain of your BTCPay Server (without `https://`)
- Example: `mybtcpay.com`
- Or: `mainnet.demo.btcpayserver.org`

### 2. API Key
**How to create:**
1. Log into BTCPay Server
2. Go to **Account → API Keys**
3. Click **"Generate Key"**
4. Enable permissions:
   - ✅ `btcpay.store.canviewinvoices`
   - ✅ `btcpay.store.webhooks.canmodifywebhooks`
5. Click **"Generate"** and copy the key

### 3. Store ID
**How to find:**
1. Go to **Stores** in BTCPay
2. Click your store name
3. Look at the URL: `/stores/{THIS_IS_YOUR_STORE_ID}/...`
4. Or find it in **Store Settings**

### 4. Webhook Secret
A random string you create. This will be used to verify webhook authenticity.
- Generate one: `openssl rand -hex 32`
- Or use any random string (save it for webhook setup later)

---

## ✅ Verification Steps

After configuration, verify the connection:

### 1. Check the mode
```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "mode": "btcpay"  ← Should say "btcpay" not "demo"
}
```

### 2. Check the dashboard
Open http://localhost:8000

You should see:
- ✅ NO yellow "Demo Mode" banner
- ✅ Real invoices from your BTCPay store
- ✅ Actual BTC amounts

### 3. Test data refresh
Click the "🔄 Refresh Data" button on the dashboard.
It should fetch your latest invoices.

---

## 🔧 Troubleshooting

### Issue: Still in Demo Mode

**Cause:** `.env` file not found or invalid credentials

**Fix:**
```bash
# Check if .env exists
ls -la .env

# Check current config
python3 << EOF
from app.config import config
print(f"Host: {config.BTCPAY_HOST}")
print(f"Store: {config.BTCPAY_STORE_ID}")
print(f"Demo Mode: {config.is_demo_mode}")
EOF
```

### Issue: "Unauthorized" or "Invalid API Key"

**Cause:** API key is wrong or missing permissions

**Fix:**
1. Regenerate API key in BTCPay
2. Make sure these permissions are enabled:
   - `btcpay.store.canviewinvoices`
   - `btcpay.store.webhooks.canmodifywebhooks`
3. Update `.env` with new key
4. Restart app

### Issue: "Store not found"

**Cause:** Wrong Store ID

**Fix:**
1. Double-check Store ID in BTCPay URL
2. Make sure your API key has access to this store
3. Update `.env`
4. Restart app

### Issue: No invoices showing

**Cause:** Store has no invoices yet

**Fix:**
1. Create a test invoice in BTCPay
2. Click "Refresh Data" in the app
3. Or wait for webhooks to deliver (if configured)

---

## 🌐 Setting Up Webhooks (For Real-Time Updates)

Once your basic connection works, set up webhooks for real-time invoice updates:

### 1. For Production (with a domain)

In BTCPay Server:
1. Go to **Store → Webhooks**
2. Click **"Create Webhook"**
3. **URL:** `https://yourdomain.com/webhook`
4. **Secret:** (use the same value from `.env` BTCPAY_WEBHOOK_SECRET)
5. **Events:** Select:
   - InvoiceSettled
   - InvoiceExpired
   - InvoiceInvalid
6. Enable **"Automatic Redelivery"**
7. Click **"Add webhook"**

### 2. For Local Testing (with ngrok)

```bash
# Install ngrok if needed
brew install ngrok

# Start ngrok
ngrok http 8000

# Output will show:
# Forwarding   https://abc123.ngrok.io -> http://localhost:8000
```

Use the `https://abc123.ngrok.io/webhook` URL in BTCPay webhook settings.

---

## 📊 Expected Behavior After Setup

### Before (Demo Mode):
- Yellow "⚠️ Demo Mode" banner
- 30 synthetic invoices
- Fake data from seed script
- Charts show random test data

### After (Real Data):
- NO demo banner
- Real invoices from your store
- Actual BTC amounts
- Live data updates via webhooks
- "Refresh Data" fetches from BTCPay API

---

## 🎯 Quick Command Reference

```bash
# Run setup wizard
python3 setup_btcpay.py

# Manual .env creation
cp .env.example .env && nano .env

# Restart app
pkill -f uvicorn && uvicorn app.main:app --reload

# Check config
cat .env

# Test connection
curl http://localhost:8000/health

# View logs
tail -f logs/app.log  # (if logging is set up)

# Clear demo data and start fresh
rm btc_crowdfund.db
python3 -m app.main  # Will recreate tables
```

---

## ✨ Next Steps

Once connected to real BTCPay data:

1. ✅ Test invoice creation in BTCPay
2. ✅ Click "Refresh Data" to see it appear
3. ✅ Set up webhooks for real-time updates
4. ✅ Configure Angor if needed (set `ANGOR_ENABLE=true`)
5. ✅ Deploy to production (see deployment guides)

---

## 💡 Need Help?

- **BTCPay Docs:** https://docs.btcpayserver.org/
- **BTCPay Support:** https://chat.btcpayserver.org/
- **API Reference:** https://docs.btcpayserver.org/API/Greenfield/v1/
- **Check Issues:** https://github.com/matthewfarrow/btc-crowd-funding/issues

---

**Remember:** Always keep your `.env` file secret and never commit it to git!
