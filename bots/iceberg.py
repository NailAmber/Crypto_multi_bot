from utilities.logger import logger
from pyrogram import Client
from pyrogram.raw.functions.messages import RequestWebView
import asyncio
from urllib.parse import unquote
import aiohttp
from utilities import config
from fake_useragent import UserAgent
from utilities.register import lang_code_by_phone
import ssl

class IcebergBot:
    def __init__(self, thread: int, session_name: str, phone_number: str):
        self.account = session_name + '.session'
        self.thread = thread

        self.client = Client(
            name=session_name,
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            workdir=config.WORKDIR,
            lang_code=lang_code_by_phone(phone_number)
        )

        headers = {'User-Agent': UserAgent(os='android').random}

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        self.session = aiohttp.ClientSession(headers=headers, trust_env=True, connector=aiohttp.TCPConnector(ssl=ssl_context))
        self.refresh_token = ''


    async def claim_daily_reward(self):
        header_token = None
        while header_token is None:
            header_token = await self.get_query()
            if header_token is None:
                logger.error(f"Iceberg | Thread {self.thread} | Error: No query, repeat")
            await asyncio.sleep(30)

        headers={
            "x-telegram-auth": f'{header_token}' 
        }
        resp = None
        while resp is None:
            try:
                resp = await self.session.delete("https://0xiceberg.store/api/v1/web-app/farming/collect/", headers=headers)
            except Exception as e:
                logger.error(f"Iceberg | Thread {self.thread} | Error Delete: {e}")
                await asyncio.sleep(10)
        
        resp_json = await resp.json()
        if resp.status == 200:
            logger.success(f"Iceberg | Thread {self.thread} | Balance: {resp_json["amount"]}")


    async def start_farming(self):
        header_token = await self.get_query()
        headers={
            "x-telegram-auth": f'{header_token}' 
        }
        resp = None
        while resp is None:
            try:
                resp = await self.session.post("https://0xiceberg.store/api/v1/web-app/farming/", headers=headers)
            except Exception as e:
                logger.error(f"Iceberg | Thread {self.thread} | Error Post: {e}, repeat")
                await asyncio.sleep(10)

        
        resp_json = await resp.json()
        if resp.status == 200:
            logger.info(f"Iceberg | Thread {self.thread} | Farm: {resp_json["amount"]}")
            return resp_json["stop_time"]
        return None
    

    async def get_balance(self):
        header_token = None
        while header_token is None:
            header_token = await self.get_query()
            if header_token is None:
                logger.error(f"Iceberg | Thread {self.thread} | Error: No query, repeat")
                await asyncio.sleep(10)

        headers={
            "x-telegram-auth": f'{header_token}' 
        }
        resp = None
        while resp is None:
            resp = await self.session.get("https://0xiceberg.store/api/v1/web-app/balance/", headers=headers)
            if resp is None:
                logger.error(f"Iceberg | Thread {self.thread} | {self.account} | Get error, repeat")
                await asyncio.sleep(10)
        
        resp_json = await resp.json()
        logger.info(f"Iceberg | Thread {self.thread} | Balance: {resp_json["amount"]}")


    async def get_query(self):
        try:
            await self.client.connect()

            web_view = await self.client.invoke(RequestWebView(
                peer=await self.client.resolve_peer('IcebergAppBot'),
                bot=await self.client.resolve_peer('IcebergAppBot'),
                platform='android',
                from_bot_menu=False,
                url='https://0xiceberg.store'
            ))
            auth_url = web_view.url
            await self.client.disconnect()
        except:
            return None
        return unquote(string=unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]))
        