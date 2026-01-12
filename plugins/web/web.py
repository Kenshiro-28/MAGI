# mypy: ignore-errors
import os
import re
import stat
import time
import random
import multiprocessing as mp
import socket
import ipaddress
import resource
import signal
import traceback
import tempfile
from dataclasses import dataclass
from typing import Any

from urllib.parse import urlparse, urlunparse, urljoin, urlsplit, urlunsplit, quote, unquote
from io import BytesIO

from ddgs import DDGS

import pycurl
from protego import Protego  # robots.txt parser


TIMEOUT = 120
WEB_SEARCH_MAX_RESULTS = 100
WEB_SCRAPE_MAX_COOLDOWN_TIME = 5  # Randomized between this minus 3 seconds
WEB_SCRAPE_MAX_DEPTH = 1
WEB_SCRAPE_MAX_LINKS = 10
WEB_SCRAPE_MAX_REDIRECTS = 5

WEB_SCRAPE_UNSUPPORTED_CONTENT = "Unsupported content type: "
WEB_SCRAPE_UNSAFE_URL = "Unsafe URL detected: "
WEB_SCRAPE_INVALID_URL = "Invalid URL according to system policies."
WEB_SCRAPE_NOT_ALLOWED = "This site doesn't authorize web scraping."
USER_AGENT = "Mozilla/5.0 (compatible; MAGI)"
WEB_SCRAPE_ERROR = "\n\n[ERROR] An exception occurred while trying to scrape a web page: "
WEB_SEARCH_ERROR = "\n\n[ERROR] An exception occurred while trying to do a web search: "
WEB_SCRAPE_VALIDATE_ERROR = "\n\n[ERROR] An exception occurred while trying to validate a web page: "
WEB_SCRAPE_CHECK_ALLOWED_ERROR = "\n\n[ERROR] An exception occurred while trying to check if scraping is allowed by robots.txt: "
SCRAPE_WALL_TIME_ERROR = "\n\n[ERROR] Scrape wall budget exceeded."
URL_TEXT_1 = "[URL: "
URL_TEXT_2 = "]\n\n"
LINK_TEXT_1 = "\n\n[LINK: "
LINK_TEXT_2 = "]\n\n"
NAV_TAGS = {'nav', 'header', 'footer', 'aside'}
NAV_CLASSES = {'nav', 'navbar', 'sidebar', 'menu', 'footer', 'header', 'topbar', 'masthead', 'site-header', 'global-header', 'site-footer', 'bottom-nav', 'footer-container'}
ID_SUBSTRINGS = {'nav', 'sidebar', 'header', 'footer', 'menu'}
IGNORED_SUBPATHS = {
    "github.com": {
        "commits",
        "branches",
        "tags",
        "pull",
        "issues",
        "wiki",
        "actions",
        "projects",
        "settings",
        "discussions",
        "pulse",
        "graphs",
        "security",
        "insights",
        "search",
        "tree",
        "forks",
        "watchers",
        "packages",
        "stargazers",
        "releases",
        "topics",
        "activity",
        "report-content",
    },
    "gitlab.com": {
        "commits",
        "branches",
        "tags",
        "merge_requests",
        "issues",
        "pipelines",
        "jobs",
        "wiki",
        "snippets",
        "search",
        "tree",
        "forks",
        "watchers",
        "packages",
        "stargazers",
        "releases",
        "topics",
        "activity",
        "report-content",
    },
}
IGNORED_FILE_ENDINGS = {".js", ".git", ".gitignore", "license"}

BLACKLISTED_DOMAINS = {
    "youtube.com",
    "youtu.be",
    "facebook.com",
    "fb.com",
    "instagram.com",
    "tiktok.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "vimeo.com",
    "twitch.tv",
    "netflix.com",
    "hulu.com",
    "spotify.com",
    "soundcloud.com",
    "pinterest.com",
    "reddit.com",
    "amazon.com",
    "ebay.com",
}

WIKIPEDIA_NAMESPACE_PREFIXES = (
    "File:", "Category:", "Template:", "Template_talk:", "Help:", "Wikipedia:",
    "Special:", "Talk:", "User:", "User_talk:", "Portal:", "Draft:", "Book:",
    "MediaWiki:", "TimedText:", "Module:", "Gadget:", "Gadget_definition:", "Topic:",
)

WIKIPEDIA_JUNK_TEXT_SELECTORS = (
    "table.infobox",
    "table.navbox",
    "div.navbox",
    "div#toc",
    "span.mw-editsection",
    "sup.reference",
    "ol.references",
    "div.reflist",
    "div.catlinks",
    "div.mw-authority-control",
    "div.printfooter",
    "div.shortdescription",
    "div.hatnote",
    "div.metadata",
)

WIKIPEDIA_JUNK_LINK_SELECTORS = (
    "table.navbox",
    "div.navbox",
    "div#toc",
    "span.mw-editsection",
    "sup.reference",
    "ol.references",
    "div.reflist",
    "div.catlinks",
    "div.mw-authority-control",
    "div.printfooter",
    "div.metadata",
)

WIKIPEDIA_STOP_HEADINGS = {
    "see also", "references", "external links", "further reading",
    "notes", "bibliography", "sources", "works cited"
}

BLOCK_TAGS = ("h1","h2","h3","h4","h5","h6","p","li","blockquote","pre")

URL_PATH_SAFE = "/:@-._~!$&'()*+,;=%"
URL_QUERY_SAFE = "/?:@-._~!$&'()*+,;=%=&"
BAD_PERCENT = re.compile(r"%(?![0-9A-Fa-f]{2})")

ROBOTS_DIRECTIVE_SPLIT = re.compile(
    r"\s+(?=(?:user-agent|disallow|allow|sitemap|crawl-delay|host)\s*:)",
    re.IGNORECASE,
)

ROBOTS_CACHE_TTL = 86400  # 24 hours
ROBOTS_CACHE: dict[str, tuple[Protego, float]] = {}  # domain_key -> (protego_parser, timestamp)
ROBOTS_MAX_BYTES = 256 * 1024  # 256 KiB cap for robots.txt

FETCH_MAX_BYTES = 100 * 1024 * 1024         # 100 MiB
PARSE_MAX_VMEM_BYTES = 1024 * 1024 * 1024   # 1 GiB
CURL_CHILD_VMEM_BYTES = 1024 * 1024 * 1024  # 1 GiB
MAX_TOTAL_TEXT_CHARS = 1_000_000            # ~333 “book pages” at ~3000 chars/page

CHILD_GRACE_SECONDS = 3        # seconds
MAX_PINNED_IP_TRIES = 4
MAX_FETCH_WALL_SECONDS = 90    # seconds per _fetch_url
HEADER_MAX_BYTES = 128 * 1024  # 128 KiB header bomb cap
LOW_SPEED_LIMIT = 1024         # bytes/sec
LOW_SPEED_TIME = 10            # seconds
SCRAPE_WALL_SECONDS = 300      # seconds
DNS_TIMEOUT = 8                # seconds

IPC_INLINE_BYTES = 1024 * 1024  # 1 MiB: bodies bigger than this spill to /tmp to avoid huge Pipe payloads

# NAT64 Well-Known Prefix (WKP). If DNS64 is in play, getaddrinfo can return these.
IPV6_NAT64_WKP = ipaddress.ip_network("64:ff9b::/96")

TMP_PREFIX = "magi_fetch_"
TMP_SUFFIX = ".bin"
TMP_SWEEP_INTERVAL = 60   # seconds (rate limit)
TMP_MAX_AGE = 3600        # seconds (delete files older than this)
TMP_SWEEP_LIMIT = 200     # max deletions per sweep

HTML_LINKS_MAX_BYTES = 2 * 1024 * 1024  # 2 MiB cap for link-extraction HTML
PLAIN_MAX_BYTES = min(FETCH_MAX_BYTES, MAX_TOTAL_TEXT_CHARS * 4)  # ~4 MiB

PROTEGO_UA_FIRST: bool | None = None

_last_tmp_sweep = 0.0
_scrape_deadlines: dict[int, float] = {}  # id(scraped_urls_set) -> monotonic deadline


@dataclass
class ResponseData:
    url: str
    status_code: int
    headers: dict[str, str]
    text: str
    content: bytes
    content_path: str | None = None


def _detect_protego_ua_first() -> bool:
    """
    Detect Protego can_fetch calling convention safely.
    Some versions expect (UA, URL), others (URL, UA).
    This function must NEVER raise; default to url-first.
    """
    rp = Protego.parse("User-agent: *\nDisallow: /private\nAllow: /\n")
    ua = "TestUA"
    priv = "http://example.com/private"
    root = "http://example.com/"

    try:
        ua_first_ok = (rp.can_fetch(ua, priv) is False) and (rp.can_fetch(ua, root) is True)
    except Exception:
        ua_first_ok = False

    try:
        url_first_ok = (rp.can_fetch(priv, ua) is False) and (rp.can_fetch(root, ua) is True)
    except Exception:
        url_first_ok = False

    if ua_first_ok and not url_first_ok:
        return True
    if url_first_ok and not ua_first_ok:
        return False

    # Safe default: url-first (your existing default)
    return False


def _protego_can_fetch(rp: Protego, url: str) -> bool:
    global PROTEGO_UA_FIRST

    if PROTEGO_UA_FIRST is None:
        PROTEGO_UA_FIRST = _detect_protego_ua_first()

    try:
        if PROTEGO_UA_FIRST:
            return bool(rp.can_fetch(USER_AGENT, url))
        return bool(rp.can_fetch(url, USER_AGENT))
    except Exception:
        # Last-ditch fallback: try the other order
        try:
            return bool(rp.can_fetch(USER_AGENT, url))
        except Exception:
            return False


def _normalize_robots_text(txt: str) -> str:
    if not txt:
        return ""
    if "\n" in txt or "\r" in txt:
        return txt.replace("\r\n", "\n").replace("\r", "\n").strip()

    low = txt.lower()
    if ("user-agent:" in low) or ("disallow:" in low) or ("allow:" in low) or ("sitemap:" in low):
        txt = txt.replace("\t", " ")
        txt = re.sub(r" +", " ", txt).strip()
        txt = ROBOTS_DIRECTIVE_SPLIT.sub("\n", txt)
    return txt.strip()


def _spill_to_tmp(data: bytes) -> str:
    # include PID to reduce collisions + make debugging easier
    fd, path = tempfile.mkstemp(prefix=f"{TMP_PREFIX}{os.getpid()}_", suffix=TMP_SUFFIX, dir="/tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        return path
    except Exception:
        try:
            os.close(fd)
        except Exception:
            pass
        try:
            os.unlink(path)
        except Exception:
            pass
        raise


def _cleanup_stale_tmp_files(now: float | None = None) -> None:
    global _last_tmp_sweep
    now = time.time() if now is None else now

    if now - _last_tmp_sweep < TMP_SWEEP_INTERVAL:
        return
    _last_tmp_sweep = now

    uid = os.getuid()

    try:
        candidates: list[tuple[float, str]] = []

        with os.scandir("/tmp") as it:
            for ent in it:
                name = ent.name
                if not (name.startswith(TMP_PREFIX) and name.endswith(TMP_SUFFIX)):
                    continue

                try:
                    st = ent.stat(follow_symlinks=False)
                except FileNotFoundError:
                    continue
                except Exception:
                    continue

                # Only touch our own regular files
                if st.st_uid != uid:
                    continue
                if not stat.S_ISREG(st.st_mode):
                    continue
                if st.st_nlink != 1:
                    continue

                age = now - float(st.st_mtime)
                if age >= TMP_MAX_AGE:
                    candidates.append((float(st.st_mtime), ent.path))

        candidates.sort(key=lambda x: x[0])
        for _, path in candidates[:TMP_SWEEP_LIMIT]:
            _cleanup_file(path)

    except Exception:
        pass


def _read_file_bytes(path: str, max_bytes: int) -> bytes:
    # Read up to max_bytes (no surprises)
    with open(path, "rb") as f:
        return f.read(max_bytes)


def _peek_file_bytes(path: str, n: int) -> bytes:
    with open(path, "rb") as f:
        return f.read(n)


def _cleanup_file(path: str | None) -> None:
    if not path:
        return
    try:
        os.unlink(path)
    except Exception:
        pass


def _remaining(deadline: float, cap: int = TIMEOUT) -> int:
    # Leave a bit of slack for child grace + small overhead.
    slack = CHILD_GRACE_SECONDS + 1
    return max(1, min(cap, int(deadline - time.monotonic() - slack)))


def _ip_is_globally_routable(ip: ipaddress._BaseAddress) -> bool:
    if not ip.is_global:
        return False
    if ip.is_reserved:
        return False
    if ip.version == 6 and ip in IPV6_NAT64_WKP:
        return False
    return True


def _canon_host(host: str) -> str:
    host = (host or "").strip().lower().rstrip(".")
    try:
        host = host.encode("idna").decode("ascii")
    except Exception:
        pass
    return host


def _cap_total(text: str) -> str:
    if len(text) > MAX_TOTAL_TEXT_CHARS:
        return text[:MAX_TOTAL_TEXT_CHARS]
    return text


def _do_curl_request_child(method, url, host_ascii, port, ip, max_bytes, timeout, conn) -> None:
    resp: ResponseData | None = None
    try:
        resp = _curl_request_once(
            method,
            url,
            host_ascii=host_ascii,
            port=port,
            ip=ip,
            max_bytes=max_bytes,
            timeout=timeout,
        )

        ok = _safe_send(conn, ("ok", resp))
        if not ok:
            # Parent won't learn the path → avoid leaking temp file
            _cleanup_file(getattr(resp, "content_path", None))

    except Exception:
        # If we already spilled before failing, clean it up.
        if resp is not None:
            _cleanup_file(getattr(resp, "content_path", None))

        _safe_send(conn, ("err", traceback.format_exc()))
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _check_scrape_deadline(deadline: float) -> None:
    if time.monotonic() >= deadline:
        raise TimeoutError(SCRAPE_WALL_TIME_ERROR)


def _sleep_with_deadline(deadline: float) -> None:
    # Random politeness delay, but never exceed remaining wall budget
    sleep_for = random.uniform(max(0.0, WEB_SCRAPE_MAX_COOLDOWN_TIME - 3.0), WEB_SCRAPE_MAX_COOLDOWN_TIME)  # noqa: S311
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError(SCRAPE_WALL_TIME_ERROR)
    if sleep_for > 0:
        time.sleep(min(sleep_for, remaining))


def _safe_send(conn, msg) -> bool:
    try:
        conn.send(msg)
        return True
    except Exception:
        return False


def _fix_bad_percents(s: str) -> str:
    # Encode any '%' that is not the start of a valid %HH escape
    s = s or ""
    return BAD_PERCENT.sub("%25", s)


def _curl_safe_url(u: str) -> str:
    s = urlsplit(u)

    if s.username or s.password:
        return u

    host = s.hostname or ""
    try:
        host_ascii = host.encode("idna").decode("ascii")
    except Exception:
        host_ascii = host

    # port can raise ValueError for netloc like ":abc"
    try:
        port = s.port
    except ValueError:
        return u  # keep as-is; upstream validators should reject anyway

    if ":" in host_ascii and not host_ascii.startswith("["):
        host_for_netloc = f"[{host_ascii}]"
    else:
        host_for_netloc = host_ascii

    if port is not None:
        netloc = f"{host_for_netloc}:{int(port)}"
    else:
        netloc = host_for_netloc

    path = quote(_fix_bad_percents(s.path), safe=URL_PATH_SAFE)
    query = quote(_fix_bad_percents(s.query), safe=URL_QUERY_SAFE)

    return urlunsplit((s.scheme.lower(), netloc, path, query, ""))


def _check_url_for_search(url: str) -> str:
    try:
        p = urlparse(url)
        scheme = (p.scheme or "").lower()
        if scheme not in ("http", "https") or not p.netloc:
            return WEB_SCRAPE_INVALID_URL

        if p.username or p.password:
            return WEB_SCRAPE_UNSAFE_URL + url

        host = _canon_host(p.hostname or "")

        try:
            ip_lit = ipaddress.ip_address(host)
            if not _ip_is_globally_routable(ip_lit):
                return WEB_SCRAPE_UNSAFE_URL + url
        except ValueError:
            pass

        if host in ("", "localhost", "0.0.0.0", "::", "::1"):
            return WEB_SCRAPE_UNSAFE_URL + url

        # bad/garbage port
        try:
            port = p.port
        except ValueError:
            return WEB_SCRAPE_INVALID_URL
        if port is not None and (port <= 0 or port > 65535):
            return WEB_SCRAPE_INVALID_URL

        if not _is_valid(url):
            return WEB_SCRAPE_INVALID_URL

        return ""

    except Exception:
        return WEB_SCRAPE_INVALID_URL


def _robots_domain_key(url: str) -> str:
    p = urlparse(url)
    scheme = (p.scheme or "").lower()
    host = _canon_host(p.hostname or "")

    # Normalize default ports so :443 / :80 don't create separate cache entries
    try:
        port = p.port
    except ValueError:
        port = None

    if port is None:
        port = 443 if scheme == "https" else 80

    is_default = (scheme == "https" and port == 443) or (scheme == "http" and port == 80)
    netloc = host if is_default else f"{host}:{int(port)}"
    return f"{scheme}://{netloc}"


def _wikipedia_truncate_after_stop_sections(container) -> None:
    # Wikipedia headings are usually h2/h3 within mw-parser-output
    for h in container.find_all(["h2", "h3"]):
        title = h.get_text(" ", strip=True).lower()
        if any(title.startswith(h) for h in WIKIPEDIA_STOP_HEADINGS):
            # remove the heading and everything after it (siblings)
            node = h
            while node is not None:
                nxt = node.next_sibling
                try:
                    node.extract()
                except Exception:
                    pass
                node = nxt
            break


def _strip_wikipedia_pronunciation(content) -> None:
    # Wikipedia pronunciation/IPA bits
    for sel in ("span.IPA", "span.ext-phonos", "span.reference", "sup.reference"):
        for t in content.select(sel):
            t.extract()


def _extract_block_text(root) -> str:
    parts: list[str] = []
    for el in root.find_all(BLOCK_TAGS):
        if el.find_parent(BLOCK_TAGS):
            continue  # avoid nested duplicates
        s = el.get_text(" ", strip=True)
        if s:
            parts.append(s)

    text = "\n".join(parts) if parts else root.get_text(" ", strip=True)

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def _wikipedia_article_link_ok(base_url: str, candidate_raw: str) -> bool:
    try:
        base = urlparse(base_url)
        p = urlparse(candidate_raw)

        # same host only (en.wikipedia.org -> en.wikipedia.org)
        if _canon_host(p.hostname or "") != _canon_host(base.hostname or ""):
            return False

        # must be /wiki/<Title>
        if not (p.path or "").startswith("/wiki/"):
            return False

        title = (p.path or "")[len("/wiki/"):]
        if not title:
            return False

        title_dec = unquote(title).lower()

        # drop namespaces (Category:, File:, Special:, etc.) (case-insensitive)
        if any(title_dec.startswith(ns.lower()) for ns in WIKIPEDIA_NAMESPACE_PREFIXES):
            return False

        q = (p.query or "").lower()
        # drop junk query links (edit/history/diff/redlinks)
        if any(k in q for k in ("action=", "oldid=", "diff=", "redlink=1")):
            return False

        return True
    except Exception:
        return False


def _is_wikipedia_url(u: str) -> bool:
    try:
        host = (urlparse(u).hostname or "").lower()
        return _host_is(host, "wikipedia.org")
    except Exception:
        return False


def _extract_text_from_html(html: str | bytes, base_url: str = "") -> str:
    """
    Convert HTML -> text.
    If base_url is Wikipedia, extract the main article body and drop common junk blocks.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html or b"", "html.parser")

    # Remove scripts/styles early
    for t in soup(["script", "style", "noscript"]):
        t.extract()

    if _is_wikipedia_url(base_url):
        # Main article container
        content = soup.select_one("#mw-content-text .mw-parser-output") or soup.select_one("#mw-content-text")
        if content is None:
            content = soup.body or soup

        # Remove small noisy bits first
        _strip_wikipedia_pronunciation(content)

        # Remove typical Wikipedia “junk” blocks
        for sel in WIKIPEDIA_JUNK_TEXT_SELECTORS:
            for t in content.select(sel):
                t.extract()

        # Remove remaining nav-ish stuff inside content by your generic heuristics
        for tag in content.find_all(
            lambda t: (
                t.name in NAV_TAGS
                or any(cls in NAV_CLASSES for cls in t.get("class", []))
                or any(sub in t.get("id", "").lower() for sub in ID_SUBSTRINGS)
            )
        ):
            tag.extract()

        # HARD STOP after "See also", "References", etc.
        _wikipedia_truncate_after_stop_sections(content)

        return _extract_block_text(content)

    # Generic non-wiki HTML cleaning
    for tag in soup.find_all(
        lambda t: (
            t.name in NAV_TAGS
            or any(cls in NAV_CLASSES for cls in t.get("class", []))
            or any(sub in t.get("id", "").lower() for sub in ID_SUBSTRINGS)
        )
    ):
        tag.extract()

    return _extract_block_text(soup)


def _kill_process(p: mp.Process) -> None:
    if not p.is_alive():
        try:
            p.join(timeout=0)
        except Exception:
            pass
        return

    pid = p.pid
    pgid = None
    try:
        if pid is not None:
            pgid = os.getpgid(pid)
    except Exception:
        pgid = None

    parent_pgrp = None
    try:
        parent_pgrp = os.getpgrp()
    except Exception:
        parent_pgrp = None

    # Only kill the process group if we *know* it's not ours.
    can_killpg = (pgid is not None) and (parent_pgrp is not None) and (pgid != parent_pgrp)

    try:
        if can_killpg:
            os.killpg(pgid, signal.SIGTERM)
        else:
            p.terminate()
    except Exception:
        pass

    p.join(1)

    if p.is_alive():
        try:
            if can_killpg:
                os.killpg(pgid, signal.SIGKILL)
            else:
                p.kill()
        except Exception:
            pass
        p.join(1)


def _child_bootstrap(fn, args: tuple, conn, vmem_limit: int | None = None) -> None:
    try:
        os.setsid()
    except Exception:
        pass

    try:
        import ctypes
        PR_SET_PDEATHSIG = 1
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        libc.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
        libc.prctl.restype = ctypes.c_int
        libc.prctl(PR_SET_PDEATHSIG, signal.SIGKILL, 0, 0, 0)
        if os.getppid() == 1:
            os._exit(1)
    except Exception:
        pass

    # Apply limits
    try:
        if vmem_limit is not None:
            resource.setrlimit(resource.RLIMIT_AS, (vmem_limit, vmem_limit))

        timeout = TIMEOUT + CHILD_GRACE_SECONDS
        resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    except Exception:
        pass

    fn(*args, conn)


def _link_candidate_ok(url: str) -> bool:
    """Cheap/safe checks for link extraction (no DNS, no robots)."""
    try:
        p = urlparse(url)
        scheme = (p.scheme or "").lower()
        if scheme not in ("http", "https") or not p.netloc:
            return False

        # block userinfo
        if p.username or p.password:
            return False

        host = _canon_host(p.hostname or "")

        if not host:
            return False
        if host in ("localhost", "0.0.0.0", "::", "::1"):
            return False

        # reject non-global IP literals (SSRF obvious cases) without DNS
        try:
            ip_lit = ipaddress.ip_address(host)
            if not _ip_is_globally_routable(ip_lit):
                return False

        except ValueError:
            pass

        # validate port syntax (":abc" should fail)
        try:
            port = p.port
        except ValueError:
            return False
        if port is not None and (port <= 0 or port > 65535):
            return False

        # your existing blacklist/subpath rules (pure parsing)
        return _is_valid(url)

    except Exception:
        return False


def _do_scrape_links_child(
    html: str | None,
    html_path: str | None,
    url: str,
    scraped_urls_list: list[str],
    conn
) -> None:
    from bs4 import BeautifulSoup

    try:
        scraped_urls = set(scraped_urls_list or [])
        links: list[str] = []

        # If we got a spilled HTML body, only read a small cap for link extraction.
        if html is None and html_path:
            raw = _read_file_bytes(html_path, HTML_LINKS_MAX_BYTES)
            html = raw.decode("utf-8", errors="replace")
        html = html or ""

        soup = BeautifulSoup(html, "html.parser")

        base_host = (urlparse(url).hostname or "").lower()
        is_wiki = _host_is(base_host, "wikipedia.org")

        if is_wiki:
            content = soup.select_one("#mw-content-text .mw-parser-output") or soup.select_one("#mw-content-text")
            search_root = content if content is not None else soup

            for sel in WIKIPEDIA_JUNK_LINK_SELECTORS:
                for t in search_root.select(sel):
                    t.extract()

            _wikipedia_truncate_after_stop_sections(search_root)
        else:
            search_root = soup

        for a in search_root.find_all("a", href=True):
            if any(
                ancestor.name in NAV_TAGS
                or any(cls in NAV_CLASSES for cls in ancestor.get("class", []))
                or any(sub in ancestor.get("id", "").lower() for sub in ID_SUBSTRINGS)
                for ancestor in a.parents
            ):
                continue

            href = (a.get("href") or "").strip()
            if not href or href.startswith("#"):
                continue

            candidate_raw = urljoin(url, href)
            if not candidate_raw:
                continue

            if is_wiki and not _wikipedia_article_link_ok(url, candidate_raw):
                continue

            if not _link_candidate_ok(candidate_raw):
                continue

            link = _normalize_url(candidate_raw)
            if link and link not in scraped_urls:
                links.append(link)

        if not is_wiki:
            random.shuffle(links)

        _safe_send(conn, ("ok", links[:WEB_SCRAPE_MAX_LINKS]))
    except Exception:
        _safe_send(conn, ("err", traceback.format_exc()))
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _run_child(fn, args: tuple, timeout: int, *, vmem_limit: int | None = None) -> Any:
    _cleanup_stale_tmp_files()

    ctx = mp.get_context("spawn")
    parent_conn, child_conn = ctx.Pipe(duplex=False)

    p = ctx.Process(
        target=_child_bootstrap,
        args=(fn, args, child_conn, vmem_limit),
        daemon=True,
    )
    p.start()
    child_conn.close()

    try:
        if not parent_conn.poll(timeout):
            _kill_process(p)
            raise TimeoutError(f"Child timed out after {timeout}s: {fn.__name__}")

        try:
            status, payload = parent_conn.recv()
        except EOFError:
            raise RuntimeError(f"Child exited without returning data: {fn.__name__}")

    finally:
        try:
            parent_conn.close()
        except Exception:
            pass

        _kill_process(p)
        try:
            p.close()
        except Exception:
            pass

    if status == "err":
        raise RuntimeError(payload)
    return payload


def _do_resolve_global_ips_child(host: str, port: int, conn) -> None:
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
        out: list[str] = []
        seen: set[str] = set()

        for _, _, _, _, sockaddr in infos:
            ip_str = sockaddr[0]
            try:
                ip = ipaddress.ip_address(ip_str)
            except ValueError:
                continue
            if not _ip_is_globally_routable(ip):
                continue
            if ip_str not in seen:
                seen.add(ip_str)
                out.append(ip_str)
                if len(out) >= 16:
                    break

        _safe_send(conn, ("ok", out))
    except Exception:
        _safe_send(conn, ("err", traceback.format_exc()))
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _resolve_global_ips_with_timeout(host: str, port: int) -> list[str]:
    """Resolve host to globally-routable IPs. Empty => treat as unsafe."""
    try:
        payload = _run_child(_do_resolve_global_ips_child, (host, port), DNS_TIMEOUT)

        return list(payload) if payload else []
    except Exception:
        return []


def _pin_global_ips(scheme: str, host_ascii: str, port: int) -> list[str]:
    """
    Resolve hostname to globally-routable IPs.
    """
    # If host is an IP literal, validate it's global and return as-is.
    try:
        ip_lit = ipaddress.ip_address(host_ascii)
        return [host_ascii] if _ip_is_globally_routable(ip_lit) else []
    except ValueError:
        pass

    ips = _resolve_global_ips_with_timeout(host_ascii, port)
    return ips[:MAX_PINNED_IP_TRIES]


def _plan_for_url(url: str) -> tuple[str, str, int, list[str]]:
    parsed_url = urlparse(url)
    scheme = (parsed_url.scheme or "").lower()
    if scheme not in ("http", "https") or not parsed_url.netloc:
        raise ValueError(f"Invalid URL: {url}")

    if parsed_url.username or parsed_url.password:
        raise ValueError("Userinfo in URL is not allowed")

    host = (parsed_url.hostname or "").strip()
    if not host:
        raise ValueError("Missing hostname")

    if host.lower() in ("localhost", "0.0.0.0", "::", "::1"):
        raise ValueError("Localhost is not allowed")

    # parsed_url.port can raise ValueError for garbage like ":abc"
    try:
        explicit_port = parsed_url.port
    except ValueError:
        raise ValueError("Invalid port")

    if explicit_port is None:
        port = 443 if scheme == "https" else 80
    else:
        port = int(explicit_port)
        # Port 0 is not a meaningful destination for HTTP(S)
        if port <= 0 or port > 65535:
            raise ValueError("Port out of range")

    # IP-literal short-circuit
    try:
        ip_lit = ipaddress.ip_address(host)
    except ValueError:
        ip_lit = None

    if ip_lit is not None:
        if not _ip_is_globally_routable(ip_lit):
            raise ValueError("IP literal is not globally routable")

        host_ascii = host
        return scheme, host_ascii, port, [host_ascii]

    try:
        host_ascii = host.encode("idna").decode("ascii")
    except Exception:
        raise ValueError("Invalid hostname encoding")

    ips = _pin_global_ips(scheme, host_ascii, port)
    if not ips:
        raise ValueError("Hostname did not resolve to any global IPs")

    # Bound worst-case wall time
    ips = ips[:MAX_PINNED_IP_TRIES]

    return scheme, host_ascii, port, ips


def _is_safe(url: str) -> bool:
    try:
        _plan_for_url(url)
        return True
    except Exception:
        return False


def _is_valid(url: str) -> bool:
    try:
        parsed_url = urlparse(url)
        host = _canon_host(parsed_url.hostname or "")
        path = (parsed_url.path or "").lower()
        path_segments = path.strip("/").split("/") if path else []

        # Blacklisted domains (exact host or subdomain)
        if any(host == d or host.endswith("." + d) for d in BLACKLISTED_DOMAINS):
            return False

        # Ignore specific file endings
        if any(path.endswith(ending) for ending in IGNORED_FILE_ENDINGS):
            return False

        # Forbidden subpaths for certain hosts (GitHub/GitLab)
        for domain, subpaths in IGNORED_SUBPATHS.items():
            if host == domain or host.endswith("." + domain):
                if any(seg in subpaths for seg in path_segments):
                    return False
                break

        return True
    except Exception as e:
        print(WEB_SCRAPE_VALIDATE_ERROR + str(e))
        return False


def _host_is(host: str, root: str) -> bool:
    host = _canon_host(host)
    root = _canon_host(root)
    return host == root or host.endswith("." + root)


def _normalize_url(url: str) -> str:
    """
    Normalize URL for dedup/logic:
      - strip fragment
      - lowercase scheme + hostname
      - IDNA-encode hostname (so unicode domains canonicalize)
      - collapse explicit default ports (:80 for http, :443 for https)
      - preserve ANY non-default explicit port
      - normalize empty path to "/" (so https://x and https://x/ dedup)
      - percent-encode path/query deterministically (handles unicode + bad %)
      - keep params as-is
      - normalize GitHub/GitLab blob -> raw (with safe rules)

    SECURITY NOTE:
      - If URL contains userinfo or an invalid port, do NOT "heal" it here.
        Return a fragment-stripped version that preserves netloc so _check_url() can reject it.
    """
    try:
        parsed_url = urlparse(url)

        scheme = (parsed_url.scheme or "").lower()

        # If it's not parseable enough, at least strip fragment.
        if not scheme or not parsed_url.netloc:
            return urlunparse(
                (parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params, parsed_url.query, "")
            )

        # Preserve userinfo as-is (so validators can reject it)
        if parsed_url.username or parsed_url.password:
            path = parsed_url.path if parsed_url.path else "/"
            return urlunparse((scheme, parsed_url.netloc, path, parsed_url.params, parsed_url.query, ""))

        hostname = (parsed_url.hostname or "").lower()
        if not hostname:
            return urlunparse((scheme, parsed_url.netloc, parsed_url.path, parsed_url.params, parsed_url.query, ""))

        # IDNA encode hostname for canonical ASCII form
        try:
            hostname_ascii = hostname.encode("idna").decode("ascii")
        except Exception:
            hostname_ascii = hostname  # best effort

        # parsed_url.port can raise ValueError for garbage like ":abc"
        try:
            port = parsed_url.port
        except ValueError:
            # Preserve invalid netloc so _check_url() can reject
            path = parsed_url.path if parsed_url.path else "/"
            return urlunparse((scheme, parsed_url.netloc, path, parsed_url.params, parsed_url.query, ""))

        # Default port for scheme
        default_port = 80 if scheme == "http" else (443 if scheme == "https" else None)

        # Collapse explicit default ports
        if port is not None and default_port is not None and port == default_port:
            port = None

        # Canonicalize empty path to "/"
        raw_path = parsed_url.path if parsed_url.path else "/"
        path_l = raw_path.lower()

        # Percent-encode path/query deterministically (fix bad % and unicode)
        path = quote(_fix_bad_percents(raw_path), safe=URL_PATH_SAFE)
        query = quote(_fix_bad_percents(parsed_url.query or ""), safe=URL_QUERY_SAFE)

        # IPv6 literals must be bracketed in netloc even when no port.
        host_for_netloc = f"[{hostname_ascii}]" if ":" in hostname_ascii else hostname_ascii

        if port is None:
            netloc = host_for_netloc
        else:
            netloc = f"{host_for_netloc}:{int(port)}"

        normalized_url = urlunparse((scheme, netloc, path, parsed_url.params, query, ""))

        # GitHub blob -> raw:
        # Only do this rewrite when the original URL is on default port (or none).
        if _host_is(hostname_ascii, "github.com") and "/blob/" in path_l:
            if port is None:
                normalized_url = urlunparse(
                    (
                        scheme,
                        "raw.githubusercontent.com",
                        quote(_fix_bad_percents(raw_path.replace("/blob/", "/")), safe=URL_PATH_SAFE),
                        "",
                        query,
                        "",
                    )
                )

        # GitLab /-/blob/ -> /-/raw/ (host stays; keep netloc incl. explicit non-default port)
        elif _host_is(hostname_ascii, "gitlab.com") and "/-/blob/" in path_l:
            normalized_url = urlunparse(
                (
                    scheme,
                    netloc,
                    quote(_fix_bad_percents(raw_path.replace("/-/blob/", "/-/raw/")), safe=URL_PATH_SAFE),
                    parsed_url.params,
                    query,
                    "",
                )
            )

        return normalized_url

    except Exception as e:
        print(WEB_SCRAPE_ERROR + str(e))
        return url


def _curl_request_once(
    method: str,
    url: str,
    *,
    host_ascii: str,
    port: int,
    ip: str,
    max_bytes: int = FETCH_MAX_BYTES,
    timeout: int = TIMEOUT,
) -> ResponseData:
    method = (method or "").lower().strip()
    if method not in ("head", "get"):
        raise ValueError(f"Unsupported method: {method}")

    timeout = max(1, int(timeout))
    max_bytes = max(1, int(max_bytes))

    headers: dict[str, str] = {}
    body = bytearray()

    header_bytes = 0
    aborted_for_size = False
    aborted_for_headers = False

    def header_cb(line: bytes) -> int:
        nonlocal header_bytes, aborted_for_headers
        header_bytes += len(line)
        if header_bytes > HEADER_MAX_BYTES:
            aborted_for_headers = True
            return 0  # abort transfer immediately

        if line.startswith(b"HTTP/"):
            headers.clear()
            return len(line)

        if b":" in line:
            k, v = line.split(b":", 1)
            key = k.decode("iso-8859-1", errors="replace").strip().lower()
            val = v.decode("iso-8859-1", errors="replace").strip()
            if key:
                headers[key] = val

        return len(line)

    def write_cb(chunk: bytes) -> int:
        nonlocal aborted_for_size
        if not chunk:
            return 0

        remaining = max_bytes - len(body)
        if remaining <= 0:
            aborted_for_size = True
            return 0  # abort transfer immediately

        if len(chunk) > remaining:
            aborted_for_size = True
            body.extend(chunk[:remaining])
            return 0  # abort transfer immediately

        body.extend(chunk)
        return len(chunk)

    def xferinfo(dltotal, dlnow, ultotal, ulnow) -> int:
        nonlocal aborted_for_size
        try:
            if float(dlnow) > float(max_bytes):
                aborted_for_size = True
                return 1
        except Exception:
            pass
        return 0

    c = pycurl.Curl()
    try:
        c.setopt(pycurl.URL, _curl_safe_url(url))
        c.setopt(pycurl.USERAGENT, USER_AGENT)

        c.setopt(pycurl.FOLLOWLOCATION, 0)
        c.setopt(pycurl.MAXREDIRS, 0)
        c.setopt(pycurl.PROTOCOLS, pycurl.PROTO_HTTP | pycurl.PROTO_HTTPS)
        c.setopt(pycurl.REDIR_PROTOCOLS, pycurl.PROTO_HTTP | pycurl.PROTO_HTTPS)

        c.setopt(pycurl.PROXY, "")
        try:
            c.setopt(pycurl.NOPROXY, "*")
        except Exception:
            pass

        c.setopt(pycurl.CONNECTTIMEOUT, min(15, timeout))
        c.setopt(pycurl.TIMEOUT, timeout)
        c.setopt(pycurl.NOSIGNAL, 1)

        try:
            c.setopt(pycurl.LOW_SPEED_LIMIT, LOW_SPEED_LIMIT)
            c.setopt(pycurl.LOW_SPEED_TIME, LOW_SPEED_TIME)
        except Exception:
            pass

        c.setopt(pycurl.SSL_VERIFYPEER, 1)
        c.setopt(pycurl.SSL_VERIFYHOST, 2)

        try:
            c.setopt(pycurl.ACCEPT_ENCODING, "identity")
        except Exception:
            pass

        try:
            c.setopt(pycurl.MAXFILESIZE_LARGE, int(max_bytes))
        except Exception:
            pass

        c.setopt(pycurl.HTTPHEADER, ["Accept: */*"])

        # Pin DNS (skip if host is IP literal)
        is_ip_literal = False
        try:
            ipaddress.ip_address(host_ascii)
            is_ip_literal = True
        except ValueError:
            is_ip_literal = False

        if not is_ip_literal:
            resolve_ip = f"[{ip}]" if ":" in ip else ip
            c.setopt(pycurl.RESOLVE, [f"{host_ascii}:{port}:{resolve_ip}"])

        c.setopt(pycurl.HEADERFUNCTION, header_cb)
        c.setopt(pycurl.WRITEFUNCTION, write_cb)

        c.setopt(pycurl.NOPROGRESS, 0)
        try:
            c.setopt(pycurl.XFERINFOFUNCTION, xferinfo)
        except Exception:
            c.setopt(pycurl.PROGRESSFUNCTION, xferinfo)

        if method == "head":
            c.setopt(pycurl.NOBODY, 1)
            c.setopt(pycurl.CUSTOMREQUEST, "HEAD")
        else:
            c.setopt(pycurl.NOBODY, 0)
            c.setopt(pycurl.HTTPGET, 1)

        try:
            c.perform()
        except pycurl.error as e:
            errno = e.args[0] if e.args else None
            write_err = getattr(pycurl, "E_WRITE_ERROR", 23)  # 23 is CURLE_WRITE_ERROR
            aborted_errno = getattr(pycurl, "E_ABORTED_BY_CALLBACK", None)

            aborted = aborted_for_size or aborted_for_headers
            if aborted and (errno in (write_err, aborted_errno) or aborted_errno is None):
                # Controlled abort (size cap or header cap) -> continue and return partial data safely
                pass
            else:
                raise

        status_code = int(c.getinfo(pycurl.RESPONSE_CODE))
        content = bytes(body)

        if aborted_for_size:
            headers["x-magi-truncated"] = "1"
        if aborted_for_headers:
            headers["x-magi-headerbomb"] = "1"

        # IMPORTANT: don’t duplicate decoded text across IPC
        text = ""

        content_path: str | None = None
        if len(content) > IPC_INLINE_BYTES:
            try:
                content_path = _spill_to_tmp(content)
                content = b""
                headers["x-magi-spilled"] = "1"
            except Exception:
                # Fallback: keep inline (may increase IPC cost)
                content_path = None

        return ResponseData(
            url=url,
            status_code=status_code,
            headers=headers,
            text=text,
            content=content,
            content_path=content_path,
        )

    finally:
        try:
            c.close()
        except Exception:
            pass


def _request(
    method: str,
    url: str,
    *,
    max_bytes: int = FETCH_MAX_BYTES,
    timeout: int = TIMEOUT,
) -> ResponseData:
    """
    Resolve+pin to global IPs, then try each pinned IP with pycurl+RESOLVE.
    """
    timeout = max(1, int(timeout))
    deadline = time.monotonic() + timeout

    _, host_ascii, port, ips = _plan_for_url(url)
    if not ips:
        raise RuntimeError(f"No pinned IPs for {url}")

    last_err: Exception | None = None

    for i, ip in enumerate(ips):
        remaining = int(deadline - time.monotonic())
        if remaining <= 0:
            break

        # Ensure we still have a chance to try later IPs.
        tries_left = max(1, len(ips) - i)
        per_try = max(1, remaining // tries_left)

        try:
            return _run_child(
                _do_curl_request_child,
                (method, url, host_ascii, port, ip, max_bytes, per_try),
                per_try + CHILD_GRACE_SECONDS,
                vmem_limit=CURL_CHILD_VMEM_BYTES,
            )

        except Exception as e:
            last_err = e

    raise TimeoutError(f"Request budget exceeded for {url}: {last_err}")


def _fetch_url(
    method: str,
    url: str,
    *,
    is_robots: bool = False,
    max_bytes: int = FETCH_MAX_BYTES,
    deadline: float | None = None,
) -> ResponseData:
    if deadline is None:
        deadline = time.monotonic() + MAX_FETCH_WALL_SECONDS

    current = url
    method = method.lower().strip()

    for _ in range(WEB_SCRAPE_MAX_REDIRECTS + 1):
        _check_scrape_deadline(deadline)

        remaining = int(deadline - time.monotonic())
        if remaining <= 0:
            raise TimeoutError(f"fetch budget exceeded for {url}")

        resp = _request(method, current, max_bytes=max_bytes, timeout=min(TIMEOUT, remaining))

        if resp.status_code not in (301, 302, 303, 307, 308):
            return resp

        # We're discarding this response body on redirect → delete spilled file now
        _cleanup_file(resp.content_path)

        location = (resp.headers.get("location") or "").strip()
        if not location:
            return resp

        nxt_raw = urljoin(current, location)

        if is_robots:
            if (not _is_safe(nxt_raw)) or (not _is_valid(nxt_raw)):
                raise RuntimeError(WEB_SCRAPE_UNSAFE_URL + nxt_raw)
        else:
            err = _check_url(nxt_raw, deadline=deadline)
            if err:
                raise RuntimeError(err)

        if resp.status_code == 303:
            method = "get"

        current = _normalize_url(nxt_raw)

    raise RuntimeError(f"Too many redirects (>{WEB_SCRAPE_MAX_REDIRECTS}): {url}")


def _is_scraping_allowed(url: str, *, deadline: float | None = None) -> bool:
    """
    Robots check with simple TTL cache.
    """
    try:
        robots_status = None

        if deadline is None:
            deadline = time.monotonic() + SCRAPE_WALL_SECONDS
        _check_scrape_deadline(deadline)

        now = time.time()
        domain_key = _robots_domain_key(url)

        cached = ROBOTS_CACHE.get(domain_key)
        if cached and (now - cached[1] < ROBOTS_CACHE_TTL):
            return _protego_can_fetch(cached[0], url)

        robots_url = domain_key + "/robots.txt"
        robots_text = ""

        robots_tmp_path: str | None = None
        try:
            _check_scrape_deadline(deadline)

            # Keep robots fetch safe; do not recurse into _check_url().
            if (not _is_safe(robots_url)) or (not _is_valid(robots_url)):
                robots_text = ""
            else:
                r = _fetch_url(
                    "get",
                    robots_url,
                    is_robots=True,
                    max_bytes=ROBOTS_MAX_BYTES,
                    deadline=deadline,
                )

                robots_status = r.status_code

                # Track possible spill path so it always gets cleaned up.
                robots_tmp_path = r.content_path

                if 200 <= r.status_code < 400:
                    raw = r.content or b""

                    # If response was spilled, read from the temp file (future-proof even though
                    # ROBOTS_MAX_BYTES < IPC_INLINE_BYTES today).
                    if (not raw) and r.content_path:
                        raw = _read_file_bytes(r.content_path, ROBOTS_MAX_BYTES)

                    # Decide whether to accept robots.txt
                    if (
                        r.headers.get("x-magi-truncated") == "1"
                        or len(raw) > ROBOTS_MAX_BYTES
                        or b"\x00" in raw[:1024]
                    ):
                        robots_text = ""
                    else:
                        robots_text = raw.decode("utf-8", errors="replace")

        except Exception:
            robots_text = ""
        finally:
            # Always cleanup spilled robots body file (if any).
            _cleanup_file(robots_tmp_path)

        # Normalize to prevent Protego failure
        robots_text = _normalize_robots_text(robots_text)

        if robots_text:
            rp = Protego.parse(robots_text)
        else:
            if robots_status in (200, 204, 404):
                rp = Protego.parse("User-agent: *\nDisallow:\n")
            else:
                rp = Protego.parse("User-agent: *\nDisallow: /\n")

        ROBOTS_CACHE[domain_key] = (rp, now)

        # Hard cap cache to prevent unbounded growth (simple + small).
        if len(ROBOTS_CACHE) > 1024:
            ROBOTS_CACHE.clear()

        return _protego_can_fetch(rp, url)

    except Exception as e:
        print(WEB_SCRAPE_CHECK_ALLOWED_ERROR + str(e))
        return False


def _check_url(url: str, *, deadline: float | None = None) -> str:
    """Validate URL for safety, subpath policies and scraping permissions."""
    try:
        if deadline is not None:
            _check_scrape_deadline(deadline)

        if not _is_safe(url):
            return (WEB_SCRAPE_UNSAFE_URL + url).strip()

        if deadline is not None:
            _check_scrape_deadline(deadline)

        if not _is_valid(url):
            return WEB_SCRAPE_INVALID_URL.strip()

        if deadline is not None:
            _check_scrape_deadline(deadline)

        if not _is_scraping_allowed(url, deadline=deadline):
            return WEB_SCRAPE_NOT_ALLOWED

        return ""

    except Exception as e:
        return (WEB_SCRAPE_VALIDATE_ERROR + str(e)).strip()


def _do_parse_child(kind: str, data: bytes | None, data_path: str | None, base_url: str, run_timeout: int, conn) -> None:
    try:
        kind = (kind or "").lower().strip()
        text_out = ""

        if data is None and data_path:
            data = _read_file_bytes(data_path, FETCH_MAX_BYTES)

        data = data or b""

        if kind == "pdf":
            from pypdf import PdfReader
            with BytesIO(data) as f:
                reader = PdfReader(f)
                text_out = "\n".join(page.extract_text() or "" for page in reader.pages)

        elif kind == "docx":
            from docx import Document
            document = Document(BytesIO(data))
            text_out = "\n".join(p.text for p in document.paragraphs)

        elif kind == "odt":
            from odf.opendocument import load
            from odf import text as odf_text, teletype
            odt_file = load(BytesIO(data))
            all_paragraphs = odt_file.getElementsByType(odf_text.P)
            text_out = "\n".join(teletype.extractText(p) for p in all_paragraphs)

        elif kind == "doc":
            import subprocess

            env = {
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
                "HOME": "/tmp",
                "PATH": "/usr/bin:/bin",
                "ANTIWORDHOME": "/usr/share/antiword",
            }

            try:
                p = subprocess.Popen(
                    ["antiword", "-w", "0", "-m", "UTF-8.txt", "-"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    env=env,
                    close_fds=True
                )
            except FileNotFoundError:
                raise RuntimeError("antiword is not installed (apt install antiword)")

            try:
                out, _ = p.communicate(input=data, timeout=max(1, int(run_timeout)))
            except subprocess.TimeoutExpired:
                try:
                    p.kill()  # SIGKILL antiword itself
                except Exception:
                    pass
                try:
                    p.communicate(timeout=1)
                except Exception:
                    pass
                raise TimeoutError("antiword timed out")

            text_out = (out or b"").decode("utf-8", errors="replace")

        elif kind == "html":
            text_out = _extract_text_from_html(data, base_url=base_url or "")

        else:
            raise ValueError(f"Unsupported parse kind: {kind}")

        if text_out:
            text_out = text_out.replace("\r\n", "\n").replace("\r", "\n")

        if len(text_out) > MAX_TOTAL_TEXT_CHARS:
            text_out = text_out[:MAX_TOTAL_TEXT_CHARS]

        _safe_send(conn, ("ok", text_out))
    except Exception:
        _safe_send(conn, ("err", traceback.format_exc()))
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _parse_with_timeout(
    kind: str,
    data: bytes | None = None,
    *,
    path: str | None = None,
    base_url: str = "",
    timeout: int = TIMEOUT,
) -> str:
    timeout = max(1, int(timeout))
    return str(
        _run_child(
            _do_parse_child,
            (kind, data, path, base_url, timeout),
            timeout + CHILD_GRACE_SECONDS,
            vmem_limit=PARSE_MAX_VMEM_BYTES,
        )
    )


def _do_ddgs_search_child(query: str, max_results: int, conn) -> None:
    try:
        urls: list[str] = []
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)
            for r in results:
                href = r.get("href") if isinstance(r, dict) else None
                if href:
                    urls.append(href)
        _safe_send(conn, ("ok", urls))
    except Exception:
        _safe_send(conn, ("err", traceback.format_exc()))
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _ddgs_search_with_timeout(query: str, max_results: int) -> list[str]:
    payload = _run_child(_do_ddgs_search_child, (query, max_results), TIMEOUT + CHILD_GRACE_SECONDS)
    return list(payload)


def _scrape_links(
    html: str | None,
    url: str,
    scraped_urls: set[str],
    *,
    html_path: str | None = None,
    deadline: float | None = None,
) -> list[str]:
    try:
        t = TIMEOUT if deadline is None else _remaining(deadline)
        payload = _run_child(
            _do_scrape_links_child,
            (html, html_path, url, list(scraped_urls)),
            t + CHILD_GRACE_SECONDS,
            vmem_limit=PARSE_MAX_VMEM_BYTES,
        )
        return list(payload) if payload else []
    except Exception as e:
        print(WEB_SCRAPE_ERROR + str(e))
        return []


def scrape(url, depth = 0, scraped_urls = None):
    text = ""
    is_root = (depth == 0)

    normalized_url = ""
    resolved_url = ""

    key = None
    deadline = None
    created_deadline = False

    resp_tmp_path: str | None = None

    try:
        links: list[str] = []

        if scraped_urls is None:
            scraped_urls = set()

        key = id(scraped_urls)
        deadline = _scrape_deadlines.get(key)
        if deadline is None:
            deadline = time.monotonic() + SCRAPE_WALL_SECONDS
            _scrape_deadlines[key] = deadline
            created_deadline = True

        _check_scrape_deadline(deadline)

        # Validate the entry URL once (includes robots)
        raw_err = _check_url(url, deadline=deadline)
        if raw_err:
            raise RuntimeError(raw_err)

        normalized_url = _normalize_url(url)
        resolved_url = normalized_url

        if normalized_url in scraped_urls:
            return ""

        scraped_urls.add(normalized_url)

        # -------------------
        # HEAD (best-effort)
        # -------------------
        head_tmp = None
        try:
            head = _fetch_url("head", resolved_url, deadline=deadline)
            head_tmp = head.content_path

            # If headers were a bomb, ignore HEAD entirely and fall back to GET
            if head.headers.get("x-magi-headerbomb") == "1":
                raise Exception("header bomb on HEAD")

            resolved_from_head = _normalize_url(head.url)

            # Only treat HEAD as a "new URL" if it actually changed.
            if resolved_from_head != normalized_url:
                if resolved_from_head in scraped_urls:
                    return ""
                scraped_urls.add(resolved_from_head)
                resolved_url = resolved_from_head
            else:
                resolved_url = normalized_url

        except RuntimeError:
            raise
        except Exception:
            # ignore HEAD failures
            resolved_url = normalized_url
        finally:
            _cleanup_file(head_tmp)

        _check_scrape_deadline(deadline)

        # -----------
        # GET
        # -----------
        resp = _fetch_url("get", resolved_url, deadline=deadline)
        resp_tmp_path = resp.content_path  # may be None

        resolved_url = _normalize_url(resp.url)

        # Header-bomb: treat as unsupported and stop right here
        if resp.headers.get("x-magi-headerbomb") == "1":
            text = WEB_SCRAPE_UNSUPPORTED_CONTENT + f"headers exceeded {HEADER_MAX_BYTES} bytes cap"
            if resp.status_code >= 400:
                text = (text + f"\n\n(HTTP error: {resp.status_code})").strip()
            text = _cap_total(text)

            if is_root and text:
                prefix = URL_TEXT_1 + url + URL_TEXT_2
                remaining = MAX_TOTAL_TEXT_CHARS - len(prefix)
                return prefix + (text[:remaining] if remaining > 0 else "")
            return text

        # Avoid pointless growth; only add if it differs and is new
        if resolved_url not in scraped_urls:
            scraped_urls.add(resolved_url)

        ctype = (resp.headers.get("content-type") or "").lower()

        # Sniff if missing content-type
        if not ctype:
            if resp.content:
                head_bytes = resp.content[:512].lstrip().lower()
            elif resp.content_path:
                head_bytes = _peek_file_bytes(resp.content_path, 512).lstrip().lower()
            else:
                head_bytes = b""

            if head_bytes.startswith(b"<!doctype html") or head_bytes.startswith(b"<html") or b"<html" in head_bytes:
                ctype = "text/html"
            elif head_bytes.startswith(b"%pdf-"):
                ctype = "application/pdf"
            elif b"\x00" in head_bytes:
                ctype = "application/octet-stream"
            else:
                ctype = "text/plain"

        _sleep_with_deadline(deadline)

        doc = None
        if "text/html" in ctype:
            doc = "html"
        elif "text/plain" in ctype:
            doc = "plain"
        elif "application/pdf" in ctype:
            doc = "pdf"
        elif "application/msword" in ctype:
            doc = "doc"
        elif "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in ctype:
            doc = "docx"
        elif "application/vnd.oasis.opendocument.text" in ctype:
            doc = "odt"

        if resp.headers.get("x-magi-truncated") == "1" and doc in ("pdf", "doc", "docx", "odt"):
            cap_mb = FETCH_MAX_BYTES // (1024 * 1024)
            text = WEB_SCRAPE_UNSUPPORTED_CONTENT + f"{ctype} (truncated at {cap_mb} MiB cap)"
            if resp.status_code >= 400:
                text = (text + f"\n\n(HTTP error: {resp.status_code})").strip()
            text = _cap_total(text)

            if is_root and text:
                prefix = URL_TEXT_1 + url + URL_TEXT_2
                remaining = MAX_TOTAL_TEXT_CHARS - len(prefix)
                return prefix + (text[:remaining] if remaining > 0 else "")
            return text

        _check_scrape_deadline(deadline)

        if doc == "plain":
            if resp.content:
                raw = resp.content[:PLAIN_MAX_BYTES]
            elif resp.content_path:
                raw = _read_file_bytes(resp.content_path, PLAIN_MAX_BYTES)
            else:
                raw = b""
            text = raw.decode("utf-8", errors="replace")

        elif doc in ("html", "pdf", "doc", "docx", "odt"):
            text = _parse_with_timeout(
                doc,
                None if resp.content_path else (resp.content or b""),
                path=resp.content_path,
                base_url=resolved_url,
                timeout=_remaining(deadline),
            )

            if doc == "html" and depth < WEB_SCRAPE_MAX_DEPTH and len(text) < MAX_TOTAL_TEXT_CHARS:
                if resp.content_path:
                    links = _scrape_links(None, resolved_url, scraped_urls, html_path=resp.content_path, deadline=deadline)
                else:
                    html_src = (resp.content or b"").decode("utf-8", errors="replace")
                    links = _scrape_links(html_src, resolved_url, scraped_urls, deadline=deadline)

        else:
            text = WEB_SCRAPE_UNSUPPORTED_CONTENT + ctype

        text = _cap_total(text)

        if resp.status_code >= 400:
            text = _cap_total((text + f"\n\n(HTTP error: {resp.status_code})").strip())

        for link in links:
            _check_scrape_deadline(deadline)

            if len(text) >= MAX_TOTAL_TEXT_CHARS:
                break
            if link in scraped_urls:
                continue

            sub = scrape(link, depth + 1, scraped_urls)
            if not sub:
                continue

            addition = LINK_TEXT_1 + link + LINK_TEXT_2 + sub
            remaining = MAX_TOTAL_TEXT_CHARS - len(text)
            if remaining <= 0:
                break
            text += addition[:remaining]
            text = _cap_total(text)

    except Exception as e:
        msg = str(e).strip()

        if msg == WEB_SCRAPE_NOT_ALLOWED:
            text = ""
        elif is_root:
            print(WEB_SCRAPE_ERROR + f"{type(e).__name__}: {msg} url={url} resolved_url={resolved_url}")

    finally:
        # Always cleanup spilled body file for this page
        _cleanup_file(resp_tmp_path)

        if created_deadline and key is not None:
            _scrape_deadlines.pop(key, None)

    if is_root and text:
        prefix = URL_TEXT_1 + url + URL_TEXT_2
        remaining = MAX_TOTAL_TEXT_CHARS - len(prefix)
        return prefix + (text[:remaining] if remaining > 0 else "")

    return _cap_total(text.strip())


def search(query, max_urls):
    """Search the web using DuckDuckGo"""
    try:
        max_urls = max(1, min(int(max_urls), WEB_SEARCH_MAX_RESULTS))
        hrefs = _ddgs_search_with_timeout(query, WEB_SEARCH_MAX_RESULTS)

        urlArray: list[str] = []
        seen: set[str] = set()

        for href in hrefs:
            # Cheap parse-only checks (no DNS/robots)
            if _check_url_for_search(href):
                continue

            u = _normalize_url(href)

            if not u or u in seen:
                continue

            seen.add(u)

            # Full check (includes robots) but only until we fill max_urls
            deadline = time.monotonic() + TIMEOUT
            err = _check_url(u, deadline = deadline)

            if err:
                continue

            urlArray.append(u)

            if len(urlArray) >= max_urls:
                break

        return urlArray

    except Exception as e:
        print(WEB_SEARCH_ERROR + str(e))
        return []


