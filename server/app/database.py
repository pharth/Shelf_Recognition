import motor.motor_asyncio
from beanie import init_beanie
from models.user import User
from config import settings

# MongoDB connection
client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
database = client[settings.DATABASE_NAME]

async def init_db():
    """Initialize database with Beanie"""
    await init_beanie(database=database, document_models=[User])

async def get_db():
    return database