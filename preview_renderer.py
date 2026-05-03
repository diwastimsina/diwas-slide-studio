"""
Renders slide deck JSON into PNG thumbnail images for the live preview panel.
"""

import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import textwrap

# Thumbnail size
W, H = 960, 540

THEMES = {
    "professional": {
        "bg": "#0D1B2A", "accent": "#1E90FF", "accent2": "#00D4AA",
        "text": "#FFFFFF", "subtext": "#B0C4DE",
        "chart_colors": ["#1E90FF", "#00D4AA", "#FF6B6B", "#FFD700", "#C084FC"],
    },
    "modern": {
        "bg": "#1A1A2E", "accent": "#E94F37", "accent2": "#F5A623",
        "text": "#FFFFFF", "subtext": "#CCCCCC",
        "chart_colors": ["#E94F37", "#F5A623", "#4ECDC4", "#45B7D1", "#96CEB4"],
    },
    "minimal": {
        "bg": "#FAFAFA", "accent": "#2D3A8C", "accent2": "#06B6D4",
        "text": "#1F2937", "subtext": "#6B7280",
        "chart_colors": ["#2D3A8C", "#06B6D4", "#10B981", "#F59E0B", "#EF4444"],
    },
    "bold": {
        "bg": "#12002B", "accent": "#FF007F", "accent2": "#00FFD4",
        "text": "#FFFFFF", "subtext": "#DDDDDD",
        "chart_colors": ["#FF007F", "#00FFD4", "#FFD700", "#7C3AED", "#F97316"],
    },
}


def _hex(c): return c


def _wrap(text, width=40):
    return "\n".join(textwrap.wrap(str(text), width))


def _render_title(ax, slide, t):
    ax.set_facecolor(t["bg"])
    # Accent bar left
    ax.axvline(x=0.015, color=t["accent"], linewidth=8)
    # Bottom strip
    ax.axhline(y=0.03, color=t["accent2"], linewidth=4)
    # Decorative circle
    circle = plt.Circle((1.05, 0.85), 0.45, color=t["accent"], alpha=0.12)
    ax.add_patch(circle)
    title = slide.get("title", "Presentation")
    subtitle = slide.get("subtitle", "")
    ax.text(0.07, 0.58, _wrap(title, 35), transform=ax.transAxes,
            fontsize=22, fontweight="bold", color=t["text"],
            va="center", ha="left", wrap=True)
    ax.text(0.07, 0.35, _wrap(subtitle, 55), transform=ax.transAxes,
            fontsize=11, color=t["subtext"], va="center", ha="left")


def _render_bullets(ax, slide, t):
    ax.set_facecolor(t["bg"])
    # Header bar
    header = patches.FancyBboxPatch((0, 0.82), 1, 0.18,
                                     boxstyle="square,pad=0", facecolor=t["accent"])
    ax.add_patch(header)
    ax.text(0.04, 0.91, _wrap(slide.get("title", ""), 45), transform=ax.transAxes,
            fontsize=14, fontweight="bold", color=t["text"], va="center")
    bullets = slide.get("bullets", [])
    for i, b in enumerate(bullets[:6]):
        y = 0.74 - i * 0.115
        ax.plot([0.04], [y + 0.02], "o", color=t["accent2"],
                markersize=5, transform=ax.transAxes)
        ax.text(0.08, y, _wrap(b, 60), transform=ax.transAxes,
                fontsize=9.5, color=t["text"], va="top")


def _render_bar_chart(ax, slide, t):
    ax.set_facecolor(t["bg"])
    header = patches.FancyBboxPatch((0, 0.85), 1, 0.15,
                                     boxstyle="square,pad=0", facecolor=t["accent"])
    ax.add_patch(header)
    ax.text(0.04, 0.925, _wrap(slide.get("title", ""), 45), transform=ax.transAxes,
            fontsize=13, fontweight="bold", color=t["text"], va="center")

    data = slide.get("data", {})
    labels = data.get("labels", ["A", "B", "C"])
    values = data.get("values", [1, 2, 3])

    # Inset axes for the chart
    inset = ax.inset_axes([0.05, 0.08, 0.9, 0.72])
    inset.set_facecolor(t["bg"])
    colors = (t["chart_colors"] * 5)[:len(labels)]
    inset.bar(range(len(labels)), values, color=colors, width=0.55, edgecolor="none")
    inset.set_xticks(range(len(labels)))
    inset.set_xticklabels(labels, color=t["subtext"], fontsize=7)
    inset.tick_params(colors=t["subtext"], labelsize=7)
    inset.spines[["top", "right"]].set_visible(False)
    for sp in ["left", "bottom"]:
        inset.spines[sp].set_color(t["subtext"] + "55")
    inset.yaxis.grid(True, color=t["subtext"] + "22", zorder=0)


def _render_pie_chart(ax, slide, t):
    ax.set_facecolor(t["bg"])
    header = patches.FancyBboxPatch((0, 0.85), 1, 0.15,
                                     boxstyle="square,pad=0", facecolor=t["accent"])
    ax.add_patch(header)
    ax.text(0.04, 0.925, _wrap(slide.get("title", ""), 45), transform=ax.transAxes,
            fontsize=13, fontweight="bold", color=t["text"], va="center")

    data = slide.get("data", {})
    labels = data.get("labels", ["A", "B"])
    values = data.get("values", [50, 50])
    colors = (t["chart_colors"] * 5)[:len(labels)]

    inset = ax.inset_axes([0.2, 0.05, 0.6, 0.75])
    inset.set_facecolor(t["bg"])
    inset.pie(values, colors=colors, autopct="%1.0f%%", startangle=140,
              pctdistance=0.75,
              wedgeprops={"linewidth": 1.5, "edgecolor": t["bg"]},
              textprops={"color": t["text"], "fontsize": 7})
    inset.axis("equal")

    # Legend
    for i, (lbl, clr) in enumerate(zip(labels[:4], colors)):
        ax.add_patch(patches.FancyBboxPatch((0.02 + i * 0.25, 0.01), 0.02, 0.03,
                                             boxstyle="square,pad=0", facecolor=clr,
                                             transform=ax.transAxes))
        ax.text(0.055 + i * 0.25, 0.025, lbl[:12], transform=ax.transAxes,
                fontsize=6.5, color=t["subtext"], va="center")


def _render_two_column(ax, slide, t):
    ax.set_facecolor(t["bg"])
    header = patches.FancyBboxPatch((0, 0.85), 1, 0.15,
                                     boxstyle="square,pad=0", facecolor=t["accent"])
    ax.add_patch(header)
    ax.text(0.04, 0.925, _wrap(slide.get("title", ""), 45), transform=ax.transAxes,
            fontsize=13, fontweight="bold", color=t["text"], va="center")

    # Left col header
    lh = patches.FancyBboxPatch((0.02, 0.73), 0.455, 0.09,
                                  boxstyle="square,pad=0", facecolor=t["accent2"])
    ax.add_patch(lh)
    ax.text(0.04, 0.775, slide.get("left_header", "")[:20], transform=ax.transAxes,
            fontsize=9, fontweight="bold", color=t["bg"], va="center")

    for i, pt in enumerate(slide.get("left_points", [])[:4]):
        ax.text(0.04, 0.67 - i * 0.13, f"• {_wrap(pt, 28)}", transform=ax.transAxes,
                fontsize=8, color=t["text"], va="top")

    # Divider
    ax.axvline(x=0.5, color=t["accent"], linewidth=1.5, alpha=0.5)

    # Right col header
    rh = patches.FancyBboxPatch((0.525, 0.73), 0.455, 0.09,
                                  boxstyle="square,pad=0", facecolor=t["accent"])
    ax.add_patch(rh)
    ax.text(0.545, 0.775, slide.get("right_header", "")[:20], transform=ax.transAxes,
            fontsize=9, fontweight="bold", color=t["bg"], va="center")

    for i, pt in enumerate(slide.get("right_points", [])[:4]):
        ax.text(0.545, 0.67 - i * 0.13, f"• {_wrap(pt, 28)}", transform=ax.transAxes,
                fontsize=8, color=t["text"], va="top")


def _render_quote(ax, slide, t):
    ax.set_facecolor(t["bg"])
    ax.text(0.03, 0.92, "“", transform=ax.transAxes,
            fontsize=72, color=t["accent"], alpha=0.4, va="top")
    quote = slide.get("quote", "")
    ax.text(0.5, 0.54, _wrap(quote, 50), transform=ax.transAxes,
            fontsize=13, color=t["text"], va="center", ha="center",
            style="italic", wrap=True)
    ax.axhline(y=0.25, xmin=0.3, xmax=0.7, color=t["accent2"], linewidth=2)
    attr = slide.get("attribution", "")
    ax.text(0.5, 0.17, f"— {attr}", transform=ax.transAxes,
            fontsize=9, color=t["subtext"], va="center", ha="center")


def _render_closing(ax, slide, t):
    ax.set_facecolor(t["bg"])
    ax.axhline(y=0.97, color=t["accent"], linewidth=4)
    ax.axhline(y=0.03, color=t["accent2"], linewidth=4)
    ax.text(0.5, 0.84, slide.get("title", "Key Takeaways"), transform=ax.transAxes,
            fontsize=17, fontweight="bold", color=t["text"], va="center", ha="center")
    bullets = slide.get("bullets", [])
    colors = [t["accent"], t["accent2"]] * 5
    for i, b in enumerate(bullets[:4]):
        y = 0.66 - i * 0.13
        bp = patches.FancyBboxPatch((0.1, y - 0.04), 0.8, 0.1,
                                     boxstyle="round,pad=0.01",
                                     facecolor=colors[i], alpha=0.9)
        ax.add_patch(bp)
        ax.text(0.5, y + 0.01, _wrap(b, 55), transform=ax.transAxes,
                fontsize=8.5, fontweight="bold", color=t["bg"], va="center", ha="center")
    cta = slide.get("call_to_action", "")
    if cta:
        ax.text(0.5, 0.1, cta, transform=ax.transAxes,
                fontsize=8, color=t["subtext"], va="center", ha="center")


RENDERERS = {
    "title": _render_title,
    "bullets": _render_bullets,
    "chart_bar": _render_bar_chart,
    "chart_line": _render_bar_chart,
    "chart_pie": _render_pie_chart,
    "two_column": _render_two_column,
    "quote": _render_quote,
    "closing": _render_closing,
}


def render_slide_thumbnail(slide: dict, theme_name: str) -> bytes:
    t = THEMES.get(theme_name, THEMES["professional"])
    slide_type = slide.get("type", "bullets")
    renderer = RENDERERS.get(slide_type, _render_bullets)

    fig, ax = plt.subplots(figsize=(9.6, 5.4), facecolor=t["bg"])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    renderer(ax, slide, t)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight",
                facecolor=t["bg"], pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def render_all_thumbnails(analysis: dict) -> list[bytes]:
    theme = analysis.get("theme", "professional")
    return [render_slide_thumbnail(s, theme) for s in analysis.get("slides", [])]
