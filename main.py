# 聊天機器人版本: v1.3
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, Source
import os
import my_commands.database as db
from my_commands.stock_gpt import stock_gpt, get_reply
from my_commands.lottery_gpt import lottery_gpt
from my_commands.gold_gpt import gold_gpt
from my_commands.money_gpt import money_gpt
from my_commands.one04_gpt import one04_gpt, get_reply
import re



api = LineBotApi(os.getenv('LINE_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_SECRET'))
app = Flask(__name__)

# 初始化對話歷史
conversation_history = []
# 設定最大對話記憶長度
MAX_HISTORY_LEN = 10

@app.post("/")
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("電子簽名錯誤，請檢查密鑰是否正確？")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global conversation_history

    user_message = event.message.text
    conversation_history.append({"role": "user", "content": user_message + " reply in 繁體中文"})

    if len(conversation_history) > MAX_HISTORY_LEN * 2:
        conversation_history = conversation_history[-MAX_HISTORY_LEN * 2:]

    # 將對話歷史加入消息列表
    msg = conversation_history[-MAX_HISTORY_LEN:]

    # 使用正則表達式查找連續4個數字
    stock_code = re.search(r'\d{4}', user_message)

      # 處理樂透信息
    if any(lottery_key.lower() in user_message.lower() for lottery_key in ["威力", "雙贏彩", "3星彩", "4星彩", "四星", "三星","三星彩" "38樂合彩", "39樂合彩", "49樂合彩","運彩"]):
        reply_text = lottery_gpt(user_message)
    elif "大盤" in user_message.lower() or "台股" in user_message.lower():
        reply_text = stock_gpt("大盤")
    elif user_message.lower() == "539":
        reply_text = lottery_gpt(user_message)
    elif user_message.lower() == "大樂透" or user_message.lower() == "big":
        reply_text = lottery_gpt(user_message)
    elif any(currency.lower() in user_message.lower() for currency in ["金價", "金", "黃金", "gold"]):
        reply_text = gold_gpt()
    elif any(currency.lower() in user_message.lower() for currency in ["日幣", "日元", "jpy", "換日幣"]):
        reply_text = money_gpt("JPY")
    elif any(currency.lower() in user_message.lower() for currency in ["美金", "usd", "美元", "換美金"]):
        reply_text = money_gpt("USD")
    elif user_message.startswith("104:"):
        reply_text = one04_gpt(user_message[4:])
    elif stock_code:
        reply_text = stock_gpt(stock_code[0])
    else:
        msg.append({"role": "user", "content": user_message + " 以繁體中文回覆"})
        reply_text = get_reply(msg)

    conversation_history.append({"role": "assistant", "content": reply_text + " 以繁體中文回覆"})

    api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text))

    print("AI醬版本: v1.3")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)