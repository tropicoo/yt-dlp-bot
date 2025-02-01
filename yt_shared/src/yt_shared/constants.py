from asyncio import Lock
from typing import Final

SHARED_ASYNC_LOCK: Final[Lock] = Lock()

INSTAGRAM_HOSTS: Final[tuple[str, ...]] = ('instagram.com', 'www.instagram.com')
TIKTOK_HOSTS: Final[tuple[str, ...]] = (
    'tiktok.com',
    'vm.tiktok.com',
    'www.tiktok.com',
    'www.vm.tiktok.com',
)
TWITTER_HOSTS: Final[tuple[str, ...]] = (
    'twitter.com',
    'www.twitter.com',
    'x.com',
    'www.x.com',
    't.co',
    'www.t.co',
)
FACEBOOK_HOSTS: Final[tuple[str, ...]] = ('facebook.com', 'www.facebook.com')

REMOVE_QUERY_PARAMS_HOSTS: Final[set[str]] = {
    *TWITTER_HOSTS,
    *INSTAGRAM_HOSTS,
    *FACEBOOK_HOSTS,
}
