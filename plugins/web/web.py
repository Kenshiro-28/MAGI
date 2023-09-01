import os
import requests
from bs4 import BeautifulSoup

TIMEOUT = 10

WEB_SEARCH_TEXT = "https://www.google.com/search?q="
WEB_SEARCH_ERROR = "\n[ERROR] An exception occurred while trying to do a web search: "
WEB_SCRAPE_ERROR = "\n[ERROR] An exception occurred while trying to scrape a web page: "

def search(query, maxUrls):
	try:
		urlArray = []

		headers = {
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36"
		}

		response = requests.get(WEB_SEARCH_TEXT + query, headers=headers)
		response.raise_for_status()

		soup = BeautifulSoup(response.text, 'html.parser')
		search_results = soup.select(".g .yuRUbf a")

		for result in search_results[:maxUrls]:
			urlArray.append(result['href'])

		return urlArray
	
	except Exception as e:
		print("\n" + WEB_SEARCH_ERROR + str(e)) 		
		return [""]
    

def scrape(url):
	try:
		text = ""

		headers = {
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36"
		}

		response = requests.get(url, headers=headers)
		response.raise_for_status()

		soup = BeautifulSoup(response.text, 'html.parser')

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
		

