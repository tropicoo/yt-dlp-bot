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
    """A recognised, expected download failure.

    The wording lives in the message catalogues under ``reason.<name>_title``
    and ``reason.<name>_hint``, so the same failure reads in whichever language
    the recipient has configured.
    """

    emoji: str
    name: str

    @property
    def title_key(self) -> str:
        return f'reason.{self.name}_title'

    @property
    def hint_key(self) -> str:
        return f'reason.{self.name}_hint'


_SUSPENDED = FriendlyError('🚫', 'suspended')
_PRIVATE = FriendlyError('🔒', 'private')
_REMOVED = FriendlyError('🗑', 'removed')
_AGE_RESTRICTED = FriendlyError('🔞', 'age_restricted')
_LOGIN_REQUIRED = FriendlyError('🍪', 'login_required')
_GEO_BLOCKED = FriendlyError('🌍', 'geo_blocked')
_NOT_STARTED = FriendlyError('⏳', 'not_started')
_MEMBERS_ONLY = FriendlyError('💎', 'members_only')
_DRM = FriendlyError('🔒', 'drm')
_SITE_UNSUPPORTED = FriendlyError('🚷', 'site_unsupported')
_SUBSCRIPTION = FriendlyError('💳', 'subscription')
_NETWORK = FriendlyError('🌐', 'network')
_NO_MEDIA = FriendlyError('📭', 'no_media')
_FORMAT_UNAVAILABLE = FriendlyError('🎞', 'format_unavailable')
_RATE_LIMITED = FriendlyError('🐌', 'rate_limited')
_UNSUPPORTED_URL = FriendlyError('🔗', 'unsupported_url')
_NOT_FOUND = FriendlyError('🔍', 'not_found')
_FORBIDDEN = FriendlyError('⛔', 'forbidden')
_UNAVAILABLE = FriendlyError('❓', 'unavailable')

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
