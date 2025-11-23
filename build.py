#!/usr/bin/env python3
import os
import glob
import re
import json
import shutil
from datetime import datetime

import markdown
from jinja2 import Environment, FileSystemLoader
import email.utils

ROOT = os.path.dirname(__file__)
CONTENT = os.path.join(ROOT, 'content', 'posts')
TEMPLATES = os.path.join(ROOT, 'templates')
DIST = os.path.join(ROOT, 'dist')

def parse_md(path):
    text = open(path, 'r', encoding='utf-8').read()
    meta = {}
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if m:
        block, body = m.group(1), m.group(2)
        for line in block.splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                meta[k.strip()] = v.strip()
    else:
        body = text
    return meta, body

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

def build():
    # Site metadata for templates and RSS
    SITE_TITLE = 'My Blog'
    SITE_URL = 'https://renyson.github.io'
    SITE_DESCRIPTION = 'A lightweight static blog generated with a tiny builder.'

    env = Environment(loader=FileSystemLoader(TEMPLATES))
    post_t = env.get_template('post.html')
    index_t = env.get_template('index.html')

    ensure_dir(DIST)
    ensure_dir(os.path.join(DIST, 'posts'))

    posts = []
    for mdfile in glob.glob(os.path.join(CONTENT, '*.md')):
        meta, body = parse_md(mdfile)
        html = markdown.markdown(body, extensions=['fenced_code', 'codehilite'])
        title = meta.get('title', os.path.splitext(os.path.basename(mdfile))[0])
        date = meta.get('date', '')
        slug = meta.get('slug', os.path.splitext(os.path.basename(mdfile))[0])
        excerpt = meta.get('excerpt', '')

        out_html = post_t.render(title=title, date=date, content=html,
                                 site_title=SITE_TITLE, site_url=SITE_URL,
                                 excerpt=excerpt, slug=slug)
        out_path = os.path.join(DIST, 'posts', f"{slug}.html")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(out_html)

        posts.append({'title': title, 'date': date, 'slug': slug, 'excerpt': excerpt})

    # sort posts by date desc (ISO date expected)
    posts = sorted(posts, key=lambda p: p.get('date',''), reverse=True)

    index_html = index_t.render(posts=posts, site_title=SITE_TITLE, site_url=SITE_URL,
                                site_description=SITE_DESCRIPTION)
    with open(os.path.join(DIST, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)

    # copy assets
    static_src = os.path.join(ROOT, 'assets')
    static_dst = os.path.join(DIST, 'assets')
    if os.path.exists(static_dst):
        shutil.rmtree(static_dst)
    if os.path.exists(static_src):
        shutil.copytree(static_src, static_dst)

    # write posts.json for compatibility with SPA
    with open(os.path.join(DIST, 'posts.json'), 'w', encoding='utf-8') as f:
        json.dump(posts, f, indent=2)

    # Generate a simple RSS feed and a sitemap
    try:
        rss_items = []
        for p in posts:
            # parse date to RFC 2822 if possible
            try:
                dt = datetime.strptime(p.get('date',''), '%Y-%m-%d')
                pubdate = email.utils.format_datetime(dt)
            except Exception:
                pubdate = ''
            link = f"{SITE_URL}/posts/{p['slug']}.html"
            items = f"""
    <item>
      <title>{p['title']}</title>
      <link>{link}</link>
      <guid>{link}</guid>
      <pubDate>{pubdate}</pubDate>
      <description><![CDATA[{p.get('excerpt','')}]]></description>
    </item>
"""
            rss_items.append(items)

        rss = f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>{SITE_TITLE}</title>
    <link>{SITE_URL}</link>
    <description>{SITE_DESCRIPTION}</description>
    <lastBuildDate>{email.utils.format_datetime(datetime.utcnow())}</lastBuildDate>
{''.join(rss_items)}
  </channel>
</rss>
"""
        with open(os.path.join(DIST, 'rss.xml'), 'w', encoding='utf-8') as f:
            f.write(rss)

        # Generate sitemap.xml
        sitemap_items = []
        # Add the index page
        try:
            sitemap_items.append(f"  <url>\n    <loc>{SITE_URL}/</loc>\n    <lastmod>{datetime.utcnow().date().isoformat()}</lastmod>\n  </url>\n")
        except Exception:
            sitemap_items.append(f"  <url>\n    <loc>{SITE_URL}/</loc>\n  </url>\n")

        for p in posts:
            loc = f"{SITE_URL}/posts/{p['slug']}.html"
            lastmod = ''
            if p.get('date'):
                # expect YYYY-MM-DD
                lastmod = p.get('date')
            entry = f"  <url>\n    <loc>{loc}</loc>\n"
            if lastmod:
                entry += f"    <lastmod>{lastmod}</lastmod>\n"
            entry += "  </url>\n"
            sitemap_items.append(entry)

        sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{''.join(sitemap_items)}</urlset>
"""
        with open(os.path.join(DIST, 'sitemap.xml'), 'w', encoding='utf-8') as f:
            f.write(sitemap)
    except Exception as e:
        print('Could not write RSS/sitemap:', e)

    print('Build complete. Output in', DIST)

if __name__ == '__main__':
    build()
