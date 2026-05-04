#!/usr/bin/env python3
"""
Prospect Audit & Strategy - Hybrid Chart Generator (SEO + AEO + GEO)
===================================================================
Generates all visualizations required for DOCX and PPT outputs.
Preferred engines: Seaborn / Plotly (+ kaleido export), with Matplotlib fallback.
"""

import os
import json
import importlib.util
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle, Wedge

# Optional modern engines
try:
    import seaborn as sns
    HAS_SEABORN = True
except Exception:
    HAS_SEABORN = False
    sns = None

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except Exception:
    HAS_PLOTLY = False
    px = None
    go = None
    make_subplots = None

HAS_KALEIDO = importlib.util.find_spec("kaleido") is not None

PROSPECT_NAME = os.environ.get("PROSPECT_NAME", "PROSPECT")
DEFAULT_OUTPUT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output"))
DATA_DIR = os.environ.get("OUTPUT_DIR", DEFAULT_OUTPUT_ROOT)
OUTPUT_DIR = os.path.join(DATA_DIR, "charts")
os.makedirs(OUTPUT_DIR, exist_ok=True)
# Ensure kaleido/temp files are written to a known writable folder (important on some Windows setups).
_TMP_DIR = os.path.join(DATA_DIR, ".tmp_kaleido")
os.makedirs(_TMP_DIR, exist_ok=True)
os.environ["TMP"] = _TMP_DIR
os.environ["TEMP"] = _TMP_DIR

NAVY = '#1B2A4A'
BLUE = '#2E5090'
LIGHT_BLUE = '#4A90D9'
GREEN = '#7AB648'
CYAN = '#00AEEF'
DARK_GREY = '#2D3748'
MID_GREY = '#4A5568'
LIGHT_GREY = '#A0AEC0'
BG_WHITE = '#FFFFFF'
BG_LIGHT = '#F7FAFC'
SEO_COLOR = BLUE
AEO_COLOR = '#E67E22'
GEO_COLOR = '#9B59B6'
PALETTE = [BLUE, GREEN, CYAN, '#E67E22', '#9B59B6', '#1ABC9C', '#E74C3C', '#34495E', '#F39C12', '#2ECC71']
PLOTLY_TEMPLATE = "plotly_white"
CHART_EXPORT_DPI = 450
PLOTLY_EXPORT_SCALE = 3
FONT_STACK = ['DejaVu Sans', 'Liberation Sans', 'Noto Sans', 'Arial', 'sans-serif']
PLOTLY_FONT_FAMILY = "DejaVu Sans, Liberation Sans, Noto Sans, Arial, sans-serif"

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': FONT_STACK,
    'font.size': 12,
    'axes.titlesize': 16,
    'axes.titleweight': 'bold',
    'axes.labelsize': 12,
    'axes.edgecolor': '#E2E8F0',
    'axes.linewidth': 0.8,
    'xtick.color': DARK_GREY,
    'ytick.color': DARK_GREY,
    'text.color': DARK_GREY,
    'figure.facecolor': BG_WHITE,
    'axes.facecolor': BG_LIGHT,
    'grid.color': '#E2E8F0',
    'grid.linewidth': 0.5,
})

if HAS_SEABORN:
    sns.set_theme(style="whitegrid", context="notebook")

CHART_RENDERERS = {
    'search_demand_by_cluster': 'seaborn',
    'competitive_landscape': 'plotly',
    'opportunity_matrix': 'plotly',
    'traffic_value_opportunity': 'plotly',
    'integrated_scorecard': 'plotly',
    'layer_distribution': 'plotly',
    'three_layer_overview': 'matplotlib',
    'before_after_scores': 'plotly',
}

def _resolve_renderer(chart_key, explicit=None):
    renderer = (explicit or CHART_RENDERERS.get(chart_key, 'matplotlib')).lower()
    if renderer == 'seaborn' and not HAS_SEABORN:
        return 'matplotlib'
    if renderer == 'plotly' and not (HAS_PLOTLY and HAS_KALEIDO):
        return 'matplotlib'
    if renderer not in {'seaborn', 'plotly', 'matplotlib'}:
        return 'matplotlib'
    return renderer

def _save_plotly(fig, filename, width=1400, height=800, scale=2):
    path = os.path.join(OUTPUT_DIR, filename)
    try:
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            paper_bgcolor=BG_WHITE,
            plot_bgcolor=BG_LIGHT,
            font=dict(family=PLOTLY_FONT_FAMILY, color=DARK_GREY),
        )
        fig.write_image(path, width=width, height=height, scale=max(scale, PLOTLY_EXPORT_SCALE))
        print(f"Chart saved: {filename}")
        return True
    except Exception as e:
        print(f"[Warn] Plotly export failed for {filename}: {e}. Falling back to Matplotlib.")
        return False


def create_search_demand_chart(cluster_data, renderer=None):
    order = sorted(cluster_data, key=lambda x: x.get('volume', 0), reverse=True)
    names = [c['name'] for c in order]
    volumes = [c['volume'] for c in order]
    max_volume = max(volumes) if volumes else 1
    x_max = max_volume * 1.08
    bar_colors = ['#36A3C7', '#7DBA3B', '#4867A6'][:len(names)]

    fig, ax = plt.subplots(figsize=(14.5, 6.8))
    y_pos = np.arange(len(names))

    # Reference-style light tracks behind each dynamic bar.
    ax.barh(y_pos, [x_max] * len(names), color='#E9EFF8', height=0.56, edgecolor='none', zorder=0)
    ax.barh(y_pos, volumes, color=bar_colors, height=0.56, edgecolor='none', zorder=2)

    for idx, val in enumerate(volumes):
        label_x = min(val + x_max * 0.018, x_max * 0.975)
        ax.text(label_x, idx, f'{int(val):,}', va='center', ha='left',
                fontsize=16, color=NAVY, fontweight='bold')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=17, color=NAVY)
    ax.set_xlabel('Total Monthly Search Volume', fontsize=16, color=MID_GREY, labelpad=16)
    ax.set_title(f'{PROSPECT_NAME} - Total Addressable Search Demand by Category',
                 color=NAVY, pad=30, fontsize=29, fontweight='bold')
    ax.set_xlim(0, x_max)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'{int(x):,}'))
    ax.tick_params(axis='x', labelsize=13, colors=LIGHT_GREY, length=0)
    ax.tick_params(axis='y', length=0)
    ax.invert_yaxis()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.grid(axis='x', color='#B9C6DA', alpha=0.25, linewidth=1.0)
    ax.set_facecolor(BG_WHITE)
    fig.patch.set_facecolor(BG_WHITE)
    plt.subplots_adjust(left=0.23, right=0.97, top=0.84, bottom=0.17)
    plt.savefig(os.path.join(OUTPUT_DIR, 'search_demand_by_cluster.png'), dpi=CHART_EXPORT_DPI, bbox_inches='tight')
    plt.close()
    print('Chart saved: search_demand_by_cluster.png')


def create_competitive_landscape_chart(competitors, renderer=None):
    names = [c['name'] for c in competitors]
    engine = _resolve_renderer('competitive_landscape', renderer)
    if engine == 'plotly':
        kws = [c.get('keywords', 0) for c in competitors]
        traf = [c.get('traffic', 0) for c in competitors]
        val = [c.get('traffic_value', 0) for c in competitors]
        fig = make_subplots(rows=1, cols=3, subplot_titles=[
            'Organic Keywords', 'Monthly Organic Traffic', 'Organic Traffic Value ($)'
        ])
        fig.add_trace(go.Bar(x=names, y=kws, marker_color=PALETTE[:len(names)], showlegend=False), row=1, col=1)
        fig.add_trace(go.Bar(x=names, y=traf, marker_color=PALETTE[:len(names)], showlegend=False), row=1, col=2)
        fig.add_trace(go.Bar(x=names, y=val, marker_color=PALETTE[:len(names)], showlegend=False), row=1, col=3)
        fig.update_layout(title=f'{PROSPECT_NAME} vs. Key Competitors')
        fig.update_yaxes(tickformat=',')
        if _save_plotly(fig, 'competitive_landscape.png', width=1700, height=700, scale=2):
            return

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    metrics = [
        ('keywords', 'Organic Keywords', axes[0]),
        ('traffic', 'Monthly Organic Traffic', axes[1]),
        ('traffic_value', 'Organic Traffic Value ($)', axes[2]),
    ]

    for key, title, ax in metrics:
        vals = [c.get(key, 0) for c in competitors]
        colors = ['#E74C3C' if i == 0 else BLUE for i in range(len(names))]
        if engine == 'seaborn':
            sns.barplot(x=vals, y=names, orient='h', palette=colors, ax=ax)
        else:
            ax.barh(names, vals, color=colors, height=0.6)
        ax.set_title(title, fontweight='bold', color=NAVY, fontsize=13)
        for i, v in enumerate(vals):
            label = f'${int(v):,}' if 'value' in key else f'{int(v):,}'
            ax.text(v + (max(vals) * 0.03 if max(vals) else 1), i, label, va='center', fontsize=9, color=DARK_GREY)
        ax.invert_yaxis()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='x', alpha=0.3)

    fig.suptitle(f'{PROSPECT_NAME} vs. Key Competitors', fontsize=16, fontweight='bold', color=NAVY, y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'competitive_landscape.png'), dpi=CHART_EXPORT_DPI, bbox_inches='tight')
    plt.close()
    print('Chart saved: competitive_landscape.png')


def create_opportunity_matrix(keywords_by_cluster, renderer=None):
    engine = _resolve_renderer('opportunity_matrix', renderer)

    if engine == 'plotly':
        rows = []
        for cluster, kws in keywords_by_cluster.items():
            for k in kws:
                rows.append({
                    'cluster': cluster,
                    'competition': float(k.get('competition', 0) or 0),
                    'volume': float(k.get('volume', 0) or 0),
                    'cpc': float(k.get('cpc', 0) or 0),
                })
        if rows:
            fig = px.scatter(
                rows,
                x='competition',
                y='volume',
                size='cpc',
                color='cluster',
                title=f'{PROSPECT_NAME} - Keyword Opportunity Matrix',
                color_discrete_sequence=PALETTE,
            )
            fig.update_layout(template='simple_white')
            if _save_plotly(fig, 'opportunity_matrix.png', width=1400, height=900, scale=2):
                return

    fig, ax = plt.subplots(figsize=(14, 9))
    for i, (cluster, kws) in enumerate(keywords_by_cluster.items()):
        vols = [k.get('volume', 0) for k in kws]
        comps = [k.get('competition', 0) for k in kws]
        cpcs = [k.get('cpc', 0) for k in kws]
        sizes = [float(c) * 50 + 20 for c in cpcs]
        ax.scatter(comps, vols, s=sizes, alpha=0.6, label=cluster, color=PALETTE[i % len(PALETTE)], edgecolors='white', linewidth=0.5)
    ax.set_xlabel('Competition Level (0-1)')
    ax.set_ylabel('Monthly Search Volume')
    ax.set_title(f'{PROSPECT_NAME} - Keyword Opportunity Matrix', color=NAVY, pad=16)
    ax.legend(loc='upper right', fontsize=8, framealpha=0.9)
    ax.grid(alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'opportunity_matrix.png'), dpi=CHART_EXPORT_DPI, bbox_inches='tight')
    plt.close()
    print('Chart saved: opportunity_matrix.png')


def create_traffic_value_chart(cluster_data, renderer=None):
    sorted_data = sorted(cluster_data, key=lambda x: x['traffic_value'])
    names = [c['name'] for c in sorted_data]
    values = [c['traffic_value'] for c in sorted_data]
    colors = [GREEN if v > 1000 else '#F39C12' if v > 500 else '#E74C3C' for v in values]
    engine = _resolve_renderer('traffic_value_opportunity', renderer)
    if engine == 'plotly':
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=values,
            y=names,
            orientation='h',
            marker=dict(color=colors, line=dict(color='#FFFFFF', width=1)),
            text=[f'${int(v):,}' for v in values],
            textposition='outside',
        ))
        fig.update_layout(
            title=f'{PROSPECT_NAME} - Traffic Value Opportunity by Category',
            xaxis_title='Estimated Monthly Traffic Value ($)',
            yaxis_title='',
        )
        fig.update_xaxes(tickformat=',')
        if _save_plotly(fig, 'traffic_value_opportunity.png', width=1400, height=800, scale=2):
            return

    fig, ax = plt.subplots(figsize=(12, 7))
    if engine == 'seaborn':
        sns.barplot(x=values, y=names, orient='h', palette=colors, ax=ax)
    else:
        ax.barh(names, values, color=colors, height=0.6, edgecolor='white', linewidth=0.5)

    for i, val in enumerate(values):
        ax.text(val + (max(values) * 0.02 if max(values) else 1), i, f'${int(val):,}', va='center', fontsize=10, color=DARK_GREY, fontweight='bold')
    ax.set_xlabel('Estimated Monthly Traffic Value ($)')
    ax.set_title(f'{PROSPECT_NAME} - Traffic Value Opportunity by Category', color=NAVY, pad=16)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'traffic_value_opportunity.png'), dpi=CHART_EXPORT_DPI, bbox_inches='tight')
    plt.close()
    print('Chart saved: traffic_value_opportunity.png')


def create_integrated_scorecard(scores, renderer=None):
    def overall_readiness(score):
        if score >= 75:
            return 'High'
        if score >= 45:
            return 'Moderate'
        return 'Low'

    def insight_text(label, score):
        if label == 'SEO Readiness':
            return 'Needs stronger technical SEO foundation' if score < 55 else 'Strong technical SEO coverage'
        if label == 'AEO Readiness':
            return 'Moderate answer-engine visibility' if score < 75 else 'Strong answer-engine visibility'
        if label == 'GEO Readiness':
            return 'No generative-engine presence yet' if score < 15 else 'Early generative-engine visibility'
        if label == 'Content Readiness':
            return 'Expand guides, FAQs, and structured content' if score < 70 else 'Content framework is improving'
        return 'Build stronger entity and trust signals' if score < 75 else 'Authority and trust signals are strong'

    rows = [
        ('SEO Readiness', int(scores.get('seo_score', 0) or 0), 85, SEO_COLOR),
        ('AEO Readiness', int(scores.get('aeo_score', 0) or 0), 80, AEO_COLOR),
        ('GEO Readiness', int(scores.get('geo_score', 0) or 0), 70, GEO_COLOR),
        ('Content Readiness', int(scores.get('cro_score', 0) or 0), 78, SEO_COLOR),
        ('Authority Readiness', int(scores.get('overall_score', 0) or 0), 75, BLUE),
    ]
    overall = int(scores.get('overall_score', 0) or 0)

    fig = plt.figure(figsize=(14, 8), facecolor=BG_WHITE)
    canvas = fig.add_axes([0, 0, 1, 1])
    canvas.set_xlim(0, 1)
    canvas.set_ylim(0, 1)
    canvas.axis('off')

    canvas.text(0.03, 0.93, f'{PROSPECT_NAME} - Integrated Search Audit Scorecard',
                fontsize=24, fontweight='bold', color='black', ha='left', va='center')
    canvas.text(0.03, 0.865, 'Current vs target readiness across search visibility, content, and authority layers',
                fontsize=14, color='#666666', ha='left', va='center')

    badge = FancyBboxPatch((0.75, 0.885), 0.20, 0.07,
                           boxstyle='round,pad=0.01,rounding_size=0.008',
                           linewidth=1.0, edgecolor='#D6DEE8', facecolor='#F6F8FB')
    canvas.add_patch(badge)
    canvas.text(0.765, 0.92, 'Overall Readiness:', fontsize=13, fontweight='bold',
                color=NAVY, ha='left', va='center')
    canvas.text(0.94, 0.92, overall_readiness(overall), fontsize=14, fontweight='bold',
                color=NAVY, ha='right', va='center')

    y = 0.68
    for label, value, target, color in rows:
        card = FancyBboxPatch((0.03, y - 0.055), 0.94, 0.085,
                              boxstyle='round,pad=0.01,rounding_size=0.006',
                              linewidth=1.0, edgecolor='#E6EBF1', facecolor='#FBFCFE')
        canvas.add_patch(card)
        canvas.text(0.045, y - 0.012, label, fontsize=16, fontweight='bold', color=NAVY,
                    ha='left', va='center')

        bar_x, bar_y = 0.28, y - 0.035
        bar_w, bar_h = 0.54, 0.038
        canvas.add_patch(Rectangle((bar_x, bar_y), bar_w, bar_h, facecolor='#E8EEF5', edgecolor='none'))
        canvas.add_patch(Rectangle((bar_x, bar_y), bar_w * (value / 100.0), bar_h, facecolor=color, edgecolor='none'))

        value_x = min(bar_x + bar_w * (value / 100.0) + 0.012, 0.62)
        canvas.text(value_x, y - 0.012, f'{value}/100', fontsize=15, fontweight='bold',
                    color=NAVY, ha='left', va='center')

        target_x = bar_x + bar_w * (target / 100.0)
        canvas.plot([target_x, target_x], [bar_y - 0.012, bar_y + bar_h + 0.012],
                    color=AEO_COLOR, linewidth=2.4)
        canvas.text(min(target_x + 0.005, 0.80), bar_y + bar_h + 0.02, f'Target {target}',
                    fontsize=11, color=AEO_COLOR, ha='center', va='center')

        canvas.text(0.93, y - 0.012, insight_text(label, value), fontsize=11.5,
                    color=MID_GREY, ha='right', va='center')
        y -= 0.135

    canvas.text(0.28, 0.07, 'Current', fontsize=13, color=SEO_COLOR, fontweight='bold', ha='left')
    canvas.text(0.37, 0.07, '|', fontsize=16, color='#AEB9C8', ha='center')
    canvas.text(0.385, 0.07, 'Target marker', fontsize=13, color=AEO_COLOR, fontweight='bold', ha='left')
    canvas.text(0.90, 0.07, 'Scores shown out of 100', fontsize=12, color='#7A869A', ha='right')

    plt.savefig(os.path.join(OUTPUT_DIR, 'integrated_scorecard.png'), dpi=CHART_EXPORT_DPI, bbox_inches='tight', facecolor=BG_WHITE)
    plt.close()
    print('Chart saved: integrated_scorecard.png')


def create_layer_distribution_chart(layer_data, renderer=None):
    layers = ['SEO', 'AEO', 'GEO']
    counts = [layer_data[l]['count'] for l in layers]
    volumes = [layer_data[l]['total_volume'] for l in layers]
    colors = [SEO_COLOR, AEO_COLOR, GEO_COLOR]
    engine = _resolve_renderer('layer_distribution', renderer)

    if engine == 'plotly':
        fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'domain'}, {'type': 'domain'}]],
                            subplot_titles=('Keywords by Search Layer', 'Search Volume by Layer'))
        fig.add_trace(go.Pie(labels=layers, values=counts, hole=0.55, marker_colors=colors), row=1, col=1)
        fig.add_trace(go.Pie(labels=layers, values=volumes, hole=0.55, marker_colors=colors), row=1, col=2)
        fig.update_layout(title=f'{PROSPECT_NAME} - Keyword Opportunity by Search Layer', template='simple_white')
        if _save_plotly(fig, 'layer_distribution.png', width=1600, height=700, scale=2):
            return

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    axes[0].pie(counts, labels=layers, colors=colors, autopct='%1.0f%%', startangle=90)
    axes[0].set_title('Keywords by Search Layer', fontweight='bold', color=NAVY)
    axes[1].pie(volumes, labels=layers, colors=colors, autopct='%1.0f%%', startangle=90)
    axes[1].set_title('Search Volume by Layer', fontweight='bold', color=NAVY)
    fig.suptitle(f'{PROSPECT_NAME} - Keyword Opportunity by Search Layer', fontsize=14, fontweight='bold', color=NAVY, y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'layer_distribution.png'), dpi=CHART_EXPORT_DPI, bbox_inches='tight')
    plt.close()
    print('Chart saved: layer_distribution.png')


def create_three_layer_overview(scores, keyword_counts, renderer=None):
    def readiness_label(score):
        if score >= 70:
            return 'Strong Visibility'
        if score >= 45:
            return 'Moderate Visibility'
        if score <= 10:
            return 'No AI Visibility Yet'
        return 'Needs Improvement'

    def overall_label(score_values):
        overall = int(round(sum(score_values) / max(len(score_values), 1)))
        if overall >= 75:
            return 'High'
        if overall >= 45:
            return 'Moderate'
        return 'Low'

    def draw_gauge(ax, score, color, text_color):
        ax.set_xlim(-1.05, 1.05)
        ax.set_ylim(-0.05, 1.05)
        ax.set_aspect('equal')
        ax.axis('off')

        outer_r = 0.82
        inner_r = 0.58
        segments = 6

        ax.add_patch(Wedge((0, 0), outer_r, 0, 180, width=outer_r - inner_r, facecolor='#EEF1F5', edgecolor='none'))

        for idx in range(1, segments):
            angle = idx * 180 / segments
            radians = np.deg2rad(angle)
            x1, y1 = (inner_r - 0.01) * np.cos(radians), (inner_r - 0.01) * np.sin(radians)
            x2, y2 = (outer_r + 0.01) * np.cos(radians), (outer_r + 0.01) * np.sin(radians)
            ax.plot([x1, x2], [y1, y2], color='#C7D0DC', linewidth=1.1, zorder=3)

        if score > 0:
            end_angle = 180 - (score / 100.0) * 180
            ax.add_patch(Wedge((0, 0), outer_r, end_angle, 180, width=outer_r - inner_r, facecolor=color, edgecolor='none', alpha=0.95))
            ax.add_patch(Circle((0, 0), inner_r - 0.02, color='white', zorder=2))
        else:
            ax.add_patch(Circle((0, 0), inner_r - 0.02, color='white', zorder=2))

        if score <= 10:
            angle = np.deg2rad(180 - (max(score, 3) / 100.0) * 180)
            needle_len = outer_r * 0.68
            ax.plot([0, needle_len * np.cos(angle)], [0, needle_len * np.sin(angle)], color='#6B7280', linewidth=2.5, zorder=4)
            ax.add_patch(Circle((0, 0), 0.05, color='#6B7280', zorder=5))

        ax.text(0, 0.15, f'{score}', ha='center', va='center', fontsize=28, fontweight='bold', color=text_color)
        ax.text(0, -0.08, '/100', ha='center', va='center', fontsize=14, color=MID_GREY)

    scores_only = [scores['seo_score'], scores['aeo_score'], scores['geo_score']]
    overall = overall_label(scores_only)

    fig = plt.figure(figsize=(14, 8), facecolor=BG_WHITE)
    canvas = fig.add_axes([0, 0, 1, 1])
    canvas.set_xlim(0, 1)
    canvas.set_ylim(0, 1)
    canvas.axis('off')

    canvas.text(0.035, 0.92, f'{PROSPECT_NAME} - Search Visibility Snapshot', fontsize=24, fontweight='bold', color=NAVY, ha='left', va='center')
    canvas.text(0.035, 0.86, 'Traditional, answer-engine, and generative-engine performance at a glance', fontsize=14, color=MID_GREY, ha='left', va='center')

    badge = FancyBboxPatch((0.73, 0.885), 0.24, 0.06, boxstyle='round,pad=0.008,rounding_size=0.012',
                           linewidth=1.2, edgecolor='#D6DEE8', facecolor='#F7F9FC')
    canvas.add_patch(badge)
    canvas.text(0.745, 0.915, 'Overall AI Search Readiness:', fontsize=13, color=MID_GREY, ha='left', va='center')
    canvas.text(0.94, 0.915, overall, fontsize=13, fontweight='bold', color=AEO_COLOR if overall == 'Low' else NAVY, ha='right', va='center')
    canvas.plot([0.02, 0.98], [0.79, 0.79], color='#DCE3EB', linewidth=1.2)

    layers_info = [
        ('SEO', 'Traditional Search', scores['seo_score'], keyword_counts.get('SEO', 0), SEO_COLOR, 'Google, Bing'),
        ('AEO', 'Answer Engines', scores['aeo_score'], keyword_counts.get('AEO', 0), AEO_COLOR, 'Snippets, PAA'),
        ('GEO', 'Generative Engines', scores['geo_score'], keyword_counts.get('GEO', 0), GEO_COLOR, 'ChatGPT, Perplexity, AI Overviews'),
    ]

    card_positions = [(0.03, 0.24, 0.30, 0.48), (0.355, 0.24, 0.30, 0.48), (0.68, 0.24, 0.30, 0.48)]
    bottom_messages = [
        'Strong traditional search visibility',
        'Moderate answer-engine readiness',
        'No generative-engine presence detected',
    ]

    for idx, ((layer, subtitle, score, kw_count, color, footnote), pos) in enumerate(zip(layers_info, card_positions)):
        x, y, w, h = pos
        card = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.012,rounding_size=0.018',
                              linewidth=1.2, edgecolor='#CDD7E2', facecolor='#FBFCFE')
        canvas.add_patch(card)

        title_color = color if layer != 'SEO' else SEO_COLOR
        canvas.text(x + w / 2, y + h - 0.04, layer, fontsize=22, fontweight='bold', color=title_color, ha='center', va='center')

        gauge_ax = fig.add_axes([x + 0.03, y + 0.19, w - 0.06, 0.22], frameon=False)
        draw_gauge(gauge_ax, score, color, title_color)

        canvas.plot([x + 0.02, x + w - 0.02], [y + 0.20, y + 0.20], color='#E0E6EE', linewidth=1.0)
        canvas.text(x + w / 2, y + 0.165, subtitle, fontsize=13, fontweight='bold', color=NAVY, ha='center', va='center')
        canvas.plot([x + 0.02, x + w - 0.02], [y + 0.135, y + 0.135], color='#E0E6EE', linewidth=1.0)
        canvas.text(x + w / 2, y + 0.105, readiness_label(score), fontsize=12, fontweight='bold', color=title_color, ha='center', va='center')
        canvas.plot([x + 0.02, x + w - 0.02], [y + 0.075, y + 0.075], color='#E0E6EE', linewidth=1.0)
        canvas.text(x + w / 2, y + 0.045, f'{kw_count:,} keyword opportunities', fontsize=11, color=NAVY, ha='center', va='center')
        canvas.text(x + w / 2, y + 0.008, footnote, fontsize=10.5, color=LIGHT_GREY, ha='center', va='center', style='italic')

        strip_x = [0.04, 0.36, 0.68][idx]
        strip_w = [0.28, 0.28, 0.29][idx]
        canvas.add_patch(Rectangle((strip_x, 0.16), strip_w, 0.05, facecolor='#F3F6F9', edgecolor='none'))
        canvas.text(strip_x + strip_w / 2, 0.185, bottom_messages[idx], fontsize=10.8,
                    color=NAVY, ha='center', va='center', fontweight='bold' if idx == 2 else None)

    canvas.plot([0.333, 0.333], [0.165, 0.205], color='#D7DEE8', linewidth=1.2)
    canvas.plot([0.665, 0.665], [0.165, 0.205], color='#D7DEE8', linewidth=1.2)

    plt.savefig(os.path.join(OUTPUT_DIR, 'three_layer_overview.png'), dpi=CHART_EXPORT_DPI, bbox_inches='tight', facecolor=BG_WHITE)
    plt.close()
    print('Chart saved: three_layer_overview.png')


def create_before_after_chart(current_scores, renderer=None):
    labels = ['SEO', 'AEO', 'GEO']
    current = [current_scores['seo_score'], current_scores['aeo_score'], current_scores['geo_score']]
    projected = [min(100, c + 40) for c in current]
    engine = _resolve_renderer('before_after_scores', renderer)
    if engine == 'plotly':
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Current State (Before)', x=labels, y=current, marker_color=MID_GREY))
        fig.add_trace(go.Bar(name='Strategic Target (After)', x=labels, y=projected, marker_color=GREEN))
        fig.update_layout(
            title=f'Projected Visibility Impact: {PROSPECT_NAME}',
            yaxis_title='Optimization Score (0-100)',
            barmode='group',
        )
        fig.update_yaxes(range=[0, 110])
        if _save_plotly(fig, 'before_after_scores.png', width=1200, height=700, scale=2):
            return

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(labels))
    width = 0.35
    if engine == 'seaborn':
        ax.bar(x - width/2, current, width, label='Current State (Before)', color=MID_GREY, alpha=0.5)
        ax.bar(x + width/2, projected, width, label='Strategic Target (After)', color=GREEN)
    else:
        ax.bar(x - width/2, current, width, label='Current State (Before)', color=MID_GREY, alpha=0.5)
        ax.bar(x + width/2, projected, width, label='Strategic Target (After)', color=GREEN)
    ax.set_ylabel('Optimization Score (0-100)')
    ax.set_title(f'Projected Visibility Impact: {PROSPECT_NAME}', fontweight='bold', color=NAVY)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 110)
    ax.legend()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'before_after_scores.png'), dpi=CHART_EXPORT_DPI, bbox_inches='tight')
    plt.close()
    print('Chart saved: before_after_scores.png')


def _chart_validation_issues(mi, audit):
    issues = []
    prospect = mi.get('prospect', {}) or {}
    scorecard = audit.get('scorecard', {}) or {}

    if not prospect:
        issues.append('market_intelligence.json is missing prospect data.')
    if int(prospect.get('organic_keywords', 0) or 0) <= 0:
        issues.append('Prospect organic keyword count is missing or zero.')
    if int(prospect.get('organic_traffic', 0) or 0) <= 0:
        issues.append('Prospect organic traffic is missing or zero.')
    if int(prospect.get('organic_traffic_value', 0) or 0) <= 0:
        issues.append('Prospect traffic value is missing or zero.')
    if len(mi.get('competitors', []) or []) < 2:
        issues.append('Competitor market data is incomplete.')
    if not scorecard or scorecard.get('overall_score') in (None, '', 0, '0'):
        issues.append('Audit scorecard data is incomplete.')
    layer_scores = [int(scorecard.get(key, 0) or 0) for key in ('seo_score', 'aeo_score', 'geo_score')]
    if layer_scores.count(0) == 3:
        issues.append('Technical audit produced all-zero SEO/AEO/GEO scores.')
    error_findings = sum(
        1
        for bucket in ('seo_findings', 'aeo_findings', 'geo_findings')
        for finding in (audit.get(bucket, []) or [])
        if str((finding or {}).get('current_status', '')).upper() == 'ERROR'
    )
    if error_findings >= 2:
        issues.append('Technical audit contains transport/access errors.')
    return issues


if __name__ == '__main__':
    mi = {}
    audit = {}
    try:
        with open(os.path.join(DATA_DIR, 'market_intelligence.json'), 'r', encoding='utf-8') as f:
            mi = json.load(f)
    except Exception as e:
        print(f'Error loading MI data: {e}')

    try:
        with open(os.path.join(DATA_DIR, 'audit_findings.json'), 'r', encoding='utf-8') as f:
            audit = json.load(f)
    except Exception as e:
        print(f'Error loading audit data: {e}')

    validation_issues = _chart_validation_issues(mi, audit)
    if validation_issues:
        raise ValueError("Cannot build charts from incomplete audit data: " + " | ".join(validation_issues))

    real_competitors = [
        {
            'name': 'PROSPECT',
            'keywords': mi.get('prospect', {}).get('organic_keywords', 0),
            'traffic': mi.get('prospect', {}).get('organic_traffic', 0),
            'traffic_value': mi.get('prospect', {}).get('organic_traffic_value', 0),
        }
    ]
    for comp in mi.get('competitors', [])[:3]:
        real_competitors.append({
            'name': comp.get('domain', '').replace('www.', ''),
            'keywords': comp.get('organic_keywords', 0),
            'traffic': comp.get('organic_traffic', 0),
            'traffic_value': comp.get('organic_traffic_value', 0),
        })

    real_scores = audit.get('scorecard', {
        'seo_score': 0, 'aeo_score': 0, 'geo_score': 0, 'cro_score': 0, 'overall_score': 0
    })

    aeo_kws = mi.get('aeo_indicators', {}).get('question_keywords_found', 0)
    geo_kws = mi.get('geo_indicators', {}).get('informational_keywords_found', 0)
    seo_kws = mi.get('prospect', {}).get('organic_keywords', 0)

    aeo_vol = sum(int(k.get('Search Volume', 0) or 0) for k in mi.get('aeo_indicators', {}).get('top_question_keywords', []))
    geo_vol = sum(int(k.get('Search Volume', 0) or 0) for k in mi.get('geo_indicators', {}).get('top_informational_keywords', []))
    seo_vol = sum(int(k.get('Search Volume', 0) or 0) for k in mi.get('prospect', {}).get('top_keywords', []))

    real_layer_data = {
        'SEO': {'count': seo_kws, 'total_volume': seo_vol},
        'AEO': {'count': aeo_kws, 'total_volume': aeo_vol},
        'GEO': {'count': geo_kws, 'total_volume': geo_vol},
    }
    real_kw_counts = {'SEO': seo_kws, 'AEO': aeo_kws, 'GEO': geo_kws}

    real_clusters = [
        {'name': 'Transactional SEO', 'volume': seo_vol, 'traffic_value': mi.get('prospect', {}).get('organic_traffic_value', 0)},
        {'name': 'AEO Question Intent', 'volume': aeo_vol, 'traffic_value': int(aeo_vol * 0.1)},
        {'name': 'GEO Informational', 'volume': geo_vol, 'traffic_value': int(geo_vol * 0.05)},
    ]

    create_search_demand_chart(real_clusters, renderer='seaborn')
    create_competitive_landscape_chart(real_competitors, renderer='plotly')

    # Build cluster-wise keyword sample for opportunity matrix
    kw_cluster_data = {
        'Transactional SEO': [
            {'volume': max(10, int(seo_vol * 0.15)), 'competition': 0.62, 'cpc': 7.0},
            {'volume': max(10, int(seo_vol * 0.12)), 'competition': 0.55, 'cpc': 5.2},
        ],
        'AEO Question Intent': [
            {'volume': max(10, int(aeo_vol * 0.4)), 'competition': 0.28, 'cpc': 3.1},
            {'volume': max(10, int(aeo_vol * 0.3)), 'competition': 0.35, 'cpc': 2.7},
        ],
        'GEO Informational': [
            {'volume': max(10, int(geo_vol * 0.4)), 'competition': 0.22, 'cpc': 2.0},
            {'volume': max(10, int(geo_vol * 0.3)), 'competition': 0.3, 'cpc': 1.8},
        ],
    }

    create_opportunity_matrix(kw_cluster_data, renderer='plotly')
    create_traffic_value_chart(real_clusters, renderer='plotly')
    create_integrated_scorecard(real_scores, renderer='plotly')
    create_layer_distribution_chart(real_layer_data, renderer='plotly')
    create_three_layer_overview(real_scores, real_kw_counts, renderer='matplotlib')
    create_before_after_chart(real_scores, renderer='plotly')

    print(f"\nAll charts saved to: {OUTPUT_DIR}")
    if not HAS_SEABORN:
        print('[Info] Seaborn unavailable, used Matplotlib fallback where needed.')
    if not HAS_PLOTLY:
        print('[Info] Plotly unavailable, used Matplotlib fallback where needed.')
    elif not HAS_KALEIDO:
        print('[Info] Kaleido unavailable, Plotly image export fell back to Matplotlib.')
