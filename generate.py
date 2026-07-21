#!/usr/bin/env python3
"""
Generate static site for video ideas.

Usage:
    python3 generate.py [--date 2026-05-14]   # rebuild one date
    python3 generate.py                        # rebuild all dates
"""
import re, pathlib, html, json, sys, argparse

ROOT      = pathlib.Path(__file__).parent.parent
SITE      = pathlib.Path(__file__).parent
IDEAS_DIR = ROOT / "ideas"

MONTH_FULL = {
    "01":"января","02":"февраля","03":"марта","04":"апреля","05":"мая","06":"июня",
    "07":"июля","08":"августа","09":"сентября","10":"октября","11":"ноября","12":"декабря",
}
MONTH_SHORT = {
    "01":"янв","02":"фев","03":"мар","04":"апр","05":"мая","06":"июн",
    "07":"июл","08":"авг","09":"сен","10":"окт","11":"ноя","12":"дек",
}

def split_report_date(date):
    """Split 'YYYY-MM-DD' or 'YYYY-MM-DD_N' (a re-run of the same report date)
    into (yyyy, mm, dd, suffix_label), where suffix_label is '' or ' · Выпуск N'."""
    yyyy, mm, dd_raw = date.split('-')
    m = re.match(r'(\d+)(?:_(.+))?$', dd_raw)
    dd, suffix = m.group(1), m.group(2)
    suffix_label = f' · Выпуск {suffix}' if suffix else ''
    return yyyy, mm, dd, suffix_label


# ── Parsing ───────────────────────────────────────────────────────────────────

def extract_section(text, pattern):
    """Extract text block after a ## header matching pattern."""
    m = re.search(r'## ' + pattern + r'.*?\n\n(.*?)(?=\n## |\Z)', text, re.DOTALL)
    if not m:
        return ''
    raw = m.group(1).strip()
    raw = re.sub(r'^```\n?', '', raw)
    raw = re.sub(r'\n?```$', '', raw)
    return raw

def parse_idea(md_path):
    text = md_path.read_text()
    title_m = re.match(r'# .+? — (.+)', text)
    title = title_m.group(1).strip() if title_m else md_path.stem
    slug = md_path.stem
    hashtag = re.match(r'# #?(\S+)', text)
    hashtag = hashtag.group(1).lower() if hashtag else slug

    return {
        'slug': slug,
        'hashtag': slug,
        'title': title,
        'desc': extract_section(text, r'Краткое описание идеи'),
        'first_frame_prompt': extract_section(text, r'Промпт для генерации первого кадра.*?'),
        'video_prompt': extract_section(text, r'Промпт для генерации видео'),
    }

def get_runs(slug, date):
    """Get every completed run (one per photo profile) from the pipeline JSON,
    in the order they appear in `runs`. Each dict has at least
    frame/video/descriptor keys; failed runs are skipped."""
    p = IDEAS_DIR / date / f'{slug}_pipeline.json'
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
    except Exception:
        return []
    out = []
    for run in data.get('runs', []):
        if run.get('status') != 'completed':
            continue
        out.append({
            'frame': run.get('d167_image'),
            'video': run.get('d156_video'),
            'descriptor': run.get('photo_descriptor') or '',
            'photo': run.get('photo') or '',
        })
    return out


# ── Shared CSS ────────────────────────────────────────────────────────────────

COMMON_CSS = """
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      background: #f4f4f5; color: #111; font-size: 14px; line-height: 1.5;
    }
    .page-header {
      background: #fff; border-bottom: 1px solid #e4e4e7; position: sticky;
      top: 0; z-index: 100; box-shadow: 0 1px 8px rgba(0,0,0,.05);
    }
    .header-inner {
      max-width: 1100px; margin: 0 auto; padding: 14px 28px;
      display: flex; align-items: center; gap: 20px;
    }
    .brand {
      font-size: 18px; font-weight: 800; letter-spacing: -.5px; color: #111;
      white-space: nowrap; user-select: none; text-decoration: none;
    }
    .brand-tik { color: #fe2c55; }
    .brand-tok { color: #010101; }
    .brand-dot { color: #d1d1d1; margin: 0 6px; font-weight: 300; }
    .brand-cc  { color: #888; font-size: 12px; font-weight: 500; }
    .header-text { flex: 1; min-width: 0; }
    .page-title {
      font-size: 15px; font-weight: 700; letter-spacing: -.2px;
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .page-sub { font-size: 11.5px; color: #999; margin-top: 2px; }
    .date-badge {
      background: #fe2c55; color: #fff; font-weight: 700; font-size: 12px;
      border-radius: 8px; padding: 6px 14px; line-height: 1.4;
      text-align: center; white-space: nowrap; flex-shrink: 0;
    }
    .date-badge span { display: block; font-size: 10px; font-weight: 500; opacity: .8; }
    .page-nav {
      max-width: 1100px; margin: 0 auto; padding: 0 28px;
      display: flex; gap: 2px; border-top: 1px solid #f0f0f0;
    }
    .nav-a {
      text-decoration: none; color: #999; font-size: 12.5px; font-weight: 500;
      padding: 9px 14px; border-bottom: 2px solid transparent;
      transition: color .15s, border-color .15s;
    }
    .nav-a:hover { color: #fe2c55; }
    .nav-a.active { color: #fe2c55; border-bottom-color: #fe2c55; }
    .content { max-width: 1100px; margin: 0 auto; padding: 36px 28px 80px; }
    .section { margin-bottom: 52px; }
    .section-header { display: flex; align-items: baseline; gap: 10px; margin-bottom: 16px; }
    .section-title { font-size: 19px; font-weight: 800; letter-spacing: -.4px; }
    .section-badge {
      font-size: 10.5px; font-weight: 600; color: #999; background: #ebebeb;
      padding: 3px 8px; border-radius: 20px; text-transform: uppercase; letter-spacing: .4px;
    }
    @media (max-width: 768px) {
      .header-inner { gap: 12px; padding: 12px 16px; }
      .date-badge { display: none; }
      .page-nav { padding: 0 16px; }
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


# ── site/index.html ────────────────────────────────────────────────────────────

def gen_main_index(date_entries):
    """date_entries: list of (date, n_ideas, n_videos)"""
    cards = ''
    for date, n_ideas, n_videos in sorted(date_entries, reverse=True):
        yyyy, mm, dd, suffix_label = split_report_date(date)
        cards += f"""
    <a class="report-card" href="./{date}/">
      <div class="card-top">
        <div class="card-flag">🎬</div>
        <div class="card-date-badge">{dd}.{mm}.{yyyy}<span>Дата отчёта{suffix_label}</span></div>
      </div>
      <div class="card-title-text">TikTok US · Видео-идеи</div>
      <div class="card-period">{int(dd)} {MONTH_FULL[mm]} {yyyy}{suffix_label}</div>
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

    n = len(date_entries)
    badge = f"{n} {'отчёт' if n==1 else 'отчёта' if n<5 else 'отчётов'}"

    return head("Video Ideas — Отчёты") + f"""
  <style>
{COMMON_CSS}
    .report-grid {{
      display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px;
    }}
    .report-card {{
      background: #fff; border-radius: 12px; padding: 24px 28px;
      box-shadow: 0 1px 4px rgba(0,0,0,.07), 0 0 0 1px rgba(0,0,0,.05);
      text-decoration: none; color: inherit; display: block;
      transition: box-shadow .15s, transform .15s;
    }}
    .report-card:hover {{
      box-shadow: 0 4px 16px rgba(0,0,0,.10), 0 0 0 1px rgba(0,0,0,.07);
      transform: translateY(-1px);
    }}
    .card-top {{
      display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;
    }}
    .card-flag {{ font-size: 32px; line-height: 1; }}
    .card-date-badge {{
      background: #fe2c55; color: #fff; font-weight: 700; font-size: 11px;
      border-radius: 7px; padding: 4px 10px; line-height: 1.5; text-align: center;
    }}
    .card-date-badge span {{ display: block; font-size: 9px; font-weight: 500; opacity: .8; }}
    .card-title-text {{ font-size: 17px; font-weight: 800; letter-spacing: -.3px; margin-bottom: 4px; }}
    .card-period {{ font-size: 12px; color: #888; font-weight: 500; margin-bottom: 16px; }}
    .card-stats {{
      display: flex; gap: 20px; padding-top: 16px; border-top: 1px solid #f2f2f2;
    }}
    .card-stat-item {{ flex: 1; }}
    .card-stat-val {{ font-size: 16px; font-weight: 800; letter-spacing: -.3px; }}
    .card-stat-lbl {{ font-size: 10px; font-weight: 500; color: #aaa; text-transform: uppercase; letter-spacing: .3px; margin-top: 1px; }}
    .card-arrow {{ display: flex; align-items: center; justify-content: flex-end; gap: 5px; margin-top: 16px; font-size: 12px; font-weight: 600; color: #fe2c55; }}
    @media (max-width: 768px) {{ .report-grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
<div class="page-header">
  <div class="header-inner">
    <a class="brand" href="./">
      <span class="brand-tik">Tik</span><span class="brand-tok">Tok</span>
      <span class="brand-dot">·</span><span class="brand-cc">Video Ideas</span>
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
    <span class="section-badge">{badge}</span>
  </div>
  <div class="report-grid">{cards}
  </div>
</div>
</body>
</html>"""


# ── site/{date}/index.html ────────────────────────────────────────────────────

def gen_date_index(date, ideas_with_media):
    """ideas_with_media: list of (idea_dict, runs) where runs is get_runs()'s list"""
    yyyy, mm, dd, suffix_label = split_report_date(date)

    rows = ''
    for i, (idea, runs) in enumerate(ideas_with_media, 1):
        frame_url = runs[0]['frame'] if runs else None
        thumb = f'<img class="thumb-img" src="{frame_url}" alt="#{idea["hashtag"]}">' if frame_url else '<div class="thumb-placeholder"></div>'
        rows += f"""
      <tr>
        <td class="thumb-cell">{thumb}</td>
        <td><div class="td-inner">
          <span class="rank-num">{i}</span>
          <span style="width:16px"></span>
          <a class="htag-link" href="./{idea['slug']}/"><span class="htag-hash">#</span>{html.escape(idea['slug'])}</a>
        </div></td>
        <td class="td-title">{html.escape(idea['title'])}</td>
        <td class="td-arrow">→</td>
      </tr>"""

    n = len(ideas_with_media)
    n_videos = sum(1 for _, runs in ideas_with_media if any(r['video'] for r in runs))

    return head(f"Video Ideas — {int(dd)} {MONTH_FULL[mm]} {yyyy}{suffix_label}") + f"""
  <style>
{COMMON_CSS}
    .table-wrap {{
      background: #fff; border-radius: 12px; overflow: hidden;
      box-shadow: 0 1px 4px rgba(0,0,0,.07), 0 0 0 1px rgba(0,0,0,.05);
    }}
    .ht-table {{ width: 100%; border-collapse: collapse; }}
    .ht-table thead th {{
      text-align: left; padding: 10px 16px; font-size: 10.5px; font-weight: 600;
      text-transform: uppercase; letter-spacing: .5px; color: #aaa;
      background: #f9f9f9; border-bottom: 1px solid #ebebeb;
    }}
    .ht-table tbody td {{ padding: 0; border-bottom: 1px solid #f2f2f2; vertical-align: middle; }}
    .ht-table tbody tr:last-child td {{ border-bottom: none; }}
    .ht-table tbody tr:hover td {{ background: #fafbff; }}
    .td-inner {{ padding: 12px 16px; display: flex; align-items: center; }}
    .rank-num {{ font-weight: 800; font-size: 14px; display: inline-block; min-width: 24px; text-align: right; color: #ccc; }}
    .thumb-cell {{ padding: 8px 10px 8px 16px !important; }}
    .thumb-img {{ width: 44px; height: 78px; object-fit: cover; border-radius: 6px; display: block; background: #eee; }}
    .thumb-placeholder {{ width: 44px; height: 78px; border-radius: 6px; background: #eee; }}
    .htag-link {{ font-weight: 700; font-size: 14px; color: #111; text-decoration: none; display: inline-flex; align-items: center; gap: 1px; }}
    .htag-link:hover {{ color: #fe2c55; }}
    .htag-hash {{ color: #bbb; font-weight: 400; }}
    .td-title {{ font-size: 13px; color: #555; padding-left: 12px; }}
    .td-arrow {{ color: #ddd; font-size: 13px; padding: 12px 20px 12px 8px !important; text-align: right; }}
    .ht-table tbody tr:hover .td-arrow {{ color: #fe2c55; }}
    @media (max-width: 520px) {{ .td-title {{ display: none; }} }}
  </style>
</head>
<body>
<div class="page-header">
  <div class="header-inner">
    <a class="brand" href="../">
      <span class="brand-tik">Tik</span><span class="brand-tok">Tok</span>
      <span class="brand-dot">·</span><span class="brand-cc">Video Ideas</span>
    </a>
    <div class="header-text">
      <div class="page-title">Видео-идеи · {int(dd)} {MONTH_FULL[mm]} {yyyy}{suffix_label}</div>
      <div class="page-sub">AI-сгенерированные эффекты по трендовым хештегам TikTok US</div>
    </div>
    <div class="date-badge">{dd}.{mm}.{yyyy}<span>Дата отчёта{suffix_label}</span></div>
  </div>
  <nav class="page-nav">
    <a href="../" class="nav-a">← Все отчёты</a>
    <a href="#ideas" class="nav-a active">Идеи</a>
  </nav>
</div>
<div class="content">
  <section id="ideas" class="section">
    <div class="section-header">
      <h2 class="section-title">Идеи</h2>
      <span class="section-badge">{n} {'идея' if n==1 else 'идеи' if n<5 else 'идей'} · {n_videos} видео</span>
    </div>
    <div class="table-wrap">
      <table class="ht-table">
        <thead><tr>
          <th style="width:68px"></th>
          <th>Хештег</th>
          <th>Идея</th>
          <th style="width:48px"></th>
        </tr></thead>
        <tbody>{rows}
        </tbody>
      </table>
    </div>
  </section>
</div>
</body>
</html>"""


# ── site/{date}/{slug}/index.html ─────────────────────────────────────────────

IDEA_CSS = """
    .idea-lead {{
      background: #fff; border-radius: 12px; padding: 36px 40px 32px;
      box-shadow: 0 1px 4px rgba(0,0,0,.07), 0 0 0 1px rgba(0,0,0,.05);
      margin-bottom: 40px;
    }}
    .idea-hashtag {{ font-size: 13px; font-weight: 700; color: #fe2c55; margin-bottom: 8px; }}
    .idea-title {{ font-size: 26px; font-weight: 800; letter-spacing: -.6px; line-height: 1.25; margin-bottom: 16px; }}
    .idea-desc {{ font-size: 14px; color: #444; line-height: 1.75; max-width: 720px; }}
    .media-grid {{
      display: grid; grid-template-columns: auto 1fr; gap: 28px; align-items: start;
    }}
    .video-multi {{
      display: flex; gap: 16px; flex-wrap: wrap;
    }}
    .video-item {{
      width: 200px; display: flex; flex-direction: column; gap: 8px; flex-shrink: 0;
    }}
    .video-caption {{
      font-size: 11px; color: #999; line-height: 1.4; padding: 0 2px;
    }}
    .video-player {{
      width: 100%; aspect-ratio: 9/16; object-fit: cover; border-radius: 12px;
      display: block; box-shadow: 0 2px 16px rgba(0,0,0,.14);
    }}
    .frame-img {{
      width: 100%; aspect-ratio: 9/16; object-fit: cover; border-radius: 12px;
      display: block; box-shadow: 0 2px 16px rgba(0,0,0,.14);
    }}
    .prompts-col {{ display: flex; flex-direction: column; gap: 12px; }}
    .prompt-block {{
      background: #fff; border-radius: 10px;
      box-shadow: 0 1px 4px rgba(0,0,0,.07), 0 0 0 1px rgba(0,0,0,.05); overflow: hidden;
    }}
    .prompt-block summary {{
      padding: 14px 18px; font-size: 13px; font-weight: 700; cursor: pointer;
      user-select: none; list-style: none; display: flex; align-items: center; gap: 8px; color: #333;
    }}
    .prompt-block summary::-webkit-details-marker {{ display: none; }}
    .prompt-block summary::before {{ content: '▶'; font-size: 8px; color: #bbb; transition: transform .15s; flex-shrink: 0; }}
    .prompt-block[open] summary::before {{ transform: rotate(90deg); }}
    .prompt-block summary:hover {{ color: #fe2c55; }}
    .prompt-block summary:hover::before {{ color: #fe2c55; }}
    .prompt-label {{ font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: .5px; color: #bbb; margin-left: auto; }}
    .prompt-text {{
      padding: 14px 18px 16px; font-family: 'SF Mono','Fira Code','Menlo',monospace;
      font-size: 11.5px; line-height: 1.7; color: #555; background: #f9f9f9;
      border-top: 1px solid #f0f0f0; white-space: pre-wrap; word-break: break-word;
      max-height: 320px; overflow-y: auto;
    }}
    @media (max-width: 900px) {{
      .media-grid {{ grid-template-columns: 1fr; }}
      .video-multi {{ justify-content: center; }}
      .idea-lead {{ padding: 24px 22px 22px; }}
    }}
    @media (max-width: 520px) {{ .idea-title {{ font-size: 22px; }} }}
"""

def gen_idea_page(date, idea, runs):
    yyyy, mm, dd, suffix_label = split_report_date(date)
    slug = idea['slug']

    if runs:
        items = ''
        for run in runs:
            frame_url, video_url = run['frame'], run['video']
            if video_url and frame_url:
                item_media = f'<video class="video-player" controls muted loop playsinline poster="{frame_url}"><source src="{video_url}" type="video/mp4"></video>'
            elif frame_url:
                item_media = f'<img class="frame-img" src="{frame_url}" alt="#{slug}">'
            else:
                item_media = '<div style="aspect-ratio:9/16;background:#eee;border-radius:12px;"></div>'
            caption = html.escape(run['descriptor']) if run['descriptor'] else ''
            items += f"""
        <div class="video-item">{item_media}
          <div class="video-caption">{caption}</div>
        </div>"""
        media_html = f'<div class="video-multi">{items}\n      </div>'
    else:
        media_html = '<div class="video-multi"><div class="video-item"><div style="aspect-ratio:9/16;background:#eee;border-radius:12px;"></div></div></div>'

    return head(f"#{slug} — {html.escape(idea['title'])} · Video Ideas") + f"""
  <style>
{COMMON_CSS}
{IDEA_CSS}
  </style>
</head>
<body>
<div class="page-header">
  <div class="header-inner">
    <a class="brand" href="../../">
      <span class="brand-tik">Tik</span><span class="brand-tok">Tok</span>
      <span class="brand-dot">·</span><span class="brand-cc">Video Ideas</span>
    </a>
    <div class="header-text">
      <div class="page-title">#{html.escape(slug)}</div>
      <div class="page-sub">Видео-идея · {int(dd)} {MONTH_FULL[mm]} {yyyy}{suffix_label}</div>
    </div>
    <div class="date-badge">{dd}.{mm}.{yyyy}<span>Дата{suffix_label}</span></div>
  </div>
  <nav class="page-nav">
    <a href="../../" class="nav-a">← Все отчёты</a>
    <a href="../" class="nav-a">← {int(dd)} {MONTH_SHORT[mm]} {yyyy}{suffix_label}</a>
    <a href="#" class="nav-a active">#{html.escape(slug)}</a>
  </nav>
</div>
<div class="content">
  <div class="idea-lead">
    <div class="idea-hashtag">#{html.escape(slug)}</div>
    <h1 class="idea-title">{html.escape(idea['title'])}</h1>
    <p class="idea-desc">{html.escape(idea['desc'])}</p>
  </div>
  <section class="section">
    <div class="section-header">
      <h2 class="section-title">Видео</h2>
      <span class="section-badge">Пример генерации</span>
    </div>
    <div class="media-grid">
      {media_html}
      <div class="prompts-col">
        <details class="prompt-block">
          <summary>Промпт для первого кадра <span class="prompt-label">GPT Image 2</span></summary>
          <pre class="prompt-text">{html.escape(idea['first_frame_prompt'])}</pre>
        </details>
        <details class="prompt-block">
          <summary>Промпт для видео <span class="prompt-label">Kling · Grok</span></summary>
          <pre class="prompt-text">{html.escape(idea['video_prompt'])}</pre>
        </details>
      </div>
    </div>
  </section>
</div>
</body>
</html>"""


# ── Main ──────────────────────────────────────────────────────────────────────

def collect_date(date):
    """Parse ideas + media for a date without writing any HTML."""
    ideas_dir = IDEAS_DIR / date
    skip = {'_pipeline', '_nobrand'}

    md_files = sorted(
        f for f in ideas_dir.glob('*.md')
        if not any(s in f.stem for s in skip)
    )
    ideas = [parse_idea(f) for f in md_files]

    ideas_with_media = []
    for idea in ideas:
        runs = get_runs(idea['slug'], date)
        ideas_with_media.append((idea, runs))

    return ideas_with_media


def write_date(date, ideas_with_media):
    """Write the date-index page and every idea page for one date."""
    date_dir = SITE / date
    date_dir.mkdir(exist_ok=True)

    # Date index page
    (date_dir / 'index.html').write_text(gen_date_index(date, ideas_with_media))
    print(f'  wrote {date}/index.html  ({len(ideas_with_media)} ideas)')

    # Individual idea pages
    for idea, runs in ideas_with_media:
        slug_dir = date_dir / idea['slug']
        slug_dir.mkdir(exist_ok=True)
        (slug_dir / 'index.html').write_text(gen_idea_page(date, idea, runs))
        print(f'  wrote {date}/{idea["slug"]}/index.html')


def build_date(date):
    """Back-compat helper: collect + write a single date, return its ideas_with_media."""
    ideas_with_media = collect_date(date)
    write_date(date, ideas_with_media)
    return ideas_with_media


def build_all():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', help='Rebuild only this date (YYYY-MM-DD). The main index is always '
                                        'regenerated from every date folder on disk, regardless of --date.')
    args = parser.parse_args()

    all_dates = sorted(
        d.name for d in IDEAS_DIR.iterdir() if d.is_dir() and re.match(r'\d{4}-\d{2}-\d{2}', d.name)
    )
    dates_to_write = {args.date} if args.date else set(all_dates)

    all_entries = []
    for date in all_dates:
        print(f'\n{"Building" if date in dates_to_write else "Scanning"} {date}...')
        ideas_with_media = collect_date(date)
        if date in dates_to_write:
            write_date(date, ideas_with_media)
        n_videos = sum(1 for _, runs in ideas_with_media if any(r['video'] for r in runs))
        all_entries.append((date, len(ideas_with_media), n_videos))

    # Main index — always reflects every date folder, even when only one was rebuilt
    (SITE / 'index.html').write_text(gen_main_index(all_entries))
    print(f'\nwrote index.html  ({len(all_entries)} dates)')


if __name__ == '__main__':
    build_all()
