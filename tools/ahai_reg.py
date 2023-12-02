import contextlib
from time import sleep

from seleniumbase import SB, BaseCase


def register_by_mail(reg_data:list[str]|None=None) -> None:
    """
    * case 4 - 1
    前往網站 10 min email 網站創建email，生成隨機密碼。
    填寫電子郵件和密碼，點選註冊，再通過電子郵件中的鏈接驗證帳戶。
    """
    with SB() as sb:
        sb: type[BaseCase]
        sb.open("https://earnaha.com/")
        sb.click('a[href="https://app.earnaha.com/api/auth/signup"]')
        if reg_data is None:
            sb.execute_script("window.open('https://10minutemail.net/?lang=zh-tw', '_blank');")
            def gen_pwd():
                from random import choice, choices, sample
                from string import ascii_letters, ascii_lowercase, ascii_uppercase, digits, punctuation
                pwd = f"{choice(ascii_lowercase)}{choice(ascii_uppercase)}{choice(punctuation)}" + "".join(choices(f"{ascii_letters}{digits}{punctuation}", k=5))
                return "".join(sample(pwd, len(pwd)))
            pwd = gen_pwd()
            sb.switch_to_window(-1)
            email = sb.get_attribute("#fe_text","value")
            sb.switch_to_window(0)
        else:
            email,pwd = reg_data
        sb.type("#email", email)
        sb.type("#password", pwd)
        sb.click("//button[text()='Continue']",by="xpath")
        sb.switch_to_window(1)
        verify_url = None
        while verify_url is None:
            sleep(3)
            sb.refresh()
            # sb.refresh_page()
            with contextlib.suppress(Exception):
                sb.click('//a[text()="Verify your account | Aha"]')
                verify_url = sb.get_text('//*[@id="tab1"]/div[2]/div/div/div/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[3]/td/table/tbody/tr[3]/td[2]')
        sb.open(verify_url)


def register_by_google_auth(register_mail,register_pwd) -> None:
    """
    * case 4 - 2
    """
    with SB() as sb:
        sb: type[BaseCase]
        sb.open("https://earnaha.com/")
        sb.click('a[href="https://app.earnaha.com/api/auth/signup"]')
        sb.click('button[data-action-button-secondary="true"]')
        sb.type('input[name="identifier"]', register_mail)
        sb.click("#identifierNext")
        sb.type('input[name="Passwd"]', register_pwd)
        sb.click("#passwordNext")
        sb.open("https://gmail.com/")
        sb.click("span:contains('Verify your account | Aha')")
        sb.click("a[href*='email-verification']")