from bots.blum import BlumBot
from bots.yescoin import YesBot
from bots.iceberg import IcebergBot
from bots.pixeltap import PilexTapBot
from bots.timefarm import TimeFarmBot
from asyncio import sleep
from random import uniform
from utilities.logger import logger
import datetime
import pandas as pd
from utilities.telegram import Accounts
import asyncio
from aiohttp.client_exceptions import ContentTypeError
from datetime import datetime
import time

async def startBlum(thread: int, session_name: str, phone_number: str):
    blum = BlumBot(session_name=session_name, thread=thread, phone_number=phone_number, proxy=None)
    account = session_name + '.session'

    await sleep(uniform(5, 15))
    await blum.login()

    while True:
        try:

            await asyncio.sleep(5)
            if await blum.need_new_login():
                if await blum.login() is None:
                    return
                
            msg = await blum.claim_daily_reward()
            if isinstance(msg, bool) and msg:
                logger.success(f"Blum | Thread {thread} | Claimed daily reward!")

            timestamp, start_time, end_time, play_passes = await blum.balance()

            await blum.claim_daily_reward()
            await sleep(uniform(2, 8))

            await blum.play_game()
            await sleep(uniform(2, 8))

            await blum.tasks()
            await sleep(uniform(2, 8))

            timestamp, start_time, end_time, play_passes = await blum.balance()

            if start_time is None and end_time is None:
                await blum.start()
                logger.info(f"Blum | Thread {thread} | {account} | Start farming!")

            elif start_time is not None and end_time is not None and timestamp >= end_time:
                timestamp, balance = await blum.claim()
                logger.success(f"Blum | Thread {thread} | {account} | Claimed reward! Balance: {balance}")

            else:
                logger.info(f"Blum | Thread {thread} | {account} | Sleep {end_time - timestamp} seconds!")
                await sleep(end_time - timestamp)

            await sleep(30)

        except OSError as e:
            if e.winerror == 121:
                logger.warning(f"Blum | Thread {thread} | {account} | WinError 121, ignoring it")
            else:
                raise

        except ContentTypeError as e:
            logger.error(f"Blum | Thread {thread} | {account} | Error: {e}")
            await asyncio.sleep(120)

        except Exception as e:
            logger.error(f"Blum | Thread {thread} | {account} | Error: {e}")


async def startYes(thread: int, session_name: str, phone_number: str):
    yesbot = YesBot(session_name=session_name, thread=thread, phone_number=phone_number)
    account = session_name + '.session'
    await sleep(uniform(5, 15))
    await yesbot.login()

    while True:
        try:
            await asyncio.sleep(5)
            if await yesbot.need_new_login():
                if await yesbot.login() is None:
                    return
                
            await yesbot.claim_daily_reward()
            
            logger.info(f"YesCoin | Thread {thread} | {account} | Sleep {6 * 60 * 60} seconds!")
            await sleep(6 * 60 * 60)

            await sleep(30)

        except OSError as e:
            if e.winerror == 121:
                logger.warning(f"YesCoin | Thread {thread} | {account} | WinError 121, ignoring it")
            else:
                raise

        except Exception as e:
            logger.error(f"YesCoin | Thread {thread} | Error: {e}")
            await sleep(120)


async def startIceberg(thread: int, session_name: str, phone_number: str):
    icebergbot = IcebergBot(session_name=session_name, thread=thread, phone_number=phone_number)
    account = session_name + '.session'
    await sleep(uniform(5, 15))

    while True:
        try:
            await icebergbot.claim_daily_reward()
            await sleep(uniform(2, 8))

            await icebergbot.get_balance()
            await sleep(uniform(5, 8))

            stop_time_resp = await icebergbot.start_farming()
            if stop_time_resp is not None:
                current_time_str = datetime.now().strftime("%H:%M:%S")
                current_time = current_time_str.split(":")
                stop_time = stop_time_resp.split(":")
                stop_time_in_seconds = (int(stop_time[0][-2:])+3) * 60 * 60 + int(stop_time[1]) * 60 + int(stop_time[2][:2])
                current_time_in_seconds = int(current_time[0]) * 60 * 60 + int(current_time[1]) * 60 + int(current_time[2])
                if stop_time_in_seconds < current_time_in_seconds:
                    sleep_time = 24 * 60 * 60 - current_time_in_seconds + stop_time_in_seconds
                else:
                    sleep_time = stop_time_in_seconds - current_time_in_seconds
                logger.info(f"Iceberg | Thread {thread} | {account} | Sleep {sleep_time}")
                await sleep(sleep_time)
                
            await sleep(30)

        except OSError as e:
            if e.winerror == 121:
                logger.warning(f"Iceberg | Thread {thread} | {account} | WinError 121, ignoring it")
            else:
                raise

        except Exception as e:
            logger.error(f"iceberg | Thread {thread} | Error: {e}")
            await sleep(120)
        
    
async def startPixelTap(thread: int, session_name: str, phone_number: str):
    pixeTapBot = PilexTapBot(session_name=session_name, thread=thread, phone_number=phone_number)
    account = session_name + '.session'
    await sleep(uniform(5, 15))

    while True:
        try:
            stop_time = await pixeTapBot.claim_daily_reward()

            if stop_time is not None:
                date_obj = datetime.strptime(stop_time, "%Y-%m-%dT%H:%M:%S.%fZ")
                stop_timestamp = date_obj.timestamp()
                sleep_time = (stop_timestamp - time.time()) / 2
                logger.info(f"PixelTap | Thread {thread} | {account} | Sleep {sleep_time}")
                await sleep(sleep_time)
            
            await sleep(30)

        except OSError as e:
            if e.winerror == 121:
                logger.warning(f"PixelTap | Thread {thread} | {account} | WinError 121, ignoring it")
            else:
                raise

        except Exception as e:
            logger.error(f"PixelTap | Thread {thread} | Error: {e}")
            await sleep(120)


async def startTimeFarm(thread: int, session_name: str, phone_number: str):
    timeFarmBot = TimeFarmBot(session_name=session_name, thread=thread, phone_number=phone_number)
    account = session_name + '.session'
    await sleep(uniform(5, 15))
    await timeFarmBot.login()

    while True:
        try:
            await asyncio.sleep(5)
            if await timeFarmBot.need_new_login():
                if await timeFarmBot.login() is None:
                    return
                
            await timeFarmBot.finish_daily_reward()
            await sleep(uniform(5, 15))

            sleep_time = await timeFarmBot.claim_daily_reward()

            if sleep_time is not None:
                logger.info(f"TimeFarm | Thread {thread} | {account} | Sleep {sleep_time}")
                await sleep(sleep_time)

            await sleep(uniform(5, 15))
            await sleep(30)

        except OSError as e:
            if e.winerror == 121:
                logger.warning(f"TimeFarm | Thread {thread} | {account} | WinError 121, ignoring it")
            else:
                raise

        except Exception as e:
            logger.error(f"TimeFarm | Thread {thread} | Error: {e}")
            await sleep(120)


async def stats():
    accounts = await Accounts().get_accounts()

    tasks = []
    for thread, account, in enumerate(accounts):
        if not account: break
        tasks.append(asyncio.create_task(BlumBot(account=account, thread=thread).stats()))

    data = await asyncio.gather(*tasks)

    path = f"statistics/statistics_{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.csv"
    columns = ['Phone number', 'Name', 'Points', 'Play passes', 'Referrals', 'Limit invites', 'Referral link']

    df = pd.DataFrame(data, columns=columns)
    df['Name'] = df['Name'].astype(str)
    df.to_csv(path, index=False, encoding='urf-8-sig')

    logger.success(f"Saved statistics to {path}")