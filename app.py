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
import os
import sys
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.environ['SCRAP_LINEbot_CHANNEL_ACCESS_TOKEN']
CHANNEL_SECRET = os.environ['SCRAP_LINEbot_CHANNEL_SECRET']
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

def Select_Url(prefecture):
    # LINEのコメントから取得した文字列でスクレイピングするURLを選択
    load_url = 'https://realdgame.jp/ajito/'

    if prefecture == '福岡':
        load_url += 'fukuoka_tenjin/'
    elif prefecture == '岡山':
        load_url += 'okayama/'
    elif prefecture == '大阪':
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
        sys.exit()

    return load_url

def ScrapInfo(prefecture, load_url):
    # Webページを取得して解析
    html = requests.get(load_url)
    # Webページからクローリング
    soup = BeautifulSoup(html.content, 'html.parser')

    # 各イベントのURLを取得
    detail_url = soup.find_all(class_='asset-more-link')
    # 取得したURLを格納するリストを生成
    detail_url_list = []
    for url in detail_url:
        # aタグの中のhref属性からURLのみ取得し、リストに格納
        detail_url_list.append(url.find('a').get('href'))

    # 各イベントの情報を取得
    event_info = soup.find_all(class_='post-content text_area')
    # オンライン版以外の情報を取得するため、取得した情報に県名（prefecture）がある情報のみリストに格納
    event_info = [s for s in event_info if prefecture in  s.text]
    # オンライン版以外の情報を取得
    event_info_list = []
    for i, element in enumerate(event_info):
        # 情報の最初に点線を加える
        if i == 0:
            event_info_list.append('------------------------------\n')
        # event_infoリストは改行情報があるため、これを区切りにして改行を削除
        info_list = element.text.split('\n')
        # 空白（''）を削除
        info_list = [s for s in info_list if s != '']
        # ここでイベントのURLを格納
        info_list.append(detail_url_list[i])
        
        # インデント番号0と1が同じ情報のため削除
        info_list.pop(0)
        
        ## 情報の種類で改行を入れる
        # プレイ形式の前に改行を入れる
        play_form = 'プレイ形式'
        if play_form in info_list:
            n = info_list.index(play_form)
            info_list[n:n] = '\n'
        
        # 会場は不要な情報のため削除し、改行を入れる
        place = '会場'
        if place in info_list:
            n = info_list.index(place)
            info_list[n:n+2] = '\n'
        
        # 開催日程の前に改行を入れる
        date = '開催日程'
        if date in info_list:
            n = info_list.index(date)
            info_list[n:n] = ''
        
        # １つのイベントが終わるたびに点線を入れる
        info_list.append('\n------------------------------\n')
        # すべての文字列ごとに改行を入れる
        event_info_list.append('\n'.join(info_list))
        
    # LINE Messaging APIではリストとして出力することができないため、文字列として変数に代入
    event_info_text = ''.join(event_info_list)
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
    # 送られてきたメッセージが「アジト」の場合、選択できるアジト名を返す
    if event.message.text == 'アジト':
        text = '・福岡\n・岡山\n・大阪\n・京都\n・横浜\n・下北沢\n・浅草\n・東新宿\n・仙台\n・札幌'
    else:
        # 送られてきたメッセージからURLを取得
        load_url = Select_Url(event.message.text)
        # 取得したURLからイベント情報を取得
        text = ScrapInfo(event.message.text, load_url)
    # LINEから返すメッセージ
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=text))

if __name__ == "__main__":
    app.run()