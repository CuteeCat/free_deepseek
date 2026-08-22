import base64
import json
import subprocess

import requests


def getres():
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    return requests.post(
        'https://chat.deepseek.com/api/v0/chat/create_pow_challenge',
        cookies=config["cookies"],
        headers=config["headers"],
        json={'target_path': '/api/v0/chat/completion'},
    ).json()


def submitanswer(res):
    ch = res["data"]["biz_data"]["challenge"]
    # 让 pow.exe 暴力求解，answer 从 stdout 拿回
    answer = int(subprocess.check_output(
        ["pow.exe", ch["salt"], str(ch["expire_at"]),
         str(ch["difficulty"]), ch["challenge"]],
        text=True).strip())
    pow = {
        "algorithm": "DeepSeekHashV1",
        "target_path": "/api/v0/chat/completion",
        "challenge": ch["challenge"],
        "salt": ch["salt"],
        "answer": answer,
        "signature": ch["signature"],
    }
    return base64.b64encode(
        json.dumps(pow, separators=(',', ':')).encode("utf-8")
    ).decode()