from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

engine = create_async_engine(settings.db_async_url)

async_session = async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_postgres_connection():

    async with async_session() as session:
        try:
            yield session
        
        except Exception as e:
            await session.rollback()
            raise e
        
        finally:
            await session.aclose()