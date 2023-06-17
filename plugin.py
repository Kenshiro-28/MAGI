import core
from plugins import web

WEB_SEARCH_TEXT = "\n[WEB SEARCH] "
WEB_SEARCH_LIMIT = 3 # Number of web pages per search
GOOGLE_TRANSLATE_URL_TEXT = "translate.google.com"

# Web operations
def webSearch(query):
	context = []
	summary	= ""

	query = query.replace('"', '')

	core.print_system_text(WEB_SEARCH_TEXT + query, True)

	urls = web.search(query, WEB_SEARCH_LIMIT)

	for url in urls:
		# Ignore translated web pages
		if GOOGLE_TRANSLATE_URL_TEXT in url:
			continue
			
		core.print_system_text("\n" + url, True)	
		text = web.scrape(url)
		blockArray = core.split_text_in_blocks(text)

		webSummary = core.summarize_block_array(query, blockArray)

		summary = core.update_summary(query, context, summary, webSummary)

		if webSummary:			
			core.print_system_text("\n" + webSummary, True)
			
	return summary
	
	
