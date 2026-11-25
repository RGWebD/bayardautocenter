#!/usr/bin/env python3
"""Build outlined Bayard Auto Center logo SVGs and PNG exports.

Wordmark text is converted to filled glyph outlines. The SVGs contain no
<text> elements. Run from the repo root: python3 scripts/build_logo.py
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import cairosvg
from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "logo"
FONT_DIR = Path("/tmp/fonts")
DISPLAY = FONT_DIR / "BebasNeue-Regular.ttf"
CONDENSED = FONT_DIR / "BarlowCondensed-Medium.ttf"

RED = "#D83830"
RED_DEEP = "#B4231C"
WHITE = "#F4F5F7"
INK = "#14161B"
MUTED_ON_DARK = "#C5CAD3"
MUTED_ON_LIGHT = "#3C414B"
CHARCOAL = "#121418"

# Badge geometry. The car is a symmetric front view, split on x = CX.
VW, VH = 640, 720
CX = 320


def shield_outer() -> str:
    return (
        "M 64 40 H 576 "
        "C 608 40 624 58 624 90 "
        "V 312 "
        "C 624 452 536 560 424 652 "
        "L 320 708 "
        "L 216 652 "
        "C 104 560 16 452 16 312 "
        "V 90 "
        "C 16 58 32 40 64 40 Z"
    )


def shield_inner() -> str:
    return (
        "M 90 66 H 550 "
        "C 576 66 590 82 590 108 "
        "V 304 "
        "C 590 428 514 524 416 606 "
        "L 320 662 "
        "L 224 606 "
        "C 126 524 50 428 50 304 "
        "V 108 "
        "C 50 82 64 66 90 66 Z"
    )


def car_body() -> str:
    """Front-view sedan with a flat roof, wide glass, and a low bumper."""
    return (
        "M 252 214 "
        "C 286 190 354 190 388 214 "
        "L 430 262 "
        "C 442 276 448 292 440 306 "
        "L 502 318 "
        "C 522 324 528 340 516 350 "
        "L 456 360 "
        "L 464 448 "
        "C 468 492 454 520 424 534 "
        "L 216 534 "
        "C 186 520 172 492 176 448 "
        "L 184 360 "
        "L 124 350 "
        "C 112 340 118 324 138 318 "
        "L 200 306 "
        "C 192 292 198 276 210 262 Z"
    )


def windshield() -> str:
    return (
        "M 272 222 "
        "H 368 "
        "C 382 222 392 232 400 246 "
        "L 424 300 "
        "C 428 310 418 316 406 316 "
        "H 234 "
        "C 222 316 212 310 216 300 "
        "L 240 246 "
        "C 248 232 258 222 272 222 Z"
    )


def headlight(side: str) -> str:
    if side == "left":
        return (
            "M 168 352 "
            "H 246 "
            "C 258 352 264 360 262 372 "
            "L 254 404 "
            "C 252 416 240 422 228 422 "
            "H 178 "
            "C 164 422 156 412 158 400 "
            "L 162 366 "
            "C 164 356 168 352 168 352 Z"
        )
    return (
        "M 472 352 "
        "H 394 "
        "C 382 352 376 360 378 372 "
        "L 386 404 "
        "C 388 416 400 422 412 422 "
        "H 462 "
        "C 476 422 484 412 482 400 "
        "L 478 366 "
        "C 476 356 472 352 472 352 Z"
    )


def lamp(side: str) -> str:
    if side == "left":
        return "M 182 368 H 236 C 242 368 244 374 242 380 V 400 C 242 408 236 412 228 412 H 188 C 180 412 176 406 178 398 V 376 C 178 370 182 368 182 368 Z"
    return "M 458 368 H 404 C 398 368 396 374 398 380 V 400 C 398 408 404 412 412 412 H 452 C 460 412 464 406 462 398 V 376 C 462 370 458 368 458 368 Z"


def grille() -> str:
    return (
        "M 262 356 H 378 "
        "C 388 356 392 364 392 374 "
        "V 408 "
        "C 392 418 384 422 374 422 "
        "H 266 "
        "C 256 422 248 418 248 408 "
        "V 374 "
        "C 248 364 252 356 262 356 Z"
    )


def intake() -> str:
    return (
        "M 188 456 H 452 "
        "C 464 456 470 464 470 476 "
        "V 502 "
        "C 470 512 460 516 448 516 "
        "H 192 "
        "C 180 516 170 512 170 502 "
        "V 476 "
        "C 170 464 176 456 188 456 Z"
    )


def side_intake(side: str) -> str:
    if side == "left":
        return "M 160 460 H 180 V 504 H 162 C 154 504 150 496 152 488 Z"
    return "M 480 460 H 460 V 504 H 478 C 486 504 490 496 488 488 Z"


BADGE_DEFS = f"""
  <linearGradient id="metal" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#FBFBFC"/>
    <stop offset="0.42" stop-color="#A7ADB6"/>
    <stop offset="0.55" stop-color="#ECEEF1"/>
    <stop offset="1" stop-color="#5E646E"/>
  </linearGradient>
  <linearGradient id="faceL" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#3A404A"/>
    <stop offset="1" stop-color="#23262D"/>
  </linearGradient>
  <linearGradient id="faceR" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#1C1F26"/>
    <stop offset="1" stop-color="#0C0D11"/>
  </linearGradient>
  <linearGradient id="paintW" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#FFFFFF"/>
    <stop offset="1" stop-color="#E4E7EC"/>
  </linearGradient>
  <linearGradient id="paintR" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#E24B43"/>
    <stop offset="0.55" stop-color="{RED}"/>
    <stop offset="1" stop-color="{RED_DEEP}"/>
  </linearGradient>
  <linearGradient id="glass" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#2A3340"/>
    <stop offset="1" stop-color="#07090C"/>
  </linearGradient>
  <clipPath id="halfL"><rect x="0" y="0" width="{CX}" height="{VH}"/></clipPath>
  <clipPath id="halfR"><rect x="{CX}" y="0" width="{CX}" height="{VH}"/></clipPath>
  <clipPath id="innerClip"><path d="{shield_inner()}"/></clipPath>
  <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="8" stdDeviation="8" flood-color="#000" flood-opacity="0.35"/>
  </filter>
"""


def badge_markup(shadow: bool = False) -> str:
    body = car_body()
    filt = ' filter="url(#soft)"' if shadow else ""
    return f"""
  <g id="badge"{filt}>
    <path d="{shield_outer()}" fill="url(#metal)"/>
    <path d="{shield_inner()}" fill="url(#faceL)" clip-path="url(#halfL)"/>
    <path d="{shield_inner()}" fill="url(#faceR)" clip-path="url(#halfR)"/>
    <path d="M {CX} 66 V 662" stroke="#6A707A" stroke-width="1.25" opacity="0.7"/>
    <g clip-path="url(#innerClip)">
      <path d="{body}" fill="none" stroke="#9AA1AB" stroke-width="8" stroke-linejoin="round"/>
      <path d="{body}" fill="url(#paintW)" clip-path="url(#halfL)"/>
      <path d="{body}" fill="url(#paintR)" clip-path="url(#halfR)"/>
      <path d="{windshield()}" fill="url(#glass)"/>
      <path d="M 300 230 H 360 L 372 248 H 312 Z" fill="#FFFFFF" opacity="0.38"/>
      <path d="{headlight('left')}" fill="#101318"/>
      <path d="{headlight('right')}" fill="#101318"/>
      <path d="{lamp('left')}" fill="#F4F6F8"/>
      <path d="{lamp('right')}" fill="#F4F6F8"/>
      <path d="{grille()}" fill="#0C0E12"/>
      <path d="M 274 380 H 366" stroke="#D5DAE1" stroke-width="3.5" stroke-linecap="round"/>
      <path d="M 274 398 H 366" stroke="#8E949E" stroke-width="3.5" stroke-linecap="round"/>
      <path d="M 274 416 H 366" stroke="#D5DAE1" stroke-width="3" stroke-linecap="round" opacity="0.75"/>
      <path d="{intake()}" fill="#0C0E12"/>
      <path d="M 196 484 H 444" stroke="#3A3F47" stroke-width="4" stroke-linecap="round"/>
      <path d="M 196 500 H 444" stroke="#2A2E35" stroke-width="3" stroke-linecap="round" opacity="0.85"/>
      <path d="{side_intake('left')}" fill="#0C0E12"/>
      <path d="{side_intake('right')}" fill="#0C0E12"/>
      <path d="M {CX} 176 V 530" stroke="#1A1C20" stroke-width="2" opacity="0.45"/>
    </g>
  </g>
"""


def svg_doc(body: str, w: float, h: float, title: str, desc: str, bg: str | None = None) -> str:
    background = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}" width="{w:g}" height="{h:g}" role="img" aria-labelledby="logoTitle logoDesc">
  <title id="logoTitle">{title}</title>
  <desc id="logoDesc">{desc}</desc>
  <defs>
{BADGE_DEFS}
  </defs>
  {background}
  {body}
</svg>
'''


class FontOutliner:
    def __init__(self, path: Path):
        self.font = TTFont(path)
        self.gs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upem = self.font["head"].unitsPerEm

    def missing(self, text: str) -> list[str]:
        return [ch for ch in text if ch != " " and ord(ch) not in self.cmap]

    def measure(self, text: str, size: float, tracking: float) -> float:
        scale = size / self.upem
        width = 0.0
        for i, ch in enumerate(text):
            name = self.cmap.get(ord(ch))
            if name is None:
                raise SystemExit(f"Missing glyph U+{ord(ch):04X} ({ch!r})")
            width += self.gs[name].width * scale
            if i != len(text) - 1:
                width += tracking
        return width

    def bounds(self, text: str, size: float, tracking: float, x: float, baseline: float):
        scale = size / self.upem
        pen = BoundsPen(self.gs)
        cursor = x
        for i, ch in enumerate(text):
            if ch == " ":
                name = self.cmap[ord(" ")]
                cursor += self.gs[name].width * scale
                if i != len(text) - 1:
                    cursor += tracking
                continue
            name = self.cmap[ord(ch)]
            tpen = TransformPen(pen, Transform(scale, 0, 0, -scale, cursor, baseline))
            self.gs[name].draw(tpen)
            cursor += self.gs[name].width * scale
            if i != len(text) - 1:
                cursor += tracking
        return pen.bounds  # xmin, ymin, xmax, ymax in user space (y down)

    def outlines(self, text: str, size: float, tracking: float, x: float, baseline: float, fill: str) -> str:
        scale = size / self.upem
        parts = []
        cursor = x
        for i, ch in enumerate(text):
            name = self.cmap[ord(ch)]
            glyph = self.gs[name]
            if ch != " ":
                pen = SVGPathPen(self.gs)
                tpen = TransformPen(pen, Transform(scale, 0, 0, -scale, cursor, baseline))
                glyph.draw(tpen)
                d = pen.getCommands() or ""
                if not d.strip():
                    raise SystemExit(f"Empty outline for {ch!r}")
                bad = re.search(r"\b(?:nan|inf|infinity)\b", d, re.I)
                if bad:
                    raise SystemExit(f"Non-finite coordinate in {ch!r}: {d[:120]}")
                # Reject broken path tokens.
                if re.search(r"[^MmLlHhVvCcSsQqTtAaZz0-9eE+.,\s-]", d):
                    raise SystemExit(f"Unexpected path data for {ch!r}: {d[:120]}")
                parts.append(
                    f'<path data-char="{ch}" d="{d}" fill="{fill}" fill-rule="nonzero"/>'
                )
            cursor += glyph.width * scale
            if i != len(text) - 1:
                cursor += tracking
        return "\n".join(parts)


def render_png(svg_path: Path, png_path: Path, width: int, height: int | None = None, background=None):
    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(png_path),
        output_width=width,
        output_height=height,
        background_color=background,
    )


def check_png_glyphs(png_path: Path, letters: list[dict], background_rgb: tuple[int, int, int]):
    im = Image.open(png_path).convert("RGBA")
    problems = []
    for letter in letters:
        x0, y0, x1, y1 = [int(round(v)) for v in letter["box"]]
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(im.width - 1, x1)
        y1 = min(im.height - 1, y1)
        if x1 <= x0 or y1 <= y0:
            problems.append(f"{letter['ch']} has an empty pixel box {letter['box']}")
            continue
        crop = im.crop((x0, y0, x1 + 1, y1 + 1))
        ink = 0
        for px in crop.getdata():
            r, g, b, a = px
            if a < 20:
                continue
            # Differ from a flat background by more than a small delta.
            if abs(r - background_rgb[0]) + abs(g - background_rgb[1]) + abs(b - background_rgb[2]) > 30:
                ink += 1
        if ink < 12:
            problems.append(f"{letter['ch']} rendered with almost no ink ({ink} px) at {letter['box']}")
    return problems


def hole_samples(font: FontOutliner, ch: str, size: float) -> list[tuple[float, float]]:
    """Return hole sample points in glyph units (y up), relative to origin."""
    name = font.cmap[ord(ch)]
    pen = BoundsPen(font.gs)
    font.gs[name].draw(pen)
    if not pen.bounds:
        return []
    x0, y0, x1, y1 = pen.bounds
    # Fractions of the glyph bbox (y up) that should fall in a counter.
    spots = {
        "A": [(0.50, 0.62)],
        "B": [(0.62, 0.73), (0.62, 0.30)],
        "D": [(0.58, 0.50)],
        "O": [(0.50, 0.50)],
        "R": [(0.62, 0.72)],
    }.get(ch, [])
    return [(x0 + (x1 - x0) * fx, y0 + (y1 - y0) * fy) for fx, fy in spots]


def point_in_glyph(font: FontOutliner, ch: str, pt) -> bool:
    """Even-odd hit test using the raw glyph contours is unnecessary if we
    rasterize one glyph. Used as a raster check instead."""
    return False


def raster_hole_check(font: FontOutliner, ch: str, size: float = 240) -> str | None:
    samples = hole_samples(font, ch, size)
    if not samples:
        return None
    name = font.cmap[ord(ch)]
    pen = BoundsPen(font.gs)
    font.gs[name].draw(pen)
    x0, y0, x1, y1 = pen.bounds
    scale = size / font.upem
    pad = 8
    width = int(math.ceil((x1 - x0) * scale)) + pad * 2
    height = int(math.ceil((y1 - y0) * scale)) + pad * 2
    baseline = pad + (y1 * scale)  # y-down baseline so glyph top sits near pad
    # glyph y-up origin maps: user_y = baseline - glyph_y * scale, user_x = pad - x0*scale
    svg_pen = SVGPathPen(font.gs)
    origin_x = pad - x0 * scale
    tpen = TransformPen(svg_pen, Transform(scale, 0, 0, -scale, origin_x, baseline))
    font.gs[name].draw(tpen)
    d = svg_pen.getCommands()
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
        f'<rect width="100%" height="100%" fill="#101014"/>'
        f'<path d="{d}" fill="#F4F5F7" fill-rule="nonzero"/></svg>'
    )
    png = cairosvg.svg2png(bytestring=svg.encode())
    im = Image.open(__import__("io").BytesIO(png)).convert("RGB")
    for gx, gy in samples:
        ux = int(round(origin_x + gx * scale))
        uy = int(round(baseline - gy * scale))
        if not (0 <= ux < im.width and 0 <= uy < im.height):
            return f"{ch} hole sample fell outside the raster ({ux},{uy})"
        r, g, b = im.getpixel((ux, uy))
        # A counter must show the dark background, not the white fill.
        if r > 80 or g > 80 or b > 80:
            return f"{ch} counter looks filled at ({ux},{uy}) color {(r, g, b)}"
    return None


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    display = FontOutliner(DISPLAY)
    condensed = FontOutliner(CONDENSED)
    for label, font, text in (
        ("display", display, "BAYARD AUTO CENTER"),
        ("condensed", condensed, "WE DO EVERYTHING ON ANYTHING"),
    ):
        missing = font.missing(text)
        if missing:
            raise SystemExit(f"{label} font missing {missing}")

    desc = (
        "Bayard Auto Center logo. A dark shield holds a front-facing sedan "
        "split white on the left and red on the right, with the wordmark "
        "Bayard Auto Center and the line We do everything on anything."
    )

    badge = svg_doc(
        badge_markup(False),
        VW,
        VH,
        "Bayard Auto Center badge",
        "Shield badge with a front-facing sedan, half white and half red.",
    )
    (OUT / "badge.svg").write_text(badge)

    # Horizontal lockups -------------------------------------------------
    badge_h = 300
    badge_scale = badge_h / VH
    badge_w = VW * badge_scale
    name_size = 92
    name_track = 4
    sub_size = 34
    sub_track = 6
    tag_size = 16
    tag_track = 3.2
    text_x = badge_w + 36
    name_w = display.measure("BAYARD", name_size, name_track)
    sub_w = display.measure("AUTO CENTER", sub_size, sub_track)
    tag_w = condensed.measure("WE DO EVERYTHING ON ANYTHING", tag_size, tag_track)
    block_w = max(name_w, sub_w, tag_w)
    total_w = text_x + block_w + 28
    total_h = 340
    # Optical alignment: text block sits a little above the shield's point.
    baseline_name = 132
    baseline_sub = 178
    baseline_tag = 232

    def horizontal(theme: str) -> tuple[str, list[dict]]:
        if theme == "dark":
            name_fill, sub_fill, tag_fill, auto_fill = WHITE, WHITE, MUTED_ON_DARK, RED
        else:
            name_fill, sub_fill, tag_fill, auto_fill = INK, INK, MUTED_ON_LIGHT, RED
        name = display.outlines("BAYARD", name_size, name_track, text_x, baseline_name, name_fill)
        auto = display.outlines("AUTO", sub_size, sub_track, text_x, baseline_sub, auto_fill)
        auto_w = display.measure("AUTO", sub_size, sub_track)
        # Space after AUTO uses the font's space plus tracking.
        space = display.measure(" ", sub_size, 0)
        center = display.outlines(
            "CENTER",
            sub_size,
            sub_track,
            text_x + auto_w + space + sub_track,
            baseline_sub,
            sub_fill,
        )
        tag = condensed.outlines(
            "WE DO EVERYTHING ON ANYTHING",
            tag_size,
            tag_track,
            text_x,
            baseline_tag,
            tag_fill,
        )
        rule_w = min(220, block_w * 0.46)
        y_shift = 16
        body = f"""
  <g transform="translate(8 {y_shift}) scale({badge_scale:.6f})">
    {badge_markup(False)}
  </g>
  <g>
    {name}
    {auto}
    {center}
    <rect x="{text_x:.2f}" y="{baseline_sub + 16:.2f}" width="{rule_w:.2f}" height="3" rx="1.5" fill="{RED}"/>
    {tag}
  </g>
"""
        letters = []
        # Record boxes in final SVG coordinates for the proof render.
        def record(font, text, size, tracking, x, baseline, fill):
            cursor = x
            scale = size / font.upem
            for i, ch in enumerate(text):
                name_g = font.cmap[ord(ch)]
                adv = font.gs[name_g].width * scale
                if ch != " ":
                    bpen = BoundsPen(font.gs)
                    font.gs[name_g].draw(bpen)
                    if bpen.bounds:
                        gx0, gy0, gx1, gy1 = bpen.bounds
                        letters.append(
                            {
                                "ch": ch,
                                "box": (
                                    cursor + gx0 * scale,
                                    baseline - gy1 * scale,
                                    cursor + gx1 * scale,
                                    baseline - gy0 * scale,
                                ),
                            }
                        )
                cursor += adv
                if i != len(text) - 1:
                    cursor += tracking

        record(display, "BAYARD", name_size, name_track, text_x, baseline_name, name_fill)
        record(display, "AUTO", sub_size, sub_track, text_x, baseline_sub, auto_fill)
        record(
            display,
            "CENTER",
            sub_size,
            sub_track,
            text_x + auto_w + space + sub_track,
            baseline_sub,
            sub_fill,
        )
        record(condensed, "WE DO EVERYTHING ON ANYTHING", tag_size, tag_track, text_x, baseline_tag, tag_fill)
        doc = svg_doc(body, total_w, total_h, "Bayard Auto Center", desc)
        return doc, letters

    dark_h, letters_h = horizontal("dark")
    light_h, _ = horizontal("light")
    (OUT / "lockup-horizontal-dark.svg").write_text(dark_h)
    (OUT / "lockup-horizontal-light.svg").write_text(light_h)

    # Stacked lockups ----------------------------------------------------
    s_badge = 250
    s_scale = s_badge / VH
    s_bw = VW * s_scale
    s_name = 86
    s_name_tr = 5
    s_sub = 30
    s_sub_tr = 5.5
    s_tag = 15
    s_tag_tr = 2.8
    s_name_w = display.measure("BAYARD", s_name, s_name_tr)
    s_sub_w = display.measure("AUTO CENTER", s_sub, s_sub_tr)
    s_tag_w = condensed.measure("WE DO EVERYTHING ON ANYTHING", s_tag, s_tag_tr)
    s_w = max(s_bw, s_name_w, s_sub_w, s_tag_w) + 64
    s_h = 520

    def stacked(theme: str) -> str:
        if theme == "dark":
            name_fill, sub_fill, tag_fill, auto_fill = WHITE, WHITE, MUTED_ON_DARK, RED
        else:
            name_fill, sub_fill, tag_fill, auto_fill = INK, INK, MUTED_ON_LIGHT, RED
        cx = s_w / 2
        badge_x = cx - s_bw / 2
        name_x = cx - s_name_w / 2
        # AUTO CENTER centered as a whole, AUTO in red.
        sub_x = cx - s_sub_w / 2
        auto_w = display.measure("AUTO", s_sub, s_sub_tr)
        space = display.measure(" ", s_sub, 0)
        tag_x = cx - s_tag_w / 2
        base_name = 318
        base_sub = 360
        base_tag = 412
        rule_w = 148
        body = f"""
  <g transform="translate({badge_x:.2f} 8) scale({s_scale:.6f})">
    {badge_markup(False)}
  </g>
  {display.outlines("BAYARD", s_name, s_name_tr, name_x, base_name, name_fill)}
  {display.outlines("AUTO", s_sub, s_sub_tr, sub_x, base_sub, auto_fill)}
  {display.outlines("CENTER", s_sub, s_sub_tr, sub_x + auto_w + space + s_sub_tr, base_sub, sub_fill)}
  <rect x="{(cx - rule_w/2):.2f}" y="{base_sub + 16:.2f}" width="{rule_w}" height="3" rx="1.5" fill="{RED}"/>
  {condensed.outlines("WE DO EVERYTHING ON ANYTHING", s_tag, s_tag_tr, tag_x, base_tag, tag_fill)}
"""
        return svg_doc(body, s_w, s_h, "Bayard Auto Center", desc)

    (OUT / "lockup-stacked-dark.svg").write_text(stacked("dark"))
    (OUT / "lockup-stacked-light.svg").write_text(stacked("light"))

    # Raster exports -----------------------------------------------------
    render_png(OUT / "badge.svg", OUT / "icon-512.png", 512, 512)
    render_png(OUT / "badge.svg", OUT / "favicon-32.png", 32, 32)
    # Apple touch is opaque charcoal with the badge centered.
    apple_svg = OUT / "_apple.svg"
    apple_svg.write_text(
        svg_doc(
            f'<g transform="translate(46 18) scale({300/VH:.6f})">{badge_markup(False)}</g>',
            400,
            400,
            "Bayard Auto Center",
            "App icon",
            bg=CHARCOAL,
        )
    )
    render_png(apple_svg, OUT / "apple-touch.png", 180, 180)
    apple_svg.unlink()

    render_png(OUT / "lockup-horizontal-light.svg", OUT / "logo-1024.png", 1024)

    # Open Graph card, 1200x630, outlined type.
    og_w, og_h = 1200, 630
    og_scale = 460 / VH
    og_name = 92
    og_sub = 36
    og_tag = 22
    og_meta = 26
    tx = 520
    og_body = f"""
  <rect width="{og_w}" height="{og_h}" fill="{CHARCOAL}"/>
  <rect width="{og_w}" height="8" fill="{RED}"/>
  <circle cx="180" cy="560" r="280" fill="{RED}" opacity="0.16"/>
  <g transform="translate(36 70) scale({og_scale:.6f})">{badge_markup(False)}</g>
  {display.outlines("BAYARD", og_name, 4, tx, 210, WHITE)}
  {display.outlines("AUTO CENTER", og_sub, 5, tx, 268, WHITE)}
  <rect x="{tx}" y="292" width="180" height="4" fill="{RED}"/>
  {condensed.outlines("WE DO EVERYTHING ON ANYTHING", og_tag, 2.4, tx, 340, MUTED_ON_DARK)}
  {condensed.outlines("JACKSONVILLE, FL  ·  (904) 400-4100", og_meta, 1.2, tx, 420, WHITE)}
  {condensed.outlines("AUTO REPAIR ON PHILIPS HIGHWAY", 20, 2.2, tx, 468, RED)}
"""
    og_svg = OUT / "og.svg"
    og_svg.write_text(svg_doc(og_body, og_w, og_h, "Bayard Auto Center", desc, bg=None))
    render_png(og_svg, OUT / "og.png", 1200, 630)

    # Favicon ico (16 and 32).
    icon32 = Image.open(OUT / "favicon-32.png").convert("RGBA")
    icon16 = icon32.resize((16, 16), Image.Resampling.LANCZOS)
    icon32.save(ROOT / "favicon.ico", sizes=[(16, 16), (32, 32)], append_images=[icon16])
    icon32.save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32)], append_images=[icon16])

    # Validation ---------------------------------------------------------
    problems = []
    for svg in sorted(OUT.glob("*.svg")):
        text = svg.read_text()
        if "<text" in text or "<tspan" in text:
            problems.append(f"{svg.name} still contains live text")
        if re.search(r"\bnan\b|\bNaN\b|Infinity", text):
            problems.append(f"{svg.name} contains a non-finite coordinate")
        # Every path d should parse as numbers.
        for d in re.findall(r'\bd="([^"]+)"', text):
            if "nan" in d.lower():
                problems.append(f"{svg.name} path has NaN")

    # Rasterize the dark horizontal lockup on charcoal and confirm every glyph has ink.
    proof = Path("/tmp/lockup-proof.png")
    render_png(OUT / "lockup-horizontal-dark.svg", proof, 1400, background="#121418")
    scale = 1400 / total_w
    scaled_letters = []
    for letter in letters_h:
        x0, y0, x1, y1 = letter["box"]
        scaled_letters.append(
            {
                "ch": letter["ch"],
                "box": (x0 * scale, y0 * scale, x1 * scale, y1 * scale),
            }
        )
    problems.extend(check_png_glyphs(proof, scaled_letters, (18, 20, 24)))

    for ch in "ABDOR":
        msg = raster_hole_check(display, ch)
        if msg:
            problems.append(msg)
    for ch in "ABDOR":
        # Tagline font too, for O, D, A, R, B if present. Condensed has them.
        if ch in "WE DO EVERYTHING ON ANYTHING":
            msg = raster_hole_check(condensed, ch)
            if msg:
                problems.append("tagline " + msg)

    # Glyph contact sheet for visual QA.
    sheet = Image.new("RGB", (1600, 360), (18, 20, 24))
    draw = ImageDraw.Draw(sheet)
    # Paste crops from the proof in order, scaled up by redrawing each letter.
    x = 10
    y = 20
    seen = []
    for ch in "BAYARD AUTO CENTER":
        if ch == " " or ch in seen:
            continue
        seen.append(ch)
    # Draw from a dedicated render of the alphabet we use.
    alpha_svg_parts = []
    cursor = 20
    baseline = 150
    size = 120
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if display.missing(ch):
            continue
        alpha_svg_parts.append(display.outlines(ch, size, 0, cursor, baseline, WHITE))
        cursor += display.measure(ch, size, 0) + 18
    alpha_svg = svg_doc("\n".join(alpha_svg_parts), cursor + 20, 220, "Glyph proof", "Glyph proof")
    alpha_png = Path("/tmp/glyph-proof.png")
    Path("/tmp/glyph-proof.svg").write_text(alpha_svg)
    render_png(Path("/tmp/glyph-proof.svg"), alpha_png, 1800, background="#121418")

    if problems:
        print("LOGO PROBLEMS:")
        for p in problems:
            print(" -", p)
        raise SystemExit(1)

    print("Logo files written to", OUT)
    for p in sorted(OUT.iterdir()):
        print(f"  {p.name:32} {p.stat().st_size:8d}")


if __name__ == "__main__":
    build()
