import requests
import json
import argparse
import pow
import new

parser = argparse.ArgumentParser(description='prompt')
parser.add_argument("-p",  type=str, dest="prompt", help="填写你的prompt")
args = parser.parse_args()

p = args.prompt

ssid = new.newsession()

powres = pow.getres()
powtk = pow.submitanswer(powres)
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    
    
cookies = config["cookies"]

headers = config["headers"]

headers["x-ds-pow-response"] = powtk
json_data = {
    'chat_session_id': ssid,
    'parent_message_id': None,
    'model_type': 'default',
    'prompt': '',
    'ref_file_ids': [],
    'thinking_enabled': False,
    'search_enabled': True,
    'action': None,
    'preempt': False,
}
json_data["prompt"] = p
res = requests.post('https://chat.deepseek.com/api/v0/chat/completion',
                    cookies=cookies, headers=headers, json=json_data,
                    stream=True)   

for line in res.iter_lines(decode_unicode=True):
    if not line or not line.startswith('data:'):
        continue
    payload = line[len('data:'):].strip()
    if not payload:
        continue
    try:
        obj = json.loads(payload)
    except json.JSONDecodeError:
        continue
    if not isinstance(obj, dict):
        continue
    if obj.get('p') == 'response/status' and obj.get('v') == 'FINISHED':
        break
    if obj.get('p') == 'response/fragments/-1/content' and obj.get('o') == 'APPEND':
        print(obj['v'], end='', flush=True)
    elif set(obj.keys()) == {'v'} and isinstance(obj.get('v'), str):
        print(obj['v'], end='', flush=True)

print()