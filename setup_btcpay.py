#!/usr/bin/env python3
"""
BTCPay Server Setup Wizard
Interactive setup to connect your app to a real BTCPay Server
"""

import os
import sys
from pathlib import Path

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def print_step(step, text):
    print(f"\n📍 Step {step}: {text}")
    print("-" * 60)

def main():
    print_header("🚀 BTC Crowdfund Analytics - BTCPay Setup Wizard")
    
    print("""
This wizard will help you connect to a REAL BTCPay Server instance.

You have two options:
1. Use an existing BTCPay Server (your own or a hosted one)
2. Use the BTCPay Server public demo for testing

Current Status: ⚠️  DEMO MODE (using fake data)
Target Status:  ✅ CONNECTED TO REAL BTCPAY SERVER
    """)
    
    # Option selection
    print("\nSelect your option:")
    print("  1. I have my own BTCPay Server")
    print("  2. Use BTCPay public demo (mainnet.demo.btcpayserver.org)")
    print("  3. I need to create a BTCPay Server first")
    print("  0. Exit")
    
    choice = input("\nEnter choice (0-3): ").strip()
    
    if choice == "0":
        print("\n👋 Exiting setup wizard.")
        sys.exit(0)
    
    elif choice == "3":
        print_header("Creating a BTCPay Server")
        print("""
To use real data, you need access to a BTCPay Server. Here are your options:

🔹 Option A: Use a Hosted BTCPay Service
   - BTCPay Jungle: https://btcpayjungle.com/ (Free tier available)
   - Luna Node: https://www.lunanode.com/
   - Voltage: https://voltage.cloud/
   
🔹 Option B: Self-Host on VPS
   - DigitalOcean, AWS, Azure, etc.
   - Follow: https://docs.btcpayserver.org/Deployment/
   - Requires: Linux VPS, domain name, ~4GB RAM
   
🔹 Option C: Run Locally (Docker)
   - Install Docker: https://docs.docker.com/get-docker/
   - Follow: https://docs.btcpayserver.org/Docker/
   - Good for development/testing

After setting up BTCPay Server, re-run this wizard with option 1 or 2.
        """)
        sys.exit(0)
    
    # Collect credentials
    env_vars = {}
    
    if choice == "1":
        print_step(1, "Enter Your BTCPay Server Details")
        print("\nYou'll need:")
        print("  • Your BTCPay Server host/domain")
        print("  • An API key with store permissions")
        print("  • Your store ID")
        print("  • A webhook secret (you'll create this)")
        
        env_vars['BTCPAY_HOST'] = input("\n🌐 BTCPay Host (e.g., mybtcpay.com): ").strip()
        
    elif choice == "2":
        print_step(1, "Using BTCPay Public Demo")
        print("\n⚠️  NOTE: The demo server is shared and public.")
        print("   • Data is visible to others")
        print("   • Not suitable for production")
        print("   • Good for testing the integration")
        
        env_vars['BTCPAY_HOST'] = "mainnet.demo.btcpayserver.org"
        print(f"\n✓ Using host: {env_vars['BTCPAY_HOST']}")
    
    # Get API Key
    print_step(2, "Create and Enter API Key")
    print(f"""
To create an API key in BTCPay Server:

1. Log into your BTCPay Server: https://{env_vars['BTCPAY_HOST']}
2. Go to Account → API Keys
3. Click "Generate Key"
4. Enable these permissions:
   ✓ View invoices
   ✓ Create invoices (optional, for future features)
   ✓ Modify stores webhooks
5. Click "Generate" and copy the API key
    """)
    
    env_vars['BTCPAY_API_KEY'] = input("\n🔑 Paste your API Key: ").strip()
    
    if not env_vars['BTCPAY_API_KEY']:
        print("\n❌ API Key is required!")
        sys.exit(1)
    
    # Get Store ID
    print_step(3, "Enter Store ID")
    print("""
To find your Store ID:

1. In BTCPay Server, go to Stores
2. Click on your store name
3. Look at the URL - it will show: /stores/{StoreId}/...
4. Copy the Store ID from the URL

OR look at the Store Settings page - it's shown there.
    """)
    
    env_vars['BTCPAY_STORE_ID'] = input("\n🏪 Enter your Store ID: ").strip()
    
    if not env_vars['BTCPAY_STORE_ID']:
        print("\n❌ Store ID is required!")
        sys.exit(1)
    
    # Webhook Secret
    print_step(4, "Create Webhook Secret")
    print("""
The webhook secret is used to verify that webhook deliveries are
authentic and come from your BTCPay Server.
    """)
    
    default_secret = "btcpay_webhook_" + os.urandom(8).hex()
    print(f"\nSuggested secret: {default_secret}")
    
    custom = input("Use this secret? (Y/n): ").strip().lower()
    if custom == 'n':
        env_vars['BTCPAY_WEBHOOK_SECRET'] = input("Enter your custom secret: ").strip()
    else:
        env_vars['BTCPAY_WEBHOOK_SECRET'] = default_secret
    
    # Angor
    print_step(5, "Enable Angor Integration (Optional)")
    angor = input("\n📡 Enable Angor crowdfunding projects? (y/N): ").strip().lower()
    env_vars['ANGOR_ENABLE'] = 'true' if angor == 'y' else 'false'
    
    # Write .env file
    print_step(6, "Saving Configuration")
    
    env_content = f"""# BTCPay Server Configuration
BTCPAY_HOST={env_vars['BTCPAY_HOST']}
BTCPAY_API_KEY={env_vars['BTCPAY_API_KEY']}
BTCPAY_STORE_ID={env_vars['BTCPAY_STORE_ID']}
BTCPAY_WEBHOOK_SECRET={env_vars['BTCPAY_WEBHOOK_SECRET']}

# Angor Configuration
ANGOR_ENABLE={env_vars['ANGOR_ENABLE']}

# Application Configuration
DATABASE_URL=sqlite:///./btc_crowdfund.db
"""
    
    env_path = Path(__file__).parent.parent / '.env'
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"\n✅ Configuration saved to: {env_path}")
    
    # Summary
    print_header("✅ Setup Complete!")
    print(f"""
Your configuration:

  Host:     {env_vars['BTCPAY_HOST']}
  Store ID: {env_vars['BTCPAY_STORE_ID']}
  API Key:  {env_vars['BTCPAY_API_KEY'][:10]}...{env_vars['BTCPAY_API_KEY'][-4:]}
  Webhook:  {env_vars['BTCPAY_WEBHOOK_SECRET'][:10]}...
  Angor:    {'Enabled' if env_vars['ANGOR_ENABLE'] == 'true' else 'Disabled'}

Next steps:

1. Restart your application:
   $ pkill -f uvicorn
   $ uvicorn app.main:app --reload

2. The app will automatically:
   ✓ Detect BTCPay configuration
   ✓ Exit demo mode
   ✓ Fetch real invoices from your store

3. Set up webhooks in BTCPay:
   • Go to your Store → Webhooks
   • Click "Create Webhook"
   • URL: https://your-domain.com/webhook
   • Secret: {env_vars['BTCPAY_WEBHOOK_SECRET']}
   • Events: InvoiceSettled, InvoiceExpired, InvoiceInvalid

4. For local testing, use ngrok:
   $ ngrok http 8000
   Then use the ngrok URL in BTCPay webhook settings

🎉 Your app is now connected to REAL BTCPay data!
    """)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
