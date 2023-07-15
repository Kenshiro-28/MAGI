import web

GOOGLE_TRANSLATE_URL_TEXT = "translate.google.com"
WEB_SEARCH = "Who was Sun Tzu?"
MAX_URLS = 3

print("\nWeb search: " + WEB_SEARCH)

urls = web.search(WEB_SEARCH, MAX_URLS)

for url in urls:
	if GOOGLE_TRANSLATE_URL_TEXT in url:
		continue

	print("\n" + url)
	text = web.scrape(url)
	print("\n" + text)

