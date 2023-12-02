
from subprocess import PIPE, CalledProcessError, Popen

from loguru import logger
from sanic import HTTPResponse, Sanic
from sanic.response import file, file_stream, html, json, redirect, text
from sanic_ext import Extend, openapi

import tools.append_subdir
from tools.ahai_reg import register_by_google_auth, register_by_mail

app = Sanic("Aha_Ai_Test_Api")
Extend(app)
app.config["API_VERSION"] = "0.1.0"
app.config["API_TITLE"] = "Aha Ai Test Api"
app.config["API_DESCRIPTION"] = "Aha Ai Test Api..."
app.config["API_CONTACT_EMAIL"] = "enorenor@gmail.com"

@app.get("/")
async def case_1and2(request) -> HTTPResponse:
    """
    函數“case_1and2”執行子進程命令或程序並捕獲其輸出和錯誤。
    
    Args:
      request: “request”參數是一個對象，表示向服務器發出的 HTTP 請求。它包含請求方法、標頭、查詢參數和正文等信息。在本例中，它用於處理傳入的 HTTP 請求並返回適當的 HTTP
    響應。
    
    Returns:
      HTTPResponse 對象。
    """
    try:
        # 使用 subprocess 執行命令或程序，例如：
        process = Popen(["python", "case_exam/main.py"], stdout=PIPE, stderr=PIPE, text=True)
        output, errors = process.communicate()  # 等待子進程完成並捕獲輸出和錯誤信息

        if errors:
            logger.warning("子進程發生異常:", errors)
            return json({"code": 2, "msg": errors})
        logger.success("子進程執行成功")
        return json({"code": 0, "msg": "success"})
    except CalledProcessError as e:
        logger.error("子進程發生異常:", errors)
        logger.error("子進程返回了非零退出碼:", e.returncode)
        logger.error("錯誤輸出:", e.output)
        return json({"code": 3, "msg": f"{e.returncode} || {e.output}"})


@app.get("/reg")
@openapi.parameter(name="pwd", description="password", required=True, _in="query", type="str")
@openapi.parameter(name="email", description="email", required=True, _in="query", type="str")
@openapi.parameter(name="mode", description="input 'email' or 'google'", required=True, _in="query", type="str")
async def register(request) -> HTTPResponse:
    """
    `register_by_mail` 函數根據提供的模式通過電子郵件或 Google 身份驗證來註冊用戶。
    
    Args:
      request: “request”参数是一个对象，表示向“/reg”端点发出的 HTTP
    請求。它包含有關請求的信息，例如請求方法、標頭和查詢參數。在本例中，“request”對像用於訪問查詢參數“email”、“
    
    Returns:
      该代码返回带有代码和消息的 JSON
    響應。如果模式為“email”或“google”，則返回成功消息，代碼為0。如果模式既不是“email”也不是“google”，則返回消息，說明註冊機僅支持“email”或“google”模式，代碼為
    4。
    """
    email,pwd,mode = request.args.get("email"),request.args.get("pwd"),request.args.get("mode")
    if mode == "email":
        register_by_mail([email,pwd])
        return json({"code": 0, "msg": "Registration completed, however email-registered accounts require self-verification."})
    if mode == "google":
        register_by_google_auth(email,pwd)
        return json({"code": 0, "msg": "success"})
    return json({"code": 4, "msg": "register only support 'email' or 'google' mode"})

@app.exception(Exception)
async def handle_unexpected_error(_, exc) -> HTTPResponse:
    error_message = f"Unknown ERROR，{type(exc).__name__}:{str(exc)}"
    return json(status=500, body={"code":9999,"msg": error_message}, ensure_ascii=False)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8087, workers=4, auto_reload=True)