from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

# Initialize the Mongo client
client = AsyncIOMotorClient(settings.mongodb_uri)

# If your URI includes the database name (e.g. mongodb://.../mydb),
# you can grab it via get_default_database()
db = client.get_default_database()