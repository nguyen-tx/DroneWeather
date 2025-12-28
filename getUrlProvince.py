import requests
from bs4 import BeautifulSoup

filename = "province_urls.txt"
url = "https://nchmf.gov.vn/kttv/vi-VN/1/index.html"
r = requests.get(url)
soup = BeautifulSoup(r.text, "html.parser")

province_links = []
for link in soup.find_all("a", href=True):
    href = link['href']
    if href.endswith(".html") and "-w" in href:
        province_links.append(href)

with open(filename, "w", encoding="utf-8") as f:
    for u in province_links:
        f.write(u + "\n")