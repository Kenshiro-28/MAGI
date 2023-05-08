from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup

TIMEOUT = 10

WEB_SEARCH_TEXT = "https://www.google.com/search?q="
WEB_SEARCH_ERROR = "[ERROR] An exception occurred while trying to do a web search."
WEB_SCRAPE_ERROR = "[ERROR] An exception occurred while trying to scrape a web page."

def search(query, maxUrls):
	try:
		urlArray = []
		numUrls = 0

		options = webdriver.FirefoxOptions()
		options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36")
		options.headless = True
		options.add_argument("--disable-gpu")

		driver = webdriver.Firefox(executable_path=GeckoDriverManager().install(), options=options, service_log_path='null', service_args=["--log", "fatal"])

		driver.get(WEB_SEARCH_TEXT + query)

		WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".g .yuRUbf a")))

		# Extract the search result URLs from the page
		search_results = driver.find_elements_by_css_selector(".g .yuRUbf a")
		
		for result in search_results:
			if numUrls < maxUrls:
				urlArray.append(result.get_attribute("href"))  
				numUrls += 1
			else:
				break
		
		driver.quit()

		return urlArray
		
	except:
		print(WEB_SEARCH_ERROR) 		
		return []
    

def scrape(url):
	try:
		text = ""

		options = webdriver.FirefoxOptions()
		options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36")
		options.headless = True
		options.add_argument("--disable-gpu")
		
		driver = webdriver.Firefox(executable_path=GeckoDriverManager().install(), options=options, service_log_path='null', service_args=["--log", "fatal"])

		driver.get(url)

		WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

		# Get the HTML content directly from the browser's DOM
		page_source = driver.execute_script("return document.body.outerHTML;")
		soup = BeautifulSoup(page_source, "html.parser")

		for script in soup(["script", "style"]):
			script.extract()

		text = soup.get_text()
		lines = (line.strip() for line in text.splitlines())
		chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
		text = "\n".join(chunk for chunk in chunks if chunk)

		driver.quit()

		return text
		
	except:
		print(WEB_SCRAPE_ERROR)
		return ""
		
		
