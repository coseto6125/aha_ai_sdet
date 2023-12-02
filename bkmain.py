# @Author: E-NoR
# @Date:   2022-11-23 15:29:25
# @Last Modified by:   E-NoR
# @Last Modified time: 2023-04-19 10:35:48
import asyncio
from hashlib import md5
from pathlib import Path
from time import time
from urllib.parse import urlencode

import aiohttp
import colorama
from gs_info import fill_agent_data, get_info, init_login_info, update_refresh_time
from lib.local_redis import BACKEND_CONFIG, redis_load_md5deskey_cookie
from loguru import logger
from module.AES128_ECB_pkcs7 import EncryptDate
from module.basic_aiohttp import AioConnection
from module.bot_monitor_reboot import reboot_sv
from module.jenkins_event import run_job, stop_jenkins_jobs
from module.mmbot_module import MMBot
from orjson import dumps, loads
from pydantic import BaseModel, ValidationError, field_validator
from requests import request
from sanic import HTTPResponse, Request, Sanic, empty, text
from sanic.exceptions import SanicException
from sanic.response import file, file_stream, html, json, redirect

colorama.init()

# from module.checkTimer import check_timer

app = Sanic(__name__)

app.static("/static", "C:/Users/enor.deng/Documents/fastApiServer/static", resource_type="dir")


class UnicornExceptionError(Exception):

    def __init__(self, name: str):
        self.name = name


def aio_platform(platform: str) -> AioConnection:
    if session := AIO_SESSIONS[platform]:
        return session
    AIO_SESSIONS[platform] = AioConnection(platform)
    return AIO_SESSIONS[platform]


AIO_SESSIONS = {
    "MP_GLO_SIT": None,
    "YL_HCI_SIT": None,
    "YL_HCI_UAT": None,
    "NW_HCI_SIT": None,
    "NW_HCI_UAT": None,
    "V8_HCI_SIT": None,
    "V8_HCI_UAT": None,
    "GKX_HCI_SIT": None,
    "GKX_HCI_UAT": None,
    "KX_SIT": None,
    "KX_UAT": None,
    "LY_DEV153": None,
    "LY_DEV155": None,
    "LY_SIT": None,
    "NW_SIT": None,
    "NW_UAT": None,
    "V8_SIT": None,
    "YL_SIT": None,
    "KX_GLO_SIT": None,
}

# @app.get("/")
# async def read_index():
#     return file_stream("index.html")


def quick_parse(key_list, args):
    if len(args) == 4:
        args |= {"currency": ["CNY"]}
    return [args[k][0] for k in key_list]


@app.get("/login")
async def login(request: Request):
    platform = request.args.get("platform")

    is_oversea = False if Request is not False else "ngrok" in request.url

    *acc_data, check = get_info(platform, is_oversea)
    if acc_data[1] == "":
        return text(f"登入平台：{platform}，登入帳號為空，請於表單輸入帳號")
    method = aio_platform(platform)

    async def connect():
        res = await method.get_login_url(*acc_data)
        if all(i not in res for i in ("http:", "https:")):
            return res
        init_login_info(platform, check)
        return redirect(res)

    if isinstance(res := await connect(), HTTPResponse):
        return res
    if res["code"] in {31, 32}:
        await method.create_acc_single_wallet_v8_sit(acc_data)
        acc_data[2] = 0
        if isinstance(res := await connect(), HTTPResponse):
            return res
    try:
        plat_base = "_".join(platform.rsplit("_", 1)[:-1])
        err_code_filepath = f"config/errorCode/{plat_base}_msg.json"
        if Path(err_code_filepath).exists():
            err_code = res["code"]
            if err_code == 89 and platform in {"YL_HCI", "YL_HCI_UAT"}:
                res = "代理餘額不足，請自行去台充值"
            else:
                with open(f"config/errorCode/{plat_base}_msg.json", encoding="utf-8-sig") as f:
                    er_c = loads(f.read())
                res |= {"err_msg": er_c.get(str(err_code))}
            return res
    except Exception as e:
        raise SanicException(status_code=404, context=e) from e


@app.route("/download_swv/<filename:path>")
async def serve_file(request, filename):
    path = Path("C:/Users/qatest/Documents/single_wallect/data/") / filename
    # path = Path("C:/abc/") / filename
    return await file(path)


@app.get("/agent_info_update/")
async def agent_info_update(request):
    pl_info = BACKEND_CONFIG.keys()
    fail_list = []

    for platform in pl_info:
        print(platform)
        if platform not in {  # * skip
            "YL_HCI_SIT",
            "YL_HCI_UAT",
            "NW_HCI_SIT",
            "NW_HCI_UAT",
            "NW_HCI_PRD",
            "V8_HCI_SIT",
            "V8_HCI_UAT",
            "GKX_HCI_SIT",
            "GKX_HCI_UAT",
            "KX_SIT",
            "LY_DEV153",
            "LY_DEV155",
            "LY_SIT",
            "NW_SIT",
            "V8_SIT",
            "YL_SIT",
            "KX_GLO_SIT",
        }:
            continue
        try:
            method = aio_platform(platform)
            # await method.login()
            data = await method.add_white_list()
            fill_agent_data(platform, data)
        except Exception:
            fail_list.append(platform)
    update_refresh_time()
    html_content = """
            <html>
                <head>
                <title>快速登入--更新完畢視窗自動關閉</title>
                </head>
                <body>
                <script>window.close()</script>
                </body>
            </html>
            """
    return html(html_content)


@app.get("/add_white_list")
async def add_agent_white_list(request: Request):
    platform, agent = quick_parse(("platform", "agent"), request.args)

    method = aio_platform(platform)
    await method.add_white_list(agent)
    return json({"code": 0, "agent": agent})


@app.get("/get_md5_deskey")
async def get_md5_deskey(request: Request | list):
    if isinstance(request, Request):
        platform, agent = quick_parse(("platform", "agent"), request.args)
    else:
        platform, agent = request

    method = aio_platform(platform)
    result = {"code": 0}
    if "HCI" in platform:
        result |= await method.get_missing_agent_data(agent)
    else:
        result |= await method.get_missing_agent_data_base(agent)
    return json(result)


@app.get("/check_single_wallet")
async def check_single_wallet(request: Request):
    platform, agent = quick_parse(("platform", "agent"), request.args)
    method = aio_platform(platform)
    if "HCI" in platform:
        result = await method.check_single_wallet(agent)
    else:
        result = await method.check_single_wallet_base(agent)
    return json({"code": 0, "is_single_wallet": result})


@app.get("/ws")
async def get_ws_token(request: Request):
    # platform = 'V8_UAT'
    # with contextlib.suppress(SanicException):
    try:
        platform, *params = quick_parse(("platform", "agent", "account", "money", "currency"), request.args)
        agent = params[1]
        method = aio_platform(platform)

        async def connect():
            return await method.get_login_url(*params)

        task = asyncio.create_task(connect())
        res = await task

        if isinstance(res, HTTPResponse):
            return res
        if isinstance(res, str):
            # parsed_url = urlparse(s["url"])
            data = {}
            for i in res.split("?")[1].split("&"):
                param = i.split("=", 1)
                data[param[0]] = param[1]
            return json(data)

        if res["code"] in {31, 32}:
            await method.create_acc_single_wallet_v8_sit(params)
            params[2] = 0
            task = asyncio.create_task(connect())
            res = await task
            if isinstance(res, str) and "token" not in res:
                raise SanicException(status_code=404, message=res)
            data = {}
            for i in res.split("?")[1].split("&"):
                param = i.split("=", 1)
                data[param[0]] = param[1]
            return json(data)

        err_code = res["code"]
        if "HCI" in platform:
            if err_code == 89:
                raise SanicException(status_code=500, message=f"{agent}:代理餘額不足，請自行去後台充值")
            if err_code == 39:
                raise SanicException(status_code=500, message="帳號餘額太多，請自行去後台取款減少餘額")

        plat_base = "_".join(platform.rsplit("_", 1)[:-1])
        if Path(err_code_filepath := f"config/errorCode/{plat_base}_msg.json").exists():
            with open(err_code_filepath, encoding="utf-8-sig") as f:
                res.update(loads(f.read())[str(err_code)])
            return json(res)
        return None
    except Exception as e:
        raise SanicException(status_code=404, message=res)


@app.exception(ValidationError)
async def validation_exception_handler(request, exc):
    msg = {
        "code": 422,
        "reason": {i["loc"][1]: i["msg"] for i in exc._errors},
        "tips": "格式需為json，要求如下",
        "content": {
            "title": "str",
            "msg": "str | list[str]",
            "link": "str | dict[str, str] (optional)",
            "sub_title": "str (optional)",
            "assign": "str | list[str] (optional)",
        },
    }
    return json(status=422, body={"error": msg})


@app.exception(KeyError)
async def handle_unexpected_error(_, exc):
    error_message = f"輸入參數錯誤，{type(exc).__name__}:{str(exc)},如確認參數無誤，找E-NoR修復"
    return json(status=500, body={"error": error_message}, ensure_ascii=False)


@app.exception(Exception)
async def handle_unexpected_error(_, exc):
    error_message = f"無法預期的錯誤，{type(exc).__name__}:{str(exc)}, 如輸入參數無誤，找E-NoR修復"
    return json(status=500, body={"error": error_message}, ensure_ascii=False)


@app.get("/stop_jenkins_jobs")
async def show_embedded_1(request: Request):
    is_oversea = request.args.get("is_oversea")
    job_result = await stop_jenkins_jobs("V8-SIT-one", is_oversea)
    msg = await run_job(job_result)
    try:
        return html(f"{job_result['job_name']} 操作成功 -- {msg}")
    except Exception:
        return html(f"{job_result['job_name']} 關閉失敗 -- {msg}")


@app.get("/stop_jenkins_job")
async def show_embedded_0(request: Request):
    is_oversea = False if Request is not False else "ngrok" in request.url._url

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <title>Confirmation Dialog</title>
    <script>
    window.onload = function() {{
        showConfirmation();
    }}
    var message = "你確定要關閉 KX_GLOBAL_UAT ?";
    var message2 = "再次確認，是否確定要關閉 KX_GLOBAL_UAT ?\\n\\n關閉後要重啟需要手動開啟專案與重建job，\\n請確認是否要執行關閉操作。";
    function showConfirmation() {{
        var result = confirm(message);
        var result2 = confirm(message2);
        if (result) {{
            // 用戶點擊了 Yes
            // 執行相應的操作，調用關閉jobAPI
            // ...
            if (result2) {{
                window.location.href = "/stop_jenkins_jobs?is_oversea={is_oversea}";
            }} else {{
                window.location.href = "https://docs.google.com/spreadsheets/d/1OI-8ahqx1qdW6EQBO6I7ctsfpmZONepQ6ktbyz96nfg";
            }}
        }} else {{
            // 用戶點擊了 No
            // 執行相應的操作，跳轉到指定網頁
            window.location.href = "https://docs.google.com/spreadsheets/d/1OI-8ahqx1qdW6EQBO6I7ctsfpmZONepQ6ktbyz96nfg";
        }}
    }}
    </script>
    </head>
    <body>
    </body>
    </html>
    """
    return html(html_content)


@app.get("/return_org_url")
async def return_org_url(request: request):
    url = request.args.get("url")
    return redirect(url)


@app.route("/favicon.ico")
async def favicon(request):
    return HTTPResponse(status=204, headers={"Cache-Control": "public, max-age=3600"})


class BotMsg(BaseModel):
    mode: str = "report"
    title: str
    msg: str | list[str]
    link: str | dict[str, str] | None = None
    sub_title: str | None = None
    assign: str | list[str] | None = None

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, mode):
        if mode not in {"report", "warning", "msg_announce"}:
            raise ValueError('Invalid mode value. Must be "report" or "warning"')
        return mode


@app.post("/bot_msg")
async def bot_post_msg(request: Request):
    msg = BotMsg(**request.json)
    mm_bot = MMBot("qa-ornd", "api")
    mm_bot.token = await mm_bot.login_get_token()
    msg_combine = await mm_bot.api_post_msg(msg)
    return json({"msg": "success", "content": msg_combine}, indent=4)


@app.get("/reboot_relay_sv")
async def reboot_relay_sv(request: Request):
    platform = request.args.get("platform")
    try:
        await reboot_sv(platform)
    except Exception as e:
        return json({"code": 1, "msg": "fail", "error": str(e)}, indent=4)
    else:
        return json({"code": 0, "msg": "success"}, indent=4)


@app.get("/evrp")
async def evrp(request: Request):
    return text(str(asyncio.get_event_loop()))


@app.get("/reload")
async def reload(request: Request):
    try:
        file_path = Path("main.py")
        with file_path.open("r", encoding="utf-8") as file:
            content = file.read()

        if "111" in content:
            search_text, replace_text = "111", "111"
        else:
            search_text, replace_text = "111", "111"
        modified_content = content.replace(search_text, replace_text)
        with file_path.open("w", encoding="utf-8") as file:
            file.write(modified_content)

    except Exception as e:
        return json({"code": 1, "msg": "fail", "error": str(e)}, indent=4)
    else:
        return json({"code": 0, "msg": "success"}, indent=4)


@app.post("/st_test_m")
async def st_test(request: Request):
    val = request.json["val"]
    # print(f"test:{val}")
    return json({"code": val})


@app.get("/recharge")
async def recharge(request: Request):
    platform: str = request.args.get("platform")
    agent_acc: str = request.args.get("account")
    money: str = int(request.args.get("money"))
    currency: str = request.args.get("currency") or "CNY"
    agent, account = agent_acc.split("_", 1)
    agent = int(agent)
    config = BACKEND_CONFIG[platform]
    single_wallect = False
    if single_wallect:
        url = config["single_wallet_url"]
        if platform.rsplit("_", 1)[0] == "V8":
            payload = {"s": 1, "agent": agent, "account": account, "gold": money, "method": ""}
        else:
            payload = {"serverID": 2, "agent": agent, "account": account, "money": money}
        header = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6",
            "cache-control": "max-age=0",
            "content-length": "47",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://wc2-wallet.twow42.com",
            "referer": "https://wc2-wallet.twow42.com/wallet",
            "sec-ch-ua": '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
        }
        res = aiohttp.request("POST", url=url, headers=header, json=payload)
        return {
            "cmd": "syncPlayerGold",
            "emitter": "Player",
            "server": "hall",
            "params": [],
        }
    agent_key = redis_load_md5deskey_cookie(platform, account) or loads((await get_md5_deskey((platform, agent))).body)
    agent_key = {i.lower(): v for i, v in agent_key.items()}
    mode = "2" if money > 0 else "3"
    param = {
        "s": mode,  # 2:上分 3:下分
        "account": account,
        "money": abs(money),
        "orderid": f"{agent}{int(time())}{account}",
        "currency": currency,
        "GameArrNo": "0",
    }

    timestamp = int(time())
    paramData = EncryptDate(agent_key["deskey"]).encrypt(urlencode(param)).encode("utf8").decode()

    payload = {
        "agent": agent,
        "timestamp": timestamp,
        "param": paramData,
        "channel": agent,
        "mTime": timestamp,
        "paramerter": paramData,
        "key": md5(f"{agent}{timestamp}{agent_key['md5key']}".encode()).hexdigest(),
    }
    async with aiohttp.request("GET", config["channel_handler"], params=payload) as resp:
        res = loads(await resp.text())
        if (status_code := (res.get("d") or res.get("dataStr"))["code"]) != 0:
            with logger.contextualize(user=account):
                logger.error(f"充值錯誤  code:{status_code}")
            raise SanicException(status_code=500, message=res)
        logger.success("-----------------充值成功----------------")
    return json({"msg": "success", "content": "1"}, indent=4)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8087, fast=True, auto_reload=True)