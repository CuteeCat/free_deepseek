#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import time
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

WECHAT_APPID = "wx932d4fdaf46d5611"            
REDIRECT_URI = "https://chat.deepseek.com/api/v0/users/oauth/wechat/callback"

BASE_HEADERS = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9",
    "authorization": "",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://chat.deepseek.com/authorized",
    "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="140", "Google Chrome";v="140"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/140.0.7339.210 Safari/537.36"),
    "x-client-bundle-id": "com.deepseek.chat",
    "x-client-locale": "zh_CN",
    "x-client-platform": "web",
    "x-client-timezone-offset": "28800",
    "x-client-version": "2.4.0",
}


def capture():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        ctx = browser.new_context(
            user_agent=BASE_HEADERS["user-agent"],
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )
        ctx.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )

        token_holder = {"value": None}
        header_holder = {"headers": None}

        def on_request(req):
            if token_holder["value"]:
                return
            auth = req.headers.get("authorization") or ""
            m = re.match(r"^Bearer\s+(\S+)$", auth)
            if m:
                token_holder["value"] = m.group(1)
                header_holder["headers"] = dict(req.headers)


        def wire(page, tag):
            page.on("request", on_request)
            page.on("response", lambda r: _log_net(r, tag))

        def _log_net(resp, tag):
            u = resp.url
            if any(x in u for x in ("oauth/wechat", "/authorized", "open.weixin", "chat.deepseek")):
                print(f"[网络:{tag}] {resp.status} {u[:110]}")

        ctx.on("page", lambda pg: (wire(pg, "new-tab"),
                                   print("[*] 检测到新标签页: " + pg.url[:80])))
        page = ctx.new_page()
        wire(page, "main")

        qr_url = (
            "https://open.weixin.qq.com/connect/qrconnect"
            "?appid=" + WECHAT_APPID +
            "&scope=snsapi_login" +
            "&redirect_uri=" + quote(REDIRECT_URI, safe="") +
            "&state=" +
            "&login_type=jssdk" +
            "&self_redirect=true" +
            "&styletype=&sizetype=&bgcolor=&rst=" +
            "&ts=" + str(int(time.time() * 1000)) +
            "&stylelite=1&fast_login=0" +
            "#wechat_redirect"
        )
        print("[*] 打开微信二维码页，请用微信扫码并确认……")
        page.goto(qr_url, wait_until="domcontentloaded")


        deadline = time.time() + 300
        while token_holder["value"] is None and time.time() < deadline:
            for pg in ctx.pages:
                if "chat.deepseek.com" in pg.url:
                    print(f"[*] 已跳转到 DeepSeek 页面: {pg.url[:110]}")
                    pg.wait_for_timeout(3000)
            time.sleep(1)

        if token_holder["value"] is None:
            print("[x] 300 秒内未跳回 DeepSeek 或未捕获到令牌")

            browser.close()
            raise SystemExit(1)


        try:
            ctx.pages[0].goto("https://chat.deepseek.com/", wait_until="domcontentloaded")
            time.sleep(4)
        except Exception:
            pass

        cookies = {c["name"]: c["value"] for c in ctx.cookies()}
        browser.close()

        headers = dict(header_holder["headers"] or BASE_HEADERS)
        if not headers.get("authorization"):
            headers["authorization"] = "Bearer " + token_holder["value"]
        config = {"cookies": cookies, "headers": headers}

        out = Path("config.json")
        out.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[+] 已保存 {out}")



if __name__ == "__main__":
    capture()
