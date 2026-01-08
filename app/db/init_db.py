import asyncio
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from app.db.session import engine
from app.db.base import Base

async def wait_for_db(max_tries: int = 60, delay_seconds: float = 1.0) -> None:
    last_err: Exception | None = None
    for _ in range(max_tries):
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return
        except OperationalError as e:
            last_err = e
            await asyncio.sleep(delay_seconds)
    raise RuntimeError(f"Database is not ready after {max_tries} tries: {last_err}")

async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def init_db() -> None:
    await wait_for_db()
    await create_tables()
