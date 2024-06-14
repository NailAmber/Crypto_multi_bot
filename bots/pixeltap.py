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

class PilexTapBot:
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

    async def claim_daily_reward(self):
        await self.session.get("https://api-clicker.pixelverse.xyz/api/giveaway-winners/my")
        await self.session.get("https://sexyzbot.pxlvrs.io/")
        await self.session.get("https://api-clicker.pixelverse.xyz/api/users")
        await self.session.get("https://api-clicker.pixelverse.xyz/api/mining/progress")
        await self.session.get("https://api-clicker.pixelverse.xyz/api/tasks/my")
        await asyncio.sleep(10)
        header_token = None
        while header_token is None:
            header_token = await self.get_query()
            if header_token is None:
                logger.error(f"PixelTap | Thread {self.thread} | Error: No query, repeat")
                await asyncio.sleep(30)

        headers={
            "initData": f"{header_token}"
        }
        await asyncio.sleep(10)
        resp = None
        while resp is None:
            try:
                resp = await self.session.post("https://api-clicker.pixelverse.xyz/api/mining/claim", headers=headers)
            except Exception as e:
                logger.error(f"PixelTap | Thread {self.thread} | Error Post: {e}")
                await asyncio.sleep(120)
        if resp.status == 201:
            resp_json = await resp.json()
            logger.success(f"PixelTap | Thread {self.thread} | Claimed! Reward: {resp_json["claimedAmount"]}")
            return resp_json["nextFullRestorationDate"]
        else:
            logger.error(f"PixelTap | Thread {self.thread} | Error: {resp.status}")
            await asyncio.sleep(120)
    
    
    async def get_query(self):
        try:
            await self.client.connect()

            web_view = await self.client.invoke(RequestWebView(
                peer=await self.client.resolve_peer('pixelversexyzbot'),
                bot=await self.client.resolve_peer('pixelversexyzbot'),
                platform='android',
                from_bot_menu=False,
                url='https://api-clicker.pixelverse.xyz'
            ))
            auth_url = web_view.url
            await self.client.disconnect()
        except Exception as e:
            print(e)
            return None
        return unquote(string=unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]))
    