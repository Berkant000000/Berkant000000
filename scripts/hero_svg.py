"""Animated hero card (SVG) for the profile README.

GitHub shows SVGs through <img>, so: no scripts, no web fonts, SMIL + CSS animations only.
"""

from __future__ import annotations

import math
from html import escape

W, H = 1000, 560
COLORS = ["#8b5cf6", "#ff4fd8", "#22d3ee", "#34d399", "#ffd166", "#f97316"]
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace"


def human(n: float, it: bool = True) -> str:
    for unit, size in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(n) >= size:
            s = f"{n / size:.1f}".rstrip("0").rstrip(".")
            return (s.replace(".", ",") if it else s) + unit
    return f"{n:.0f}"


def money(v: float) -> str:
    return f"${v:,.0f}".replace(",", ".")


def build_hero(data: dict) -> str:
    projects = data["projects"]
    total = sum(p["total"] for p in projects)
    cost = sum(p["cost"] for p in projects)
    out = sum(p["output"] for p in projects)
    cw = sum(p["cache_write"] for p in projects)
    cr = sum(p["cache_read"] for p in projects)
    inp = sum(p["input"] for p in projects)
    hit = cr / (cr + cw + inp) * 100 if (cr + cw + inp) else 0
    full_price = total * data["pricing"]["input"] / 1e6
    big = f"{total / 1e9:.2f}".replace(".", ",")

    # ---- donut ----
    cx, cy, r, sw = 808, 262, 124, 24
    circ = 2 * math.pi * r
    gap = 6
    segs, start = [], 0.0
    for i, p in enumerate(projects):
        frac = p["total"] / total
        length = max(frac * circ - gap, 2)
        color = COLORS[i % len(COLORS)]
        delay = 0.35 + i * 0.25
        segs.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-dasharray="{length:.1f} {circ:.1f}" '
            f'stroke-dashoffset="{length:.1f}" transform="rotate({-90 + start * 360:.2f} {cx} {cy})" '
            f'filter="url(#glow)">'
            f'<animate attributeName="stroke-dashoffset" from="{length:.1f}" to="0" begin="{delay:.2f}s" '
            f'dur="1.4s" fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1" keyTimes="0;1"/></circle>'
        )
        start += frac

    # ---- project bars ----
    rows = []
    top = max(p["total"] for p in projects)
    for i, p in enumerate(projects[:5]):
        y = 318 + i * 38
        color = COLORS[i % len(COLORS)]
        wbar = max(240 * p["total"] / top, 4)
        rows.append(
            f'<g class="fade" style="animation-delay:{0.9 + i * 0.15:.2f}s">'
            f'<circle cx="62" cy="{y - 5}" r="5" fill="{color}"/>'
            f'<text x="76" y="{y}" class="row">{escape(p["name"])}</text>'
            f'<rect x="236" y="{y - 12}" width="240" height="10" rx="5" fill="#ffffff" fill-opacity=".06"/>'
            f'<rect x="236" y="{y - 12}" width="0" height="10" rx="5" fill="{color}">'
            f'<animate attributeName="width" from="0" to="{wbar:.1f}" begin="{1.0 + i * 0.15:.2f}s" dur="1.1s" '
            f'fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1" keyTimes="0;1"/></rect>'
            f'<text x="490" y="{y}" class="val">{human(p["total"])}</text>'
            f'<text x="620" y="{y}" class="cost" text-anchor="end">{money(p["cost"])}</text></g>'
        )

    # ---- stat chips ----
    chips = [("OUTPUT", human(out)), ("SCRITTURA CACHE", human(cw)),
             ("LETTURA CACHE", human(cr)), ("CACHE HIT", f"{hit:.0f}%")]
    chip_svg = []
    for i, (label, value) in enumerate(chips):
        x = 48 + i * 232
        chip_svg.append(
            f'<g class="fade" style="animation-delay:{1.5 + i * 0.12:.2f}s">'
            f'<rect x="{x}" y="502" width="216" height="40" rx="12" fill="#ffffff" fill-opacity=".04" '
            f'stroke="#ffffff" stroke-opacity=".09"/>'
            f'<text x="{x + 16}" y="527" class="chipl">{label}</text>'
            f'<text x="{x + 200}" y="527" class="chipv" text-anchor="end">{value}</text></g>'
        )

    sparks = []
    for i in range(26):
        x = (i * 137) % W
        y = (i * 89) % H
        sparks.append(
            f'<circle cx="{x}" cy="{y}" r="{1 + (i % 3) * 0.6:.1f}" fill="#fff" opacity="0">'
            f'<animate attributeName="opacity" values="0;.55;0" dur="{3 + i % 4}s" begin="{(i % 7) * 0.6:.1f}s" '
            f'repeatCount="indefinite"/></circle>'
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{big} miliardi di token con Claude Code, {money(cost)} a prezzi API Opus 5.5">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0d0b1f"/><stop offset=".55" stop-color="#090a14"/><stop offset="1" stop-color="#0a1320"/></linearGradient>
  <linearGradient id="txt" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#c4b5fd"/><stop offset=".45" stop-color="#ff7ae6"/><stop offset="1" stop-color="#5eead4"/>
    <animate attributeName="x1" values="0;-.6;0" dur="8s" repeatCount="indefinite"/><animate attributeName="x2" values="1;.4;1" dur="8s" repeatCount="indefinite"/></linearGradient>
  <radialGradient id="blob1"><stop offset="0" stop-color="#8b5cf6" stop-opacity=".55"/><stop offset="1" stop-color="#8b5cf6" stop-opacity="0"/></radialGradient>
  <radialGradient id="blob2"><stop offset="0" stop-color="#ff4fd8" stop-opacity=".35"/><stop offset="1" stop-color="#ff4fd8" stop-opacity="0"/></radialGradient>
  <radialGradient id="blob3"><stop offset="0" stop-color="#22d3ee" stop-opacity=".3"/><stop offset="1" stop-color="#22d3ee" stop-opacity="0"/></radialGradient>
  <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="#fff" stroke-opacity=".035"/></pattern>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="soft"><feGaussianBlur stdDeviation="40"/></filter>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="24"/></clipPath>
</defs>
<style>
  text {{ font-family: {FONT}; }}
  .eyebrow {{ font: 700 13px {MONO}; letter-spacing: 3px; fill: #a78bfa; }}
  .big {{ font-weight: 800; font-size: 118px; letter-spacing: -4px; }}
  .unit {{ font-weight: 700; font-size: 30px; fill: #e9e7ff; }}
  .sub {{ font-size: 17px; fill: #9aa0bd; }}
  .row {{ font-size: 16px; font-weight: 600; fill: #e9e7ff; }}
  .val {{ font: 700 14px {MONO}; fill: #e9e7ff; }}
  .cost {{ font: 600 14px {MONO}; fill: #ffd166; }}
  .chipl {{ font: 700 10.5px {MONO}; letter-spacing: 1.5px; fill: #8b90ad; }}
  .chipv {{ font: 800 16px {MONO}; fill: #fff; }}
  .money {{ font-weight: 800; font-size: 44px; fill: #ffd166; letter-spacing: -1px; }}
  .moneyl {{ font: 700 11px {MONO}; letter-spacing: 2px; fill: #b6b0d6; }}
  .note {{ font-size: 12px; fill: #6f7593; }}
  .fade {{ opacity: 0; animation: up .8s cubic-bezier(.2,.8,.2,1) forwards; }}
  .pulse {{ animation: pulse 2.4s ease-in-out infinite; transform-origin: 56px 52px; }}
  @keyframes up {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: none; }} }}
  @keyframes pulse {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: .35; }} }}
</style>
<g clip-path="url(#card)">
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <rect width="{W}" height="{H}" fill="url(#grid)"/>
  <circle cx="160" cy="80" r="260" fill="url(#blob1)"><animate attributeName="cx" values="160;260;160" dur="14s" repeatCount="indefinite"/></circle>
  <circle cx="820" cy="120" r="240" fill="url(#blob2)"><animate attributeName="cy" values="120;220;120" dur="12s" repeatCount="indefinite"/></circle>
  <circle cx="760" cy="520" r="260" fill="url(#blob3)"><animate attributeName="cx" values="760;640;760" dur="16s" repeatCount="indefinite"/></circle>
  {''.join(sparks)}
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="24" fill="none" stroke="#fff" stroke-opacity=".1"/>

  <circle cx="56" cy="52" r="5" fill="#34d399" class="pulse"/>
  <text x="72" y="57" class="eyebrow">CLAUDE CODE · TOKEN USAGE</text>

  <g class="fade" style="animation-delay:.15s">
    <text x="44" y="186" class="big" fill="url(#txt)" filter="url(#glow)">{big}</text>
    <text x="{48 + len(big) * 62}" y="186" class="unit">miliardi</text>
    <text x="48" y="222" class="sub">di token bruciati con Claude Code su {len(projects)} progetti</text>
  </g>
  <line x1="48" y1="262" x2="620" y2="262" stroke="#fff" stroke-opacity=".08"/>
  <text x="48" y="290" class="eyebrow" style="font-size:11px;fill:#8b90ad">PROGETTO</text>
  <text x="620" y="290" text-anchor="end" class="eyebrow" style="font-size:11px;fill:#8b90ad">API</text>
  {''.join(rows)}

  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#fff" stroke-opacity=".05" stroke-width="{sw}"/>
  <circle cx="{cx}" cy="{cy}" r="{r - 40}" fill="#ffd166" fill-opacity=".05" filter="url(#soft)"/>
  {''.join(segs)}
  <g class="fade" style="animation-delay:1.2s">
    <text x="{cx}" y="{cy - 6}" text-anchor="middle" class="money">{money(cost)}</text>
    <text x="{cx}" y="{cy + 20}" text-anchor="middle" class="moneyl">VALORE A PREZZI API</text>
    <text x="{cx}" y="{cy + 40}" text-anchor="middle" class="moneyl" style="fill:#8b90ad">OPUS 5.5</text>
  </g>
  <text x="{cx}" y="{cy + r + 52}" text-anchor="middle" class="note">a prezzo pieno d'input sarebbero {money(full_price)}</text>

  {''.join(chip_svg)}
</g>
</svg>
'''
