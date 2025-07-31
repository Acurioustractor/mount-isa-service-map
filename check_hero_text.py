#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re

# Fetch the page
response = requests.get('https://mount-isa-service-map.vercel.app/')
soup = BeautifulSoup(response.text, 'html.parser')

# Look for hero section
hero = soup.find('section', class_='hero-section')
if hero:
    print("Hero section found:")
    print(hero.get_text(strip=True))
else:
    print("No hero section found")

# Look for any text containing service counts
text = response.text
service_patterns = [
    r'Serving \d+ services',
    r'\d+ services',
    r'supporting \d+ services',
    r'connecting.*\d+ services'
]

print("\n\nService count mentions found:")
for pattern in service_patterns:
    matches = re.findall(pattern, text, re.IGNORECASE)
    if matches:
        for match in matches[:5]:  # First 5 matches
            print(f"- {match}")

# Look for hero title/subtitle
title = soup.find('h1', class_='hero-title')
subtitle = soup.find('p', class_='hero-subtitle')

if title:
    print(f"\nHero title: {title.get_text(strip=True)}")
if subtitle:
    print(f"Hero subtitle: {subtitle.get_text(strip=True)}")