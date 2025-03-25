import os
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
import stock_utils

# 如果你是用本地 .env，可保留這行
load_dotenv()

app = FastAPI()

CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        return {"status": "invalid signature"}
    return {"status": "ok"}

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent):
    msg = event.message.text.strip().upper()

    if msg.isdigit():  # 台股（數字代碼）
        result = stock_utils.get_taiwan_stock(msg)
    else:              # 美股（英文字母）
        result = stock_utils.get_us_stock(msg)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=result)
    )
