import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse, urlunparse
from io import BytesIO
from odf import text as odf_text, teletype
from docx import Document
from PyPDF2 import PdfReader

TIMEOUT = 30
WEB_SEARCH_TEXT = "https://www.google.com/search?q="
GOOGLE_TRANSLATE_TEXT = "translate.google.com"
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


def _selenium_request(url):
    try:
        browser = None

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(WEBDRIVER_USER_AGENT)
        options.add_experimental_option("prefs", {"download.default_directory": "/dev/null"})

        service = Service(executable_path = '/usr/bin/chromedriver')

        browser = webdriver.Chrome(service = service, options = options)

        browser.get(url) 

        WebDriverWait(browser, TIMEOUT).until(lambda d: d.execute_script('return document.readyState') == 'complete')

        soup = BeautifulSoup(browser.page_source, 'html.parser')

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

    finally:
        if browser:
            browser.quit()


def _scrape_pdf(url):
    response = requests.get(url, headers = REQUESTS_USER_AGENT, timeout = TIMEOUT)

    with BytesIO(response.content) as f:
        reader = PdfReader(f)
        text = "\n".join(page.extract_text() for page in reader.pages)
        
    return text


def _scrape_odt(url):
    response = requests.get(url, headers = REQUESTS_USER_AGENT, timeout = TIMEOUT)
    odt_file = odf_text.load(BytesIO(response.content))
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

        response = requests.get(WEB_SEARCH_TEXT + query, headers = REQUESTS_USER_AGENT, timeout = TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        search_results = soup.select(".g .yuRUbf a")

        for result in search_results:
            url = result['href']
            
            if url and _is_scraping_allowed(url) and GOOGLE_TRANSLATE_TEXT not in url:
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


