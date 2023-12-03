import contextlib
from time import sleep

from seleniumbase import BaseCase

from modules.load_config import PASSWORD, REGISTER_MAIL, REGISTER_PWD, USERNAME


class AhaAI(BaseCase):
        
    def test_case1_login(self) -> None:
        """
        * case 1
        執行一系列操作來模擬登錄過程並驗證登錄是否成功。
        """
        self.open("https://earnaha.com/")
        self.click('a[href="https://app.earnaha.com/api/auth/login"]')
        self.click('button[data-action-button-secondary="true"]')
        self.type('input[name="identifier"]' ,USERNAME)
        self.click("#identifierNext")
        self.type('input[name="Passwd"]', PASSWORD)
        self.click("#passwordNext")
        verify_login = bool(self.find_text("All Clubs",timeout=20))
        self.assert_true(verify_login, msg="Login Fail")
        
    def test_case2_logout(self) -> None:
        """
        * case 2
        該函數通過單擊頭像、導航到設置頁面、單擊 logout 按鈕並驗證用戶是否重定向到登錄頁面來測試 logout 功能。
        """
        self.click(".MuiAvatar-root.MuiAvatar-circular.css-2qlgr0",timeout=20)
        self.click('a[href="/profile/settings"]')
        self.click("//button[text()='LOG OUT']",by="xpath")
        self.click("//button[text()='Yes']",by="xpath")
        verify_logout = bool(self.find_text("Login to Practice",timeout=20))
        self.assert_true(verify_logout, msg="Login Fail")
        
    def test_edit_profile(self) -> None:
        """
        * case 3
        透過登入網站後，單擊各種元素來編輯用戶的個人資料中的生日，再保存更改。
        """
        self.open("https://earnaha.com/")
        self.click('a[href="https://app.earnaha.com/api/auth/login"]')
        self.click('button[data-action-button-secondary="true"]')
        self.click(".MuiAvatar-root.MuiAvatar-circular.css-2qlgr0",timeout=20)
        self.click('a[href="/profile/account/edit"]')
        self.click('input[name="birthday"]')
        self.click('button[title="Previous month"]')
        self.click(".MuiButtonBase-root.css-11duv1i")
        self.click("//button[text()='OK']",by="xpath")
        self.click("//div[text()='Save']",by="xpath")
        self.wait_for_element("//p[text()='Changes saved successfully!']",by="xpath")
        self.driver.quit()

    
    def test_register_by_google_auth(self) -> None:
        """
        * case 4
        """
        # self.get_new_driver()
        self.open("https://earnaha.com/")
        self.delete_all_cookies()
        self.click('a[href="https://app.earnaha.com/api/auth/signup"]')
        self.type("#email", REGISTER_MAIL)
        self.type("#password", REGISTER_PWD)
        self.click("//button[text()='Continue']",by="xpath")
        self.open("https://gmail.com/")
        self.type('input[name="identifier"]', REGISTER_MAIL)
        self.click("#identifierNext")
        self.type('input[name="Passwd"]', REGISTER_PWD)
        self.click("#passwordNext")
        # self.click("//span[text()='Verify your account | Aha']",by="xpath",timeout=600)
        self.wait_for_text("Verify your account")
        self.find_elements("//span[text()='Verify your account | Aha']")[-1].click()
        self.click("a[href*='email-verification']")
        self.find_text("All Clubs",timeout=30)
        self.driver.quit()

    def test_register_by_mail(self) -> None:
        """
        * case 4 : special 10 min email
        """
        self.get_new_driver()
        self.open("https://earnaha.com/")
        self.delete_all_cookies()
        self.click('a[href="https://app.earnaha.com/api/auth/signup"]')
        self.execute_script("window.open('https://10minutemail.net/?lang=zh-tw', '_blank');")
        def gen_pwd() -> str:
            from random import choice, choices, sample
            from string import ascii_letters, ascii_lowercase, ascii_uppercase, digits, punctuation
            pwd = f"{choice(ascii_lowercase)}{choice(ascii_uppercase)}{choice(punctuation)}" + "".join(choices(f"{ascii_letters}{digits}{punctuation}", k=5))
            return "".join(sample(pwd, len(pwd)))
        pwd = gen_pwd()
        self.switch_to_window(-1)
        email = self.get_attribute("#fe_text","value")
        self.switch_to_window(0)
        self.type("#email", email)
        self.type("#password", pwd)
        self.click("//button[text()='Continue']",by="xpath")
        self.switch_to_window(1)
        verify_url = None
        while verify_url is None:
            sleep(3)
            self.refresh()
            with contextlib.suppress(Exception):
                self.click('//a[text()="Verify your account | Aha"]')
                verify_url = self.get_text('//*[@id="tab1"]/div[2]/div/div/div/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[3]/td/table/tbody/tr[3]/td[2]')
        self.open(verify_url)

def main() -> None:
    BaseCase.main(__name__, __file__,"--rs","--uc")

if __name__ == "__main__":
    main()
