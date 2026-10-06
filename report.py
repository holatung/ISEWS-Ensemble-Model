"""HTML report renderer: self-contained, inline SVG charts, light and dark themes."""
import html
import datetime as dt
from .data import MODALITIES, MODALITY_KEYS, EVENTS, AGGREGATES, SOURCES, SURVEILLANCE, SURV_INDICATORS, DISCREPANCIES
from .pipeline import TIERS

e = lambda s: html.escape(str(s), quote=True)
TIER_CLASS = {"Low": "good", "Watch": "warn", "Warning": "serious", "Critical": "crit"}
TIER_ICON = {"Low": "&#9675;", "Watch": "&#9651;", "Warning": "&#9670;", "Critical": "&#9632;"}
STATUS_TXT = {"VERIFIED": "Verified", "EXTRACTED": "Machine-extracted", "REPORTED": "Reported, not re-verified",
              "BRIEF": "ChatVE brief", "CODED": "Analyst-coded"}
MOD_LABEL = {m[0]: m[1] for m in MODALITIES}
MOD_LABEL["surveillance_policy"] = "Surveillance and control policy"

CSS = r"""
/* Layout: an operations briefing. Summary watchlist first, then per-country replays, then models and evidence. */
:root{
  --bg:#f4f5f3; --surface:#fcfcfb; --raised:#ffffff; --ink:#0f1112; --ink2:#4d5052; --muted:#80837f;
  --grid:#e1e0d9; --axis:#c3c2b7; --line:rgba(15,17,18,.10); --accent:#1f5fae; --accent-wash:rgba(42,120,214,.08);
  --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a; --track:#e6e8ec;
  --good:#0ca30c; --warn:#fab219; --serious:#ec835a; --crit:#d03b3b; --good-ink:#006300;
  --sans:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,"SFMono-Regular",Menlo,Consolas,monospace;
  --cond:"IBM Plex Sans Condensed","IBM Plex Sans",system-ui,sans-serif;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#0f1011; --surface:#1a1a19; --raised:#202120; --ink:#f4f4f2; --ink2:#c3c2b7; --muted:#8e8d86;
  --grid:#2c2c2a; --axis:#46463f; --line:rgba(255,255,255,.10); --accent:#6da7ec; --accent-wash:rgba(57,135,229,.12);
  --s1:#3987e5; --s2:#d95926; --s3:#199e70; --track:#2b2d30; --good-ink:#0ca30c; color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#0f1011; --surface:#1a1a19; --raised:#202120; --ink:#f4f4f2; --ink2:#c3c2b7; --muted:#8e8d86;
  --grid:#2c2c2a; --axis:#46463f; --line:rgba(255,255,255,.10); --accent:#6da7ec; --accent-wash:rgba(57,135,229,.12);
  --s1:#3987e5; --s2:#d95926; --s3:#199e70; --track:#2b2d30; --good-ink:#0ca30c; color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.55;margin:0}
.wrap{max-width:1180px;margin:0 auto;padding-inline:clamp(16px,4vw,40px);padding-block:28px 64px;display:flex;flex-direction:column;gap:40px}
h1,h2,h3{font-family:var(--cond);text-wrap:balance;margin:0;letter-spacing:-.005em}
h1{font-size:clamp(1.9rem,4.2vw,2.8rem);font-weight:600;line-height:1.08}
h2{font-size:1.45rem;font-weight:600}
h3{font-size:1.06rem;font-weight:600}
p{margin:0;max-width:72ch}
a{color:var(--accent)}
.mono{font-family:var(--mono);font-size:.82rem}
.eyebrow{font-family:var(--mono);font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;color:var(--muted)}
.muted{color:var(--muted)} .ink2{color:var(--ink2)}
header.top{display:grid;gap:14px;border-bottom:1px solid var(--line);padding-bottom:24px}
.runline{display:flex;flex-wrap:wrap;gap:6px 18px;color:var(--ink2)}
.runline span b{color:var(--ink);font-weight:500}
.prov{display:flex;flex-wrap:wrap;gap:8px}
.badge{display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:.7rem;letter-spacing:.03em;padding:2px 8px;border-radius:4px;border:1px solid var(--line);color:var(--ink2);background:var(--surface);white-space:nowrap}
.badge i{width:7px;height:7px;border-radius:50%;display:inline-block}
.b-VERIFIED i{background:var(--good)} .b-EXTRACTED i{background:var(--warn)} .b-REPORTED i{background:var(--serious)}
.b-BRIEF i{background:var(--s1)} .b-CODED i{background:var(--muted)} .b-SIM i{background:transparent;border:1.5px dashed var(--ink2)}
section{display:flex;flex-direction:column;gap:16px}
.sechead{display:flex;flex-direction:column;gap:6px}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:8px}
.tblwrap{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:.88rem}
th{font-family:var(--mono);font-size:.68rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:500;text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:0}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.pill{display:inline-flex;align-items:center;gap:5px;font-size:.78rem;font-weight:600;padding:1px 9px 1px 7px;border-radius:99px;white-space:nowrap;border:1px solid transparent}
.pill.good{color:var(--good-ink);border-color:var(--good)} .pill.warn{color:var(--ink);background:color-mix(in srgb,var(--warn) 22%,transparent);border-color:var(--warn)}
.pill.serious{color:var(--ink);background:color-mix(in srgb,var(--serious) 22%,transparent);border-color:var(--serious)}
.pill.crit{color:#fff;background:var(--crit);border-color:var(--crit)}
.meter{display:flex;align-items:center;gap:8px;min-width:140px}
.meter .trk{flex:1;height:8px;border-radius:4px;background:var(--track);overflow:hidden}
.meter .fill{height:100%;border-radius:0 4px 4px 0}
.meter b{font-variant-numeric:tabular-nums;font-weight:600;min-width:2.6em;text-align:right}
.fill.good{background:var(--good)} .fill.warn{background:var(--warn)} .fill.serious{background:var(--serious)} .fill.crit{background:var(--crit)}
.chips{display:flex;flex-wrap:wrap;gap:4px}
.chip{font-size:.74rem;padding:1px 7px;border-radius:4px;background:var(--accent-wash);color:var(--ink);white-space:nowrap}
.chip.off{background:transparent;border:1px dashed var(--line);color:var(--muted)}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,520px),1fr));gap:16px}
.card{padding:18px;display:flex;flex-direction:column;gap:12px;min-width:0}
.card .hd{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}
.card .hd>div{min-width:0}
.kv{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}
.kv div{display:flex;flex-direction:column;gap:2px;min-width:0}
.kv .k{font-family:var(--mono);font-size:.64rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.kv .v{font-weight:600;font-variant-numeric:tabular-nums;font-size:1rem}
.basis{font-size:.82rem;color:var(--ink2);border-left:2px solid var(--axis);padding-left:10px}
svg{display:block;width:100%;height:auto;overflow:visible}
svg text{font-family:var(--sans);fill:var(--muted);font-size:10.5px}
svg .lbl{fill:var(--ink2)} svg .ink{fill:var(--ink)}
.legend{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:.78rem;color:var(--ink2)}
.legend span{display:inline-flex;align-items:center;gap:6px}
.legend i{display:inline-block;width:14px;height:2px;border-radius:1px}
.legend i.dot{width:8px;height:8px;border-radius:50%}
.legend i.band{width:12px;height:8px;border-radius:2px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,170px),1fr));gap:12px}
.tile{padding:14px 16px;display:flex;flex-direction:column;gap:4px}
.tile .v{font-size:1.9rem;font-weight:600;line-height:1.1;font-family:var(--cond)}
.tile .l{font-size:.82rem;color:var(--ink2)}
.tile .badge{align-self:flex-start;margin-top:4px}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,440px),1fr));gap:16px}
.two>*{min-width:0}
.mcard{padding:18px;display:flex;flex-direction:column;gap:10px}
.arch{font-family:var(--mono);font-size:.76rem;background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:10px 12px;overflow-x:auto;white-space:pre;color:var(--ink2)}
.tag{font-family:var(--mono);font-size:.66rem;letter-spacing:.06em;text-transform:uppercase;padding:2px 6px;border-radius:3px;border:1px solid var(--line);color:var(--ink2)}
.tag.dl{border-color:var(--s2)} .tag.ml{border-color:var(--s1)}
ul.clean{margin:0;padding-left:18px;display:flex;flex-direction:column;gap:6px;max-width:80ch}
.callout{padding:14px 16px;border-radius:8px;border:1px solid var(--line);background:var(--accent-wash);display:flex;flex-direction:column;gap:6px}
.src{font-size:.82rem;display:flex;flex-direction:column;gap:4px}
.src li{word-break:break-word}
#tip{position:fixed;pointer-events:none;z-index:9;background:var(--raised);color:var(--ink);border:1px solid var(--line);border-radius:6px;padding:6px 9px;font-size:.78rem;box-shadow:0 4px 18px rgba(0,0,0,.14);max-width:260px;opacity:0;transition:opacity .08s}
[data-tip]{cursor:default}
.hit{fill:transparent}
@media (max-width:560px){.kv{grid-template-columns:repeat(2,minmax(0,1fr))} .meter{min-width:110px}}
@media (prefers-reduced-motion:reduce){#tip{transition:none}}
footer{border-top:1px solid var(--line);padding-top:18px;font-size:.8rem;color:var(--muted)}
"""

JS = r"""
(function(){
  var tip=document.getElementById('tip');
  document.addEventListener('pointerover',function(ev){var t=ev.target.closest('[data-tip]');if(!t)return;tip.textContent=t.getAttribute('data-tip');tip.style.opacity=1;});
  document.addEventListener('pointermove',function(ev){if(tip.style.opacity!=='1')return;var x=ev.clientX+14,y=ev.clientY+14;var r=tip.getBoundingClientRect();if(x+r.width>innerWidth-8)x=ev.clientX-r.width-14;if(y+r.height>innerHeight-8)y=ev.clientY-r.height-14;tip.style.left=x+'px';tip.style.top=y+'px';});
  document.addEventListener('pointerout',function(ev){if(ev.target.closest('[data-tip]'))tip.style.opacity=0;});
})();
"""


# ------------------------------------------------------------------ chart helpers
def timeline_svg(sc):
    W, H, L, R_, T, B = 400, 180, 28, 8, 10, 24
    hs, sc_, E = sc["hours"], sc["score"], sc["E"]
    x0, x1 = 23, 167
    X = lambda h: L + (h - x0) / (x1 - x0) * (W - L - R_)
    Y = lambda v: T + (1 - v / 100) * (H - T - B)
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="ISEWS score over 7 days for {e(sc["country"])}">']
    # tier bands (very light) and gridlines
    for th in (25, 50, 75):
        out.append(f'<line x1="{L}" x2="{W-R_}" y1="{Y(th):.1f}" y2="{Y(th):.1f}" stroke="var(--grid)" stroke-width="1"/>')
        out.append(f'<text x="{L-6}" y="{Y(th)+3.5:.1f}" text-anchor="end">{th}</text>')
    out.append(f'<line x1="{L}" x2="{W-R_}" y1="{Y(0):.1f}" y2="{Y(0):.1f}" stroke="var(--axis)" stroke-width="1"/>')
    out.append(f'<text x="{L-6}" y="{Y(0)+3.5:.1f}" text-anchor="end">0</text><text x="{L-6}" y="{Y(100)+3.5:.1f}" text-anchor="end">100</text>')
    for d in range(0, 8):
        h = d * 24
        if x0 <= h <= 167:
            out.append(f'<text x="{X(h):.1f}" y="{H-8}" text-anchor="middle">D{d+1}</text>')
    if sc["onset"] is not None:
        xo = X(sc["onset"])
        out.append(f'<line x1="{xo:.1f}" x2="{xo:.1f}" y1="{T}" y2="{Y(0):.1f}" stroke="var(--ink2)" stroke-width="1"/>')
        anchor = "end" if sc["onset"] > 120 else "start"
        dx = -4 if anchor == "end" else 4
        out.append(f'<text x="{xo+dx:.1f}" y="{Y(0)-6:.1f}" text-anchor="{anchor}" class="lbl">onset h{sc["onset"]}</text>')
    pe = " ".join(f"{X(h):.1f},{Y(v*100):.1f}" for h, v in zip(hs, E))
    out.append(f'<polyline points="{pe}" fill="none" stroke="var(--s2)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
    ps = " ".join(f"{X(h):.1f},{Y(v):.1f}" for h, v in zip(hs, sc_))
    area = f"{X(hs[0]):.1f},{Y(0):.1f} " + ps + f" {X(hs[-1]):.1f},{Y(0):.1f}"
    out.append(f'<polygon points="{area}" fill="var(--s1)" opacity=".10"/>')
    out.append(f'<polyline points="{ps}" fill="none" stroke="var(--s1)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
    # peak marker + label
    i = max(range(len(sc_)), key=lambda k: sc_[k])
    out.append(f'<circle cx="{X(hs[i]):.1f}" cy="{Y(sc_[i]):.1f}" r="4" fill="var(--s1)" stroke="var(--surface)" stroke-width="2"/>')
    # hover columns every 3 h
    step = (W - L - R_) / (x1 - x0)
    for k in range(0, len(hs), 3):
        h = hs[k]
        tipt = f"Hour {h} (day {h//24+1}, {h%24:02d}:00): score {sc_[k]:.0f}, escalation {E[k]*100:.0f}"
        out.append(f'<rect class="hit" x="{X(h)-1.5*step:.1f}" y="{T}" width="{3*step:.1f}" height="{H-T-B}" data-tip="{e(tipt)}"/>')
    out.append("</svg>")
    return "".join(out)


def hbars_svg(items, maxv=1.0, fmt="{:.2f}", W=390, row=22, label_w=185, color="var(--s1)", thresh=None, unit=""):
    H = row * len(items) + 8
    bw = W - label_w - 50
    out = [f'<svg viewBox="0 0 {W} {H}" role="img">']
    if thresh is not None:
        xt = label_w + thresh / maxv * bw
        out.append(f'<line x1="{xt:.1f}" x2="{xt:.1f}" y1="0" y2="{H-6}" stroke="var(--axis)" stroke-width="1"/>')
    for i, it in enumerate(items):
        lab, v = it[0], it[1]
        c = it[2] if len(it) > 2 and it[2] else color
        y = 4 + i * row
        w = max(v / maxv * bw, 0)
        out.append(f'<text x="{label_w-8}" y="{y+row/2+3.5:.1f}" text-anchor="end" class="lbl">{e(lab)}</text>')
        out.append(f'<rect x="{label_w}" y="{y+5:.1f}" width="{bw}" height="{row-10}" rx="3" fill="var(--track)" opacity=".55"/>')
        if w > 0.5:
            out.append(f'<path d="M{label_w},{y+5:.1f} h{max(w-4,0):.1f} a4,4 0 0 1 4,4 v{row-18:.1f} a4,4 0 0 1 -4,4 h-{max(w-4,0):.1f} z" fill="{c}"/>')
        out.append(f'<text x="{label_w+w+6:.1f}" y="{y+row/2+3.5:.1f}" class="ink">{fmt.format(v)}{unit}</text>')
        out.append(f'<rect class="hit" x="0" y="{y}" width="{W}" height="{row}" data-tip="{e(lab)}: {fmt.format(v)}{unit}"/>')
    out.append("</svg>")
    return "".join(out)


def dot_compare_svg(rows, W=460, row=24, label_w=205, lo=0.85, hi=1.0):
    H = row * len(rows) + 26
    bw = W - label_w - 20
    X = lambda v: label_w + (min(max(v, lo), hi) - lo) / (hi - lo) * bw
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="F1 by modality, Temporal CNN versus gradient boosting">']
    for t in [lo, lo + (hi - lo) / 3, lo + 2 * (hi - lo) / 3, hi]:
        out.append(f'<line x1="{X(t):.1f}" x2="{X(t):.1f}" y1="2" y2="{H-22}" stroke="var(--grid)"/>')
        out.append(f'<text x="{X(t):.1f}" y="{H-8}" text-anchor="middle">{t:.2f}</text>')
    for i, r in enumerate(rows):
        y = 6 + i * row + row / 2
        a, b = r["tcn_f1"], r["gbm_f1"]
        out.append(f'<text x="{label_w-8}" y="{y+3.5:.1f}" text-anchor="end" class="lbl">{e(r["label"])}</text>')
        out.append(f'<line x1="{X(min(a,b)):.1f}" x2="{X(max(a,b)):.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="var(--axis)" stroke-width="2"/>')
        out.append(f'<circle cx="{X(b):.1f}" cy="{y:.1f}" r="5" fill="var(--s1)" stroke="var(--surface)" stroke-width="2"/>')
        out.append(f'<circle cx="{X(a):.1f}" cy="{y:.1f}" r="5" fill="var(--s2)" stroke="var(--surface)" stroke-width="2"/>')
        out.append(f'<rect class="hit" x="0" y="{y-row/2:.1f}" width="{W}" height="{row}" data-tip="{e(r["label"])}: TCN F1 {a:.3f}, GBM F1 {b:.3f} (support {r["support"]})"/>')
    out.append("</svg>")
    return "".join(out)


def loss_svg(hist, W=460, H=170):
    L, R_, T, B = 40, 10, 10, 26
    ep = [h["epoch"] for h in hist]
    tr = [h["train_loss"] for h in hist]
    va = [h.get("val_loss", 0) for h in hist]
    ymax = max(tr + va) * 1.1
    X = lambda x: L + (x - 1) / (max(ep) - 1) * (W - L - R_)
    Y = lambda v: T + (1 - v / ymax) * (H - T - B)
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="TCN training curve">']
    for k in range(4):
        v = ymax * k / 3
        out.append(f'<line x1="{L}" x2="{W-R_}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{"var(--axis)" if k==0 else "var(--grid)"}"/>')
        out.append(f'<text x="{L-6}" y="{Y(v)+3.5:.1f}" text-anchor="end">{v:.2f}</text>')
    for x in [1, max(ep) // 2, max(ep)]:
        out.append(f'<text x="{X(x):.1f}" y="{H-8}" text-anchor="middle">epoch {x}</text>')
    for ser, col in ((tr, "var(--s1)"), (va, "var(--s2)")):
        pts = " ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in zip(ep, ser))
        out.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2" stroke-linejoin="round"/>')
        out.append(f'<circle cx="{X(ep[-1]):.1f}" cy="{Y(ser[-1]):.1f}" r="4" fill="{col}" stroke="var(--surface)" stroke-width="2"/>')
    for a, b, c in zip(ep, tr, va):
        out.append(f'<rect class="hit" x="{X(a)-6:.1f}" y="{T}" width="12" height="{H-T-B}" data-tip="Epoch {a}: train {b:.4f}, validation {c:.4f}"/>')
    out.append("</svg>")
    return "".join(out)


def meter(score, tier):
    c = TIER_CLASS[tier]
    return f'<div class="meter"><div class="trk"><div class="fill {c}" style="width:{score:.1f}%"></div></div><b>{score:.0f}</b></div>'


def pill(tier):
    return f'<span class="pill {TIER_CLASS[tier]}"><span aria-hidden="true">{TIER_ICON[tier]}</span>{tier}</span>'


def badge(status):
    return f'<span class="badge b-{status}"><i></i>{STATUS_TXT.get(status, status)}</span>'


def lead_txt(v, onset):
    if onset is None:
        return '<span class="muted">no onset</span>'
    if v is None:
        return '<span class="muted">not reached</span>'
    if v <= 0:
        return f'{abs(v)} h after onset' if v < 0 else 'at onset'
    return f'<b>{v} h</b> before'


# ------------------------------------------------------------------ render
def render(R, full=True):
    now = dt.datetime.now().strftime("%d %B %Y, %H:%M")
    S = R["scenarios"]
    st, mo, an = R["structural"], R["modality"], R["anomaly"]
    A = AGGREGATES["access_now_2025"]
    o = []
    o.append('<title>ISEWS Shutdown Monitor</title>')
    if full:
        o = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">',
             '<title>ISEWS Shutdown Monitor</title>']
    o.append('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
             '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">')
    o.append(f"<style>{CSS}</style>")
    if full:
        o.append("</head><body>")
    o.append('<div id="tip" role="tooltip"></div><div class="wrap">')

    # ---------------- header
    o.append(f'''<header class="top">
<div class="eyebrow">ChatVE · Research, Development and Innovation · Prototype v0.1</div>
<h1>ISEWS Shutdown Monitor</h1>
<p class="ink2">The Internet Shutdown Early Warning System (ISEWS) scores the risk of full or regional shutdowns,
social media and app bans, IP blocking, DNS/HTTP censorship, VPN targeting, bandwidth throttling, protocol downgrades,
targeted slowdowns and surveillance. It fuses three inputs: a structural risk model trained on
country-month history, a trigger feed, and deep-learning detectors that read 14 network-telemetry channels.</p>
<div class="runline mono"><span>Generated <b>{now}</b></span><span>Seed <b>{R["meta"]["seed"]}</b></span>
<span>Runtime <b>{R["meta"].get("runtime_s","-")} s</b></span><span>Scenarios <b>{len(S)}</b></span>
<span>Historical records <b>{len(EVENTS)}</b></span></div>
<div class="prov">{badge("VERIFIED")}{badge("EXTRACTED")}{badge("REPORTED")}{badge("BRIEF")}{badge("CODED")}
<span class="badge b-SIM"><i></i>Simulated</span></div>
<div class="callout"><b>Read this first</b><p class="ink2">Historical records and global figures come from Access Now,
the Internet Society, Project Ainita and the other sources listed below, and each one carries a provenance badge. The telemetry traces,
the country-month training panel and every model score are <b>simulated</b>. They show how the system works, not live conditions
or measured accuracy. Replace them with the Access Now STOP dataset and live Cloudflare Radar, IODA and OONI feeds before using any
result operationally.</p></div>
</header>''')

    # ---------------- watchlist
    rows = []
    for s in sorted(S, key=lambda s: -s["peak"]):
        chips = "".join(f'<span class="chip" data-tip="p = {d["p"]:.2f}, first flagged hour {d["first_h"]}{"" if d["active"] else " (no longer active)"}">{e(d["label"])}</span>'
                        for d in s["detected"]) or '<span class="chip off">none detected</span>'
        det_lat = (f'{s["first_detect"]-s["onset"]:+d} h' if (s["first_detect"] is not None and s["onset"] is not None) else '<span class="muted">-</span>')
        rows.append(f'''<tr><td><b>{e(s["country"])}</b><div class="muted" style="font-size:.8rem">{e(s["title"])}</div></td>
<td>{meter(s["peak"], s["tier"])}</td><td>{pill(s["tier"])}</td><td class="num">{s["S"]:.2f}</td>
<td><div class="chips">{chips}</div></td><td>{lead_txt(s["lead"][50], s["onset"])}</td><td class="num">{det_lat}</td></tr>''')
    o.append(f'''<section id="watchlist"><div class="sechead"><div class="eyebrow">01 · Watchlist</div><h2>Peak risk across nine replay scenarios</h2>
<p class="ink2">Each row replays seven days of simulated telemetry modelled on a documented case. The tiers are Low (0-24),
Watch (25-49), Warning (50-74) and Critical (75-100). <i>Warning lead</i> is how many hours before onset the score first reached Warning.
<i>Detection latency</i> is the time from onset until the first modality was confirmed, which requires three consecutive hours at p ≥ 0.5.
A negative latency means telemetry flagged precursors, such as VPN blocking, before the main event.</p></div>
<div class="tblwrap"><table><thead><tr><th>Country / scenario</th><th>Peak ISEWS score</th><th>Tier</th><th class="num">Structural S</th>
<th>Modalities detected</th><th>Warning lead</th><th class="num">Detection latency</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div></section>''')

    # ---------------- scenario cards
    cards = []
    for s in S:
        bars = [(MOD_LABEL[k], p, "var(--s1)" if p >= .5 else "var(--axis)") for k, p in zip(MODALITY_KEYS, s["P_max"])]
        mech = f'<div class="basis"><b>Shutdown mechanism (inferred):</b> {e(s["mechanism"])}</div>' if s["mechanism"] else ""
        cards.append(f'''<article class="panel card" id="sc-{s["key"]}"><div class="hd"><div><div class="eyebrow">{e(s["country"])}</div><h3>{e(s["title"])}</h3></div>{pill(s["tier"])}</div>
<div class="kv"><div><span class="k">Peak</span><span class="v">{s["peak"]:.0f}</span></div><div><span class="k">Now (h167)</span><span class="v">{s["final"]:.0f}</span></div>
<div><span class="k">Structural S</span><span class="v">{s["S"]:.2f}</span></div><div><span class="k">Warning lead</span><span class="v" style="font-size:.9rem">{lead_txt(s["lead"][50], s["onset"])}</span></div></div>
<div class="legend"><span><i style="background:var(--s1)"></i>ISEWS score</span><span><i style="background:var(--s2)"></i>Trigger escalation ×100</span><span><i style="background:var(--ink2);width:1px;height:10px"></i>Onset</span></div>
{timeline_svg(s)}
<div class="eyebrow" style="margin-top:4px">Modality probability (strongest sustained evidence, TCN)</div>
{hbars_svg(bars, maxv=1.0, fmt="{:.2f}", thresh=0.5)}
{mech}<div class="basis"><b>Modelled on:</b> {e(s["basis"])}</div></article>''')
    o.append(f'''<section id="scenarios"><div class="sechead"><div class="eyebrow">02 · Scenario replays</div><h2>How the score builds before and during each event</h2>
<p class="ink2">Hover a chart to read the hourly score. The two Ethiopia cards show the same event twice. In the AS-level view the blackout is clear.
In the national aggregate, where connectivity fell only to about 82%, the modality classifier finds nothing. Only the autoencoder registers an unusual dip,
and the alert rests on that anomaly plus escalation, with no way to say what happened or where. That is the case for subnational, per-ASN measurement.</p></div>
<div class="cards">{"".join(cards)}</div></section>''')

    # ---------------- taxonomy
    trs = []
    for k, lab, sev, d, sig in MODALITIES:
        exs = [ev["id"] for ev in EVENTS if k in ev["modalities"]]
        trs.append(f'<tr><td><b>{e(lab)}</b></td><td class="num">{sev:.2f}</td><td>{e(d)}</td><td class="ink2">{e(sig)}</td><td class="mono">{e(", ".join(exs)) or "-"}</td></tr>')
    o.append(f'''<section id="taxonomy"><div class="sechead"><div class="eyebrow">03 · Interference taxonomy</div><h2>Nine modalities, each with a telemetry signature</h2>
<p class="ink2">The severity weight scales a modality's probability into detection strength D. Signatures come from the documented cases.
The Iran stealth-blackout signature, for example, follows Project Ainita (IETF 123) and Aryapour (2025): BGP stays up, traffic falls about 97%, only ports 53, 80 and 443 pass, and DNS answers point to 10.10.34.34.</p></div>
<div class="tblwrap"><table><thead><tr><th>Modality</th><th class="num">Severity</th><th>Definition</th><th>Telemetry signature</th><th>Historical records</th></tr></thead><tbody>{"".join(trs)}</tbody></table></div>
<div class="tblwrap"><table><thead><tr><th>#</th><th>Telemetry channel</th><th>Production source</th></tr></thead><tbody>
{"".join(f'<tr><td class="mono">{i+1:02d}</td><td>{e(c)}</td><td class="ink2">{e(src)}</td></tr>' for i,(c,src) in enumerate(zip(R["telemetry"]["channels"],R["telemetry"]["sources"])))}
</tbody></table></div></section>''')

    # ---------------- models
    srows = "".join(f'<tr><td>{e(r["model"])}</td><td class="num">{r["auc"]:.3f}</td><td class="num">{r["ap"]:.3f}</td><td class="num">{r["brier"]:.4f}</td></tr>' for r in st["results"])
    imp = [(a, max(b, 0)) for a, b in st["importance"]]
    o.append(f'''<section id="models"><div class="sechead"><div class="eyebrow">04 · Models</div><h2>Machine learning and deep learning components</h2>
<p class="ink2">Five model families run in three layers. All metrics are from held-out <b>simulated</b> data. They show the pipeline works end to end and are not estimates of real-world accuracy.</p></div>
<div class="two">
<div class="panel mcard"><div class="chips"><span class="tag ml">Machine learning</span><span class="tag">Layer 1 · structural risk</span></div>
<h3>Country-month shutdown risk</h3>
<p class="ink2">The models train on {st["n_train"]:,} country-months (2016-2022) and are tested on {st["n_test"]:,} (2023-2025), a temporal split across {st["n_countries"]} countries.
The positive rate is {st["pos_rate"]:.1%}. Each country's latent propensity is anchored to its 2025 Access Now count. S, the structural risk, is the equal-weight mean of the three models.</p>
<div class="tblwrap"><table><thead><tr><th>Model</th><th class="num">ROC-AUC</th><th class="num">PR-AUC</th><th class="num">Brier</th></tr></thead><tbody>{srows}</tbody></table></div>
<div class="eyebrow">Permutation importance, gradient boosting (drop in AUC)</div>
{hbars_svg(imp, maxv=max(b for _, b in imp) or 1, fmt="{:.3f}", label_w=230, W=470)}
</div>
<div class="panel mcard"><div class="chips"><span class="tag dl">Deep learning</span><span class="tag">Layer 2 · modality detection</span></div>
<h3>Dilated temporal CNN, multi-label</h3>
<div class="arch">input   24 h × 14 channels (z-scored)
Conv1D  14→32  k=3 d=1  ReLU
Conv1D  32→32  k=3 d=2  ReLU
Conv1D  32→32  k=3 d=4  ReLU   receptive field 15 h
pool    [mean ‖ max] over time → 64
Dense   64→9   sigmoid (one per modality)
loss    class-weighted BCE · Adam · cosine LR
params  {mo["tcn_params"]:,} · NumPy, hand-derived gradients</div>
<p class="ink2">The network trains on {R["telemetry"]["n_train"]:,} windows and is tested on {R["telemetry"]["n_test"]:,}. Macro F1 is <b>{mo["tcn_macro_f1"]:.3f}</b> and macro AUC {mo["tcn_macro_auc"]:.3f}.
The ML baseline, gradient boosting on 84 engineered window features, scores macro F1 {mo["gbm_macro_f1"]:.3f}. On clean simulated signatures the hand-built features do slightly better.
The TCN learns from raw sequences instead, so it needs no re-engineering when censors change tactics.</p>
<div class="legend"><span><i class="dot" style="background:var(--s2)"></i>Temporal CNN (DL)</span><span><i class="dot" style="background:var(--s1)"></i>Gradient boosting (ML)</span></div>
{dot_compare_svg(mo["per_label"])}
</div>
<div class="panel mcard"><div class="chips"><span class="tag dl">Deep learning</span><span class="tag ml">Machine learning</span><span class="tag">Layer 2 · anomaly</span></div>
<h3>Deep autoencoder and Isolation Forest</h3>
<div class="arch">autoencoder  336 → 128 → 32 → 128 → 336  (ReLU, Adam)
trained on   {an["n_normal"]:,} normal windows only
alarm        reconstruction error > 99th pct of normal
fusion term  A = 0 at that threshold, 1 at 3× it</div>
<div class="tblwrap"><table><thead><tr><th>Detector</th><th class="num">ROC-AUC</th><th class="num">Event recall</th><th class="num">False alarms</th><th class="num">Benign flagged</th></tr></thead><tbody>
<tr><td>Deep autoencoder (DL)</td><td class="num">{an["ae_auc"]:.3f}</td><td class="num">{an["ae_detect"]:.1%}</td><td class="num">{an["ae_far"]:.1%}</td><td class="num">{an["ae_benign"]:.0%}</td></tr>
<tr><td>Isolation Forest (ML)</td><td class="num">{an["iso_auc"]:.3f}</td><td class="num">{an["iso_detect"]:.1%}</td><td class="num">{an["iso_far"]:.1%}</td><td class="num">{an["iso_benign"]:.0%}</td></tr></tbody></table></div>
<p class="ink2">Both detectors flag benign outages such as power cuts and cable faults, which is expected because an anomaly detector cannot see intent.
In those cases the modality classifier and human review make the call. Operators blamed undersea cables during Kenya's June 2024 disruption, which is exactly this ambiguity.</p>
</div>
<div class="panel mcard"><div class="chips"><span class="tag">Layer 3 · fusion and alerting</span></div>
<h3>ISEWS score</h3>
<div class="arch">score = 100 × [1 − (1 − 0.35·S)(1 − 0.55·E)(1 − 0.80·D)]
S  structural 30-day risk (ensemble mean)
E  trigger escalation from the ACLED/news feed (0-1)
D  max( maxₖ pₖ·severityₖ , 0.6·A )</div>
<p class="ink2">The noisy-OR form lets any one strong signal raise the score, and no single input can push it past its own ceiling.
Context alone (S and E) can reach Warning, so alerts can go out before telemetry moves. Every alert at Warning or above goes to a human reviewer before tiered release by API and WhatsApp.</p>
<div class="eyebrow">TCN training curve (class-weighted BCE)</div>
<div class="legend"><span><i style="background:var(--s1)"></i>Train</span><span><i style="background:var(--s2)"></i>Validation</span></div>
{loss_svg(mo["history"])}
</div></div>
<div class="panel mcard"><h3>Roadmap models (not yet built)</h3><ul class="clean ink2">
<li><b>LSTM or Temporal Fusion Transformer</b> forecaster for 72-hour risk curves from the escalation feed.</li>
<li><b>Graph neural network</b> over the AS-level topology, to locate where a cut is made (gateway, IXP or operator).</li>
<li><b>Multilingual transformer</b> (for example AfroXLMR) to pull trigger events from news and social posts in Hausa, Yoruba, Swahili, Amharic and Tigrinya.</li>
<li><b>Calibration</b> with isotonic regression on the real STOP labels, and conformal intervals on the score.</li></ul></div>
</section>''')

    # ---------------- surveillance
    srow = []
    for c, d in SURVEILLANCE.items():
        known = [k for k, _, _ in SURV_INDICATORS if d.get(k) is not None]
        idx = sum(w for k, _, w in SURV_INDICATORS if d.get(k) == 1)
        cov = sum(1 for k, _, _ in SURV_INDICATORS if d.get(k) == 1)
        chips = "".join(f'<span class="chip{"" if d.get(k)==1 else " off"}">{e(lab)}{"" if d.get(k)==1 else ": no data"}</span>' for k, lab, _ in SURV_INDICATORS)
        srow.append(f'<tr><td><b>{e(c)}</b></td><td class="num">{idx:.2f}</td><td class="num">{cov} of {len(SURV_INDICATORS)}</td><td><div class="chips">{chips}</div></td><td class="ink2" style="font-size:.82rem">{e(d["note"])}</td></tr>')
    o.append(f'''<section id="surveillance"><div class="sechead"><div class="eyebrow">05 · Surveillance and control</div><h2>Surveillance and control index</h2>
<p class="ink2">Network telemetry rarely shows surveillance directly. ISEWS combines a technical signal (the TLS-interception modality, from certificate-mismatch rates)
with six policy and infrastructure indicators coded from the cited sources. The index is the weighted sum of indicators confirmed present.
An indicator marked <i>no data</i> was not confirmed by any source used here, so a low index means <b>unknown</b>, not safe.</p></div>
<div class="tblwrap"><table><thead><tr><th>Country</th><th class="num">Index</th><th class="num">Confirmed</th><th>Indicators</th><th>Basis</th></tr></thead><tbody>{"".join(srow)}</tbody></table></div>
<p class="muted" style="font-size:.82rem">Weights: {", ".join(f"{lab} {w:.2f}" for _, lab, w in SURV_INDICATORS)}. Hong Kong's March 2026 decryption-refusal offence (Project Ainita) is logged in the historical records as a policy indicator.</p></section>''')

    # ---------------- global context
    tiles = [("313", "shutdowns in 2025 (Access Now)", "VERIFIED"), ("52", "countries affected in 2025", "VERIFIED"),
             ("94", "platform blocks across 40 countries", "EXTRACTED"), ("125", "conflict-related shutdowns, 40% of the total", "VERIFIED"),
             ("14", "satellite (LEO) shutdowns in 7 countries, up from 4", "VERIFIED"), ("916", "Pulse shutdown events, 61 countries, 2019-2025 (ISOC)", "VERIFIED")]
    ttxt = "".join(f'<div class="panel tile"><span class="v">{v}</span><span class="l">{e(l)}</span>{badge(s)}</div>' for v, l, s in tiles)
    trig = [(a, b) for a, b, _ in AGGREGATES["triggers_2025"]]
    plat = AGGREGATES["platform_blocks_2025"]
    afr = AGGREGATES["africa_2025"]
    o.append(f'''<section id="context"><div class="sechead"><div class="eyebrow">06 · Historical baseline</div><h2>What the record shows</h2>
<p class="ink2">Global figures anchor the structural model. Access Now reports that no day in 2025 passed without at least one shutdown.</p></div>
<div class="tiles">{ttxt}</div>
<div class="two">
<div class="panel mcard"><h3>Shutdowns by trigger, 2025</h3><p class="muted" style="font-size:.8rem">Access Now. Conflict is from the press release; the rest are machine-extracted from the annual report.</p>{hbars_svg(trig, maxv=130, fmt="{:.0f}", label_w=200, W=460)}</div>
<div class="panel mcard"><h3>Most-blocked platforms, 2025</h3><p class="muted" style="font-size:.8rem">Access Now annual report (machine-extracted). TikTok blocks rose from 10 in 2024.</p>{hbars_svg(plat, maxv=35, fmt="{:.0f}", label_w=200, W=460)}</div>
<div class="panel mcard"><h3>African countries with shutdowns, 2025</h3><p class="muted" style="font-size:.8rem">Access Now annual report (machine-extracted): {sum(b for _,b in afr)} shutdowns across {len(afr)} countries. Spot-check against the PDF before citing.</p>{hbars_svg(afr, maxv=9, fmt="{:.0f}", label_w=200, row=20, W=460)}</div>
<div class="panel mcard"><h3>Top perpetrators, 2025</h3><p class="muted" style="font-size:.8rem">Access Now. Myanmar is from the press release; the others are machine-extracted.</p>{hbars_svg([(a,b) for a,b,_ in AGGREGATES["top_countries_2025"]], maxv=100, fmt="{:.0f}", label_w=200, W=460)}
<h3 style="margin-top:8px">Conflicting figures</h3><ul class="clean ink2" style="font-size:.84rem">{"".join(f"<li>{e(d)}</li>" for d in DISCREPANCIES)}</ul></div>
</div></section>''')

    # ---------------- historical records
    er = []
    for ev in EVENTS:
        srcs = []
        for sid in ev["source"].split(";"):
            t, u = SOURCES[sid]
            srcs.append(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(sid)}</a>' if u.startswith("http") else e(sid))
        mods = "".join(f'<span class="chip">{e(MOD_LABEL[m])}</span>' for m in ev["modalities"])
        when = e(ev["start"]) + (f" → {e(ev['end'])}" if ev["end"] and ev["end"] != ev["start"] else "")
        er.append(f'<tr><td class="mono">{e(ev["id"])}</td><td><b>{e(ev["country"])}</b></td><td class="mono" style="white-space:nowrap">{when}</td>'
                  f'<td>{e(ev["trigger"])}</td><td><div class="chips">{mods}</div></td><td class="ink2" style="font-size:.84rem;min-width:260px">{e(ev["mechanism"])}</td>'
                  f'<td class="mono">{" · ".join(srcs)}</td><td>{badge(ev["status"])}</td></tr>')
    o.append(f'''<section id="records"><div class="sechead"><div class="eyebrow">07 · Historical records</div><h2>Event records behind the signatures</h2>
<p class="ink2">These {len(EVENTS)} curated records, from Access Now, the Internet Society, Project Ainita, IODA and others, set the telemetry signatures and the scenario designs.
The next step is to load the full Access Now STOP dataset as training labels using <span class="mono">panel.load_events_csv()</span>.</p></div>
<div class="tblwrap"><table><thead><tr><th>ID</th><th>Country</th><th>Dates</th><th>Trigger</th><th>Modalities</th><th>Mechanism and evidence</th><th>Source</th><th>Status</th></tr></thead><tbody>{"".join(er)}</tbody></table></div></section>''')

    # ---------------- limitations + sources
    srcl = "".join(f'<li><span class="mono">{e(k)}</span> - {e(t)}{f" · <a href={chr(34)}{e(u)}{chr(34)} target={chr(34)}_blank{chr(34)} rel={chr(34)}noopener{chr(34)}>{e(u)}</a>" if u.startswith("http") else ""}</li>' for k, (t, u) in SOURCES.items())
    o.append(f'''<section id="limits"><div class="sechead"><div class="eyebrow">08 · Limitations and sources</div><h2>What this prototype does not prove</h2></div>
<ul class="clean ink2">
<li>All telemetry, the training panel and every score are <b>simulated</b>. The high detection scores reflect clean, designed signatures. Real traffic is noisier and censors adapt.</li>
<li>Regime and conflict codes for the 50 panel countries are approximate analyst codes. Replace them with V-Dem and ACLED data.</li>
<li>Escalation curves are hand-set stand-ins for an ACLED and news feed. Tigray escalation follows the ChatVE brief's sequence for 23-24 September 2026.</li>
<li>The fusion weights (0.35, 0.55, 0.80) and the severity weights are design choices, not fitted values. Tune them on backtests before deployment.</li>
<li>National aggregates hide regional cuts, as the Ethiopia national-view card shows. Deployment needs per-ASN and subnational feeds.</li>
<li>A wrong alert in a conflict zone has real costs, so release stays gated by human review.</li></ul>
<div class="panel mcard"><h3>Sources</h3><ul class="clean src">{srcl}</ul></div></section>''')
    o.append(f'<footer>ISEWS prototype · ChatVE, Lagos · Israel Olatunji Tijani, Founder and Head of Research, Development and Innovation · Generated {now}. '
             'Reproduce with <span class="mono">python run_isews.py</span>.</footer></div>')
    o.append(f"<script>{JS}</script>")
    if full:
        o.append("</body></html>")
    return "\n".join(o)
