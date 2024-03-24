import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse, urlunparse

TIMEOUT = 30
WEB_SEARCH_TEXT = "https://www.google.com/search?q="
GOOGLE_TRANSLATE_TEXT = "translate.google.com"
WEB_SEARCH_ERROR = "\n[ERROR] An exception occurred while trying to do a web search: "
WEB_SCRAPE_ERROR = "\n[ERROR] An exception occurred while trying to scrape a web page: "


def is_scraping_allowed(url):
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


def search(query, maxUrls):
	try:
		urlArray = []

		headers = {
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36"
		}

		response = requests.get(WEB_SEARCH_TEXT + query, headers = headers, timeout = TIMEOUT)
		response.raise_for_status()

		soup = BeautifulSoup(response.text, 'html.parser')
		search_results = soup.select(".g .yuRUbf a")

		for result in search_results:
			url = result['href']
			
			if is_scraping_allowed(url) and GOOGLE_TRANSLATE_TEXT not in url:
				urlArray.append(url)

				if len(urlArray) >= maxUrls:
					break

		return urlArray

	except Exception as e:
		print("\n" + WEB_SEARCH_ERROR + str(e)) 		
		return [""]


def scrape(url):
	browser = None

	try:
		options = Options()
		options.add_argument("--headless")
		options.add_argument("--no-sandbox")
		options.add_argument("--disable-dev-shm-usage")
		options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36")

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


