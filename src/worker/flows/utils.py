from src.cache import QueryCache, FileCache
from src.clients import RedisClient

async def clear_all_cache():
    redis = await RedisClient.get()
    await QueryCache(redis).clear()
    await FileCache(redis).clear()
