import asyncio
import os
import signal

from presentation.db import database, create_tables
print("create_tables imported")
from infrastructure.repositories.sql_trash_repo import SQLTrashRepository
from infrastructure.repositories.sql_user_repo import SQLUserRepository
from application.services.self_delete_x_time import DeleteXTime


INTERVAL_SECONDS = int(os.getenv("SELF_DELETE_INTERVAL_SECONDS", "86400"))  # default once per day


async def run_worker():
    await database.connect()
    await create_tables(database)

    repo = SQLTrashRepository()
    user_repo = SQLUserRepository()

    ttl_days = int(os.getenv("SELF_DELETE_TTL_DAYS", "30"))
    deleter = DeleteXTime(repo, ttl_days,user_repo)

    try:
        while True:
            try:
                users = await user_repo.get_all()
                total_deleted = 0

                for user in users:
                    total_deleted += await deleter.execute_all(user.uuid)

                print(f"Self-delete: removed {total_deleted} notes")
            except Exception as e:
                print("Error during self-delete run:", e)

            await asyncio.sleep(INTERVAL_SECONDS)
    finally:
        await database.disconnect()


async def _handle_signals():
    loop = asyncio.get_running_loop()
    stop = loop.create_future()

    def _handle(sig, frame):
        stop.set_result(sig)

    signal.signal(signal.SIGTERM, _handle)
    signal.signal(signal.SIGINT, _handle)
    return await stop

async def main():
    # Run the worker as a task and wait for signals
    worker_task = asyncio.create_task(run_worker())
    signal_future = await _handle_signals()
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    asyncio.run(main())

