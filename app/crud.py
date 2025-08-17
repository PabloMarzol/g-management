from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Client, CashRun

async def get_clients(db: AsyncSession):
    res = await db.execute(select(Client).order_by(Client.name))
    return res.scalars().all()

async def create_client(db: AsyncSession, **kwargs):
    c = Client(**kwargs)
    db.add(c)
    await db.commit()
    return c