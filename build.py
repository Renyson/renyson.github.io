#!/usr/bin/env python3
import os
import glob
import re
import json
import shutil
from datetime import datetime

import markdown
from jinja2 import Environment, FileSystemLoader

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

        out_html = post_t.render(title=title, date=date, content=html)
        out_path = os.path.join(DIST, 'posts', f"{slug}.html")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(out_html)

        posts.append({'title': title, 'date': date, 'slug': slug, 'excerpt': excerpt})

    # sort posts by date desc (ISO date expected)
    posts = sorted(posts, key=lambda p: p.get('date',''), reverse=True)

    index_html = index_t.render(posts=posts)
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

    print('Build complete. Output in', DIST)

if __name__ == '__main__':
    build()
