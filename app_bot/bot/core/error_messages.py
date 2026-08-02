"""Translation of yt-dlp failure reasons into human-readable messages.

Most download failures are not bugs: the tweet was posted by a suspended
account, the video is private, the channel is members-only and so on. Those
cases deserve a short explanation instead of a stack trace, which is what this
module provides. Anything not recognised here is treated as a real error and
reported with full details.
"""

import re
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class FriendlyError:
    """A recognised, expected download failure."""

    emoji: str
    title: str
    hint: str


_SUSPENDED = FriendlyError(
    '🚫',
    'Account suspended',
    'The account that posted this has been suspended, so the media is no longer '
    'served by the site.',
)
_PRIVATE = FriendlyError(
    '🔒',
    'Private content',
    'This content is private and cannot be accessed without permission from its owner.',
)
_REMOVED = FriendlyError(
    '🗑',
    'Content removed',
    'This content has been deleted or taken down and is no longer available.',
)
_AGE_RESTRICTED = FriendlyError(
    '🔞',
    'Age-restricted content',
    'The site only serves this to a signed-in adult account. Adding cookies for a '
    'logged-in account may help.',
)
_LOGIN_REQUIRED = FriendlyError(
    '🍪',
    'Login required',
    'The site refused to serve this without an authenticated session. Add your '
    'cookies to fix it — see the Cookies section in the README.',
)
_GEO_BLOCKED = FriendlyError(
    '🌍',
    'Blocked in this region',
    'The site does not serve this content from the server\'s location.',
)
_NOT_STARTED = FriendlyError(
    '⏳',
    'Not available yet',
    'This is an upcoming stream or premiere. Try again once it has started.',
)
_MEMBERS_ONLY = FriendlyError(
    '💎',
    'Members-only content',
    'This is restricted to channel members. Cookies for a subscribed account are '
    'required.',
)
_DRM = FriendlyError(
    '🔒',
    'Protected by DRM',
    'This site encrypts its media, so yt-dlp will not download from it. Spotify, '
    'Netflix, Disney+ and similar services all work this way.',
)
_SITE_UNSUPPORTED = FriendlyError(
    '🚷',
    'Site not supported',
    'yt-dlp deliberately does not support this site and will not add it.',
)
_SUBSCRIPTION = FriendlyError(
    '💳',
    'Paid content',
    'The account behind the cookies does not have access to this. A subscription '
    'or purchase is required.',
)
_NETWORK = FriendlyError(
    '🌐',
    'Could not reach the site',
    'The request never completed. This is usually temporary — try again shortly.',
)
_NO_MEDIA = FriendlyError(
    '📭',
    'Nothing to download',
    'The link opens fine, but there is no video or audio in it to download.',
)
_FORMAT_UNAVAILABLE = FriendlyError(
    '🎞',
    'Requested quality unavailable',
    'The chosen quality does not exist for this media. Try another one.',
)
_RATE_LIMITED = FriendlyError(
    '🐌',
    'Rate limited',
    'The site is temporarily refusing requests from this server. Wait a while and '
    'try again.',
)
_UNSUPPORTED_URL = FriendlyError(
    '🔗',
    'Unsupported link',
    'yt-dlp has no extractor for this URL. Double-check the link is correct.',
)
_NOT_FOUND = FriendlyError(
    '🔍',
    'Not found',
    'The site returned 404 for this link. It is likely wrong or already deleted.',
)
_FORBIDDEN = FriendlyError(
    '⛔',
    'Access denied',
    'The site returned 403. It may require cookies or be blocking this server.',
)
_UNAVAILABLE = FriendlyError(
    '❓',
    'Content unavailable',
    'The site reports this content as unavailable without giving a specific reason.',
)

# Ordered from most to least specific: the first match wins, so narrow patterns
# such as "sign in to confirm your age" must be tried before the broad ones.
_PATTERNS: Final[tuple[tuple[re.Pattern[str], FriendlyError], ...]] = tuple(
    (re.compile(pattern, re.IGNORECASE), error)
    for pattern, error in (
        # Refusals yt-dlp issues on principle, before it even looks at the URL.
        (r'known to use drm|drm protection|drm[- ]protected', _DRM),
        (r'primarily used for piracy|not supported and will not be supported'
         r'|no longer supported since', _SITE_UNSUPPORTED),
        (r'\bsuspended\b', _SUSPENDED),
        (r'sign in to confirm your age|age[- ]restricted|\bnsfw\b', _AGE_RESTRICTED),
        (r"members[- ]only|join this channel|channel's members", _MEMBERS_ONLY),
        (r'will begin in|premieres in|\bupcoming\b|has not started', _NOT_STARTED),
        (r'available in your country|geo[- ]?restrict|geo[- ]?block'
         r'|blocked it in your country|available from your location', _GEO_BLOCKED),
        # Checked before the broad "private" rule: these say "sign in" too.
        # yt-dlp writes some of these with a typographic apostrophe.
        (r"confirm you['’]re not a bot|cookies are no longer valid"
         r'|use --cookies', _LOGIN_REQUIRED),
        # "Private video. Sign in if you've been granted access" must not be
        # mistaken for a plain authentication problem.
        (r'\bprivate\b|\bprotected\b', _PRIVATE),
        (r'\bremoved\b|\bdeleted\b|taken down|terminated', _REMOVED),
        (r'not subscribed|subscription required|requires a subscription'
         r'|purchase this|rent this|paid (?:video|content)', _SUBSCRIPTION),
        (r'login required|requires authentication|authentication is required'
         r'|\bsign in\b|\blog in\b', _LOGIN_REQUIRED),
        # "No video in this post" is a different problem from "the formats I
        # asked for are missing", so it is matched first.
        (r'no video could be found|there ?i?s no video|no media could be found'
         r'|no media found|unable to find media', _NO_MEDIA),
        (r'requested format is not available|no video formats found'
         r'|requested format not available', _FORMAT_UNAVAILABLE),
        (r'too many requests|rate[- ]?limit|http error 429', _RATE_LIMITED),
        (r'unsupported url|is not a valid url', _UNSUPPORTED_URL),
        (r'http error 404|\bnot found\b', _NOT_FOUND),
        (r'http error 403|\bforbidden\b', _FORBIDDEN),
        (r'unable to download (?:webpage|json|xml|api page)|a network error'
         r'|failed to resolve|connection (?:broken|reset|refused)|timed out'
         r'|read timeout', _NETWORK),
        (r'unavailable|does not exist|no longer available', _UNAVAILABLE),
    )
)

# yt-dlp prefixes reasons with the extractor name and media id,
# e.g. "[twitter] 2083594794454921589: Suspended".
_EXTRACTOR_PREFIX: Final[re.Pattern[str]] = re.compile(r'^\[[^\]]+\]\s*[^:]*:\s*')


def classify(reason: str | None) -> FriendlyError | None:
    """Map a raw yt-dlp failure reason to a friendly error, if it is a known one."""
    if not reason:
        return None
    for pattern, error in _PATTERNS:
        if pattern.search(reason):
            return error
    return None


def strip_extractor_prefix(reason: str) -> str:
    """Remove yt-dlp's "[extractor] id: " prefix from a failure reason."""
    return _EXTRACTOR_PREFIX.sub('', reason).strip()


def extract_reason(raw: str) -> str:
    """Pick the single line that best explains a failure.

    A yt-dlp message leads with the reason and only then dumps frames, whereas a
    Python traceback is the other way round and ends with the exception itself.
    """
    lines = [line.strip() for line in strip_extractor_prefix(raw).splitlines() if line.strip()]
    if not lines:
        return ''
    if lines[0].startswith('Traceback (most recent call last)'):
        return lines[-1]
    return lines[0]
