import requests
import socket
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse, urlunparse, parse_qs
from io import BytesIO
from odf.opendocument import load
from odf import text as odf_text, teletype
from docx import Document
from PyPDF2 import PdfReader

TIMEOUT = 30
BROWSER_COOLDOWN_TIME = 1
WEB_SEARCH_TEXT = "https://duckduckgo.com/html/?q="
HEADERS = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36"
REQUESTS_USER_AGENT = {"User-Agent": HEADERS}
WEBDRIVER_USER_AGENT = "user-agent=" + HEADERS

WEB_SEARCH_ERROR = "\n[ERROR] An exception occurred while trying to do a web search: "
WEB_SCRAPE_ERROR = "\n[ERROR] An exception occurred while trying to scrape a web page: "


def _is_scraping_allowed(url):
    try:
        parsed_url = urlparse(url)
        url_components = (parsed_url.scheme, parsed_url.netloc, '/robots.txt', '', '', '')
        robots_url = urlunparse(url_components)

        robot_file_parser = RobotFileParser()
        robot_file_parser.set_url(robots_url)
        robot_file_parser.read()

        is_allowed = robot_file_parser.can_fetch("*", url)

        return is_allowed

    except Exception:
        return False


def _selenium_request_raw(url):
    try:
        browser = None

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument(WEBDRIVER_USER_AGENT)
        options.add_experimental_option("prefs", {"download.default_directory": "/dev/null"})

        service = Service(executable_path = '/usr/bin/chromedriver')

        browser = webdriver.Chrome(service = service, options = options)

        browser.set_page_load_timeout(TIMEOUT)

        browser.get(url)

        WebDriverWait(browser, TIMEOUT).until(lambda d: d.execute_script('return document.readyState') == 'complete')

        return browser.page_source

    except Exception as e:
        print("\n" + WEB_SCRAPE_ERROR + str(e))
        return ""

    finally:
        if browser:
            browser.quit()
            time.sleep(BROWSER_COOLDOWN_TIME)


def _selenium_request(url):
    try:
        response = _selenium_request_raw(url)

        if not response:
            return ""

        soup = BeautifulSoup(response, 'html.parser')

        for script in soup(["script", "style"]):
            script.extract()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)

        return text

    except Exception as e:
        print("\n" + WEB_SCRAPE_ERROR + str(e))
        return ""


def _scrape_pdf(url):
    response = requests.get(url, headers = REQUESTS_USER_AGENT, timeout = TIMEOUT)

    with BytesIO(response.content) as f:
        reader = PdfReader(f)
        text = "\n".join(page.extract_text() for page in reader.pages)
        
    return text


def _scrape_odt(url):
    response = requests.get(url, headers = REQUESTS_USER_AGENT, timeout = TIMEOUT)
    odt_file = load(BytesIO(response.content))
    all_paragraphs = odt_file.getElementsByType(odf_text.P)
    text = "\n".join(teletype.extractText(p) for p in all_paragraphs)

    return text


def _scrape_doc(url):
    response = requests.get(url, headers = REQUESTS_USER_AGENT, timeout = TIMEOUT)
    document = Document(BytesIO(response.content))
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)

    return text


def search(query, maxUrls):
    try:
        urlArray = []

        response = _selenium_request_raw(WEB_SEARCH_TEXT + query)

        soup = BeautifulSoup(response, 'html.parser')
        search_results = soup.select("a.result__a")

        for result in search_results:
            ad_container = result.find_parent("div", class_=lambda classes: classes and "result--ad" in classes)

            # If it's an ad, ignore it
            if ad_container:
                continue        
        
            relative_link = result['href']

            # Make sure it's a full link
            if relative_link.startswith('//'):
                full_link = 'https:' + relative_link
            else:
                full_link = relative_link

            # Parse the 'uddg' query param to get the real URL
            parsed = urlparse(full_link)
            qs = parse_qs(parsed.query)
            url_list = qs.get('uddg', [])

            if url_list:
                url = url_list[0]

                if url and _is_scraping_allowed(url):
                    urlArray.append(url)

                    if len(urlArray) >= maxUrls:
                        break

        return urlArray

    except Exception as e:
        print("\n" + WEB_SEARCH_ERROR + str(e))         
        return urlArray


def scrape(url):
    try:
        text = ""

        # Check the content type
        head_response = requests.head(url, headers = REQUESTS_USER_AGENT, timeout = TIMEOUT)
        content_type = head_response.headers.get('Content-Type', '')

        if 'text/html' in content_type:
            text = _selenium_request(url)

        elif 'application/pdf' in content_type:
            text = _scrape_pdf(url)

        elif 'application/msword' in content_type or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
            text = _scrape_doc(url)

        elif 'application/vnd.oasis.opendocument.text' in content_type:
            text = _scrape_odt(url)

        return text

    except Exception as e:
        print("\n" + WEB_SCRAPE_ERROR + str(e))
        return ""


socket.setdefaulttimeout(TIMEOUT)

