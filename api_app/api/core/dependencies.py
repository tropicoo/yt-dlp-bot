from yt_shared.rabbit.publisher import Publisher


async def get_publisher():
    yield Publisher()
