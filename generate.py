#!/usr/bin/env python3
"""Generate static site for video ideas."""
import re, pathlib, html

ROOT      = pathlib.Path(__file__).parent.parent
SITE      = pathlib.Path(__file__).parent
IDEAS_DIR = ROOT / "ideas"
RESULTS   = ROOT / "results"

def extract_block(text, header):
    m = re.search(rf'## {re.escape(header)}\s*```(.*?)```', text, re.DOTALL)
    return m.group(1).strip() if m else None

def extract_text_section(text, header):
    m = re.search(rf'## {re.escape(header)}\s*\n(.*?)(?=\n## |\Z)', text, re.DOTALL)
    return m.group(1).strip() if m else None

def extract_first_frame(text):
    for h in ["Промпт для генерации первого кадра (GPT Image 2)",
              "Промпт для генерации первого кадра (NanoBanana2)"]:
        r = extract_block(text, h)
        if r: return r
    return None

def parse_idea(path):
    text = path.read_text()
    title_m = re.match(r'# (.+)', text)
    raw_title = title_m.group(1) if title_m else path.stem
    parts = raw_title.split(' — ', 1)
    hashtag = parts[0].lstrip('#').strip()
    short_title = parts[1].strip() if len(parts) > 1 else hashtag
    desc = extract_text_section(text, "Краткое описание идеи") or ""
    video_prompt = extract_block(text, "Промпт для генерации видео") or ""
    return {
        "name": path.stem,
        "hashtag": hashtag,
        "title": short_title,
        "desc": desc,
        "video_prompt": video_prompt,
    }

SHARED_CSS = """
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      background: #f4f4f5;
      color: #111;
      font-size: 14px;
      line-height: 1.5;
    }
    .page-header {
      background: #fff;
      border-bottom: 1px solid #e4e4e7;
      position: sticky;
      top: 0;
      z-index: 100;
      box-shadow: 0 1px 8px rgba(0,0,0,.05);
    }
    .header-inner {
      max-width: 1100px;
      margin: 0 auto;
      padding: 14px 28px;
      display: flex;
      align-items: center;
      gap: 20px;
    }
    .brand {
      font-size: 18px;
      font-weight: 800;
      letter-spacing: -.5px;
      color: #111;
      white-space: nowrap;
      user-select: none;
      text-decoration: none;
    }
    .brand-tik { color: #fe2c55; }
    .brand-tok { color: #010101; }
    .brand-dot { color: #d1d1d1; margin: 0 6px; font-weight: 300; }
    .brand-cc  { color: #888; font-size: 12px; font-weight: 500; }
    .header-text { flex: 1; min-width: 0; }
    .page-title { font-size: 15px; font-weight: 700; letter-spacing: -.2px; }
    .page-sub { font-size: 11.5px; color: #999; margin-top: 2px; }
    .content {
      max-width: 1100px;
      margin: 0 auto;
      padding: 40px 28px 80px;
    }
    .section-header {
      display: flex;
      align-items: baseline;
      gap: 10px;
      margin-bottom: 24px;
    }
    .section-title { font-size: 19px; font-weight: 800; letter-spacing: -.4px; }
    .section-badge {
      font-size: 10.5px;
      font-weight: 600;
      color: #999;
      background: #ebebeb;
      padding: 3px 8px;
      border-radius: 20px;
      text-transform: uppercase;
      letter-spacing: .4px;
    }
    @media (max-width: 768px) {
      .header-inner { padding: 12px 16px; }
      .content { padding: 24px 16px 60px; }
    }
"""

def head(title):
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">"""

# ── INDEX ────────────────────────────────────────────────────────────────────

def gen_index(dates):
    cards_html = ""
    for date, n_ideas, n_videos in dates:
        dd, mm, yyyy = date.split("-")[2], date.split("-")[1], date.split("-")[0]
        month_names = {"01":"янв","02":"фев","03":"мар","04":"апр","05":"мая",
                       "06":"июн","07":"июл","08":"авг","09":"сен","10":"окт","11":"ноя","12":"дек"}
        month = month_names[mm]
        cards_html += f"""
    <a class="report-card" href="./{date}/">
      <div class="card-top">
        <div class="card-flag">🎬</div>
        <div class="card-date-badge">{dd}.{mm}.{yyyy}<span>Дата отчёта</span></div>
      </div>
      <div class="card-country">TikTok US · Видео-идеи</div>
      <div class="card-period">8–14 мая 2026</div>
      <div class="card-stats">
        <div class="card-stat-item">
          <div class="card-stat-val">{n_ideas}</div>
          <div class="card-stat-lbl">Идей</div>
        </div>
        <div class="card-stat-item">
          <div class="card-stat-val">{n_videos}</div>
          <div class="card-stat-lbl">Видео</div>
        </div>
      </div>
      <div class="card-arrow">Смотреть идеи →</div>
    </a>"""

    return head("Video Ideas — Отчёты") + f"""
  <style>
{SHARED_CSS}
    .report-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 16px;
    }}
    .report-card {{
      background: #fff;
      border-radius: 12px;
      padding: 24px 28px;
      box-shadow: 0 1px 4px rgba(0,0,0,.07), 0 0 0 1px rgba(0,0,0,.05);
      text-decoration: none;
      color: inherit;
      display: block;
      transition: box-shadow .15s, transform .15s;
    }}
    .report-card:hover {{
      box-shadow: 0 4px 16px rgba(0,0,0,.10), 0 0 0 1px rgba(0,0,0,.07);
      transform: translateY(-1px);
    }}
    .card-top {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
    }}
    .card-flag {{ font-size: 32px; line-height: 1; }}
    .card-date-badge {{
      background: #fe2c55;
      color: #fff;
      font-weight: 700;
      font-size: 11px;
      border-radius: 7px;
      padding: 4px 10px;
      line-height: 1.5;
      text-align: center;
    }}
    .card-date-badge span {{ display: block; font-size: 9px; font-weight: 500; opacity: .8; }}
    .card-country {{ font-size: 17px; font-weight: 800; letter-spacing: -.3px; margin-bottom: 4px; }}
    .card-period {{ font-size: 12px; color: #888; font-weight: 500; margin-bottom: 16px; }}
    .card-stats {{
      display: flex;
      gap: 20px;
      padding-top: 16px;
      border-top: 1px solid #f2f2f2;
    }}
    .card-stat-item {{ flex: 1; }}
    .card-stat-val {{ font-size: 16px; font-weight: 800; letter-spacing: -.3px; }}
    .card-stat-lbl {{ font-size: 10px; font-weight: 500; color: #aaa; text-transform: uppercase; letter-spacing: .3px; margin-top: 1px; }}
    .card-arrow {{ display: flex; align-items: center; justify-content: flex-end; gap: 5px; margin-top: 16px; font-size: 12px; font-weight: 600; color: #fe2c55; }}
    @media (max-width: 768px) {{
      .report-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>

<div class="page-header">
  <div class="header-inner">
    <a class="brand" href="./">
      <span class="brand-tik">Tik</span><span class="brand-tok">Tok</span>
      <span class="brand-dot">·</span>
      <span class="brand-cc">Video Ideas</span>
    </a>
    <div class="header-text">
      <div class="page-title">Архив видео-идей</div>
      <div class="page-sub">AI-сгенерированные видео-эффекты по трендовым хештегам</div>
    </div>
  </div>
</div>

<div class="content">
  <div class="section-header">
    <h2 class="section-title">Отчёты</h2>
    <span class="section-badge">{len(dates)} отчёт</span>
  </div>
  <div class="report-grid">
{cards_html}
  </div>
</div>

</body>
</html>"""


# ── REPORT PAGE ───────────────────────────────────────────────────────────────

def gen_report(date, ideas, results_base):
    dd, mm, yyyy = date.split("-")[2], date.split("-")[1], date.split("-")[0]
    month_names_full = {"01":"января","02":"февраля","03":"марта","04":"апреля","05":"мая",
                        "06":"июня","07":"июля","08":"августа","09":"сентября","10":"октября","11":"ноября","12":"декабря"}
    date_label = f"{int(dd)} {month_names_full[mm]} {yyyy}"

    n_videos = sum(1 for idea in ideas if (ROOT / "results" / date / "01750ad3" / f"{idea['name']}_video.mp4").exists())

    cards_html = ""
    for idea in ideas:
        frame_rel = f"{results_base}/{idea['name']}_frame.png"
        video_rel = f"{results_base}/{idea['name']}_video.mp4"
        has_video = (ROOT / "results" / date / "01750ad3" / f"{idea['name']}_video.mp4").exists()

        video_block = ""
        if has_video:
            video_block = f"""
        <div class="card-video-wrap">
          <video controls muted loop playsinline
                 poster="{frame_rel}"
                 style="width:100%;aspect-ratio:9/16;object-fit:cover;border-radius:10px;display:block;">
            <source src="{video_rel}" type="video/mp4">
          </video>
        </div>"""
        else:
            video_block = f"""
        <div class="card-video-wrap">
          <div class="card-no-video">
            <img src="{frame_rel}" alt="First frame" style="width:100%;aspect-ratio:9/16;object-fit:cover;border-radius:10px;display:block;">
            <div class="no-video-badge">Видео недоступно</div>
          </div>
        </div>"""

        prompt_escaped = html.escape(idea['video_prompt'])
        desc_escaped = html.escape(idea['desc'])

        cards_html += f"""
    <div class="idea-card">
      {video_block}
      <div class="card-body">
        <div class="card-meta">
          <span class="hashtag-pill">#{html.escape(idea['hashtag'])}</span>
        </div>
        <h3 class="card-title">{html.escape(idea['title'])}</h3>
        <p class="card-desc">{desc_escaped}</p>
        <details class="prompt-details">
          <summary>Промпт для видео</summary>
          <pre class="prompt-text">{prompt_escaped}</pre>
        </details>
      </div>
    </div>"""

    return head(f"Video Ideas — {date_label}") + f"""
  <style>
{SHARED_CSS}
    .page-nav {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 10px 28px;
      font-size: 12px;
    }}
    .page-nav a {{ color: #888; text-decoration: none; }}
    .page-nav a:hover {{ color: #fe2c55; }}
    .date-badge {{
      background: #fe2c55;
      color: #fff;
      font-weight: 700;
      font-size: 12px;
      border-radius: 8px;
      padding: 6px 14px;
      line-height: 1.4;
      text-align: center;
      white-space: nowrap;
      flex-shrink: 0;
    }}
    .date-badge span {{ display: block; font-size: 10px; font-weight: 500; opacity: .8; }}
    .ideas-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 24px;
    }}
    .idea-card {{
      background: #fff;
      border-radius: 14px;
      box-shadow: 0 1px 4px rgba(0,0,0,.07), 0 0 0 1px rgba(0,0,0,.05);
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }}
    .card-video-wrap {{
      position: relative;
      background: #000;
    }}
    .card-no-video {{ position: relative; }}
    .no-video-badge {{
      position: absolute;
      bottom: 10px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(0,0,0,.6);
      color: #fff;
      font-size: 11px;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 20px;
      white-space: nowrap;
    }}
    .card-body {{
      padding: 18px 20px 20px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      flex: 1;
    }}
    .card-meta {{ display: flex; align-items: center; gap: 8px; }}
    .hashtag-pill {{
      background: #fe2c55;
      color: #fff;
      font-size: 11px;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 20px;
      letter-spacing: .2px;
    }}
    .card-title {{
      font-size: 16px;
      font-weight: 800;
      letter-spacing: -.3px;
      line-height: 1.3;
    }}
    .card-desc {{
      font-size: 13px;
      color: #444;
      line-height: 1.6;
    }}
    .prompt-details {{
      margin-top: auto;
      border-top: 1px solid #f0f0f0;
      padding-top: 12px;
    }}
    .prompt-details summary {{
      font-size: 12px;
      font-weight: 600;
      color: #888;
      cursor: pointer;
      user-select: none;
      list-style: none;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .prompt-details summary::-webkit-details-marker {{ display: none; }}
    .prompt-details summary::before {{
      content: '▶';
      font-size: 9px;
      transition: transform .15s;
    }}
    .prompt-details[open] summary::before {{ transform: rotate(90deg); }}
    .prompt-details summary:hover {{ color: #fe2c55; }}
    .prompt-text {{
      margin-top: 10px;
      font-family: 'SF Mono', 'Fira Code', monospace;
      font-size: 11px;
      line-height: 1.7;
      color: #555;
      background: #f8f8f8;
      border: 1px solid #ebebeb;
      border-radius: 8px;
      padding: 12px 14px;
      white-space: pre-wrap;
      word-break: break-word;
      max-height: 260px;
      overflow-y: auto;
    }}
    @media (max-width: 768px) {{
      .ideas-grid {{ grid-template-columns: 1fr; }}
      .page-nav {{ padding: 10px 16px; }}
    }}
  </style>
</head>
<body>

<div class="page-header">
  <div class="header-inner">
    <a class="brand" href="../">
      <span class="brand-tik">Tik</span><span class="brand-tok">Tok</span>
      <span class="brand-dot">·</span>
      <span class="brand-cc">Video Ideas</span>
    </a>
    <div class="header-text">
      <div class="page-title">Видео-идеи · {date_label}</div>
      <div class="page-sub">AI-сгенерированные эффекты по трендовым хештегам TikTok US</div>
    </div>
    <div class="date-badge">{dd}.{mm}.{yyyy}<span>Дата отчёта</span></div>
  </div>
</div>
<div class="page-nav"><a href="../">← Все отчёты</a></div>

<div class="content">
  <div class="section-header">
    <h2 class="section-title">Идеи</h2>
    <span class="section-badge">{len(ideas)} идей · {n_videos} видео</span>
  </div>
  <div class="ideas-grid">
{cards_html}
  </div>
</div>

</body>
</html>"""


# ── MAIN ──────────────────────────────────────────────────────────────────────

DATE = "2026-05-14"
SKIP = {"lakers_nobrand"}

ideas_dir = IDEAS_DIR / DATE
results_base_rel = f"../../results/{DATE}/01750ad3"

idea_files = sorted(
    f for f in ideas_dir.glob("*.md")
    if f.stem not in SKIP and not f.stem.endswith("_pipeline")
)
ideas = [parse_idea(f) for f in idea_files]

results_dir = ROOT / "results" / DATE / "01750ad3"
n_videos = sum(1 for idea in ideas if (results_dir / f"{idea['name']}_video.mp4").exists())

# Write index.html
index_html = gen_index([(DATE, len(ideas), n_videos)])
(SITE / "index.html").write_text(index_html)
print(f"wrote site/index.html")

# Write report page
report_dir = SITE / DATE
report_dir.mkdir(exist_ok=True)
report_html = gen_report(DATE, ideas, results_base_rel)
(report_dir / "index.html").write_text(report_html)
print(f"wrote site/{DATE}/index.html")
print(f"  {len(ideas)} ideas, {n_videos} videos")
