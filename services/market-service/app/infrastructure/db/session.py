from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.db_async_url
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session():
     async with async_session_factory() as session:
        try:
            yield session
        
        except Exception as e:
            await session.rollback()
            raise e
        
        finally:
            await session.aclose()