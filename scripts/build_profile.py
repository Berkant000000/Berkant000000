"""Build the profile README and charts from the data files in this repo.

Inputs (all optional; missing files give a "waiting for data" section):
  usage/daily.json   output of `npx ccusage@latest daily --breakdown --json --timezone Europe/Rome`
  data/activity.json ClipFactory build activity: {"updated": "...", "days": [{"date", "commits", "added", "removed"}]}

Outputs: README.md, assets/tokens.png, assets/activity.png

Run: python scripts/build_profile.py   (needs matplotlib)
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
USAGE = ROOT / "usage" / "daily.json"
ACTIVITY = ROOT / "data" / "activity.json"
ASSETS = ROOT / "assets"
TZ = ZoneInfo("Europe/Rome")

BG = "#0b0d14"
PANEL = "#11141f"
GRID = "#262b3d"
TEXT = "#e6e8f2"
MUTED = "#8a90a8"
LINE = "#ffd166"
MODEL_COLORS = {
    "fable": "#ff4fd8",
    "mythos": "#ff4fd8",
    "opus": "#7c5cff",
    "sonnet": "#22d3ee",
    "haiku": "#34d399",
}
OTHER_COLOR = "#64748b"


# ---------- helpers ----------

def human(n: float) -> str:
    n = float(n)
    for unit, size in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(n) >= size:
            return f"{n / size:.1f}{unit}".replace(".0", "")
    return f"{n:.0f}"


def family(model: str) -> str:
    m = model.lower()
    for key in ("fable", "mythos", "opus", "sonnet", "haiku"):
        if key in m:
            return key
    return "altro"


def nice_family(f: str) -> str:
    return {"altro": "Altro"}.get(f, f.capitalize())


def tokens_of(row: dict) -> int:
    if "totalTokens" in row:
        return int(row["totalTokens"] or 0)
    return int(
        sum(
            row.get(k, 0) or 0
            for k in ("inputTokens", "outputTokens", "cacheCreationTokens", "cacheReadTokens")
        )
    )


def cost_of(row: dict) -> float:
    for k in ("totalCost", "cost", "costUSD"):
        if k in row and row[k] is not None:
            return float(row[k])
    return 0.0


def style_axes(ax) -> None:
    ax.set_facecolor(PANEL)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def short_date(d: str) -> str:
    try:
        return datetime.strptime(d[:10], "%Y-%m-%d").strftime("%d/%m")
    except ValueError:
        return d


# ---------- usage (ccusage) ----------

def load_usage() -> list[dict] | None:
    if not USAGE.exists():
        return None
    raw = json.loads(USAGE.read_text(encoding="utf-8"))
    rows = raw.get("daily", raw) if isinstance(raw, dict) else raw
    if not isinstance(rows, list) or not rows:
        return None
    days = []
    for row in rows:
        date = str(row.get("date") or row.get("day") or "")[:10]
        if not date:
            continue
        by_model: dict[str, int] = defaultdict(int)
        for b in row.get("modelBreakdowns") or []:
            by_model[family(str(b.get("modelName") or b.get("model") or ""))] += tokens_of(b)
        total = tokens_of(row)
        if not by_model:
            by_model["altro"] = total
        days.append({"date": date, "tokens": total, "cost": cost_of(row), "models": dict(by_model)})
    days.sort(key=lambda d: d["date"])
    return days or None


def chart_tokens(days: list[dict]) -> None:
    fams = [f for f in ("fable", "mythos", "opus", "sonnet", "haiku", "altro")
            if any(d["models"].get(f) for d in days)]
    labels = [short_date(d["date"]) for d in days]
    x = range(len(days))

    fig, ax = plt.subplots(figsize=(10, 4.6), dpi=150)
    fig.patch.set_facecolor(BG)
    style_axes(ax)
    bottom = [0.0] * len(days)
    for f in fams:
        vals = [d["models"].get(f, 0) for d in days]
        ax.bar(x, vals, bottom=bottom, color=MODEL_COLORS.get(f, OTHER_COLOR),
               width=0.68, label=nice_family(f), zorder=2)
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: human(v)))
    ax.set_xticks(list(x), labels)
    ax.set_ylabel("token al giorno", color=MUTED, fontsize=9)

    ax2 = ax.twinx()
    cum, run = [], 0.0
    for d in days:
        run += d["cost"]
        cum.append(run)
    ax2.plot(list(x), cum, color=LINE, linewidth=2.2, marker="o", markersize=4,
             label="Costo API equivalente (cumulativo)", zorder=3)
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax2.tick_params(colors=LINE, labelsize=9)
    for side in ("top", "left", "bottom"):
        ax2.spines[side].set_visible(False)
    ax2.spines["right"].set_color(GRID)
    ax2.set_ylim(bottom=0)

    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    leg = ax.legend(h1 + h2, l1 + l2, loc="upper left", frameon=False, fontsize=8.5,
                    ncol=min(3, len(h1 + h2)))
    for t in leg.get_texts():
        t.set_color(TEXT)
    ax.set_title("Token consumati con Claude Code", color=TEXT, fontsize=13,
                 loc="left", pad=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(ASSETS / "tokens.png", facecolor=BG)
    plt.close(fig)


# ---------- ClipFactory activity ----------

def load_activity() -> list[dict] | None:
    if not ACTIVITY.exists():
        return None
    raw = json.loads(ACTIVITY.read_text(encoding="utf-8"))
    days = sorted(raw.get("days") or [], key=lambda d: d["date"])
    return days or None


def chart_activity(days: list[dict]) -> None:
    labels = [short_date(d["date"]) for d in days]
    x = range(len(days))
    fig, ax = plt.subplots(figsize=(10, 3.6), dpi=150)
    fig.patch.set_facecolor(BG)
    style_axes(ax)
    ax.bar(x, [d["added"] for d in days], color="#22d3ee", width=0.68, label="Righe aggiunte", zorder=2)
    ax.bar(x, [-d["removed"] for d in days], color="#ff4fd8", width=0.68, label="Righe rimosse", zorder=2)
    for i, d in enumerate(days):
        ax.annotate(f"{d['commits']} commit", (i, d["added"]), textcoords="offset points",
                    xytext=(0, 5), ha="center", color=MUTED, fontsize=8)
    ax.axhline(0, color=GRID, linewidth=0.8)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: human(abs(v))))
    ax.set_xticks(list(x), labels)
    leg = ax.legend(loc="upper left", frameon=False, fontsize=8.5, ncol=2)
    for t in leg.get_texts():
        t.set_color(TEXT)
    ax.set_title("ClipFactory: codice scritto per giorno", color=TEXT, fontsize=13,
                 loc="left", pad=12, fontweight="bold")
    ax.margins(y=0.15)
    fig.tight_layout()
    fig.savefig(ASSETS / "activity.png", facecolor=BG)
    plt.close(fig)


# ---------- plan usage (Settings > Usage) ----------

PLAN = ROOT / "data" / "plan_usage.json"


def load_plan() -> dict | None:
    if not PLAN.exists():
        return None
    raw = json.loads(PLAN.read_text(encoding="utf-8"))
    snaps = sorted(raw.get("snapshots") or [], key=lambda s: s["at"])
    if not snaps:
        return None
    raw["snapshots"] = snaps
    return raw


def chart_plan(plan: dict) -> None:
    snaps = plan["snapshots"]
    last = snaps[-1]
    has_hist = len(snaps) >= 2
    fig = plt.figure(figsize=(10, 4.4 if has_hist else 2.6), dpi=150)
    fig.patch.set_facecolor(BG)
    gs = fig.add_gridspec(2 if has_hist else 1, 1, height_ratios=[1, 1.3] if has_hist else [1])

    ax = fig.add_subplot(gs[0])
    ax.set_facecolor(BG)
    rows = [("Settimana (tutti i modelli)", last["weekly"], "#7c5cff"),
            ("Settimana (Fable)", last["fable"], "#ff4fd8"),
            ("Sessione corrente", last["session"], "#22d3ee")]
    for i, (label, val, color) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.barh(y, 100, color=GRID, height=0.42)
        ax.barh(y, val, color=color, height=0.42)
        ax.text(-2, y, label, ha="right", va="center", color=TEXT, fontsize=10)
        ax.text(101.5, y, f"{val}%", ha="left", va="center", color=TEXT, fontsize=10, fontweight="bold")
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.axis("off")
    ax.set_title(f"Limiti del piano · si azzera {last.get('weekly_reset', '')}", color=TEXT,
                 fontsize=13, loc="left", pad=10, fontweight="bold", x=-0.38)

    if has_hist:
        ax2 = fig.add_subplot(gs[1])
        style_axes(ax2)
        times = [datetime.fromisoformat(s["at"]) for s in snaps]
        ax2.plot(times, [s["weekly"] for s in snaps], color="#7c5cff", linewidth=2.2,
                 marker="o", markersize=3, label="Settimana")
        ax2.plot(times, [s["fable"] for s in snaps], color="#ff4fd8", linewidth=1.6,
                 marker="o", markersize=2.5, label="Fable")
        ax2.set_ylim(0, 100)
        ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
        import matplotlib.dates as mdates
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m %Hh", tz=TZ))
        leg = ax2.legend(loc="upper left", frameon=False, fontsize=8.5, ncol=2)
        for t in leg.get_texts():
            t.set_color(TEXT)

    fig.subplots_adjust(left=0.3, right=0.94, top=0.86, bottom=0.12, hspace=0.35)
    fig.savefig(ASSETS / "plan.png", facecolor=BG)
    plt.close(fig)


# ---------- README ----------

def fmt_int(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def build() -> None:
    ASSETS.mkdir(exist_ok=True)
    usage = load_usage()
    activity = load_activity()
    now = datetime.now(TZ).strftime("%d/%m/%Y %H:%M")
    parts = ["# Ciao 👋", "",
             "Sto costruendo **ClipFactory**, un servizio che trasforma video lunghi in clip "
             "verticali pronte per TikTok e Shorts, scritto quasi interamente con Claude Code.", ""]

    plan = load_plan()
    if plan:
        chart_plan(plan)
        last = plan["snapshots"][-1]
        parts += [f"## 🔋 Piano Claude {plan.get('plan', 'Max')}", "",
                  "![Utilizzo del piano](assets/plan.png)", "",
                  f"Settimana: **{last['weekly']}%** usato (si azzera {last.get('weekly_reset', '—')}) · "
                  f"Fable: **{last['fable']}%** · Sessione: **{last['session']}%** · "
                  f"Letture: {len(plan['snapshots'])}", "",
                  "<sub>Percentuali lette dalla pagina Utilizzo delle impostazioni di Claude.</sub>", ""]

    parts += ["## ⚡ Token con Claude Code", ""]
    if usage:
        chart_tokens(usage)
        today_key = datetime.now(TZ).strftime("%Y-%m-%d")
        month_key = today_key[:7]
        last = usage[-1]
        today = next((d for d in usage if d["date"] == today_key), None)
        month = [d for d in usage if d["date"].startswith(month_key)]
        totals_by_model: dict[str, int] = defaultdict(int)
        for d in usage:
            for f, v in d["models"].items():
                totals_by_model[f] += v
        top = max(totals_by_model.items(), key=lambda kv: kv[1])[0] if totals_by_model else "—"
        all_tok = sum(d["tokens"] for d in usage)
        all_cost = sum(d["cost"] for d in usage)
        best = max(usage, key=lambda d: d["tokens"])
        day_label = "Oggi" if today else f"Ultimo giorno ({short_date(last['date'])})"
        day = today or last
        parts += [
            "![Token consumati](assets/tokens.png)", "",
            "| | Token | Costo API equivalente |",
            "|---|---:|---:|",
            f"| {day_label} | {fmt_int(day['tokens'])} | ${day['cost']:,.2f} |",
            f"| Questo mese | {fmt_int(sum(d['tokens'] for d in month))} | "
            f"${sum(d['cost'] for d in month):,.2f} |",
            f"| Da sempre | **{fmt_int(all_tok)}** | **${all_cost:,.2f}** |",
            "",
            f"Modello più usato: **{nice_family(top)}** · Giorno record: "
            f"**{short_date(best['date'])}** con {human(best['tokens'])} token · "
            f"Giorni tracciati: {len(usage)}",
            "",
            "<sub>Dati da [ccusage](https://github.com/ryoppippi/ccusage). Il costo è quanto "
            "costerebbero gli stessi token pagando le API, non quanto pago con l'abbonamento.</sub>",
            "",
        ]
    else:
        parts += ["_In attesa del primo conteggio: il grafico compare appena la sessione di "
                  "Claude Code carica i dati di ccusage._", ""]

    if activity:
        chart_activity(activity)
        commits = sum(d["commits"] for d in activity)
        added = sum(d["added"] for d in activity)
        removed = sum(d["removed"] for d in activity)
        parts += ["## 🏭 ClipFactory in numeri", "",
                  "![Attività ClipFactory](assets/activity.png)", "",
                  f"**{fmt_int(commits)}** commit · **+{fmt_int(added)}** righe · "
                  f"**−{fmt_int(removed)}** righe in {len(activity)} giorni", ""]

    parts += ["---", f"<sub>Aggiornato automaticamente il {now} (ora italiana).</sub>", ""]
    (ROOT / "README.md").write_text("\n".join(parts), encoding="utf-8")


if __name__ == "__main__":
    build()
