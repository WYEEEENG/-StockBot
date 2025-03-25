import twstock
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib
import datetime
import os

# ✅ 使用英文字體避免亂碼
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False

def get_taiwan_stock(stock_id):
    try:
        stock = twstock.realtime.get(stock_id)
        if stock['success']:
            name = stock['info']['name']
            price = stock['realtime']['latest_trade_price']
            volume = stock['realtime']['accumulate_trade_volume']
            return f"{stock_id} {name}\nPrice: {price} NTD\nVolume: {volume} shares"
        else:
            return f"{stock_id} failed to load data"
    except Exception as e:
        print(f"❌ Taiwan stock error: {e}")
        return f"{stock_id} query error"

def get_us_stock(symbol):
    try:
        stock = yf.Ticker(symbol)
        price = stock.info.get('regularMarketPrice')
        volume = stock.info.get('volume')
        return f"{symbol}\nPrice: ${price}\nVolume: {volume}"
    except Exception as e:
        print(f"❌ US stock error: {e}")
        return f"{symbol} query error"

def draw_stock_chart(symbol):
    try:
        print(f"▶️ Drawing chart: {symbol}")
        is_tw = symbol.isdigit()
        plt.figure(figsize=(10, 5))
        today = datetime.date.today()

        dates = []
        prices = []

        if is_tw:
            print(f"🔍 Fetching TW stock history: {symbol}")
            stock = twstock.Stock(symbol)
            hist = stock.fetch_from(today.year - 1, today.month)
            last_30 = hist[-30:]
            for d in last_30:
                dates.append(d.date.strftime("%m/%d"))
                prices.append(d.close)
        else:
            print(f"🔍 Fetching US stock history: {symbol}")
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1mo")
            if hist.empty:
                print(f"❌ {symbol} no history data")
                return None
            dates = hist.index.strftime("%m/%d").tolist()
            prices = hist["Close"].tolist()

        if not prices or len(prices) == 0:
            print(f"❌ {symbol} has no prices, can't draw chart")
            return None

        plt.plot(dates, prices, marker='o')
        plt.title(f"{symbol} Price Trend (Last 30 Days)")
        plt.xlabel("Date")
        plt.ylabel("Close Price")
        plt.xticks(rotation=45)
        plt.tight_layout()

        os.makedirs("charts", exist_ok=True)
        path = f"charts/{symbol}.png"
        plt.savefig(path)
        plt.close()
        print(f"✅ Chart saved: {path}")
        print(f"📁 Location = {os.path.abspath(path)}")
        return path

    except Exception as e:
        print(f"❌ draw_stock_chart error: {e}")
        return None
