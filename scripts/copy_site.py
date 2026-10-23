"""Snapshot public pages and assets; never sends forms to the original site."""
import hashlib
import json
import re
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

BASE = 'https://abnequipamentos.com.br/'
ROOT = Path(__file__).resolve().parents[1] / 'mirror'
ASSETS = ROOT / 'assets'
PAGES = ROOT / 'pages'
assets = {}
failures = []


def decode_emails(soup):
    for tag in soup.select('[data-cfemail]'):
        encoded = bytes.fromhex(tag['data-cfemail'])
        email = ''.join(chr(value ^ encoded[0]) for value in encoded[1:])
        tag.string = email
        link = tag if tag.name == 'a' else tag.find_parent('a')
        if link:
            link['href'] = 'mailto:' + email
        del tag['data-cfemail']


def asset(url):
    if not url.startswith(('http://', 'https://')):
        return url
    if url not in assets:
        suffix = Path(urlsplit(url).path).suffix[:10]
        assets[url] = hashlib.sha256(url.encode()).hexdigest()[:24] + suffix
    return '/mirror-assets/' + assets[url]


def css_urls(text, base):
    return re.sub(r'url\(\s*([\"\']?)([^)\"\']+)\1\s*\)',
                  lambda m: 'url("' + asset(urljoin(base, m[2].strip())) + '")', text)


def fetch(url):
    response = requests.get(url, timeout=40)
    response.raise_for_status()
    return response


def download(item):
    url, filename = item
    try:
        response = fetch(url)
        return url, filename, response.content, response.headers.get('Content-Type', '')
    except requests.RequestException as error:
        return url, filename, None, str(error)


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    PAGES.mkdir(parents=True, exist_ok=True)
    queue, visited, mapping = deque([BASE]), set(), {}
    while queue and len(visited) < 60:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        try:
            response = fetch(url)
            if 'text/html' not in response.headers.get('Content-Type', ''):
                continue
        except requests.RequestException as error:
            failures.append({'url': url, 'error': str(error)})
            continue
        soup = BeautifulSoup(response.content, 'html.parser')
        decode_emails(soup)
        for tag in soup.select('script'):
            src = tag.get('src', '')
            if (src and ('/wp-content/themes/' in src or '/wp-includes/js/jquery/' in src or
                         'unpkg.com/aos' in src or 'cdn.jsdelivr.net/npm/@popperjs' in src)):
                continue
            if src or any(word in tag.get_text() for word in ('gtag', 'googletagmanager', 'wpcf7', 'cmplz', 'wp-emoji')):
                tag.decompose()
        for tag in soup.select('link'):
            if not set(tag.get('rel', [])).intersection({'stylesheet', 'icon', 'apple-touch-icon'}):
                tag.decompose()
        for tag in soup.select('iframe, .wpcf7, #cmplz-cookiebanner-container, .cmplz-cookiebanner, .cmplz-manage-consent'):
            tag.decompose()
        for form in soup.select('form'):
            notice = soup.new_tag('p')
            notice.string = 'Ambiente de testes: envio de formulários desativado.'
            form.replace_with(notice)
        for tag in soup.find_all(True):
            for attr in ('src', 'poster', 'data-src', 'data-background'):
                if tag.get(attr):
                    tag[attr] = asset(urljoin(url, tag[attr]))
            if tag.get('srcset'):
                tag['srcset'] = ', '.join(asset(urljoin(url, part.strip().split()[0])) +
                                         (' ' + ' '.join(part.strip().split()[1:]) if len(part.strip().split()) > 1 else '')
                                         for part in tag['srcset'].split(',') if part.strip())
            if tag.name == 'link' and tag.get('href'):
                tag['href'] = asset(urljoin(url, tag['href']))
            if tag.get('style'):
                tag['style'] = css_urls(tag['style'], url)
            if tag.name == 'style' and tag.string:
                tag.string = css_urls(tag.string, url)
        for link in soup.select('a[href]'):
            target = urljoin(url, link['href'])
            parsed = urlsplit(target)
            if parsed.netloc == urlsplit(BASE).netloc:
                if parsed.path.startswith(('/wp-', '/feed', '/comments', '/xmlrpc')):
                    link['href'] = asset(target) if Path(parsed.path).suffix in {'.pdf', '.jpg', '.png', '.svg', '.webp'} else '#'
                    continue
                clean = BASE.rstrip('/') + (parsed.path or '/')
                if not parsed.query and clean not in visited:
                    queue.append(clean)
                link['href'] = (parsed.path or '/') + ('#' + parsed.fragment if parsed.fragment else '')
        contact_item = soup.select_one('li#menu-item-145')
        if contact_item and not soup.select_one('li#menu-item-fornecedores'):
            supplier_item = soup.new_tag('li', id='menu-item-fornecedores')
            supplier_item['class'] = ['menu-item', 'menu-item-type-post_type', 'menu-item-object-page']
            supplier_link = soup.new_tag('a', href='/fornecedores/')
            supplier_link.string = 'Avaliação de fornecedores'
            supplier_item.append(supplier_link)
            contact_item.insert_after(supplier_item)
        filename = hashlib.sha256(urlsplit(url).path.encode()).hexdigest()[:20] + '.html'
        (PAGES / filename).write_text(str(soup), encoding='utf-8')
        mapping[urlsplit(url).path] = filename
    completed = set()
    types = {}
    while pending := [(url, name) for url, name in assets.items() if url not in completed]:
        with ThreadPoolExecutor(max_workers=8) as pool:
            for url, filename, data, content_type in pool.map(download, pending):
                completed.add(url)
                if data is None:
                    failures.append({'url': url, 'error': content_type})
                    continue
                types[filename] = content_type.split(';')[0]
                if 'text/css' in content_type or filename.endswith('.css'):
                    data = css_urls(data.decode('utf-8', errors='replace'), url).encode('utf-8')
                (ASSETS / filename).write_bytes(data)
    (ROOT / 'pages.json').write_text(json.dumps(mapping, indent=2), encoding='utf-8')
    (ROOT / 'asset-types.json').write_text(json.dumps(types, indent=2), encoding='utf-8')
    (ROOT / 'report.json').write_text(json.dumps({'source': BASE, 'pages': len(mapping), 'assets': len(completed), 'failures': failures}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Copied {len(mapping)} pages and {len(completed)} assets. Failures: {len(failures)}')


if __name__ == '__main__':
    main()
