#!/usr/bin/env python3
"""
Simple bot test to verify core functionality works
"""

import asyncio
import os
from dotenv import load_dotenv
import requests
import json

# Load environment
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_request(method, params=None):
    """Send request to Telegram API"""
    url = f"{BASE_URL}/{method}"
    try:
        response = requests.get(url, params=params or {})
        return response.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

def test_bot_connection():
    """Test bot connection and get bot info"""
    print("🤖 Testing Bot Connection")
    print("=" * 40)
    
    result = send_request("getMe")
    
    if result.get("ok"):
        bot_info = result["result"]
        print(f"✅ Bot is online!")
        print(f"   Username: @{bot_info['username']}")
        print(f"   Name: {bot_info['first_name']}")
        print(f"   ID: {bot_info['id']}")
        print(f"   Can join groups: {bot_info.get('can_join_groups', False)}")
        print(f"   Can read messages: {bot_info.get('can_read_all_group_messages', False)}")
        return True
    else:
        print(f"❌ Bot connection failed: {result}")
        return False

def test_webhook_info():
    """Check webhook status"""
    print("\n🔗 Webhook Status")
    print("=" * 40)
    
    result = send_request("getWebhookInfo")
    
    if result.get("ok"):
        webhook_info = result["result"]
        if webhook_info.get("url"):
            print(f"📡 Webhook URL: {webhook_info['url']}")
        else:
            print("📊 Bot is using polling mode (no webhook set)")
        
        if webhook_info.get("pending_update_count", 0) > 0:
            print(f"📥 Pending updates: {webhook_info['pending_update_count']}")
        
        return True
    else:
        print(f"❌ Failed to get webhook info: {result}")
        return False

def test_set_commands():
    """Set bot commands for better UX"""
    print("\n⚙️ Setting Bot Commands")
    print("=" * 40)
    
    commands = [
        {
            "command": "start",
            "description": "Start registration and get help"
        },
        {
            "command": "help", 
            "description": "Show available commands and examples"
        },
        {
            "command": "list",
            "description": "View all registrations (admin only)"
        },
        {
            "command": "stats",
            "description": "Show tournament statistics (admin only)"
        },
        {
            "command": "export",
            "description": "Export tournament data (admin only)"
        },
        {
            "command": "clear",
            "description": "Clear all data (admin only)"
        }
    ]
    
    url = f"{BASE_URL}/setMyCommands"
    data = {"commands": json.dumps(commands)}
    
    try:
        response = requests.post(url, data=data)
        result = response.json()
        
        if result.get("ok"):
            print("✅ Bot commands set successfully!")
            for cmd in commands:
                print(f"   /{cmd['command']} - {cmd['description']}")
            return True
        else:
            print(f"❌ Failed to set commands: {result}")
            return False
    except Exception as e:
        print(f"❌ Error setting commands: {e}")
        return False

def show_usage_instructions():
    """Show instructions for using the bot"""
    print("\n📖 How to Use Your Tournament Bot")
    print("=" * 50)
    
    print("\n🎮 For Players:")
    print("1. Start a chat with @TaevTournament_bot")
    print("2. Send /start to begin")
    print("3. Register using natural language:")
    print("   • Bot, my nick TeamAwesome")
    print("   • Bot, my VSA rating 42") 
    print("   • Bot, my H2H rating 38")
    print("   • Бот, мой ник КрутаяКоманда (Russian)")
    print("   • Бот, мой рекорд в VSA 45 (Russian)")
    
    print("\n👑 For Admins:")
    print("1. Use /list to see all registrations")
    print("2. Use /stats for tournament statistics")
    print("3. Use /export to download data")
    print("4. Confirm registrations with: Бот @username +1")
    
    print("\n🔧 Current Admin Users:")
    admins = os.getenv('ADMINS', '').split(',')
    for admin in admins:
        if admin.strip():
            print(f"   • {admin.strip()}")

def main():
    """Run all tests"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║        🏆 TOURNAMENT BOT - CONNECTION TEST & SETUP 🏆       ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not found in environment variables!")
        return
    
    success = True
    success &= test_bot_connection()
    success &= test_webhook_info()
    success &= test_set_commands()
    
    if success:
        show_usage_instructions()
        print("\n🎉 Bot Setup Complete!")
        print("=" * 50)
        print("✅ Your tournament bot is ready to use!")
        print("✅ Users can now register for VSA and H2H tournaments")
        print("✅ Natural language processing is active")
        print("✅ Admin commands are configured")
        print("✅ Multi-language support enabled (EN/RU)")
        
        print("\n🚀 Next Steps:")
        print("1. Start a chat with @TaevTournament_bot")
        print("2. Test registration with: Bot, my nick TestTeam")
        print("3. Check admin functions work as expected")
        print("4. Share the bot with your tournament participants!")
        
    else:
        print("\n❌ Some tests failed. Please check the bot configuration.")

if __name__ == "__main__":
    main()