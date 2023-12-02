from os import getenv

from dotenv import load_dotenv

load_dotenv()

USERNAME = getenv("USERNAME")
PASSWORD = getenv("PASSWORD")
EMAIL = getenv("EMAIL")
SLACK_WEBHOOK = getenv("SLACK_WEBHOOK")
REGISTER_MAIL = getenv("REGISTER_MAIL")
REGISTER_PWD = getenv("REGISTER_PWD")
SENDGRID_API_KEY = getenv("SENDGRID_API_KEY")