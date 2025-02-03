import argparse
import os
import pathlib
import re
import requests
from bs4 import BeautifulSoup, ResultSet
from urllib.parse import ParseResult, urljoin, urlparse
from urllib import robotparser
from typing import Optional

USER_AGENT = "SpiderBot"
DEFAULT_DEPTH = 5
DEFAULT_PATH = './data'
EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']

total_downloads: int = 0

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='An image scraper')
    parser.add_argument('-r', '--recursive', action='store_true', help='Download images recursively')
    parser.add_argument('-l', '--level', dest='depth', type=int, help='Depth level of recursive image search')
    parser.add_argument('-p', '--path', type=pathlib.Path, help='Path to save downloaded images')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Enable verbose mode')
    parser.add_argument('URL', help='URL to download images from')
    args = parser.parse_args()
    
    if args.depth is None:
        args.depth = DEFAULT_DEPTH if args.recursive else 1
    elif args.depth and not args.recursive:
        parser.error("argument -l/--level: expected -r/--recursive argument.")
    
    if args.path is None:
        args.path = pathlib.Path(DEFAULT_PATH)
    
    return args

def create_save_directory(path: pathlib.Path) -> None:
    os.makedirs(path, exist_ok=True)
    if not os.path.isdir(path) or not os.access(path, os.W_OK):
        raise PermissionError(f'Permission denied: {path}')

def check_robots(url: str) -> None:
    path_to_check = urlparse(url).path
    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    robots_url = f"{base_url}/robots.txt"
    parser = robotparser.RobotFileParser()
    parser.set_url(robots_url)
    parser.read()
    if not parser.can_fetch(USER_AGENT, path_to_check):
        raise PermissionError(f'{robots_url} forbids access to {path_to_check}')

def get_url_content(url: str) -> bytes:
    check_robots(url)
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=5)
    response.raise_for_status()
    return response.content

def check_url(url: str) -> None:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError('Invalid URL: missing scheme or netloc')
    if parsed.scheme not in ['http', 'https']:
        raise ValueError('URL scheme must be http or https')

def validate_url(args: argparse.Namespace) -> None:
    try:
        check_url(args.URL)
    except ValueError:
        if not re.match('^[a-z]*://', args.URL):
            args.URL = 'http://' + args.URL
            validate_url(args)
        else:
            raise

def check_url_connection(args: argparse.Namespace) -> None:
    validate_url(args)
    get_url_content(args.URL)

def resolve_full_url(base_url: str, path: str) -> str:
    parsed = urlparse(path)
    if not parsed.netloc:
        return urljoin(base_url, parsed.path)
    if not parsed.scheme:
        return 'http://' + parsed.netloc + parsed.path
    return parsed.geturl()

def get_links_from_url(url: str, soup: BeautifulSoup) -> set[str]:
    urls = set()
    for tag in soup.find_all('a', href=True):
        link = resolve_full_url(url, tag['href'])
        if link and link != url and urlparse(link).netloc == urlparse(url).netloc:
            urls.add(link)
    return urls

def download_image(image_url: str, save_dir: str) -> int:
    global total_downloads
    save_path = os.path.join(save_dir, os.path.basename(image_url))
    try:
        if os.path.exists(save_path):
            return 0
        content = get_url_content(image_url)
        with open(save_path, 'wb') as f:
            f.write(content)
        total_downloads += 1
        return 1
    except Exception:
        return 0

def download_images_from_url(args: argparse.Namespace, url: str, soup: BeautifulSoup) -> None:
    for img_tag in soup.find_all('img', src=True):
        if os.path.splitext(img_tag['src'])[-1].lower() in EXTENSIONS:
            download_image(resolve_full_url(url, img_tag['src']), str(args.path))

def download_images_recursively(args: argparse.Namespace, url: str, visited_urls: set = set(), current_depth: int = 0) -> None:
    if current_depth >= args.depth or url in visited_urls:
        return
    visited_urls.add(url)
    try:
        content = get_url_content(url)
        soup = BeautifulSoup(content, 'html.parser')
        download_images_from_url(args, url, soup)
        if current_depth + 1 < args.depth:
            for link in get_links_from_url(url, soup):
                download_images_recursively(args, link, visited_urls, current_depth + 1)
    except Exception:
        pass

def scrape(args: argparse.Namespace) -> None:
    check_url_connection(args)
    create_save_directory(args.path)
    download_images_recursively(args, args.URL)
    print(f'Total images downloaded: {total_downloads}')

def main() -> None:
    args = parse_args()
    scrape(args)

if __name__ == '__main__':
    main()
