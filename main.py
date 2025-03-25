import os
import json
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FollowEvent, ImageSendMessage
)
from linebot.exceptions import InvalidSignatureError
import stock_utils
import re
from fastapi.staticfiles import StaticFiles

# 初始化 FastAPI 並掛載靜態圖表路徑
app = FastAPI()
app.mount("/static", StaticFiles(directory="charts"), name="static")

# 載入 .env 設定
load_dotenv()

CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

USERS_FILE = "users.json"

# --- 儲存使用者 ID ---
def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)

# --- Webhook 接收事件 ---
@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()

    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        return {"status": "invalid signature"}
    return {"status": "ok"}

# --- 處理加好友事件 ---
@handler.add(FollowEvent)
def handle_follow(event: FollowEvent):
    user_id = event.source.user_id
    save_user(user_id)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="✅ 你已成功訂閱每日股市通知！傳 2330 或 TSLA 試試看")
    )

# --- 處理訊息事件 ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent):
    msg = event.message.text.strip().upper()
    user_id = event.source.user_id

    # 👉 顯示自己的 ID
    if msg == "我的ID":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"你的 User ID 是：\n{user_id}")
        )
        return

    # 👉 判斷是否為「股票 + 關鍵字」
    trigger_words = ["交易紀錄", "走勢", "圖表", "CHART", "股價圖"]
    for keyword in trigger_words:
        if keyword in msg:
            symbol = re.sub(rf"{keyword}", "", msg, flags=re.IGNORECASE)
            symbol = re.sub(r"[^\w]", "", symbol).upper()
            print(f"⏳ 嘗試查詢圖表 symbol = {symbol}")

            chart_path = stock_utils.draw_stock_chart(symbol)
            if chart_path:
                url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/static/{symbol}.png"
                image_message = ImageSendMessage(
                    original_content_url=url,
                    preview_image_url=url
                )
                line_bot_api.reply_message(event.reply_token, image_message)
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="⚠️ 無法產生圖表，可能代碼有誤或資料不足")
                )
            return

    # 👉 股票價格查詢（純文字）
    if msg.isdigit():
        result = stock_utils.get_taiwan_stock(msg)
    else:
        result = stock_utils.get_us_stock(msg)

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))

# --- 定時推播任務 ---
def scheduled_push():
    users = load_users()
    if not users:
        print("⚠️ 沒有任何使用者可以推播")
        return

    tw_stocks = ["2330", "0056", "0050"]
    us_stocks = ["TSLA", "VOO", "NVDA"]
    messages = []

    for code in tw_stocks:
        messages.append(stock_utils.get_taiwan_stock(code))
    for code in us_stocks:
        messages.append(stock_utils.get_us_stock(code))

    text_summary = "\n\n".join(messages)

    for uid in users:
        try:
            line_bot_api.push_message(uid, TextSendMessage(text=text_summary))
            for code in tw_stocks + us_stocks:
                img_path = stock_utils.draw_stock_chart(code)
                if img_path:
                    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/static/{code}.png"
                    line_bot_api.push_message(
                        uid,
                        ImageSendMessage(
                            original_content_url=url,
                            preview_image_url=url
                        )
                    )
        except Exception as e:
            print(f"推播給 {uid} 失敗：{e}")

# --- 啟動排程器 ---
scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_push, "cron", hour=11, minute=0)
scheduler.add_job(scheduled_push, "cron", hour=17, minute=30)
scheduler.start()
