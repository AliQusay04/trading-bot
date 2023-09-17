import discord
from discord.ext import commands
import requests
import math
from binance.um_futures import UMFutures
import os 
from dotenv import find_dotenv, load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

key = os.getenv("KEY")
secret = os.getenv("SECRET")
bot_token = os.getenv("BOT_TOKEN")

print(key)
print(secret)
print(bot_token)

um_futures_client = UMFutures(base_url="https://testnet.binancefuture.com", key=key, secret=secret)

def get_country_info(country_name):
    url = f"https://restcountries.com/v3.1/name/{country_name}"
    response = requests.get(url)
    return response.json()[0] if response.status_code == 200 else None

async def place_order(order_type, coin_name, message):
    symbol = coin_name + "USDT"

    try:
        price_url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(price_url)
        response.raise_for_status()

        price = float(response.json()["price"])

        exchange_info = um_futures_client.exchange_info()
        symbol_info = next(info for info in exchange_info["symbols"] if info["symbol"] == symbol)
        min_quantity_increment = float(symbol_info["filters"][2]["minQty"])
        precision = int(abs(math.log10(min_quantity_increment)))

        account_balance = um_futures_client.account()
        quantity = round(float(account_balance['totalWalletBalance']) * 0.01, precision)
        quantity2 = quantity / price

        um_futures_client.new_order(
            symbol=symbol,
            side=order_type,
            type="MARKET",
            quantity=round(quantity2, precision),
        )

        await message.channel.send(f"Successfully placed a trade to {order_type} {round(quantity2)} {symbol} at {price} BTC.")

    except Exception as error:
        await message.channel.send(f"Failed to place {order_type} order: {error}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.event
async def on_message(message):
    coin_name = message.content[5:].strip()

    if message.author == bot.user:
        return

    if message.content.startswith('!buy'):
        await place_order("BUY", coin_name, message)

    elif message.content.startswith('!sell'):
        await place_order("SELL", coin_name, message)

    elif message.content.startswith('!country'):
        country_name = message.content[9:].strip()

        country_info = get_country_info(country_name)

        if country_info:
            response = f"Country Information for {country_name}\n"
            response += f"Name: {country_info.get('name', 'N/A')}\n"
            response += f"Population: {country_info.get('population', 'N/A')}\n"
            response += f"Region: {country_info.get('region', 'N/A')}\n"
            response += f"Capital: {country_info.get('capital', 'N/A')}\n"

            await message.channel.send(response)
        else:
            await message.channel.send(f"Sorry, I couldn't find information for {country_name}.")

bot.run(bot_token)