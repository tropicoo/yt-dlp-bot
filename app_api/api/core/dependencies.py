from yt_shared.rabbit.publisher import RmqPublisher


async def get_rmq_publisher():
    yield RmqPublisher()
