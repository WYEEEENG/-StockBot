import os
import json
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FollowEvent
)
from linebot.exceptions import InvalidSignatureError
import stock_utils

from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="charts"), name="static")

# Load environment variables
load_dotenv()

app = FastAPI()

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

    if msg == "我的ID":
        uid = event.source.user_id
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"你的 User ID 是：\n{uid}")
        )
        return

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

    # 產文字
    for code in tw_stocks:
        messages.append(stock_utils.get_taiwan_stock(code))
    for code in us_stocks:
        messages.append(stock_utils.get_us_stock(code))

    text_summary = "\n\n".join(messages)

    # 推播給所有使用者
    for uid in users:
        try:
            # 先傳文字
            line_bot_api.push_message(uid, TextSendMessage(text=text_summary))

            # 再一張一張圖傳
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
