# BTC Crowdfund Analytics

A weekend MVP for Bitcoin crowdfunding analytics. Displays dashboard analytics from BTCPay Server invoices with Angor project support and demo fallback.

## 🚀 Features

- **BTCPay Server Integration**: Fetch and cache invoices via Greenfield API
- **Webhook Support**: Receive real-time invoice updates with HMAC-SHA256 verification
- **Analytics Dashboard**: KPI cards, time-series charts, and status distribution
- **Angor Adapter**: View decentralized crowdfunding projects with demo fallback
- **Demo Mode**: Runs with synthetic data when BTCPay is not configured
- **SQLite Caching**: Fast local persistence with SQLModel
- **Server-Rendered**: Clean Jinja2 templates with Chart.js visualizations

## 📋 Tech Stack

- **Python 3.11**
- **FastAPI** - Web framework
- **SQLModel** - SQLite ORM
- **Jinja2** - Server-side templates
- **Chart.js** - Interactive charts
- **httpx** - HTTP client
- **pytest** - Unit tests

## 🏗️ Project Structure

```
btc-crowd-funding/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app setup
│   ├── config.py            # Environment configuration
│   ├── models.py            # SQLModel database schemas
│   ├── btcpay_client.py     # BTCPay Greenfield API wrapper
│   ├── webhook.py           # Webhook handler with HMAC verification
│   ├── repo.py              # Database CRUD operations
│   ├── analytics.py         # Aggregation and analytics functions
│   ├── angor_adapter.py     # Angor integration with demo fallback
│   ├── views.py             # Web routes and controllers
│   └── seed_demo.py         # Demo data seeder
├── templates/
│   ├── base.html            # Base template
│   ├── index.html           # Dashboard page
│   ├── settings.html        # Settings page
│   └── logs.html            # Webhook logs page
├── static/
│   └── style.css            # Application styles
├── data/
│   └── angor_demo.json      # Demo Angor projects
├── tests/
│   └── test_app.py          # Unit tests
├── requirements.txt
├── Makefile
├── .env.example
└── README.md
```

## 🔧 Installation

### Step 1: Clone and Setup Virtual Environment

```bash
cd btc-crowd-funding

# Create virtual environment (use python3 on macOS)
python3 -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your BTCPay Server credentials:

```env
BTCPAY_HOST=mainnet.demo.btcpayserver.org
BTCPAY_API_KEY=your_api_key_here
BTCPAY_STORE_ID=your_store_id_here
BTCPAY_WEBHOOK_SECRET=your_webhook_secret_here
ANGOR_ENABLE=false
```

**Note**: If you don't configure BTCPay, the app runs in demo mode automatically.

### Step 3: Seed Demo Data (Optional)

If running in demo mode, seed synthetic invoices:

```bash
python3 -m app.seed_demo
```

This creates 30 sample invoices over the last 14 days.

### Step 4: Run the Application

```bash
# Development server with auto-reload
uvicorn app.main:app --reload

# Or use the Makefile
make run
```

Open your browser to: **http://localhost:8000**

## 📊 Usage

### Dashboard

- View KPI cards: Total raised, invoice count, average contribution, status distribution
- Interactive charts: Daily raised (line chart) and status distribution (doughnut)
- Toggle between BTCPay invoices and Angor projects (if enabled)
- Click **Refresh Data** to fetch latest invoices from BTCPay

### Settings

- View current BTCPay configuration (masked API keys)
- See connection status (Demo Mode vs Connected)
- Find webhook URL for BTCPay store configuration

### Webhook Logs

- View recent webhook deliveries
- Check signature verification status
- Inspect event types and timestamps

## 🔐 BTCPay Server Setup

### Creating an API Key

1. Log in to your BTCPay Server instance
2. Go to **Account Settings** → **API Keys**
3. Click **Generate Key**
4. Select permissions: `btcpay.store.canviewinvoices`, `btcpay.store.webhooks.canmodifywebhooks`
5. Copy the generated API key to your `.env` file

### Configuring Webhooks

1. In BTCPay Server, go to your **Store Settings** → **Webhooks**
2. Click **Create Webhook**
3. Set the webhook URL: `https://your-domain.com/webhook`
4. Set the secret (must match `BTCPAY_WEBHOOK_SECRET` in `.env`)
5. Enable events: `InvoiceSettled`, `InvoiceExpired`, `InvoiceInvalid`
6. Enable automatic redelivery (optional but recommended)

**For local testing**, use ngrok to expose your local server:

```bash
ngrok http 8000
```

Then use the ngrok URL in your BTCPay webhook configuration.

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest -v

# Or use Makefile
make test
```

### Test Coverage

The test suite includes:

- ✅ Webhook signature verification (HMAC-SHA256)
- ✅ Invoice status mapping
- ✅ Timestamp parsing with multiple formats
- ✅ Analytics aggregation functions
- ✅ Daily bucketing for time-series
- ✅ BTCPay API header construction

## 🔗 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard page |
| `/refresh` | POST | Refresh invoice data from BTCPay |
| `/settings` | GET | Settings and configuration page |
| `/logs` | GET | Webhook delivery logs |
| `/webhook` | POST | BTCPay webhook receiver |
| `/health` | GET | Health check (returns JSON) |

## 🎬 Three-Minute Demo Script

### 1. Show Settings (30 seconds)

1. Navigate to **Settings** page
2. Point out the masked API key showing last 4 characters
3. Note the connection status (Demo or Connected)
4. Explain the webhook URL configuration

### 2. Dashboard Overview (1 minute)

1. Return to **Dashboard**
2. Walk through the KPI cards:
   - Total BTC raised
   - Number of invoices
   - Average contribution
   - Status breakdown (Paid/Expired/Pending)
3. Highlight the two charts:
   - Daily raised over last 30 days (line chart)
   - Status distribution (doughnut chart)

### 3. Refresh Data (30 seconds)

1. Click the **Refresh Data** button
2. Show the page reload with updated data
3. Explain that this fetches the latest invoices from BTCPay

### 4. Webhook Logs (1 minute)

1. Navigate to **Webhook Logs**
2. Show recent webhook deliveries
3. Point out:
   - Timestamp of delivery
   - Event type (InvoiceSettled, InvoiceExpired, etc.)
   - Verification status (✓ Verified or ✗ Failed)
   - Signature preview

### 5. Live Demo (optional, if time)

1. Create a test invoice in BTCPay Server (small amount like 1 cent)
2. Pay the invoice using testnet or Lightning
3. Return to the dashboard - show the new entry in logs
4. Refresh dashboard to see the KPI and charts update

## 🧩 Testing Webhooks Manually

Simulate a webhook delivery with curl:

```bash
# Compute HMAC signature
SECRET="your_webhook_secret_here"
PAYLOAD='{"type":"InvoiceSettled","invoiceId":"test123","storeId":"mystore","price":"10.00","currency":"USD","cryptoPrice":"0.00015","createdTime":"2024-10-11T12:00:00Z","paidTime":"2024-10-11T12:05:00Z"}'

# On macOS/Linux
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')

# Send webhook
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -H "BTCPay-Sig: $SIGNATURE" \
  -d "$PAYLOAD"
```

You should see the webhook logged in `/logs` with "✓ Verified" status.

## 🛠️ Makefile Commands

```bash
make install    # Create venv and install dependencies
make run        # Run development server
make test       # Run pytest test suite
make seed       # Seed demo data
make clean      # Remove venv and database
```

## 🌐 Angor Integration

If you enable Angor support (`ANGOR_ENABLE=true` in `.env`), you can toggle to view Angor crowdfunding projects.

The adapter uses a three-tier strategy:

1. **Demo data**: Loads from `data/angor_demo.json`
2. **Angor Hub API**: Attempts to fetch from `hub.angor.io` (optional)
3. **Fallback**: Returns demo data if API unavailable

## 🚦 Architecture Notes

### Demo Mode

When `BTCPAY_HOST` or `BTCPAY_STORE_ID` are not configured, the app runs in demo mode:

- A yellow banner appears at the top
- Dashboard shows synthetic invoice data
- All features work normally for testing

### Database Schema

**Invoice Table**:
- `id` (primary key): Invoice ID from BTCPay
- `store_id`: BTCPay store ID
- `status`: Settled, Expired, Invalid, New, Processing
- `amount`: Fiat amount
- `amount_btc`: Bitcoin amount
- `created_at`, `paid_at`: Timestamps
- `payer_email`: Optional buyer email
- `metadata`: JSON metadata as text

**EventLog Table**:
- `id` (auto-increment primary key)
- `received_at`: Webhook delivery timestamp
- `signature`: BTCPay-Sig header value
- `verified`: Boolean verification result
- `event_type`: InvoiceSettled, InvoiceExpired, etc.
- `payload`: Full JSON payload as text

**SourceProject Table**:
- `id` (primary key): Project ID
- `title`: Project name
- `amount_target`: Funding goal in BTC
- `amount_raised`: Amount raised in BTC
- `created_at`: Project creation date
- `source`: "angor" or "demo"

### Security

- **HMAC Verification**: All webhooks are verified using HMAC-SHA256 with constant-time comparison
- **Secrets Management**: API keys and secrets loaded from `.env` (not committed)
- **Input Validation**: FastAPI handles request validation
- **SQL Injection**: SQLModel ORM prevents SQL injection

## 🐛 Troubleshooting

### Import errors when running

Make sure you've activated the virtual environment:

```bash
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

### Database locked errors

Only one process should access the SQLite database at a time. Stop any running instances.

### Webhook signature verification fails

1. Ensure `BTCPAY_WEBHOOK_SECRET` matches the secret in BTCPay webhook settings
2. Check that the webhook is sending the `BTCPay-Sig` header
3. Verify the payload is sent as raw JSON (not form-encoded)

### Charts not rendering

1. Check browser console for JavaScript errors
2. Ensure Chart.js CDN is accessible
3. Verify data is being passed to templates correctly

## 📝 Future Enhancements

- [ ] Add user authentication
- [ ] Support multiple BTCPay stores
- [ ] Export data to CSV/JSON
- [ ] Email notifications for settled invoices
- [ ] Advanced filtering and search
- [ ] Historical trend analysis
- [ ] Nostr integration for Angor metadata
- [ ] Docker containerization
- [ ] PostgreSQL support for production

## 📄 License

MIT License - feel free to use for your weekend hackathon!

## 🤝 Contributing

This is a weekend MVP built for clarity and speed. Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📚 References

- [BTCPay Server Greenfield API](https://docs.btcpayserver.org/API/Greenfield/v1/)
- [BTCPay Server Webhooks](https://docs.btcpayserver.org/Zapier/)
- [Angor Protocol](https://angor.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Chart.js Documentation](https://www.chartjs.org/)

## 📋 Project Documentation

For detailed technical information and integration guidance:

- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Complete status report with what's working, what's not, and critical gaps
- **[INTEGRATION_CHECKLIST.md](INTEGRATION_CHECKLIST.md)** - Step-by-step checklist for integrating real BTCPay and Angor
- **[QUESTIONS_FOR_CHATGPT.md](QUESTIONS_FOR_CHATGPT.md)** - Specific questions to ask AI assistants for improvement advice
- **[ARCHITECTURE.txt](ARCHITECTURE.txt)** - Visual system architecture diagram showing all components

**Current Status:** ✅ MVP complete in demo mode | ❌ No real service integration yet

---

**Built with ₿ by the Bitcoin community** 🚀
