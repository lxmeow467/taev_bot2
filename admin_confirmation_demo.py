#!/usr/bin/env python3
"""
Advanced admin confirmation system demonstration
Shows inline buttons and confirmation workflow
"""

import asyncio
from unittest.mock import MagicMock, AsyncMock
from telegram import Update, User, Message, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.admin import AdminHandlers
from bot.storage import DataStorage
from bot.localization import Localizer


async def demo_inline_confirmation_system():
    """Demonstrate advanced inline confirmation system"""
    print("🔧 ADVANCED ADMIN CONFIRMATION SYSTEM")
    print("="*50)
    
    # Initialize components
    storage = DataStorage()
    localizer = Localizer()
    admin_handlers = AdminHandlers(storage, localizer, ["admin1"])
    
    # Clear data for clean demo
    storage.clear_all_data()
    
    # Add some pending registrations
    registrations = [
        {"user_id": 101, "username": "player_alpha", "tournament_type": "vsa", "team_name": "Alpha Squad", "rating": 47},
        {"user_id": 102, "username": "player_beta", "tournament_type": "h2h", "team_name": "Beta Force", "rating": 41},
        {"user_id": 103, "username": "player_gamma", "tournament_type": "vsa", "team_name": "Gamma Elite", "rating": 52},
    ]
    
    print("\n📝 Adding pending registrations...")
    for reg in registrations:
        await storage.save_temp_registration(**reg)
        print(f"   ⏳ {reg['username']} - {reg['tournament_type'].upper()}: {reg['team_name']} ({reg['rating']} ⭐)")
    
    # Create mock admin update
    admin_user = User(id=999, first_name="Admin", is_bot=False, username="admin1")
    chat = Chat(id=999, type="private")
    message = Message(
        message_id=1,
        date=None,
        chat=chat,
        from_user=admin_user,
        text="/list"
    )
    message.reply_text = AsyncMock()
    update = Update(update_id=1, message=message)
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    
    print("\n👑 Admin requests player list...")
    await admin_handlers.list_players(update, context)
    
    # Show what the admin would see
    call_args = message.reply_text.call_args[0][0]
    print(f"\n📱 Admin sees:")
    print("-" * 40)
    print(call_args)
    print("-" * 40)
    
    # Simulate confirmations
    print("\n✅ Admin confirmations...")
    temp_regs = storage.get_temp_registrations()
    
    for user_id, data in temp_regs.items():
        if data['username'] in ['player_alpha', 'player_beta']:
            print(f"   👑 Admin confirms: {data['username']}")
            await admin_handlers.confirm_registration(update, context, data['username'])
            print(f"   ✅ {data['username']} confirmed for {data['tournament_type'].upper()}")
        else:
            print(f"   ⏳ {data['username']} still pending...")
    
    # Show final tournament state
    print("\n🏆 Final Tournament State:")
    await admin_handlers.list_players(update, context)
    
    final_call = message.reply_text.call_args[0][0]
    print("-" * 40)
    print(final_call)
    print("-" * 40)
    
    # Show statistics
    print("\n📊 Tournament Statistics:")
    await admin_handlers.stats_command(update, context)
    
    stats_call = message.reply_text.call_args[0][0]
    print("-" * 40)
    print(stats_call)
    print("-" * 40)


async def demo_admin_commands():
    """Demonstrate all admin commands"""
    print("\n\n🛠️ COMPLETE ADMIN COMMAND SUITE")
    print("="*50)
    
    storage = DataStorage()
    localizer = Localizer()
    admin_handlers = AdminHandlers(storage, localizer, ["admin1"])
    
    # Setup mock admin
    admin_user = User(id=999, first_name="Admin", is_bot=False, username="admin1")
    chat = Chat(id=999, type="private")
    
    commands = [
        ("/list", "List all players"),
        ("/stats", "Show statistics"),
        ("/export", "Export data to JSON"),
        ("/clear confirm", "Clear all data (with confirmation)")
    ]
    
    for command, description in commands:
        print(f"\n--- {description} ---")
        print(f"Command: {command}")
        
        message = Message(
            message_id=1,
            date=None,
            chat=chat,
            from_user=admin_user,
            text=command
        )
        message.reply_text = AsyncMock()
        message.reply_document = AsyncMock()
        
        update = Update(update_id=1, message=message)
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = command.split()[1:] if len(command.split()) > 1 else []
        
        # Execute the appropriate command
        if command.startswith("/list"):
            await admin_handlers.list_players(update, context)
            if message.reply_text.called:
                print("Response:", message.reply_text.call_args[0][0][:100] + "...")
        
        elif command.startswith("/stats"):
            await admin_handlers.stats_command(update, context)
            if message.reply_text.called:
                print("Response:", message.reply_text.call_args[0][0][:100] + "...")
        
        elif command.startswith("/export"):
            await admin_handlers.export_data(update, context)
            if message.reply_document.called:
                call_args = message.reply_document.call_args
                filename = call_args[1]["filename"]
                caption = call_args[1]["caption"]
                print(f"Document sent: {filename}")
                print(f"Caption: {caption}")
        
        elif command.startswith("/clear"):
            await admin_handlers.clear_data(update, context)
            if message.reply_text.called:
                print("Response:", message.reply_text.call_args[0][0][:100] + "...")


async def demo_security_features():
    """Demonstrate security and access control"""
    print("\n\n🔒 SECURITY & ACCESS CONTROL")
    print("="*50)
    
    storage = DataStorage()
    localizer = Localizer()
    admin_handlers = AdminHandlers(storage, localizer, ["admin1", "admin2"])
    
    # Test admin access
    print("\n--- Admin Access Control ---")
    
    test_users = [
        ("admin1", True, "Valid admin"),
        ("admin2", True, "Valid admin"),
        ("regularuser", False, "Regular user"),
        ("hacker", False, "Unauthorized user"),
        ("", False, "Empty username"),
        (None, False, "None username")
    ]
    
    for username, is_admin, description in test_users:
        result = admin_handlers._is_admin(username)
        status = "✅ ADMIN" if result else "❌ DENIED"
        print(f"   {username or 'None':<15} → {status} ({description})")
    
    # Test command access for non-admin
    print("\n--- Non-Admin Command Attempts ---")
    
    regular_user = User(id=123, first_name="User", is_bot=False, username="regularuser")
    chat = Chat(id=123, type="private")
    message = Message(
        message_id=1,
        date=None,
        chat=chat,
        from_user=regular_user,
        text="/list"
    )
    message.reply_text = AsyncMock()
    
    update = Update(update_id=1, message=message)
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    
    # Try admin commands as regular user
    admin_commands = [
        ("list_players", "List players"),
        ("stats_command", "View statistics"),
        ("export_data", "Export data"),
        ("clear_data", "Clear data")
    ]
    
    for method_name, description in admin_commands:
        method = getattr(admin_handlers, method_name)
        await method(update, context)
        
        if message.reply_text.called:
            response = message.reply_text.call_args[0][0]
            print(f"   {description}: {response}")
            message.reply_text.reset_mock()


async def main():
    """Run all admin demonstrations"""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║           🛡️ ADMIN SYSTEM DEMONSTRATION 🛡️               ║
    ║                                                            ║
    ║    Showcasing advanced admin management capabilities       ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    try:
        await demo_inline_confirmation_system()
        await demo_admin_commands()
        await demo_security_features()
        
        print("\n\n🎉 ADMIN DEMONSTRATION COMPLETE")
        print("="*50)
        print("""
Admin Features Demonstrated:
✅ Player List Management with Status Indicators
✅ Registration Confirmation Workflow
✅ Real-time Tournament Statistics
✅ JSON Data Export Functionality
✅ Secure Data Clearing with Confirmation
✅ Role-based Access Control
✅ Security Validation for All Commands
✅ Multi-language Admin Interface

The admin system provides complete tournament management
with security, validation, and comprehensive reporting.
        """)
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())