from dataclasses import dataclass
from os import environ
from boto3.session import Session

from aiogram import Bot, Dispatcher
from botocore.client import BaseClient
from dotenv import load_dotenv


load_dotenv()


@dataclass
class Config:
    bot: Bot
    dp: Dispatcher
    s3_client: BaseClient
    s3_baseurl: str
    yandex_schedule_api_key: str


def load_config():
    bot = Bot(
        token=environ.get("BOT_TOKEN"),
        parse_mode="HTML"
    )
    dp = Dispatcher()
    s3_session = Session()
    s3 = s3_session.client(
        service_name="s3",
        endpoint_url=environ.get("S3_ENDPOINT"),
        aws_access_key_id=environ.get("YANDEX_S3_ID"),
        aws_secret_access_key=environ.get("YANDEX_S3_SECRET")
    )

    return Config(
        bot=bot,
        dp=dp,
        s3_client=s3,
        s3_baseurl=environ.get("S3_ENDPOINT"),
        yandex_schedule_api_key=environ.get("YANDEX_SCHEDULE_API_KEY")
    )


config = load_config()
