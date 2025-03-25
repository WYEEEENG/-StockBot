import twstock
import yfinance as yf
import matplotlib.pyplot as plt
import datetime
import os

def get_taiwan_stock(stock_id):
    try:
        stock = twstock.realtime.get(stock_id)
        if stock['success']:
            name = stock['info']['name']
            price = stock['realtime']['latest_trade_price']
            volume = stock['realtime']['accumulate_trade_volume']
            return f"{stock_id} {name}\n現價：{price} 元\n成交量：{volume} 張"
        else:
            return f"{stock_id} 資料讀取失敗"
    except Exception as e:
        print(f"❌ 台股查詢錯誤：{e}")
        return f"{stock_id} 查詢錯誤"

def get_us_stock(symbol):
    try:
        stock = yf.Ticker(symbol)
        price = stock.info.get('regularMarketPrice')
        volume = stock.info.get('volume')
        return f"{symbol}\nPrice: ${price}\nVolume: {volume}"
    except Exception as e:
        print(f"❌ 美股查詢錯誤：{e}")
        return f"{symbol} 查詢錯誤"

def draw_stock_chart(symbol):
    try:
        is_tw = symbol.isdigit()
        plt.figure(figsize=(8, 4))
        today = datetime.date.today()

        dates = []
        prices = []

        if is_tw:
            stock = twstock.Stock(symbol)
            hist = stock.fetch_from(today.year - 1, today.month)
            last_30 = hist[-30:]
            for d in last_30:
                dates.append(d.date.strftime("%m/%d"))
                prices.append(d.close)
        else:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1mo")
            if hist.empty:
                print(f"❌ {symbol} 沒有歷史資料")
                return None
            dates = hist.index.strftime("%m/%d").tolist()
            prices = hist["Close"].tolist()

        if not prices or len(prices) == 0:
            print(f"❌ {symbol} 沒有價格資料，無法產圖")
            return None

        plt.plot(dates, prices, marker='o')
        plt.title(f"{symbol} 股價走勢圖（近30天）")
        plt.xlabel("日期")
        plt.ylabel("收盤價")
        plt.xticks(rotation=45)
        plt.tight_layout()

        os.makedirs("charts", exist_ok=True)
        path = f"charts/{symbol}.png"
        plt.savefig(path)
        plt.close()
        print(f"✅ 成功產生圖表：{path}")
        return path

    except Exception as e:
        print(f"❌ draw_stock_chart 發生錯誤：{e}")
        return None
