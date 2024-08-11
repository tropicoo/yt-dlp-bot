from asyncio import Lock

SHARED_ASYNC_LOCK: Lock = Lock()


INSTAGRAM_HOSTS: tuple[str, ...] = (
    'instagram.com',
    'www.instagram.com',
)
TIKTOK_HOSTS: tuple[str, ...] = (
    'tiktok.com',
    'vm.tiktok.com',
    'www.tiktok.com',
    'www.vm.tiktok.com',
)
TWITTER_HOSTS: tuple[str, ...] = (
    'twitter.com',
    'www.twitter.com',
    'x.com',
    'www.x.com',
    't.co',
    'www.t.co',
)
FACEBOOK_HOSTS: tuple[str, ...] = (
    'facebook.com',
    'www.facebook.com',
)


REMOVE_QUERY_PARAMS_HOSTS: set[str] = {
    *TWITTER_HOSTS,
    *INSTAGRAM_HOSTS,
    *FACEBOOK_HOSTS,
}
