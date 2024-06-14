from utilities.logger import logger
from pyrogram import Client
from pyrogram.raw.functions.messages import RequestWebView
import asyncio
from urllib.parse import unquote
from utilities import config
import aiohttp
from fake_useragent import UserAgent
from utilities.register import lang_code_by_phone
import ssl
from datetime import datetime

class TimeFarmBot:
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


    async def finish_daily_reward(self):
        resp = await self.session.post("https://tg-bot-tap.laborx.io/api/v1/farming/finish")
        resp_json = await resp.json()
        if resp.status == 200:
            logger.success(f"TimeFarm | Thread {self.thread} | {self.account} | Finish farm, Balance: {resp_json.get("balance")}")
        else:
            logger.info(f"TimeFarm | Thread {self.thread} | {self.account} | Farm is not finishing yes")
                                    

    async def claim_daily_reward(self):
        resp_info = await self.session.get("https://tg-bot-tap.laborx.io/api/v1/farming/info")
        resp_info_json = await resp_info.json()

        resp = await self.session.post("https://tg-bot-tap.laborx.io/api/v1/farming/start")

        if resp.status == 200:
            logger.success(f"TimeFarm | Thread {self.thread} | {self.account} | Farm starting, sleep")
            return resp_info_json["farmingDurationInSec"]
        else:
            logger.info(f"TimeFarm | Thread {self.thread} | {self.account} | Farm already start, sleep")
            now = datetime.now()
            now_seconds = now.hour * 3600 + now.minute * 60 + now.second
            start_time = datetime.strptime(resp_info_json["activeFarmingStartedAt"], "%Y-%m-%dT%H:%M:%S.%fZ")
            start_time_seconds = start_time.hour * 3600 + 3600 * 3 + start_time.minute * 60 + start_time.second
            end_time_seconds = start_time_seconds + resp_info_json["farmingDurationInSec"]
            if end_time_seconds > now_seconds:
                return end_time_seconds - now_seconds
            else:
                return end_time_seconds + 24 * 60 - now_seconds
            
            
    async def login(self):
        
        query = None
        while query is None:
            query = await self.get_query()
            
            if query is None:
                logger.error(f'TimeFarm | Thread {self.thread} | {self.account} | Session {self.account} invalid, repeat')
                await asyncio.sleep(30)
            
        # json_data = {"code" : query}
        
        resp = None
        while resp is None:
            try:
                resp = await self.session.post("https://tg-bot-tap.laborx.io/api/v1/auth/validate-init", data=query)
                resp_json = await resp.json()
                self.session.headers['authorization'] = "Bearer " + resp_json.get("token")
            except Exception as e:
                logger.error(f"TimeFarm | Thread {self.thread} | {self.account} | Post error: {e}, repeat")
                await asyncio.sleep(10)

        
        return True

    async def need_new_login(self):
        if (await self.session.get("https://tg-bot-tap.laborx.io/api/v1/farming/info")).status == 200:
            return False
        else:
            return True


    async def get_query(self):
        await asyncio.sleep(15)
        try:
            await self.client.connect()

            web_view = await self.client.invoke(RequestWebView(
                peer=await self.client.resolve_peer('TimeFarmCryptoBot'),
                bot=await self.client.resolve_peer('TimeFarmCryptoBot'),
                platform='android',
                from_bot_menu=False,
                url='https://tg-bot-tap.laborx.io'
            ))

            auth_url = web_view.url
            await self.client.disconnect()
        except:
            return None
        return unquote(string=unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]))
            
