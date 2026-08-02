#!/usr/bin/env python3
"""Render the animated hero as a GitHub-safe GIF.

The static ``hero.svg`` shows the finished conversation. This script replays how
it gets there: the link arrives, the format keyboard opens, a choice is made,
the download reports itself, processing takes over, and the file lands. Each
frame is the same composition drawn at one point in that sequence, so the title
block never moves and only the chat panel produces frame-to-frame deltas.

    python3 hero-motion.py            # writes ../hero.gif

Requires rsvg-convert and ffmpeg; gifsicle is optional but shrinks the result by
more than an order of magnitude, because ffmpeg writes every frame in full while
gifsicle stores only the region that actually changed.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / 'hero.gif'

BG = '#0E1621'
PANEL = '#17212B'
SENT = '#2B5278'
CARD = '#1F2C3A'
BTN = '#232F3D'
BTN_EDGE = '#33475C'
FG = '#E9EEF2'
DIM = '#A8BACA'
MUTED = '#7D8E9E'
FAINT = '#4A5B69'
BLUE = '#56A2E8'
GREEN = '#4FBF67'
TRACK = '#22303F'

SANS = '-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif'
MONO = 'ui-monospace,SFMono-Regular,Menlo,monospace'

TOTAL_MIB = 159.3


def ease_out(t: float) -> float:
    """Calm deceleration; nothing overshoots or bounces."""
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def fmt_clock(seconds: int) -> str:
    return f'{seconds // 60}:{seconds % 60:02d}'


def bubble(y_shift: float, opacity: float) -> str:
    """The link you paste, arriving from slightly below."""
    if opacity <= 0:
        return ''
    return f'''
    <g transform="translate(0 {y_shift:.1f})" opacity="{opacity:.3f}">
      <rect x="140" y="70" width="332" height="54" rx="14" fill="{SENT}"/>
      <text x="164" y="103" font-family="{MONO}" font-size="19" fill="{FG}">youtu.be/AWy1qiTF64M</text>
    </g>'''


def keyboard(y_shift: float, opacity: float, pressed: bool) -> str:
    """The inline keyboard, with the chosen button lit while it is tapped."""
    if opacity <= 0:
        return ''
    vid_fill = BLUE if pressed else BTN
    vid_edge = BLUE if pressed else BTN_EDGE
    vid_text = '#0E1621' if pressed else FG
    vid_icon = '#0E1621' if pressed else BLUE
    return f'''
    <g transform="translate(0 {y_shift:.1f})" opacity="{opacity:.3f}">
      <text x="24" y="156" font-family="{SANS}" font-size="19" fill="{MUTED}">Choose what to download</text>
      <g transform="translate(24 170)">
        <rect x="0" y="0" width="144" height="50" rx="10" fill="{vid_fill}" stroke="{vid_edge}" stroke-width="1.5"/>
        <rect x="18" y="18" width="18" height="14" rx="3" fill="{vid_icon}"/>
        <path d="M40 20 L52 25 L40 30 Z" fill="{vid_icon}"/>
        <text x="64" y="31" font-family="{SANS}" font-size="20" fill="{vid_text}">Video</text>

        <rect x="152" y="0" width="144" height="50" rx="10" fill="{BTN}" stroke="{BTN_EDGE}" stroke-width="1.5"/>
        <circle cx="176" cy="30" r="7" fill="{BLUE}"/>
        <rect x="181" y="14" width="3" height="14" rx="1.5" fill="{BLUE}"/>
        <text x="200" y="31" font-family="{SANS}" font-size="20" fill="{FG}">Audio</text>

        <rect x="304" y="0" width="144" height="50" rx="10" fill="{BTN}" stroke="{BTN_EDGE}" stroke-width="1.5"/>
        <rect x="322" y="17" width="14" height="16" rx="3" fill="none" stroke="{BLUE}" stroke-width="2.5"/>
        <rect x="330" y="21" width="14" height="16" rx="3" fill="{BTN}" stroke="{BLUE}" stroke-width="2.5"/>
        <text x="356" y="31" font-family="{SANS}" font-size="20" fill="{FG}">Both</text>
      </g>
    </g>'''


def progress(shown: float, opacity: float) -> str:
    """The one status message, edited in place as the bytes arrive.

    The bar and the numbers advance together in visible steps rather than
    flowing: the real bot throttles its edits, so a smoothly sliding bar would
    misrepresent it. Identical frames between steps also keep the GIF small.
    """
    if opacity <= 0:
        return ''
    done = TOTAL_MIB * shown / 100
    speed = 9.6
    left = int(max(0, (TOTAL_MIB - done) / speed))
    filled = 448 * shown / 100
    return f'''
    <g transform="translate(24 244)" opacity="{opacity:.3f}">
      <path d="M8 6 L8 18 M2 12 L8 18 L14 12" stroke="{BLUE}" stroke-width="2.5"
            fill="none" stroke-linecap="round" stroke-linejoin="round"/>
      <text x="28" y="18" font-family="{SANS}" font-size="20" font-weight="600"
            fill="{FG}">Downloading {shown:.1f}%</text>
      <rect x="0" y="34" width="448" height="10" rx="5" fill="{TRACK}"/>
      <rect x="0" y="34" width="{filled:.1f}" height="10" rx="5" fill="url(#bar)"/>
      <text x="0" y="70" font-family="{MONO}" font-size="18"
            fill="{MUTED}">{fmt_clock(left)} left · {done:.1f} of {TOTAL_MIB} MiB · {speed} MiB/s</text>
    </g>'''


def processing(elapsed: int, opacity: float) -> str:
    """The same message once yt-dlp hands over to FFmpeg."""
    if opacity <= 0:
        return ''
    return f'''
    <g transform="translate(24 244)" opacity="{opacity:.3f}">
      <circle cx="8" cy="12" r="7" fill="none" stroke="{BLUE}" stroke-width="2.5"/>
      <path d="M8 5 L8 12 L13 15" stroke="{BLUE}" stroke-width="2.5" fill="none" stroke-linecap="round"/>
      <text x="28" y="18" font-family="{SANS}" font-size="20" font-weight="600"
            fill="{FG}">Processing</text>
      <text x="0" y="48" font-family="{SANS}" font-size="19"
            fill="{DIM}">Merging video and audio</text>
      <text x="0" y="76" font-family="{MONO}" font-size="18"
            fill="{MUTED}">{fmt_clock(elapsed)} elapsed</text>
    </g>'''


def file_card(y_shift: float, opacity: float) -> str:
    """What the whole thing was for."""
    if opacity <= 0:
        return ''
    return f'''
    <g transform="translate(24 {338 + y_shift:.1f})" opacity="{opacity:.3f}">
      <rect x="0" y="0" width="448" height="62" rx="14" fill="{CARD}"/>
      <g transform="translate(12 5)" clip-path="url(#thumbClip)">
        <rect x="0" y="0" width="72" height="52" fill="#2A3B4D"/>
        <path d="M0 40 L20 24 L34 36 L52 18 L72 34 L72 52 L0 52 Z" fill="#3A5065"/>
        <circle cx="55" cy="14" r="7" fill="#46617A"/>
      </g>
      <path d="M42 24 L54 31 L42 38 Z" fill="{FG}"/>
      <text x="98" y="27" font-family="{SANS}" font-size="19" fill="{FG}">Rufford Ford | part 47</text>
      <text x="98" y="50" font-family="{MONO}" font-size="18" fill="{MUTED}">4:21 · 159.3 MB</text>
      <path d="M424 46 l5 5 l9 -11" stroke="{GREEN}" stroke-width="2.5" fill="none"
            stroke-linecap="round" stroke-linejoin="round"/>
    </g>'''


def frame_svg(t: float) -> str:
    """Draw the whole hero at time ``t`` seconds.

    The timeline gives the arriving file the longest still hold: it is the point
    of the whole sequence, and everything before it is setup.
    """
    # The conversation fades out at the very end so the loop returns to frame 0.
    # It reaches exactly zero a little early: the closing frames then match the
    # opening one byte for byte, which both hides the loop seam and compresses.
    fade = 1.0
    if t >= 10.85:
        fade = 0.0
    elif t >= 10.3:
        fade = 1 - ease_out((t - 10.3) / 0.55)

    url_op = ease_out((t - 0.5) / 0.45) if t >= 0.5 else 0.0
    url_dy = 14 * (1 - ease_out((t - 0.5) / 0.45)) if t >= 0.5 else 14

    kb_op = ease_out((t - 1.3) / 0.45) if t >= 1.3 else 0.0
    if t >= 2.65:
        kb_op = max(0.0, 1 - ease_out((t - 2.65) / 0.3))
    kb_dy = 14 * (1 - ease_out((t - 1.3) / 0.45)) if t >= 1.3 else 14
    pressed = 2.2 <= t < 2.65

    prog_op, shown = 0.0, 0.0
    proc_op, elapsed = 0.0, 0
    if 2.8 <= t < 6.9:
        prog_op = ease_out((t - 2.8) / 0.3)
        # Advance in half-second steps, the way an edited message really moves.
        step = (int((t - 2.95) * 2) / 2) if t >= 2.95 else 0.0
        shown = min(100.0, 100 * step / 3.4)
        if t >= 6.6:
            prog_op = max(0.0, 1 - ease_out((t - 6.6) / 0.3))
    if 6.8 <= t < 8.3:
        proc_op = ease_out((t - 6.8) / 0.3)
        elapsed = int(t - 6.8)
        if t >= 8.0:
            proc_op = max(0.0, 1 - ease_out((t - 8.0) / 0.3))

    file_op = ease_out((t - 8.2) / 0.45) if t >= 8.2 else 0.0
    file_dy = 12 * (1 - ease_out((t - 8.2) / 0.45)) if t >= 8.2 else 12

    chat = ''.join([
        bubble(url_dy, url_op * fade),
        keyboard(kb_dy, kb_op * fade, pressed),
        progress(shown, prog_op * fade),
        processing(elapsed, proc_op * fade),
        file_card(file_dy, file_op * fade),
    ])

    return f'''<svg xmlns="http://www.w3.org/2000/svg"
     width="1200" height="460" viewBox="0 0 1200 460">
  <defs>
    <linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{BLUE}"/>
      <stop offset="1" stop-color="{GREEN}"/>
    </linearGradient>
    <clipPath id="thumbClip"><rect x="0" y="0" width="72" height="52" rx="8"/></clipPath>
  </defs>

  <rect width="1200" height="460" rx="26" fill="{BG}"/>

  <g id="title-block">
    <text x="64" y="98" font-family="{MONO}" font-size="20" letter-spacing="3"
          fill="{MUTED}">SELF-HOSTED · DOCKER COMPOSE</text>
    <text x="64" y="182" font-family="{SANS}" font-size="76" font-weight="700"
          fill="{FG}">yt-dlp-bot</text>
    <text x="64" y="240" font-family="{SANS}" font-size="24" fill="{DIM}">Paste a link, choose video or audio,</text>
    <text x="64" y="276" font-family="{SANS}" font-size="24" fill="{DIM}">and get the file in the same chat.</text>
    <rect x="64" y="316" width="72" height="3" rx="1.5" fill="{BLUE}"/>
    <text x="64" y="366" font-family="{MONO}" font-size="19" fill="{MUTED}">v1.7.2</text>
    <text x="152" y="366" font-family="{MONO}" font-size="19" fill="{MUTED}">yt-dlp</text>
    <text x="240" y="366" font-family="{MONO}" font-size="19" fill="{MUTED}">Pyrogram</text>
    <text x="351" y="366" font-family="{MONO}" font-size="19" fill="{MUTED}">RabbitMQ</text>
    <text x="64" y="404" font-family="{MONO}" font-size="19" fill="{FAINT}">Creative Commons video only</text>
  </g>

  <g id="chat" transform="translate(640 0)">
    <rect x="0" y="40" width="496" height="380" rx="18" fill="{PANEL}"/>{chat}
  </g>
</svg>
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--width', type=int, default=1200,
                        help='native canvas width; GitHub renders it around 900')
    parser.add_argument('--fps', type=int, default=15)
    parser.add_argument('--colors', type=int, default=256,
                        help='the composition is mostly text, so keep the full palette')
    parser.add_argument('--out', type=Path, default=OUT)
    args = parser.parse_args()

    for binary in ('rsvg-convert', 'ffmpeg'):
        if not shutil.which(binary):
            print(f'ERROR: {binary} is required', file=sys.stderr)
            return 2

    FPS, WIDTH, out = args.fps, args.width, args.out
    duration = 11.0
    frames = int(duration * FPS)
    work = Path(tempfile.mkdtemp(prefix='hero-motion-'))

    for index in range(frames):
        t = index / FPS
        svg_path = work / f'{index:04d}.svg'
        svg_path.write_text(frame_svg(t))
        subprocess.run(
            ['rsvg-convert', '-w', str(WIDTH), str(svg_path), '-o', str(work / f'{index:04d}.png')],
            check=True,
        )

    # One palette for the whole clip and no dithering: the artwork is flat, so
    # dithering would only add moving noise and weight.
    palette = work / 'palette.png'
    subprocess.run(
        ['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS),
         '-i', str(work / '%04d.png'),
         '-vf', f'palettegen=max_colors={args.colors}:stats_mode=full', str(palette)],
        check=True,
    )
    subprocess.run(
        ['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS),
         '-i', str(work / '%04d.png'), '-i', str(palette),
         '-lavfi', 'paletteuse=dither=none:diff_mode=rectangle',
         '-loop', '0', str(out)],
        check=True,
    )

    if shutil.which('gifsicle'):
        # ffmpeg emits complete frames; gifsicle rewrites the file so each frame
        # carries only its changed rectangle. Lossless, and far smaller.
        subprocess.run(['gifsicle', '-O3', str(out), '-o', str(out)], check=True)
    else:
        print('note: install gifsicle to shrink the result substantially', file=sys.stderr)

    shutil.rmtree(work, ignore_errors=True)
    size_mb = out.stat().st_size / 1024 / 1024
    print(f'{out}: {WIDTH}px, {frames} frames, {duration:.1f}s at {FPS} fps, '
          f'{args.colors} colors, {size_mb:.2f} MB')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
