import twstock
import yfinance as yf

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
    except:
        return f"{stock_id} 查詢錯誤"

def get_us_stock(symbol):
    try:
        stock = yf.Ticker(symbol)
        price = stock.info.get('regularMarketPrice')
        volume = stock.info.get('volume')
        return f"{symbol}\nPrice: ${price}\nVolume: {volume}"
    except:
        return f"{symbol} 查詢錯誤"
