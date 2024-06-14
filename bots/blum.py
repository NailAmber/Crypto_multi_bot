import random
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

class BlumBot:
    def __init__(self, thread: int, session_name: str, phone_number: str, proxy):
        self.account = session_name + '.session'
        self.thread = thread

        if proxy:
            proxy = {
                "scheme": config.PROXY_TYPE,
                "hostname": proxy.split(":")[1].split("@")[1],
                "port": int(proxy.split(":")[2]),
                "username": proxy.split(":")[0],
                "password": proxy.split(":")[1].split("@")[0]
            }

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

    async def stats(self):
        await asyncio.sleep(random.uniform(5,10))
        await self.login()

        r = await (await self.session.get("https://game-domain.blum.codes/api/v1/user/balance")).json()
        points = r.get('availableBalance')
        plat_passes = r.get('playPasses')

        await asyncio.sleep(random.uniform(5, 7))

        r = await (await self.session.get("https://gateway.blum.codes/v1/friends/balance")).json()
        limit_invites = r.get('limitInvitation')
        referral_link = 't.me/BlumCryptoBot/app?startapp=ref_' + r.get('referralToken')

        await asyncio.sleep()(random.uniform(5, 7))

        r = await (await self.session.get("https://gateway.blum.codes/v1/friend")).json()
        referrals = len(r.get('friends'))

        await self.logout()

        await self.client.connect()
        me = await self.client.get_me()
        phone_number, name = "'" + me.phone_number, f"{me.first_name} {me.last_name if me.last_name is not None else ''}"
        await self.client.disconnect()

        return [phone_number, name, points, str(plat_passes), str(referrals), limit_invites, referral_link]
    
    
    async def tasks(self):
        for task in await self.get_tasks():
            if task['status'] == 'CLAIMED' or task["status"] == "FINISHED" or task['title'] in config.BLACKLIST_TASKS: continue
            # print(task)
            if task['status'] == "NOT_STARTED":
                await self.start_complete_task(task)
                await asyncio.sleep(random.uniform(15, 20))
            elif task['status'] == 'STARTED':
                await asyncio.sleep(random.uniform(15, 20))

            if await self.claim_task(task):
                logger.success(f"Blum | Thread {self.thread} | {self.account} | Completed task «{task['title']}»")
            else:
                logger.error(f"Blum | Thread {self.thread} | {self.account} | Failed complete task «{task['title']}»")

    async def claim_task(self, task: dict):
        resp = await self.session.post(f'https://game-domain.blum.codes/api/v1/tasks/{task["id"]}/claim', proxy=self.proxy)
        return (await resp.json()).get('status') == "CLAIMED"

    async def start_complete_task(self, task: dict):
        resp = await self.session.post(f'https://game-domain.blum.codes/api/v1/tasks/{task["id"]}/start', proxy=self.proxy)

    async def get_tasks(self):
        resp = await self.session.get('https://game-domain.blum.codes/api/v1/tasks', proxy=self.proxy)
        return await resp.json()

    async def claim_task(self, task: dict):
        resp = await self.session.post(f'https://game-domain.blum.codes/api/v1/tasks/{task["id"]}/claim')
        return (await resp.json()).get('status') == "CLAIMED"
    
    async def start_complete_task(self, task: dict):
        resp = await self.session.post(f'https://game-domain.blum.codes/api/v1/tasks/{task["id"]}/start')
        
    async def get_tasks(self):
        resp = await self.session.get('https://game-domain.blum.codes/api/v1/tasks')
        return await resp.json()
    
    async def play_game(self):
        timestamp, start_time, end_time, play_passes = await self.balance()

        while play_passes:
            await asyncio.sleep(random.uniform(2, 8))
            game_id = await self.start_game()

            if not game_id:
                logger.error(f"Blum | Thread {self.thread} | {self.account} | Couldn't start play in game!")
                await asyncio.sleep(random.uniform(2, 8))
                play_passes -= 1
                continue

            logger.info(f"Blum | Thread {self.thread} | {self.account} | Start play in game! GameId: {game_id}")
            await asyncio.sleep(37)

            msg, points = await self.claim_game(game_id)
            if isinstance(msg, bool) and msg:
                logger.success(f"Blum | Thread {self.thread} | {self.account} | Finish play in game!; reward: {points}")
            else:
                logger.error(f"Blum | Thread {self.thread} | {self.account} | Couldn't play game; msg: {msg}")
                await asyncio.sleep(random.uniform(2, 8))

            play_passes -= 1

    async def start_game(self):
        resp = await self.session.post("https://game-domain.blum.codes/api/v1/game/play")
        return (await resp.json()).get("gameId")

    async def claim_daily_reward(self):
        resp = await self.session.post("https://game-domain.blum.codes/api/v1/daily-reward?offset=-180")
        if await resp.text() == 'OK':
            logger.success(f"Blum | Thread {self.thread} | {self.account} | Claimed daily reward!")
    
    async def refresh(self):
        json_data = {'refresh': self.refresh_token}
        resp = await self.session.post("https://gateway.blum.codes/v1/auth/refresh", json=json_data)
        resp_json = await resp.json()
        self.session.headers['Authorization'] = "Bearer " + resp_json.get('access')
        self.refresh_token = resp_json.get('refresh')

    async def claim_game(self, game_id: str):
        points = random.randint(5, 10)
        json_data = {"gameId": game_id, "points": points}

        resp = await self.session.post("https://game-domain.blum.codes/api/v1/game/claim", json=json_data)
        txt = await resp.text()

        return True if txt == 'OK' else txt, points
    
    async def claim(self):
        resp = await self.session.post("https://game-domain.blum.codes/api/v1/farming/claim")
        resp_json = await resp.json()

        return int(resp_json.get("timestamp")/1000), resp_json.get("availableBalance")

    async def start(self):
        resp = await self.session.post("https://game-domain.blum.codes/api/v1/farming/start")

    async def balance(self):
        resp = await self.session.get("https://game-domain.blum.codes/api/v1/user/balance")
        resp_json = await resp.json()
        await asyncio.sleep(1)

        timestamp = resp_json.get("timestamp")
        if resp_json.get("farming"):
            start_time = resp_json.get("farming").get("startTime")
            end_time = resp_json.get("farming").get("endTime")

            return int(timestamp/1000), int(start_time/1000), int(end_time/1000), resp_json.get("playPasses")
        return int(timestamp/1000), None, None, resp_json.get("playPasses")

    async def login(self):
        self.session.headers.pop('Authorization', None)
        query = None
        while query is None:
            query = await self.get_tg_web_data()

            if query is None:
                logger.error(f"Blum | Thread {self.thread} | {self.account} | Session {self.account} invalid, reapeat")
                await asyncio.sleep(60)

        json_data = {"query": query}

        resp = None
        while resp is None:
            try:
                resp = await self.session.post("https://gateway.blum.codes/v1/auth/provider/PROVIDER_TELEGRAM_MINI_APP", json=json_data)

                resp_json = await resp.json()
                self.session.headers['Authorization'] = "Bearer " + resp_json.get("token").get("access")
            except Exception as e:
                logger.error(f"Blum | Thread {self.thread} | {self.account} | Post error {e}, repeat")
                await asyncio.sleep(10)
        
        
        return True


    async def need_new_login(self):
        if (await self.session.get("https://gateway.blum.codes/v1/user/me")).status == 200:
            return False
        else:
            return True
        

    async def get_tg_web_data(self):
        try:
            await self.client.connect()

            web_view = await self.client.invoke(RequestWebView(
                peer=await self.client.resolve_peer('BlumCryptoBot'),
                bot=await self.client.resolve_peer('BlumCryptoBot'),
                platform='android',
                from_bot_menu=False,
                url='https://telegram.blum.codes/'
            ))

            auth_url = web_view.url
            await self.client.disconnect()
        except:
            return None
        return unquote(string=unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]))
            