from asyncio import Lock

ASYNC_LOCK = Lock()


INSTAGRAM_HOSTS = (
    'instagram.com',
    'www.instagram.com',
)
TIKTOK_HOSTS = (
    'tiktok.com',
    'vm.tiktok.com',
    'www.tiktok.com',
    'www.vm.tiktok.com',
)
TWITTER_HOSTS = (
    'twitter.com',
    'www.twitter.com',
    'x.com',
    'www.x.com',
    't.co',
    'www.t.co',
)

REMOVE_QUERY_PARAMS_HOSTS = TWITTER_HOSTS + INSTAGRAM_HOSTS
