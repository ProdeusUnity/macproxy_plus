from flask import request
import requests
from bs4 import BeautifulSoup, Comment
import urllib.parse
import re

DOMAIN = "wikipedia.org"

def create_search_form():
	return '''
	<br><br><br>
	<center>
		<h6><font size="7" face="Times"><b>WIKIPEDIA</b></font><br>The Free Encyclopedia</h6>
		<form action="/wiki/" method="get">
			<input size="35" type="text" name="search" required>
			<input type="submit" value="Search">
		</form>
	</center>
	'''

def process_html(content, title):
	return f'<html><head><title>{title.replace('_', ' ')}</title></head><body>{content}</body></html>'

def handle_request(req):
	if req.method == 'GET':
		path = req.path.lstrip('/')
		
		if not path or path == 'wiki/':
			search_query = req.args.get('search', '')
			if not search_query:
				return process_html(create_search_form(), "Wikipedia, the free encyclopedia"), 200
			
			# Redirect to /wiki/[SEARCH_TERM]
			return handle_wiki_page(search_query)

		if path.startswith('wiki/'):
			page_title = urllib.parse.unquote(path.replace('wiki/', ''))
			return handle_wiki_page(page_title)

	return "Method not allowed", 405

def handle_wiki_page(title):
	try:
		url = f"https://{DOMAIN}/wiki/{urllib.parse.quote(title)}"
		response = requests.get(url)
		response.raise_for_status()

		soup = BeautifulSoup(response.text, 'html.parser')

		# Extract the page title
		title_element = soup.select_one('span.mw-page-title-main')
		if title_element:
			page_title = title_element.text
		else:
			page_title = title.replace('_', ' ')

		# Extract the main content
		content_div = soup.select_one('div#mw-content-text')
		if content_div:
			# Remove infoboxes and figures
			for element in content_div.select('table.infobox, figure'):
				element.decompose()

			# Remove shortdescription divs
			for element in content_div.select('div.shortdescription'):
				element.decompose()

			# Remove ambox tables
			for element in content_div.select('table.ambox'):
				element.decompose()
			
			# Remove style tags
			for element in content_div.select('style'):
				element.decompose()

			# Remove script tags
			for element in content_div.select('script'):
				element.decompose()
			
			# Remove edit section links
			for element in content_div.select('span.mw-editsection'):
				element.decompose()

			# Remove specific sections (External links, References, Notes)
			for section_id in ['External_links', 'References', 'Notes', 'Further_reading', 'Bibliography']:
				heading = content_div.find(['h2', 'h3'], id=section_id)
				if heading:
					parent_div = heading.find_parent('div', class_='mw-heading')
					if parent_div:
						parent_div.decompose()

			# Convert <h2> to <b> and insert <hr> after, with <br><br> before
			for h2 in content_div.find_all('h2'):
				new_structure = soup.new_tag('div')
				
				br1 = soup.new_tag('br')
				br2 = soup.new_tag('br')
				b_tag = soup.new_tag('b')
				hr_tag = soup.new_tag('hr')
				
				b_tag.string = h2.get_text()
				
				new_structure.append(br1)
				new_structure.append(br2)
				new_structure.append(b_tag)
				new_structure.append(hr_tag)
				
				h2.replace_with(new_structure)

			# Unwrap <i> tags
			for i_tag in content_div.find_all('i'):
				i_tag.unwrap()

			# Decompose <sup> tags
			for sup_tag in content_div.find_all('sup'):
				sup_tag.decompose()

			# Remove div with id "catlinks" if it exists
			catlinks = content_div.find('div', id='catlinks')
			if catlinks:
				catlinks.decompose()

			# Remove divs with class "reflist"
			for div in content_div.find_all('div', class_='reflist'):
				div.decompose()
			
			# Remove divs with class "sistersitebox"
			for div in content_div.find_all('div', class_='sistersitebox'):
				div.decompose()

			# Remove divs with class "thumb"
			for div in content_div.find_all('div', class_='thumb'):
				div.decompose()

			# Remove HTML comments
			for comment in content_div.find_all(text=lambda text: isinstance(text, Comment)):
				comment.extract()

			# Remove divs with class "navbox"
			for navbox in content_div.find_all('div', class_='navbox'):
				navbox.decompose()
			
			# Remove divs with class "navbox-styles"
			for navbox in content_div.find_all('div', class_='navbox-styles'):
				navbox.decompose()

			# Remove divs with class "printfooter"
			for div in content_div.find_all('div', class_='printfooter'):
				div.decompose()
			
			# Remove divs with class "refbegin"
			for div in content_div.find_all('div', class_='refbegin'):
				div.decompose()

			# Remove <link> tags
			for link in content_div.find_all('link'):
				link.decompose()

			# Remove all noscript tags
			for noscript_tag in soup.find_all('noscript'):
				noscript_tag.decompose()

			# Remove all img tags
			for img_tag in soup.find_all('img'):
				img_tag.decompose()

			# # Remove all class attributes to make page load faster
			# for tag in soup.find_all(class_=True):
			# 	del tag['class']
			
			# # Remove all ids to make page load faster
			# for tag in soup.find_all(id=True):
			# 	del tag['id']

			content = f"<b>{page_title}</b><hr>" + str(content_div)
			print(content)

		else:
			content = f"<h1>{page_title}</h1><p>Content not found.</p>"

		return process_html(content, f"{page_title} - Wikipedia"), 200

	except requests.RequestException as e:
		if e.response.status_code == 404:
			return process_html("<p>Page not found.</p>", f"Error - Wikipedia"), 404
		else:
			return process_html(f"<p>Error: {str(e)}</p>", "Error - Wikipedia"), 500

	except Exception as e:
		return process_html(f"<p>Error: {str(e)}</p>", "Error - Wikipedia"), 500