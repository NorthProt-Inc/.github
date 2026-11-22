#!/usr/bin/env python3
"""Build profile/chessprot-banner.svg, the ChessProt "coming soon" banner.

The banner is a dark card in the ProtChess look: --paper surface, a light wood board
corner with three meridian_shaded pieces, and the title set in Source Serif 4 with a
JetBrains Mono tag. GitHub shows README SVGs as images, which load no web fonts, so every
glyph is converted to an outline here (shaped by HarfBuzz, so kerning is kept).

Inputs (none are committed to this repo):
  --fonts   a node_modules dir with @fontsource-variable/source-serif-4 (5.3.1) and
            @fontsource/jetbrains-mono (5.3.0); both OFL-1.1
  --pieces  ProtChess web/public/pieces (meridian_shaded by Martin Sedlák, public domain):
            N.svg, P.svg, k.svg

Python deps: fonttools, uharfbuzz, brotli (for the woff2 file). check() and its tests
(test_make_banner.py) need only the standard library.

Usage, from the repo root (fonts installed outside the repo, so nothing lands in it):
  mkdir -p /tmp/np-fonts && npm i --prefix /tmp/np-fonts \
      @fontsource-variable/source-serif-4@5.3.1 @fontsource/jetbrains-mono@5.3.0
  python3 -m venv /tmp/np-venv && /tmp/np-venv/bin/pip install fonttools==4.68.0 uharfbuzz==0.57.0 brotli
  /tmp/np-venv/bin/python tools/chessprot-banner/make_banner.py --fonts /tmp/np-fonts/node_modules \
      --pieces ~/projects/protchess/web/public/pieces --out profile/chessprot-banner.svg

The script checks its own output (no <text>, <script>, <foreignObject>, <image>, <style>
or external reference; unique ids; every #reference resolved; a <title>; valid XML; at most
150 KB) and exits 1 if a check fails.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ProtChess tokens (web/app/globals.css)
PAPER = "#302e2b"
RULE = "#46433f"
INK = "#eceae6"
INK_SOFT = "#c0bab0"
BOARD_LIGHT = "#edd6b1"
BOARD_DARK = "#b88762"
BOARD_RULE = "#96693f"

W, H = 1280, 400
MARGIN = 72
SQ = 80  # board square
MAX_BYTES = 150_000

SERIF = "@fontsource-variable/source-serif-4/files/source-serif-4-latin-opsz-normal.woff2"
MONO = "@fontsource/jetbrains-mono/files/jetbrains-mono-latin-500-normal.woff"


def num(x: float) -> str:
    s = f"{x:.1f}"
    return s[:-2] if s.endswith(".0") else s


class Face:
    """One font at one variation, able to shape a run and emit it as an SVG path."""

    def __init__(self, path: Path, variations: dict[str, float] | None = None):
        # imported here, so check() and its tests run without these packages
        import uharfbuzz as hb
        from fontTools.ttLib import TTFont

        self.hb = hb
        tt = TTFont(path)  # woff/woff2 -> sfnt bytes HarfBuzz can read
        buf = io.BytesIO()
        tt.flavor = None
        tt.save(buf)
        self.upem = tt["head"].unitsPerEm
        self.font = hb.Font(hb.Face(hb.Blob(buf.getvalue())))
        if variations:
            self.font.set_variations(variations)

    def shape(self, text: str):
        hb = self.hb
        b = hb.Buffer()
        b.add_str(text)
        b.guess_segment_properties()
        hb.shape(self.font, b, {"kern": True, "liga": True})
        return b.glyph_infos, b.glyph_positions

    def width(self, text: str, size: float, tracking: float = 0.0) -> float:
        _, pos = self.shape(text)
        k = size / self.upem
        return sum(p.x_advance for p in pos) * k + tracking * max(len(pos) - 1, 0)

    def path(self, text: str, x: float, baseline: float, size: float, tracking: float = 0.0) -> str:
        from fontTools.pens.svgPathPen import SVGPathPen
        from fontTools.pens.transformPen import TransformPen

        infos, pos = self.shape(text)
        k = size / self.upem
        pen = SVGPathPen(None, ntos=num)
        cx = x
        for info, p in zip(infos, pos):
            gx = cx + p.x_offset * k
            gy = baseline - p.y_offset * k
            self.font.draw_glyph_with_pen(info.codepoint, TransformPen(pen, (k, 0, 0, -k, gx, gy)))
            cx += p.x_advance * k + tracking
        return pen.getCommands()


SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
DROP_NS = ("inkscape", "sodipodi", "rdf", "cc", "dc")


def piece_markup(path: Path, prefix: str, x: float, y: float, size: float) -> str:
    """Inline one 64x64 piece SVG as a nested <svg>, ids prefixed so three can coexist."""
    tree = ET.parse(path)
    root = tree.getroot()
    keep = []
    for child in root:
        tag = child.tag.split("}")[-1]
        if tag in ("defs", "path", "g", "circle", "ellipse", "rect", "polygon"):
            keep.append(child)

    def clean(el: ET.Element) -> None:
        for c in list(el):  # drop editor-only elements (inkscape:path-effect and the like)
            if not c.tag.startswith(f"{{{SVG_NS}}}"):
                el.remove(c)
        for name in list(el.attrib):
            if any(ns in name for ns in DROP_NS) or name.startswith("{http://sodipodi") or name.startswith("{http://www.inkscape"):
                del el.attrib[name]
        if "id" in el.attrib:
            el.attrib["id"] = prefix + el.attrib["id"]
        href = f"{{{XLINK_NS}}}href"
        if href in el.attrib and el.attrib[href].startswith("#"):
            el.attrib["href"] = "#" + prefix + el.attrib.pop(href)[1:]
        for name in ("style", "fill", "stroke"):
            if name in el.attrib:
                el.attrib[name] = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{prefix}{m.group(1)})", el.attrib[name])
        for c in el:
            clean(c)

    parts = []
    for el in keep:
        clean(el)
        s = ET.tostring(el, encoding="unicode")
        s = s.replace(f' xmlns="{SVG_NS}"', "").replace("ns0:", "").replace(":ns0", "")
        s = re.sub(r'\s+xmlns:\w+="[^"]*"', "", s)
        s = re.sub(r">\s+<", "><", s)
        parts.append(s)
    w = root.attrib.get("width", "64").replace("px", "")
    h = root.attrib.get("height", "64").replace("px", "")
    return (
        f'<svg x="{num(x)}" y="{num(y)}" width="{num(size)}" height="{num(size)}" '
        f'viewBox="0 0 {w} {h}">' + "".join(parts) + "</svg>"
    )


def build(fonts: Path, pieces: Path) -> str:
    title_face = Face(fonts / SERIF, {"wght": 600, "opsz": 60})
    sub_face = Face(fonts / SERIF, {"wght": 400, "opsz": 34})
    mono_face = Face(fonts / MONO)

    out: list[str] = []
    out.append(
        f'<svg xmlns="{SVG_NS}" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        'role="img" aria-labelledby="t">'
    )
    out.append('<title id="t">ChessProt: fair-play analysis for online chess. Coming soon.</title>')
    out.append(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="20" fill="{PAPER}" stroke="{RULE}" stroke-width="2"/>')

    # "COMING SOON" pill
    tag, tag_size, tag_track = "COMING SOON", 22, 3.5
    tag_w = mono_face.width(tag, tag_size, tag_track)
    pill_h, pill_pad, pill_y = 46, 22, 62
    out.append(
        f'<rect x="{MARGIN}" y="{pill_y}" width="{num(tag_w + 2 * pill_pad)}" height="{pill_h}" '
        f'rx="{pill_h // 2}" fill="none" stroke="{BOARD_RULE}" stroke-width="2"/>'
    )
    out.append(
        f'<path fill="{BOARD_LIGHT}" d="'
        + mono_face.path(tag, MARGIN + pill_pad, pill_y + pill_h / 2 + tag_size * 0.36, tag_size, tag_track)
        + '"/>'
    )

    # Title and subtitle
    out.append(f'<path fill="{INK}" d="' + title_face.path("ChessProt", MARGIN - 4, 222, 112) + '"/>')
    out.append(
        f'<path fill="{INK_SOFT}" d="'
        + sub_face.path("Fair-play analysis for online chess,", MARGIN, 280, 34)
        + sub_face.path("with its error rates published.", MARGIN, 324, 34)
        + '"/>'
    )

    # Board corner: files e-h, ranks 8-5 (h8 is a dark square)
    bx, by = W - MARGIN - 4 * SQ, (H - 4 * SQ) // 2
    out.append(f'<rect x="{bx}" y="{by}" width="{4 * SQ}" height="{4 * SQ}" fill="{BOARD_LIGHT}"/>')
    darks = []
    for row in range(4):  # row 0 = rank 8
        for col in range(4):  # col 0 = file e
            file_idx, rank = 5 + col, 8 - row  # e=5
            if (file_idx + rank) % 2 == 0:  # a1 (1+1) is dark
                darks.append(f'<rect x="{bx + col * SQ}" y="{by + row * SQ}" width="{SQ}" height="{SQ}"/>')
    out.append(f'<g fill="{BOARD_DARK}">' + "".join(darks) + "</g>")
    out.append(
        f'<rect x="{bx - 1}" y="{by - 1}" width="{4 * SQ + 2}" height="{4 * SQ + 2}" '
        f'fill="none" stroke="{BOARD_RULE}" stroke-width="2"/>'
    )
    for name, prefix, col, row in (("k.svg", "bk-", 2, 0), ("N.svg", "wn-", 1, 2), ("P.svg", "wp-", 3, 3)):
        out.append(piece_markup(pieces / name, prefix, bx + col * SQ, by + row * SQ, SQ))

    out.append("</svg>")
    return "".join(out) + "\n"


def check(svg: str) -> list[str]:
    problems = []
    for bad in ("<text", "<script", "<foreignObject", "<image", "@import", "<style"):
        if bad in svg:
            problems.append(f"contains {bad}")
    # an external reference is an href, xlink:href, src, url() or @import whose target does
    # not start with "#"; xmlns declarations are not references
    for m in re.finditer(r'(?:\bhref|\bsrc)="(?!#)([^"]*)"', svg):
        problems.append(f"external reference {m.group(1)}")
    for m in re.finditer(r"url\(\s*['\"]?(?!#)([^)'\"]*)", svg):
        problems.append(f"url() to {m.group(1)}")
    ids = re.findall(r'\bid="([^"]*)"', svg)
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        problems.append(f"duplicate ids {dupes}")
    refs = set(re.findall(r'href="#([^"]+)"', svg)) | set(re.findall(r"url\(\s*['\"]?#([^)'\"]+)", svg))
    missing = sorted(refs - set(ids))
    if missing:
        problems.append(f"unresolved references {missing}")
    if "<title" not in svg:
        problems.append("no <title>")
    try:
        ET.fromstring(svg)
    except ET.ParseError as e:
        problems.append(f"not valid XML: {e}")
    size = len(svg.encode())
    if size > MAX_BYTES:
        problems.append(f"{size} bytes > {MAX_BYTES}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fonts", type=Path, required=True)
    ap.add_argument("--pieces", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    svg = build(a.fonts, a.pieces)
    problems = check(svg)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(svg, encoding="utf-8")
    print(f"wrote {a.out} ({len(svg.encode())} bytes)")
    for p in problems:
        print(f"CHECK FAILED: {p}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
