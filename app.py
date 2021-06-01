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
import sys
import json
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

with open('scrap.json', 'r') as f:
    info = json.load(f)

CHANNEL_ACCESS_TOKEN = info['CHANNEL_ACCESS_TOKEN']
CHANNEL_SECRET = info['CHANNEL_SECRET']
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

def Select_Url(prefecture):
    # LINEのコメントから取得した文字列でスクレイピングするURLを選択
    load_url = 'https://realdgame.jp/ajito/'

    if prefecture == '福岡':
        load_url += 'fukuoka_tenjin/'
    elif prefecture == '岡山': # 無反応
        load_url += 'okayama/'
    elif prefecture == '大阪': # 無反応
        load_url += 'osaka_nazobldg/'
    elif prefecture == '京都':
        load_url += 'kyoto/'
    # HPの形式が異なるため一旦保留
    # elif prefecture == '名古屋':
    #     load_url += ''
    elif prefecture == '横浜':
        load_url += 'yokohama/'
    # 今のところ開発中？トップページにとぶ
    # elif prefecture == '池袋':
    #     load_url += ''
    elif prefecture == '下北沢':
        load_url += 'shimokitazawa/'
    elif prefecture == '浅草':
        load_url += 'asakusa/'
    elif prefecture == '東新宿':
        load_url += 'shinjuku/'
    elif prefecture == '仙台': # 不要な英単語
        load_url += 'sendai/'
    elif prefecture == '札幌': # 不要な英単語
        load_url += 'sapporo/'
    # 該当する地名がなければシステム自体が終了
    else:
        load_url = 'NG'
        # sys.exit()

    return load_url

def ScrapInfo(prefecture, load_url):
    # Webページを取得して解析
    html = requests.get(load_url)
    soup = BeautifulSoup(html.content, 'html.parser')

    detail_url = soup.find_all(class_='asset-more-link')
    detail_url_list = []
    for url in detail_url:
        detail_url_list.append(url.find('a').get('href'))

    event_info = soup.find_all(class_='post-content text_area')
    event_info = [s for s in event_info if prefecture in  s.text]
    event_info_list = []
    for i, element in enumerate(event_info):
        if i == 0:
            event_info_list.append('------------------------------\n')
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
    print('OK2')
    return event_info_text 

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
    load_url = Select_Url(event.message.text)
    event_info_text = ScrapInfo(event.message.text, load_url)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=load_url))

if __name__ == "__main__":
    app.run()