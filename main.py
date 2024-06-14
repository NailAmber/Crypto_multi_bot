from utilities.register import create_sessions
from utilities.telegram import Accounts
from starter import startBlum, startYes, startIceberg, startPixelTap, startTimeFarm
import asyncio
import os


async def main():
    action = int(input("\n1. Create a session\n2. Start claimer\n\n>"))

    if not os.path.exists('sessions'): os.mkdir('sessions')
    if not os.path.exists('statistics'): os.mkdir('statistics')
    if not os.path.exists('sessions/accounts.json'):
        with open("sessions/accounts.json", 'w') as f:
            f.write("[]")

    if action == 1:
        await create_sessions()

    if action == 2:
        accounts = await Accounts().get_accounts()
        
        tasks = []
        for thread, account in enumerate(accounts):
            session_name, phone_number, proxy = account.values()
            tasks.append(asyncio.create_task(startBlum(session_name=session_name, thread=thread, phone_number=phone_number)))
            tasks.append(asyncio.create_task(startYes(session_name=session_name, thread=thread, phone_number=phone_number)))
            tasks.append(asyncio.create_task(startIceberg(session_name=session_name, thread=thread, phone_number=phone_number)))
            tasks.append(asyncio.create_task(startPixelTap(session_name=session_name, thread=thread, phone_number=phone_number)))
            tasks.append(asyncio.create_task(startTimeFarm(session_name=session_name, thread=thread, phone_number=phone_number)))
        try:
            await asyncio.gather(*tasks)
        except OSError as e:
            if e.winerror == 121:
                print("121 - gather loop error")
            else:
                raise


if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except OSError as e:
            if e.winerror == 121:
                print("121 - loop error")
            else:
                raise