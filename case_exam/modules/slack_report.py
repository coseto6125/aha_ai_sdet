import aiohttp
from markdown import markdown
from modules.load_config import SENDGRID_API_KEY, SLACK_WEBHOOK
from orjson import dumps


async def send_slack_report(msg_data) -> tuple[str, str]:
    msg = lambda x:f">驗證: {x[0]}\n>時間: {x[1]}\n>狀態: {x[2]}\n{sub_msg(x[3],x[4],x[5]) if x[4] else ''}\n"
    sub_msg = lambda x,y,z:f"```位置: {x}\n異常: {y}\n詳細:\n{z}```"
    
    total = passed = failed = 0
    result_msg = ""
    for _i in msg_data:
        total+=1
        match _i[2]:
            case ":passed:":
                passed+=1
            case ":failed:":
                failed+=1
        result_msg += msg(_i)
    pass_percent = round(passed/total*100,2)

    async with aiohttp.request("POST", SLACK_WEBHOOK, data=dumps({"text": result_msg})) as response:
        print(f"send to slack : {await response.text()}")
    title = f"Aha Ai <<測試報告>> 自動化A 測試報告: {total=}, {passed=}, {failed=}, Pass%:{pass_percent}"
    return title, result_msg

async def send_email_report(subject,html_content) -> None:
    from_email = "ahaienor@gmail.com"
    to_emails = ["ahaienor@gmail.com"]
    html_content = markdown(html_content).replace("\n","<br>").replace(":failed:","FAILED").replace(":passed:","PASSED")
    url = "https://api.sendgrid.com/v3/mail/send"
    
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "personalizations": [
            {
                "to": [{"email": email} for email in to_emails],
                "subject": subject
            }
        ],
        "from": {"email": from_email},
        "content": [
            {
                "type": "text/html",
                "value": html_content
            }
        ]
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 202:
                print("郵件已成功發送")
            else:
                print("郵件發送失敗")

if __name__ == "__main__":
    import asyncio
    asyncio.run(send_email_report("1"))
