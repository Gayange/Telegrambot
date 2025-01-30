import asyncio
import sqlite3
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Replace with your Telegram Bot API token and Google Maps API key
TELEGRAM_API_TOKEN = ""
GOOGLE_MAPS_API_KEY = ""

# Initialize database
def init_db():
    conn = sqlite3.connect("driver_bot.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            details TEXT,
            latitude REAL,
            longitude REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()

# Save a report to the database
def save_report(report_type, details, latitude, longitude):
    conn = sqlite3.connect("driver_bot.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reports (type, details, latitude, longitude) VALUES (?, ?, ?, ?)",
        (report_type, details, latitude, longitude),
    )
    conn.commit()
    conn.close()

# Handle location messages and update map
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    location = update.message.location
    if location:
        latitude = location.latitude
        longitude = location.longitude

        command = context.user_data.get("command", "")
        if command == "roadblock":
            save_report("roadblock", "User-reported roadblock", latitude, longitude)
            await update.message.reply_text(
                f"Roadblock reported at Latitude: {latitude}, Longitude: {longitude}."
            )
        elif command == "hazard":
            save_report("hazard", "User-reported hazard", latitude, longitude)
            await update.message.reply_text(
                f"Hazard reported at Latitude: {latitude}, Longitude: {longitude}."
            )
        elif command == "traffic":
            # Fetch nearby hazards and update map
            await update_traffic_map(update, latitude, longitude)
        else:
            await update.message.reply_text("Location received. Thank you!")

# Fetch and update traffic data on the map
async def update_traffic_map(update: Update, latitude, longitude):
    # Fetch nearby hazards
    nearby_hazards = fetch_nearby_hazards(latitude, longitude)
    if nearby_hazards:
        # Prepare map URL with hazards as markers
        markers = "&".join(
            f"markers=label:{hazard['type'][0]}|{hazard['latitude']},{hazard['longitude']}"
            for hazard in nearby_hazards
        )
        map_url = f"https://maps.googleapis.com/maps/api/staticmap?size=600x400&{markers}&key={GOOGLE_MAPS_API_KEY}"
        await update.message.reply_photo(photo=map_url)
    else:
        await update.message.reply_text("No nearby hazards reported. Drive safely!")

# Fetch nearby hazards from the database
def fetch_nearby_hazards(latitude, longitude):
    conn = sqlite3.connect("driver_bot.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT type, details, latitude, longitude FROM reports
        WHERE ABS(latitude - ?) < 0.01 AND ABS(longitude - ?) < 0.01
        """,
        (latitude, longitude),
    )
    hazards = cursor.fetchall()
    conn.close()
    return [{"type": row[0], "details": row[1], "latitude": row[2], "longitude": row[3]} for row in hazards]

# Bot commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Welcome to the Driver Assistant Bot! 🚗\nUse /help to see available commands.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Here are the commands you can use:\n"
        "/start - Start the bot\n"
        "/help - Show help message\n"
        "/roadblock - Report a roadblock\n"
        "/hazard - Report a hazard\n"
        "/traffic - Get traffic updates"
    )

async def roadblock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["command"] = "roadblock"
    await request_location(update, "Please share your location to report the roadblock.")

async def hazard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["command"] = "hazard"
    await request_location(update, "Please share your location to report the hazard.")

async def traffic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["command"] = "traffic"
    await request_location(update, "Please share your location to get real-time traffic updates.")

# Request location
async def request_location(update: Update, message: str) -> None:
    keyboard = [[KeyboardButton("Share Location", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(message, reply_markup=reply_markup)

# Main function
def main():
    init_db()
    application = Application.builder().token(TELEGRAM_API_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("roadblock", roadblock))
    application.add_handler(CommandHandler("hazard", hazard))
    application.add_handler(CommandHandler("traffic", traffic))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))

    print("Driver Assistant Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()



# # Replace with your Telegram Bot API token
# TELEGRAM_API_TOKEN = "7881186442:AAFbez8X46jalBjiFe_nz-UDFa6ePQFYi00"

# # Replace with your Google Maps API key
# GOOGLE_MAPS_API_KEY = "AIzaSyAtXPDlFXzZTuarUgQPX-SOMD8wbQve5CM"
