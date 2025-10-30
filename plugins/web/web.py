import requests
import time
import random
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse, urlunparse, urljoin
from io import BytesIO
from pypdf import PdfReader
from docx import Document
from odf.opendocument import load
from odf import text as odf_text, teletype
from ddgs import DDGS
import ipaddress


TIMEOUT = 30
WEB_SEARCH_MAX_RESULTS = 100
WEB_SCRAPE_COOLDOWN_TIME = 5  # Randomized between 2 and 5 seconds
WEB_SCRAPE_MAX_DEPTH = 1
WEB_SCRAPE_MAX_LINKS = 50
WEB_SCRAPE_UNSUPPORTED_CONTENT = "Unsupported content type: "
WEB_SCRAPE_UNSAFE_REDIRECT = "Unsafe web redirect detected: "
WEB_SCRAPE_INVALID_URL = "Invalid URL according to system policies."
WEB_SCRAPE_NOT_ALLOWED = "This site doesn't authorize web scraping."
HEADERS = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
REQUESTS_USER_AGENT = {"User-Agent": HEADERS}
WEB_SCRAPE_ERROR = "\n\n[ERROR] An exception occurred while trying to scrape a web page: "
WEB_SEARCH_ERROR = "\n\n[ERROR] An exception occurred while trying to do a web search: "
WEB_SCRAPE_VALIDATE_ERROR = "\n\n[ERROR] An exception occurred while trying to validate a web page: "
WEB_SCRAPE_CHECK_ALLOWED_ERROR = "\n\n[ERROR] An exception occurred while trying to check if scraping is allowed by robots.txt: "
URL_TEXT_1 = "\n\n[URL: "
URL_TEXT_2 = "]\n\n"
LINK_TEXT_1 = "\n\n[LINK: "
LINK_TEXT_2 = "]\n\n"
NAV_TAGS = {'nav', 'header', 'footer', 'aside'}
NAV_CLASSES = {'nav', 'navbar', 'sidebar', 'menu', 'footer', 'header', 'topbar', 'masthead', 'site-header', 'global-header', 'site-footer', 'bottom-nav', 'footer-container'}
ID_SUBSTRINGS = {'nav', 'sidebar', 'header', 'footer', 'menu'}
IGNORED_SUBPATHS = {
    'github.com': {'commits', 'branches', 'tags', 'pull', 'issues', 'wiki', 'actions', 'projects', 'settings', 'discussions', 'pulse', 'graphs', 'security', 'insights', 'search', 'tree', 'forks', 'watchers', 'packages', 'stargazers', 'releases', 'topics', 'activity', 'report-content'},
    'gitlab.com': {'commits', 'branches', 'tags', 'merge_requests', 'issues', 'pipelines', 'jobs', 'wiki', 'snippets', 'search', 'tree', 'forks', 'watchers', 'packages', 'stargazers', 'releases', 'topics', 'activity', 'report-content'},
}
IGNORED_FILE_ENDINGS = {'.js', '.git', '.gitignore', 'license'}
FILE_CONTENT_SEGMENTS = {'blob', 'raw'}
BLACKLISTED_DOMAINS = {'youtube.com', 'youtu.be', 'facebook.com', 'fb.com', 'instagram.com', 'tiktok.com', 'twitter.com', 'x.com', 'linkedin.com', 'vimeo.com', 'twitch.tv', 'netflix.com', 'hulu.com', 'spotify.com', 'soundcloud.com', 'pinterest.com', 'reddit.com', 'amazon.com', 'ebay.com'}
ROBOTS_CACHE_TTL = 86400 # 24 hours in seconds
ROBOTS_CACHE = {}  # Key: domain, Value: (RobotFileParser, timestamp)


last_cache_sweep = time.time()


def _is_safe(url):
    """Simple URL sanitizer to prevent SSRF/injection: allow only http/https, no local/private hosts."""
    try:
        parsed_url = urlparse(url)

        if parsed_url.scheme not in ('http', 'https') or not parsed_url.netloc:
            return False

        host = parsed_url.hostname

        if host.lower() in ('localhost', '0.0.0.0'): # noqa: S104
            return False

        try:
            ip = ipaddress.ip_address(host)

            if ip.is_private or ip.is_loopback:
                return False

        except ValueError:
            pass

        return True

    except Exception:
        return False


def _is_valid(url):
    try:
        parsed_url = urlparse(url)
        netloc = parsed_url.netloc.lower()
        path = parsed_url.path.lower()
        path_segments = path.strip('/').split('/')

        # Check blacklisted domains
        if any(blacklisted in netloc for blacklisted in BLACKLISTED_DOMAINS):
            return False

        # Ignore specific file endings
        if any(path.endswith(ending) for ending in IGNORED_FILE_ENDINGS):
            return False

        # Allow file content URLs
        if any(term in path_segments for term in FILE_CONTENT_SEGMENTS):
            return True

        # Check forbidden subpaths
        for domain, subpaths in IGNORED_SUBPATHS.items():
            if domain in netloc:
                for segment in path_segments:
                    if segment in subpaths:
                        return False
                break

        return True

    except Exception as e:
        print(WEB_SCRAPE_VALIDATE_ERROR + str(e))
        return False


def _is_scraping_allowed(url):
    """Check if scraping is allowed by robots.txt, with domain caching, TTL, and periodic full-cache sweep"""
    try:
        global last_cache_sweep

        parsed_url = urlparse(url)
        domain_key = parsed_url.scheme + "://" + parsed_url.netloc
        current_time = time.time()

        # Full cache sweep
        if current_time - last_cache_sweep >= ROBOTS_CACHE_TTL:
            expired_keys = []

            # Get expired keys
            for key, (parser, timestamp) in ROBOTS_CACHE.items():
                if current_time - timestamp >= ROBOTS_CACHE_TTL:
                    expired_keys.append(key)

            # Delete expired keys
            for expired_key in expired_keys:
                del ROBOTS_CACHE[expired_key]

            last_cache_sweep = current_time

        # Check cache for current URL
        if domain_key in ROBOTS_CACHE:
            parser, timestamp = ROBOTS_CACHE[domain_key]

            if current_time - timestamp < ROBOTS_CACHE_TTL:
                return parser.can_fetch("*", url)

        # Fetch current robots.txt if cache doesn't contain a recent version
        url_components = (parsed_url.scheme, parsed_url.netloc, '/robots.txt', '', '', '')
        robots_url = urlunparse(url_components)
        robot_file_parser = RobotFileParser()
        robot_file_parser.set_url(robots_url)
        robot_file_parser.read()

        # Update cache with new timestamp
        ROBOTS_CACHE[domain_key] = (robot_file_parser, current_time)

        return robot_file_parser.can_fetch("*", url)

    except Exception as e:
        print(WEB_SCRAPE_CHECK_ALLOWED_ERROR + str(e))
        return False


def _scrape_html(html):
    """Extract text from HTML"""
    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.extract()

        # Remove navigational elements
        for tag in soup.find_all(lambda t: t.name in NAV_TAGS or any(cls in NAV_CLASSES for cls in t.get('class', [])) or any(sub in t.get('id', '').lower() for sub in ID_SUBSTRINGS)):
            tag.extract()

        # Extract text
        text = soup.get_text(separator = '\n', strip = True)

        return text

    except Exception as e:
        print(WEB_SCRAPE_ERROR + str(e))
        return ""


def _normalize_url(url):
    try:
        # Normalize url by removing fragment and converting blob to raw
        parsed_url = urlparse(url)
        normalized_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params, parsed_url.query, ''))

        # Normalize GitHub URLs
        if 'github.com' in parsed_url.netloc.lower() and 'blob' in parsed_url.path.lower():
            normalized_url = urlunparse((parsed_url.scheme, 'raw.githubusercontent.com', parsed_url.path.replace('/blob/', '/'), '', parsed_url.query, ''))

        # Normalize GitLab URLs
        elif 'gitlab.com' in parsed_url.netloc.lower() and 'blob' in parsed_url.path.lower():
            normalized_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path.replace('/-/blob/', '/-/raw/'), parsed_url.params, parsed_url.query, ''))

        return normalized_url

    except Exception as e:
        print(WEB_SCRAPE_ERROR + str(e))
        return url


def _scrape_links(html, url, scraped_urls):
    """Extract links from HTML, avoiding nav elements and ignored sublinks"""
    links = []

    try:
        soup = BeautifulSoup(html, 'html.parser')

        for a in soup.find_all('a', href = True):
            if any(
                ancestor.name in NAV_TAGS or
                any(cls in NAV_CLASSES for cls in ancestor.get('class', [])) or
                any(sub in ancestor.get('id', '').lower() for sub in ID_SUBSTRINGS)
                for ancestor in a.parents
            ):
                continue

            link = urljoin(url, a['href'].strip())

            # Normalize link
            link = _normalize_url(link)

            if link and link not in scraped_urls and not _check_url(link):
                links.append(link)

        # Randomize order
        random.shuffle(links)

        return links[:WEB_SCRAPE_MAX_LINKS]

    except Exception as e:
        print(WEB_SCRAPE_ERROR + str(e))
        return []


def _scrape_pdf(content):
    """Extract text from PDF"""
    try:
        # Scrape document
        with BytesIO(content) as f:
            reader = PdfReader(f)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)

            return text

    except Exception as e:
        print(WEB_SCRAPE_ERROR + str(e))
        return ""


def _scrape_doc(content):
    """Extract text from DOCX"""
    try:
        # Scrape document
        document = Document(BytesIO(content))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)

        return text

    except Exception as e:
        print(WEB_SCRAPE_ERROR + str(e))
        return ""


def _scrape_odt(content):
    """Extract text from ODT"""
    try:
        # Scrape document
        odt_file = load(BytesIO(content))
        all_paragraphs = odt_file.getElementsByType(odf_text.P)
        text = "\n".join(teletype.extractText(p) for p in all_paragraphs)

        return text

    except Exception as e:
        print(WEB_SCRAPE_ERROR + str(e))
        return ""


def _check_url(url):
    """Validate URL for safety, scraping permissions, and subpath policies."""
    error = ""

    if not _is_safe(url):
        error = WEB_SCRAPE_UNSAFE_REDIRECT + url
    elif not _is_scraping_allowed(url):
        error = WEB_SCRAPE_NOT_ALLOWED
    elif not _is_valid(url):
        error = WEB_SCRAPE_INVALID_URL

    return error.strip()


def scrape(url, depth = 0, scraped_urls = None):
    """Scrape a URL and its sublinks"""
    try:
        text = ""
        links = []
        is_root = True

        if depth > 0:
            is_root = False

        if scraped_urls is None:
            scraped_urls = set()

        url = _normalize_url(url)

        if not _is_safe(url) or not _is_valid(url) or url in scraped_urls:
            return ""

        scraped_urls.add(url)

        # Check redirects
        try:
            head_response = requests.head(url, headers = REQUESTS_USER_AGENT, timeout = TIMEOUT)
            error = _check_url(head_response.url)

            if error:
                return error

        except Exception:
            return ""

        # Fetch web page
        response = requests.get(url, headers = REQUESTS_USER_AGENT, timeout = TIMEOUT)
        response.raise_for_status()

        error = _check_url(response.url)

        if error:
            return error

        content_type = response.headers.get('Content-Type', '')

        time.sleep(random.uniform(2, WEB_SCRAPE_COOLDOWN_TIME)) # noqa: S311

        if 'text/html' in content_type:
            text = _scrape_html(response.text)

            if depth < WEB_SCRAPE_MAX_DEPTH:
                links = _scrape_links(response.text, url, scraped_urls)

        elif 'text/plain' in content_type:
            text = response.text

        elif 'application/pdf' in content_type:
            text = _scrape_pdf(response.content)

        elif 'application/msword' in content_type or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
            text = _scrape_doc(response.content)

        elif 'application/vnd.oasis.opendocument.text' in content_type:
            text = _scrape_odt(response.content)

        else:
            text = WEB_SCRAPE_UNSUPPORTED_CONTENT + content_type

        for link in links:
            sub_text = scrape(link, depth + 1, scraped_urls)

            if sub_text:
                text += LINK_TEXT_1 + link + LINK_TEXT_2 + sub_text

        if text and is_root:
            text = URL_TEXT_1 + url + URL_TEXT_2 + text

        return text.strip()

    except HTTPError:
        return ""

    except Exception as e:
        print(WEB_SCRAPE_ERROR + str(e))
        return ""


def search(query, max_urls):
    """Search the web using DuckDuckGo"""
    urlArray = []

    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results = WEB_SEARCH_MAX_RESULTS)

            for result in results:
                if not _check_url(result['href']):
                    urlArray.append(result['href'])

        return urlArray[:max_urls]

    except Exception as e:
        print(WEB_SEARCH_ERROR + str(e))
        return []


