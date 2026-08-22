import requests
import json
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    
    
cookies = config["cookies"]

headers = config["headers"]

json_data = {}
def newsession():
    res = requests.post('https://chat.deepseek.com/api/v0/chat_session/create', cookies=cookies, headers=headers, json=json_data)
    res_json = res.json() 
    return (res_json["data"]["biz_data"]["chat_session"]["id"])