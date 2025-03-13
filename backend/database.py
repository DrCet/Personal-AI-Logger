from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from backend.config import DATABASE_URL
import logging
from fastapi import Depends
from sqlalchemy.sql import text

logger = logging.getLogger(__name__)

# Optionally, suppress SQLAlchemy engine logs unless debugging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

# Create the async engine with conditional echo
debug_mode = False  # Set to True for debugging
engine = create_async_engine(DATABASE_URL, echo=debug_mode)

AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        logger.info(f"Connected to: {session.bind.url.database}")
        try:
            yield session
        except Exception as e:
            logger.error(f"Session creation failed: {e}")
            raise
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def check_permissions(db: AsyncSession = Depends(get_db)):
    try:
        # Get the current user
        result = await db.execute(text("SELECT current_user;"))
        current_user = result.scalar()
        print(f"Connected as user: {current_user}")

        # Check USAGE privilege on the public schema
        result = await db.execute(
            text("SELECT has_schema_privilege(:user, 'public', 'USAGE');"),
            {"user": current_user}
        )
        usage_privilege = result.scalar()
        print(f"USAGE privilege on 'public' schema: {'Yes' if usage_privilege else 'No'}")

        # Check CREATE privilege on the public schema
        result = await db.execute(
            text("SELECT has_schema_privilege(:user, 'public', 'CREATE');"),
            {"user": current_user}
        )
        create_privilege = result.scalar()
        print(f"CREATE privilege on 'public' schema: {'Yes' if create_privilege else 'No'}")

        # List tables in the public schema to verify access
        result = await db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))
        tables = result.fetchall()
        print("Tables in 'public' schema:", [row[0] for row in tables] if tables else "None found")

        # Get the current database name
        result = await db.execute(text("SELECT current_database();"))
        current_db = result.scalar()
        print(f"Connected to database: {current_db}")

    except Exception as e:
        print(f"Error checking permissions: {e}")
        logger.error(f"Error checking permissions: {e}")
        raise