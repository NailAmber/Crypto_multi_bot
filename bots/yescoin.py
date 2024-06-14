from utilities.logger import logger
from pyrogram import Client
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import InputBotAppShortName
import asyncio
from urllib.parse import unquote
from utilities import config
import aiohttp
from fake_useragent import UserAgent
from utilities.register import lang_code_by_phone
import ssl
import time

class YesBot:
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


    async def logout(self):
        await self.session.close()


    async def claim_daily_box(self):
        resp_box = await self.session.get("https://api.yescoin.gold/signIn/list")
        resp_json_box = await resp_box.json()
        if resp_json_box["code"] == 0:
            for box in resp_json_box["data"]:
                await asyncio.sleep(2)
                if box["status"] == 1:
                    json_data = {"createAt" : int(time.time()),
                               "destination" : "UQDKeQMvQ71dyUTtbmmTJKhYCJ9I-x9uPQD3TxS5yCb2yFJO",
                               "id" : f"{box["id"]}",
                               "signInType" : 1}
                    headers = {"tm": int(time.time())
                    }
                    resp = await self.session.post("https://api.yescoin.gold/signIn/claim", json=json_data, headers=headers)
                    resp_json = await resp.json()
                    if resp_json["code"] == 0:
                        logger.success(f"YesCoin | Thread {self.thread} | {self.account} | Box opened! Reward: {resp_json["data"]["reward"]}")
                    else:
                        logger.error(f"YesCoin | Thread {self.thread} | {self.account} | Error: {resp_json["data"]["message"]}")


    async def claim_daily_reward(self):
        resp = await self.session.post("https://api.yescoin.gold/game/claimOfflineYesPacBonus")
        resp_json = await resp.json()
        if resp_json['message'] == "Success":
            logger.success(f"YesCoin | Thread {self.thread} | {self.account} | Claimed reward! Reward: {resp_json["data"]["collectAmount"]}")
        else:
            logger.info(f"YesCoin | Thread {self.thread} | {self.account} | {resp_json['message']}")
        await asyncio.sleep(1)
    

    async def login(self):
        
        query = None
        while query is None:
            query = await self.get_query()
            
            if query is None:
                logger.error(f'YesCoin | Thread {self.thread} | {self.account} | Session {self.account} invalid, repeat')
                await asyncio.sleep(30)
            
        json_data = {"code" : query}
        
        resp = None
        while resp is None:
            try:
                resp = await self.session.post("https://api.yescoin.gold/user/login", json=json_data)
            except Exception as e:
                logger.error(f"YesCoin | Thread {self.thread} | {self.account} | Post error: {e}, repeat")
                await asyncio.sleep(10)

        resp_json = await resp.json()
        
        self.session.headers['token'] = resp_json.get("data").get("token")
        return True

    async def need_new_login(self):
        if (await self.session.get("https://api.yescoin.gold/user/info")).status == 200:
            return False
        else:
            return True


    async def get_query(self):
        await asyncio.sleep(10)
        try:
            await self.client.connect()
            
            bot = await self.client.resolve_peer("theYescoin_bot")
            web_view = await self.client.invoke(RequestAppWebView(
                peer=bot,
                platform='android',
                app=InputBotAppShortName(bot_id=bot, short_name="Yescoin"),
                write_allowed=True
            ))
            auth_url = web_view.url
            await self.client.disconnect()
        except:
            return None
        return unquote(string=unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]))
