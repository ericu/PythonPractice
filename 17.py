#!/usr/bin/python3

import requests
from bs4 import BeautifulSoup

url = "https://www.nytimes.com/"
html = requests.get(url).text
soup = BeautifulSoup(html, features="html.parser")
#print(soup.prettify())

#span class="balancedHeadline"
# All H3s.

#headlines = soup.find_all("span", class_="balancedHeadline")
headlines = soup.find_all("h3")
nonName = filter(lambda t : not ('eog7260' in t['class']), headlines)
for tag in nonName:
  print(tag)
