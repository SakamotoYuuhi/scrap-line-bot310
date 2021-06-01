from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
import json
import requests
from bs4 import BeautifulSoup

def ScrapInfo(prefecture):
  # Webページを取得して解析
  load_url = 'https://realdgame.jp/ajito/fukuoka_tenjin/'
  html = requests.get(load_url)
  soup = BeautifulSoup(html.content, 'html.parser')

  detail_url = soup.find_all(class_='asset-more-link')
  detail_url_list = []
  for url in detail_url:
      detail_url_list.append(url.find('a').get('href'))

  event_info = soup.find_all(class_='post-content text_area')
  event_info = [s for s in event_info if '【' + prefecture + '】' in  s.text]
  event_info_list = ['------------------------------\n']
  for i, element in enumerate(event_info):
      info_list = element.text.split('\n')
      info_list = [s for s in info_list if s != '']
      info_list.append(detail_url_list[i])
      
      info_list.pop(0)
      
      play_form = 'プレイ形式'
      n = info_list.index(play_form)
      info_list[n:n] = '\n'
      
      place = '会場'
      n = info_list.index(place)
      info_list[n:n+2] = '\n'
    
      date = '開催日程'
      n = info_list.index(date)
      info_list[n:n] = ''
      
      info_list.append('\n------------------------------\n')
      event_info_list.append('\n'.join(info_list))
      
  event_info_text = ''.join(event_info_list)
  return event_info_text 

app = Flask(__name__)

with open('scrap.json', 'r') as f:
    info = json.load(f)

CHANNEL_ACCESS_TOKEN = info['CHANNEL_ACCESS_TOKEN']
CHANNEL_SECRET = info['CHANNEL_SECRET']
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.route('/')
def test():
    return 'OK'

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
  event_info_text = ScrapInfo(event.message.text)
  event_info_text += event.message.text
  line_bot_api.reply_message(
      event.reply_token,
      TextSendMessage(text=event.message.text))


if __name__ == "__main__":
    app.run()