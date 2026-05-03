import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import textwrap

# ── Colour palettes per theme ──────────────────────────────────────────────
THEMES = {
    "professional": {
        "bg": RGBColor(0x0D, 0x1B, 0x2A),        # deep navy
        "accent": RGBColor(0x1E, 0x90, 0xFF),     # dodger blue
        "accent2": RGBColor(0x00, 0xD4, 0xAA),    # teal
        "text": RGBColor(0xFF, 0xFF, 0xFF),
        "subtext": RGBColor(0xB0, 0xC4, 0xDE),
        "chart_colors": ["#1E90FF", "#00D4AA", "#FF6B6B", "#FFD700", "#C084FC"],
    },
    "modern": {
        "bg": RGBColor(0x1A, 0x1A, 0x2E),
        "accent": RGBColor(0xE9, 0x4F, 0x37),
        "accent2": RGBColor(0xF5, 0xA6, 0x23),
        "text": RGBColor(0xFF, 0xFF, 0xFF),
        "subtext": RGBColor(0xCC, 0xCC, 0xCC),
        "chart_colors": ["#E94F37", "#F5A623", "#4ECDC4", "#45B7D1", "#96CEB4"],
    },
    "minimal": {
        "bg": RGBColor(0xFA, 0xFA, 0xFA),
        "accent": RGBColor(0x2D, 0x3A, 0x8C),
        "accent2": RGBColor(0x06, 0xB6, 0xD4),
        "text": RGBColor(0x1F, 0x29, 0x37),
        "subtext": RGBColor(0x6B, 0x72, 0x80),
        "chart_colors": ["#2D3A8C", "#06B6D4", "#10B981", "#F59E0B", "#EF4444"],
    },
    "bold": {
        "bg": RGBColor(0x12, 0x00, 0x2B),
        "accent": RGBColor(0xFF, 0x00, 0x7F),
        "accent2": RGBColor(0x00, 0xFF, 0xD4),
        "text": RGBColor(0xFF, 0xFF, 0xFF),
        "subtext": RGBColor(0xDD, 0xDD, 0xDD),
        "chart_colors": ["#FF007F", "#00FFD4", "#FFD700", "#7C3AED", "#F97316"],
    },
}


def _rgb_to_hex(rgb: RGBColor) -> str:
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


def _add_background(slide, prs, color: RGBColor):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def _add_rect(slide, left, top, width, height, color: RGBColor, transparency=0):
    shape = slide.shapes.add_shape(1, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    if transparency:
        shape.fill.fore_color.theme_color = None
    return shape


def _add_text(slide, text, left, top, width, height,
              font_size=24, bold=False, color=None, align=PP_ALIGN.LEFT,
              wrap=True):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color
    return txBox


def _make_bar_chart(labels, values, xlabel, ylabel, colors, bg_hex, text_hex) -> bytes:
    fig, ax = plt.subplots(figsize=(9, 4.5), facecolor=bg_hex)
    ax.set_facecolor(bg_hex)

    x = np.arange(len(labels))
    bar_colors = (colors * (len(labels) // len(colors) + 1))[:len(labels)]
    bars = ax.bar(x, values, color=bar_colors, width=0.55, zorder=3, edgecolor="none")

    # Value labels on bars
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.02,
                str(val), ha="center", va="bottom", color=text_hex, fontsize=10, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, color=text_hex, fontsize=10)
    ax.set_xlabel(xlabel, color=text_hex, fontsize=11, labelpad=8)
    ax.set_ylabel(ylabel, color=text_hex, fontsize=11, labelpad=8)
    ax.tick_params(colors=text_hex)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(text_hex + "55" if len(text_hex) == 7 else text_hex)
    ax.yaxis.grid(True, color=text_hex + "22" if len(text_hex) == 7 else "#ffffff22", zorder=0)
    ax.set_axisbelow(True)

    plt.tight_layout(pad=0.5)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=bg_hex)
    plt.close(fig)
    buf.seek(0)
    return buf


def _make_pie_chart(labels, values, colors, bg_hex) -> bytes:
    fig, ax = plt.subplots(figsize=(7, 5), facecolor=bg_hex)
    ax.set_facecolor(bg_hex)

    pie_colors = (colors * (len(labels) // len(colors) + 1))[:len(labels)]
    wedges, texts, autotexts = ax.pie(
        values,
        labels=None,
        colors=pie_colors,
        autopct="%1.1f%%",
        startangle=140,
        pctdistance=0.75,
        wedgeprops={"linewidth": 2, "edgecolor": bg_hex},
    )
    for at in autotexts:
        at.set_color("white")
        at.set_fontsize(10)
        at.set_fontweight("bold")

    # Legend
    legend_patches = [mpatches.Patch(color=c, label=l) for c, l in zip(pie_colors, labels)]
    ax.legend(handles=legend_patches, loc="lower center", bbox_to_anchor=(0.5, -0.12),
              ncol=min(len(labels), 3), fontsize=9,
              framealpha=0, labelcolor=bg_hex if bg_hex == "#FAFAFA" else "white")

    ax.axis("equal")
    plt.tight_layout(pad=0.3)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=bg_hex)
    plt.close(fig)
    buf.seek(0)
    return buf


def _make_line_chart(labels, values, xlabel, ylabel, colors, bg_hex, text_hex) -> bytes:
    fig, ax = plt.subplots(figsize=(9, 4.5), facecolor=bg_hex)
    ax.set_facecolor(bg_hex)

    ax.plot(labels, values, color=colors[0], linewidth=2.5, marker="o",
            markersize=7, markerfacecolor=colors[1] if len(colors) > 1 else colors[0])
    ax.fill_between(range(len(labels)), values, alpha=0.15, color=colors[0])

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, color=text_hex, fontsize=10)
    ax.set_xlabel(xlabel, color=text_hex, fontsize=11)
    ax.set_ylabel(ylabel, color=text_hex, fontsize=11)
    ax.tick_params(colors=text_hex)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(text_hex + "55" if len(text_hex) == 7 else text_hex)
    ax.yaxis.grid(True, color="#ffffff22", zorder=0)

    plt.tight_layout(pad=0.5)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=bg_hex)
    plt.close(fig)
    buf.seek(0)
    return buf


# ── Slide builders ─────────────────────────────────────────────────────────

def _build_title_slide(prs, slide_data, theme):
    layout = prs.slide_layouts[6]  # blank
    slide = prs.slides.add_slide(layout)
    W, H = prs.slide_width, prs.slide_height
    t = theme

    _add_background(slide, prs, t["bg"])

    # Accent bar left
    _add_rect(slide, 0, 0, Inches(0.25), H, t["accent"])
    # Bottom accent strip
    _add_rect(slide, 0, H - Inches(0.12), W, Inches(0.12), t["accent2"])

    # Decorative circle
    from pptx.util import Emu
    circle = slide.shapes.add_shape(
        9,  # ellipse
        W - Inches(3.5), -Inches(1),
        Inches(5), Inches(5)
    )
    circle.fill.solid()
    circle.fill.fore_color.rgb = t["accent"]
    circle.line.fill.background()
    # low opacity trick: set transparency via XML
    from lxml import etree
    sp_tree = circle._element
    solidFill = sp_tree.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}solidFill")
    if solidFill is not None:
        srgbClr = solidFill.find("{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr")
        if srgbClr is not None:
            alpha = etree.SubElement(srgbClr, "{http://schemas.openxmlformats.org/drawingml/2006/main}alpha")
            alpha.set("val", "15000")  # 15% opacity

    _add_text(slide, slide_data.get("title", "Presentation"),
              Inches(0.6), Inches(1.8), Inches(8.5), Inches(1.8),
              font_size=44, bold=True, color=t["text"], align=PP_ALIGN.LEFT)

    _add_text(slide, slide_data.get("subtitle", ""),
              Inches(0.6), Inches(3.7), Inches(7), Inches(0.9),
              font_size=20, bold=False, color=t["subtext"], align=PP_ALIGN.LEFT)

    return slide


def _build_bullets_slide(prs, slide_data, theme):
    layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(layout)
    W, H = prs.slide_width, prs.slide_height
    t = theme

    _add_background(slide, prs, t["bg"])
    _add_rect(slide, 0, 0, W, Inches(1.3), t["accent"])
    _add_rect(slide, 0, Inches(1.3), Inches(0.06), H - Inches(1.3), t["accent2"])

    # Title
    _add_text(slide, slide_data.get("title", ""),
              Inches(0.3), Inches(0.15), W - Inches(0.6), Inches(1.0),
              font_size=28, bold=True, color=t["text"], align=PP_ALIGN.LEFT)

    bullets = slide_data.get("bullets", [])
    bullet_top = Inches(1.55)
    bullet_gap = Inches(0.65)
    for i, bullet in enumerate(bullets[:7]):
        # Bullet dot
        dot = slide.shapes.add_shape(9, Inches(0.25), bullet_top + i * bullet_gap + Inches(0.1),
                                      Inches(0.12), Inches(0.12))
        dot.fill.solid()
        dot.fill.fore_color.rgb = t["accent2"]
        dot.line.fill.background()

        _add_text(slide, bullet,
                  Inches(0.55), bullet_top + i * bullet_gap, W - Inches(0.9), Inches(0.6),
                  font_size=18, color=t["text"])

    return slide


def _build_chart_bar_slide(prs, slide_data, theme):
    layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(layout)
    W, H = prs.slide_width, prs.slide_height
    t = theme

    _add_background(slide, prs, t["bg"])
    _add_rect(slide, 0, 0, W, Inches(1.1), t["accent"])

    _add_text(slide, slide_data.get("title", ""),
              Inches(0.3), Inches(0.1), W - Inches(0.6), Inches(0.9),
              font_size=26, bold=True, color=t["text"])

    data = slide_data.get("data", {})
    labels = data.get("labels", ["A", "B", "C"])
    values = data.get("values", [1, 2, 3])
    xlabel = data.get("xlabel", "")
    ylabel = data.get("ylabel", "")

    bg_hex = _rgb_to_hex(t["bg"])
    text_hex = _rgb_to_hex(t["text"])
    chart_buf = _make_bar_chart(labels, values, xlabel, ylabel,
                                t["chart_colors"], bg_hex, text_hex)

    slide.shapes.add_picture(chart_buf, Inches(0.4), Inches(1.2), W - Inches(0.8), H - Inches(1.7))

    desc = slide_data.get("description", "")
    if desc:
        _add_text(slide, desc, Inches(0.4), H - Inches(0.45), W - Inches(0.8), Inches(0.4),
                  font_size=13, color=t["subtext"], align=PP_ALIGN.CENTER)

    return slide


def _build_chart_pie_slide(prs, slide_data, theme):
    layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(layout)
    W, H = prs.slide_width, prs.slide_height
    t = theme

    _add_background(slide, prs, t["bg"])
    _add_rect(slide, 0, 0, W, Inches(1.1), t["accent"])

    _add_text(slide, slide_data.get("title", ""),
              Inches(0.3), Inches(0.1), W - Inches(0.6), Inches(0.9),
              font_size=26, bold=True, color=t["text"])

    data = slide_data.get("data", {})
    labels = data.get("labels", ["A", "B"])
    values = data.get("values", [50, 50])

    bg_hex = _rgb_to_hex(t["bg"])
    chart_buf = _make_pie_chart(labels, values, t["chart_colors"], bg_hex)

    slide.shapes.add_picture(chart_buf, Inches(1.5), Inches(1.15), Inches(7), Inches(5.1))

    desc = slide_data.get("description", "")
    if desc:
        _add_text(slide, desc, Inches(0.4), H - Inches(0.45), W - Inches(0.8), Inches(0.4),
                  font_size=13, color=t["subtext"], align=PP_ALIGN.CENTER)

    return slide


def _build_two_column_slide(prs, slide_data, theme):
    layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(layout)
    W, H = prs.slide_width, prs.slide_height
    t = theme

    _add_background(slide, prs, t["bg"])
    _add_rect(slide, 0, 0, W, Inches(1.1), t["accent"])

    _add_text(slide, slide_data.get("title", ""),
              Inches(0.3), Inches(0.1), W - Inches(0.6), Inches(0.9),
              font_size=26, bold=True, color=t["text"])

    col_w = W / 2 - Inches(0.4)
    divider_x = W / 2

    # Left column
    _add_rect(slide, Inches(0.3), Inches(1.2), col_w, Inches(0.45), t["accent2"])
    _add_text(slide, slide_data.get("left_header", "Left"),
              Inches(0.35), Inches(1.22), col_w, Inches(0.4),
              font_size=16, bold=True, color=t["bg"])

    for i, pt in enumerate(slide_data.get("left_points", [])[:5]):
        _add_text(slide, f"• {pt}",
                  Inches(0.35), Inches(1.85) + i * Inches(0.6), col_w, Inches(0.55),
                  font_size=15, color=t["text"])

    # Divider
    _add_rect(slide, divider_x - Inches(0.02), Inches(1.2),
              Inches(0.04), H - Inches(1.5), t["accent"])

    # Right column
    right_left = divider_x + Inches(0.1)
    _add_rect(slide, right_left, Inches(1.2), col_w, Inches(0.45), t["accent"])
    _add_text(slide, slide_data.get("right_header", "Right"),
              right_left + Inches(0.05), Inches(1.22), col_w, Inches(0.4),
              font_size=16, bold=True, color=t["bg"])

    for i, pt in enumerate(slide_data.get("right_points", [])[:5]):
        _add_text(slide, f"• {pt}",
                  right_left + Inches(0.05), Inches(1.85) + i * Inches(0.6), col_w, Inches(0.55),
                  font_size=15, color=t["text"])

    return slide


def _build_quote_slide(prs, slide_data, theme):
    layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(layout)
    W, H = prs.slide_width, prs.slide_height
    t = theme

    _add_background(slide, prs, t["bg"])

    # Large quote mark background decoration
    _add_text(slide, "“", Inches(0.2), Inches(0.2), Inches(3), Inches(2.5),
              font_size=180, bold=True, color=t["accent"])

    # Quote text
    quote = slide_data.get("quote", "")
    _add_text(slide, quote,
              Inches(0.8), Inches(1.2), W - Inches(1.6), Inches(3),
              font_size=24, bold=False, color=t["text"], align=PP_ALIGN.CENTER, wrap=True)

    # Attribution bar
    _add_rect(slide, Inches(3.5), H - Inches(1.6), Inches(3), Inches(0.06), t["accent2"])
    attr = slide_data.get("attribution", "")
    _add_text(slide, f"— {attr}", Inches(0.5), H - Inches(1.4), W - Inches(1), Inches(0.5),
              font_size=15, color=t["subtext"], align=PP_ALIGN.CENTER)

    return slide


def _build_closing_slide(prs, slide_data, theme):
    layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(layout)
    W, H = prs.slide_width, prs.slide_height
    t = theme

    _add_background(slide, prs, t["bg"])
    _add_rect(slide, 0, 0, W, Inches(0.12), t["accent"])
    _add_rect(slide, 0, H - Inches(0.12), W, Inches(0.12), t["accent2"])

    _add_text(slide, slide_data.get("title", "Key Takeaways"),
              Inches(0.5), Inches(0.4), W - Inches(1), Inches(1.0),
              font_size=32, bold=True, color=t["text"], align=PP_ALIGN.CENTER)

    bullets = slide_data.get("bullets", [])
    for i, b in enumerate(bullets[:4]):
        _add_rect(slide, Inches(1.2), Inches(1.6) + i * Inches(0.85),
                  W - Inches(2.4), Inches(0.65),
                  t["accent"] if i % 2 == 0 else t["accent2"])
        _add_text(slide, b,
                  Inches(1.4), Inches(1.65) + i * Inches(0.85), W - Inches(2.8), Inches(0.55),
                  font_size=17, bold=True, color=t["bg"], align=PP_ALIGN.LEFT)

    cta = slide_data.get("call_to_action", "")
    if cta:
        _add_text(slide, cta, Inches(0.5), H - Inches(1.0), W - Inches(1), Inches(0.6),
                  font_size=16, color=t["subtext"], align=PP_ALIGN.CENTER)

    return slide


# ── Main entry point ───────────────────────────────────────────────────────

SLIDE_BUILDERS = {
    "title": _build_title_slide,
    "bullets": _build_bullets_slide,
    "chart_bar": _build_chart_bar_slide,
    "chart_line": _build_chart_bar_slide,  # reuse bar for now
    "chart_pie": _build_chart_pie_slide,
    "two_column": _build_two_column_slide,
    "quote": _build_quote_slide,
    "closing": _build_closing_slide,
}


def build_presentation(analysis: dict) -> bytes:
    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)

    theme_name = analysis.get("theme", "professional")
    theme = THEMES.get(theme_name, THEMES["professional"])

    for slide_data in analysis.get("slides", []):
        slide_type = slide_data.get("type", "bullets")
        builder = SLIDE_BUILDERS.get(slide_type, _build_bullets_slide)
        builder(prs, slide_data, theme)

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf.getvalue()
