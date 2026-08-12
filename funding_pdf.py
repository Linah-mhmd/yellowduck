"""Generate Funding Optimizer PDF report."""
import os
import re
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC = True
except ImportError:
    HAS_ARABIC = False

_ARABIC_RE = re.compile(r'[\u0600-\u06FF]')
_LRM = '\u200e'
_LTR_RUN_RE = re.compile(
    r'\d+(?:[.,]\d+)*(?:%)?(?:\s*·\s*\d+(?:[.,]\d+)*%?)*'
    r'|[A-Za-z]+'
    r'|≈'
    r'|\(\d[\d,.\s]*\)'
)
PAGE_W, PAGE_H = A4
MARGIN = 54


def _register_body_font():
    candidates = [
        ('C:/Windows/Fonts/tahoma.ttf', 'C:/Windows/Fonts/tahomabd.ttf'),
        ('C:/Windows/Fonts/arial.ttf', 'C:/Windows/Fonts/arialbd.ttf'),
        ('C:/Windows/Fonts/segoeui.ttf', 'C:/Windows/Fonts/segoeuib.ttf'),
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
    ]
    for regular, bold in candidates:
        if os.path.exists(regular):
            pdfmetrics.registerFont(TTFont('YD-Regular', regular))
            if os.path.exists(bold):
                pdfmetrics.registerFont(TTFont('YD-Bold', bold))
            else:
                pdfmetrics.registerFont(TTFont('YD-Bold', regular))
            return 'YD-Regular', 'YD-Bold'
    return 'Helvetica', 'Helvetica-Bold'


def _needs_shaping(text):
    return bool(_ARABIC_RE.search(str(text or '')))


def _isolate_ltr_runs(text):
    text = str(text or '')

    def _wrap(match):
        return f'{_LRM}{match.group()}{_LRM}'

    return _LTR_RUN_RE.sub(_wrap, text)


def _display(text, rtl=False):
    text = str(text or '')
    if not rtl or not HAS_ARABIC:
        return text
    if not _needs_shaping(text):
        return text
    prepared = _isolate_ltr_runs(text)
    return get_display(arabic_reshaper.reshape(prepared))


def _fmt_num(value):
    try:
        n = float(value)
        if abs(n) >= 1000:
            return f'{n:,.2f}'
        return f'{n:.2f}'
    except (TypeError, ValueError):
        return str(value or '—')


def _wrap_text(text, font_name, font_size, max_width, rtl=False):
    text = str(text or '').strip()
    if not text:
        return ['']

    def _width(s):
        shown = _display(s, rtl=True) if rtl else s
        return pdfmetrics.stringWidth(shown, font_name, font_size)

    words = text.split()
    lines, current = [], words[0]
    for word in words[1:]:
        trial = f'{current} {word}'
        if _width(trial) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def build_funding_pdf(form, result, labels, lang='en'):
    """Build PDF bytes from form inputs, analysis result, and translated labels."""
    buffer = BytesIO()
    font, font_bold = _register_body_font()
    rtl = lang == 'ar'
    content_w = PAGE_W - 2 * MARGIN

    c = canvas.Canvas(buffer, pagesize=A4)
    y = PAGE_H - MARGIN

    yellow = (0.79, 0.62, 0.03)
    light_yellow = (1, 0.98, 0.92)
    alert_bg = (1, 0.95, 0.80)
    alert_border = (1, 0.76, 0.03)
    section_bg = (1, 0.97, 0.86)
    section_border = (0.94, 0.90, 0.63)
    gray = (0.15, 0.15, 0.15)
    muted = (0.35, 0.35, 0.35)
    line_gray = (0.91, 0.91, 0.91)

    def _bg():
        c.setFillColorRGB(*light_yellow)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    def _new_page():
        nonlocal y
        c.showPage()
        _bg()
        y = PAGE_H - MARGIN

    def _ensure(lines=1, line_h=16):
        nonlocal y
        if y < MARGIN + lines * line_h:
            _new_page()

    def _draw_line(text, size=10, bold=False, color=None, indent=0, right_x=None):
        nonlocal y
        font_name = font_bold if bold else font
        color = color or muted
        rx = right_x if right_x is not None else PAGE_W - MARGIN - indent
        max_w = rx - MARGIN - indent if rtl else content_w - indent
        logical = str(text or '')

        for part in _wrap_text(logical, font_name, size, max_w, rtl=rtl):
            shown = _display(part, rtl=rtl) if rtl else part
            _ensure(1, size + 6)
            c.setFont(font_name, size)
            c.setFillColorRGB(*color)
            if rtl:
                c.drawRightString(rx, y, shown)
            else:
                c.drawString(MARGIN + indent, y, shown)
            y -= size + 6

    def _draw_kv(label, value, indent=0):
        if rtl:
            _draw_line(f'{label} : {value}', indent=indent)
        else:
            _draw_line(f'{label}: {value}', indent=indent)

    def _draw_section_title(title):
        nonlocal y
        _ensure(3, 20)
        title_h = 26
        c.setFillColorRGB(*section_bg)
        c.setStrokeColorRGB(*section_border)
        c.rect(MARGIN, y - 8, content_w, title_h, fill=1, stroke=1)
        ty = y + 6
        c.setFont(font_bold, 12)
        c.setFillColorRGB(*gray)
        shown = _display(title, rtl=rtl)
        if rtl:
            c.drawRightString(PAGE_W - MARGIN - 10, ty, shown)
        else:
            c.drawString(MARGIN + 10, ty, shown)
        y -= title_h + 4

    def _draw_alert(title, message):
        nonlocal y
        _ensure(4, 16)
        box_h = 52
        c.setFillColorRGB(*alert_bg)
        c.setStrokeColorRGB(*alert_border)
        c.setLineWidth(1.2)
        c.rect(MARGIN, y - box_h + 14, content_w, box_h, fill=1, stroke=1)
        c.setLineWidth(1)
        ty = y - 2
        c.setFont(font_bold, 11)
        c.setFillColorRGB(0.54, 0.43, 0.0)
        shown = _display(title, rtl=rtl)
        if rtl:
            c.drawRightString(PAGE_W - MARGIN - 12, ty, shown)
        else:
            c.drawString(MARGIN + 12, ty, shown)
        ty -= 18
        c.setFont(font, 10)
        c.setFillColorRGB(0.36, 0.29, 0.0)
        for part in _wrap_text(message, font, 10, content_w - 24, rtl=rtl):
            shown = _display(part, rtl=rtl)
            if rtl:
                c.drawRightString(PAGE_W - MARGIN - 12, ty, shown)
            else:
                c.drawString(MARGIN + 12, ty, part)
            ty -= 14
        y -= box_h + 10

    def _draw_bullet(text, indent=12):
        nonlocal y
        font_name = font
        size = 10
        bullet = '•'
        rx = PAGE_W - MARGIN - indent
        logical = str(text or '')

        if rtl:
            for part in _wrap_text(logical, font_name, size, rx - MARGIN, rtl=True):
                shown = _display(part, rtl=True)
                line = f'{shown}  {bullet}'
                _ensure(1, size + 6)
                c.setFont(font_name, size)
                c.setFillColorRGB(*gray)
                c.drawRightString(rx, y, line)
                y -= size + 6
                bullet = ''  # only first line gets bullet
        else:
            for i, part in enumerate(_wrap_text(logical, font_name, size, content_w - indent)):
                prefix = f'{bullet}  ' if i == 0 else '     '
                _ensure(1, size + 6)
                c.setFont(font_name, size)
                c.setFillColorRGB(*gray)
                c.drawString(MARGIN + indent, y, f'{prefix}{part}')
                y -= size + 6

    def _draw_kv_block(rows, indent=8):
        nonlocal y
        for i, (label, value) in enumerate(rows):
            _draw_kv(label, value, indent=indent)
            if i < len(rows) - 1:
                ly = y + 3
                c.setStrokeColorRGB(*line_gray)
                c.setLineWidth(0.5)
                if rtl:
                    c.line(MARGIN + indent, ly, PAGE_W - MARGIN - indent, ly)
                else:
                    c.line(MARGIN + indent, ly, PAGE_W - MARGIN - indent, ly)
        y -= 4

    _bg()

    # Header
    _draw_line(labels.get('reportTitle', 'Funding Analysis Report'), size=18, bold=True, color=yellow)
    y -= 4
    _draw_line(labels.get('subtitle', 'Yellow Duck — Funding Optimizer'), size=11, bold=True, color=(0.4, 0.4, 0.4))
    y -= 12

    # Inputs
    _draw_section_title(labels.get('inputs', 'Inputs'))
    input_rows = [
        (labels.get('fundingNeeded', 'Funding Needed'), _fmt_num(form.get('funding'))),
        (labels.get('currentCapital', 'Current Capital'), _fmt_num(form.get('capital'))),
        (labels.get('monthlyRevenue', 'Monthly Revenue'), _fmt_num(form.get('revenue'))),
        (labels.get('monthlyExpenses', 'Monthly Expenses'), _fmt_num(form.get('expenses'))),
        (labels.get('growthRate', 'Annual Growth Rate (%)'), form.get('growth_rate', '')),
        (labels.get('duration', 'Project Duration (months)'), form.get('duration', '')),
        (
            labels.get('companyStage', 'Company Stage'),
            labels.get(f"stage_{form.get('stage', 'seed')}", form.get('stage', '')),
        ),
    ]
    if form.get('use_of_funds'):
        input_rows.append((labels.get('useOfFunds', 'Use of Funds'), form.get('use_of_funds')))
    _draw_kv_block(input_rows)
    y -= 6

    alert = result.get('runway_alert') or {}
    if alert.get('message'):
        _draw_alert(labels.get('runwayAlert', 'Funding Timeline Alert'), alert['message'])

    months_label = labels.get('months', 'months')
    runway = result.get('runway_months')

    _draw_section_title(labels.get('businessMetrics', 'Business Snapshot'))
    metric_rows = [
        (labels.get('projectedRevenue', 'Projected Monthly Revenue'), _fmt_num(result.get('projected_monthly_revenue'))),
        (labels.get('monthlyBurn', 'Monthly Burn'), _fmt_num(result.get('monthly_burn'))),
        (labels.get('runway', 'Runway (months)'), f'{runway} {months_label}' if runway is not None else '—'),
        (labels.get('breakEven', 'Break-even Revenue'), _fmt_num(result.get('break_even_revenue'))),
        (labels.get('externalNeed', 'Estimated External Need'), _fmt_num(result.get('external_need'))),
    ]
    if result.get('funding_coverage_pct') is not None:
        metric_rows.append((labels.get('fundingCoverage', 'Funding Coverage'), f"{result.get('funding_coverage_pct')}%"))
    if result.get('funding_surplus', 0) > 0:
        metric_rows.append((labels.get('fundingSurplus', 'Surplus'), _fmt_num(result.get('funding_surplus'))))
    _draw_kv_block(metric_rows)
    y -= 6

    _draw_section_title(labels.get('predictedRisk', 'Predicted Risk Level'))
    _draw_kv_block([
        (labels.get('predictedRisk', 'Risk'), str(result.get('predicted_risk', '')).upper()),
        (labels.get('profitability', 'Profitability'), f"{float(result.get('profitability', 0)) * 100:.2f}%"),
        (labels.get('stability', 'Stability'), f"{float(result.get('stability', 0)) * 100:.2f}%"),
    ])

    factors = result.get('risk_factors') or []
    if factors:
        y -= 4
        _draw_section_title(labels.get('riskFactors', 'Why this risk level?'))
        for factor in factors:
            _draw_bullet(factor)

    scenarios = result.get('scenarios') or []
    if scenarios:
        y -= 4
        _draw_section_title(labels.get('scenarios', 'What-if Scenarios'))
        scenario_titles = {
            'reduce_expenses_10': labels.get('scenarioReduceExpenses', 'If expenses decrease 10%'),
            'increase_revenue_20': labels.get('scenarioIncreaseRevenue', 'If revenue increases 20%'),
        }
        for i, sc in enumerate(scenarios):
            if i:
                y -= 6
            _draw_line(scenario_titles.get(sc.get('id'), sc.get('id', '')), bold=True, color=gray)
            _draw_kv_block([
                (labels.get('scenarioBurn', 'Monthly burn'), _fmt_num(sc.get('monthly_burn'))),
                (
                    labels.get('scenarioRunway', 'Runway'),
                    f"{sc.get('runway_months')} {months_label}" if sc.get('runway_months') is not None else '—',
                ),
                (labels.get('scenarioExternalNeed', 'External need'), _fmt_num(sc.get('external_need'))),
            ], indent=12)

    y -= 4
    _draw_section_title(labels.get('recommendedMix', 'Recommended Funding Mix'))
    _draw_kv_block([
        (labels.get('equity', 'Equity'), f"{result.get('equity')}%"),
        (labels.get('debt', 'Debt'), f"{result.get('debt')}%"),
        (labels.get('grants', 'Grants'), f"{result.get('grants')}%"),
    ])

    points = result.get('advice_points') or []
    if points:
        y -= 4
        _draw_section_title(labels.get('strategicInsight', 'Strategic Insight'))
        for point in points:
            _draw_bullet(point)

    c.save()
    buffer.seek(0)
    return buffer
