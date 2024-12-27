import asyncio
import requests
from ZAminofix import Client, SubClient
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import time

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = '6759901283:AAFwuOvI_bsHsxdz5oV4D6sxVi77qVCzTXQ'

# Amino Credentials
EMAIL = "qgayqtg17q7wh@rowdydow.com"
PASSWORD = "@whenwedie"

# Conversation States
PROFILE, CHOICE = range(2)

def send_to_telegram(chat_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("Message sent to Telegram successfully.")
        else:
            print(f"Failed to send message to Telegram. Status Code: {response.status_code}")
            print(f"Response Content: {response.text}")
    except Exception as e:
        print(f"An error occurred while sending message to Telegram: {e}")

def get_banned_profiles(profile_link, check_following=True):
    client = Client()
    
    try:
        client.login(email=EMAIL, password=PASSWORD)
        print("Logged in successfully")
        
        group_info = client.get_from_code(profile_link)
        rcommunity_id = group_info.path[1:group_info.path.index('/')]
        subclient = SubClient(comId=rcommunity_id)
        
        post_code = profile_link.split("/p/")[-1]
        user_info = client.get_from_code(post_code)
        user_id = user_info.objectId
        
        if check_following:
            users = subclient.get_user_following(userId=user_id, start=0, size=100)
            user_type = "following"
        else:
            users = subclient.get_user_followers(userId=user_id, start=0, size=100)
            user_type = "followers"

        banned_profiles = []
        if hasattr(users, 'json') and isinstance(users.json, list):
            for user in users.json:
                if user.get('nickname', '') == '-' or not user.get('nickname', '').strip():
                    try:
                        user_detail = client.get_from_id(user.get('uid', ''), objectType=0, comId=rcommunity_id)
                        short_url = user_detail.shortUrl
                        if "aminoapps.com/p/" in short_url:
                            short_url = short_url.split("aminoapps.com/p/")[-1]
                            banned_profiles.append({
                                "nickname": "-",
                                "profile_link": f"http://aminoapps.com/p/{short_url}"
                            })
                            print(f"Found banned {user_type} profile: {short_url}")
                        time.sleep(1)
                    except Exception as e:
                        print(f"Error processing banned user: {str(e)}")
            return banned_profiles
        else:
            print(f"No valid JSON data found in {user_type}.")
            return None

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

# Telegram Bot Conversation Handlers
def start(update: Update, context):
    update.message.reply_text("Welcome! Send me the user profile link.")
    return PROFILE

def get_profile_link(update: Update, context):
    context.user_data['profile_link'] = update.message.text
    update.message.reply_text("Choose 1 for followings or 2 for followers.")
    return CHOICE

def get_choice(update: Update, context):
    choice = update.message.text
    profile_link = context.user_data.get('profile_link')
    
    if choice not in ['1', '2']:
        update.message.reply_text("Invalid choice. Please send 1 or 2.")
        return CHOICE
    
    check_following = choice == '1'
    user_type = "Following" if check_following else "Followers"

    try:
        banned_profiles = get_banned_profiles(profile_link, check_following)
        if banned_profiles:
            message = f"<b>Banned {user_type} Profiles:</b>\n"
            for profile in banned_profiles:
                message += f"{profile['nickname']}: {profile['profile_link']}\n"
            update.message.reply_text(message, parse_mode='HTML')
        else:
            update.message.reply_text(f"No banned {user_type.lower()} profiles found.")
    
    except Exception as e:
        update.message.reply_text(f"An error occurred: {str(e)}")
    
    return ConversationHandler.END

def cancel(update: Update, context):
    update.message.reply_text("Cancelled.")
    return ConversationHandler.END

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PROFILE: [MessageHandler(Filters.text & ~Filters.command, get_profile_link)],
            CHOICE: [MessageHandler(Filters.text & ~Filters.command, get_choice)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if _name_ == '_main_':
    main()
