import motor.motor_asyncio
from config import settings

# MongoDB connection
client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
database = client[settings.DATABASE_NAME]

async def get_db():
    return database