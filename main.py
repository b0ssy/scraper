import datetime
import hashlib
import io
import os
import time

from PIL import Image
import requests
from selenium import webdriver

'''
Guide: https://towardsdatascience.com/image-scraping-with-python-a96feda8af2d
Download chromedriver: https://chromedriver.chromium.org/downloads
'''


def fetch_image_urls(query: str, max_links_to_fetch: int, wd: webdriver, sleep_between_interactions: int = 1):
    def scroll_to_end(wd):
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep_between_interactions)

        # build the google query

    search_url = "https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img"

    # load the page
    wd.get(search_url.format(q=query))

    image_urls = set()
    image_count = 0
    results_start = 0
    while image_count < max_links_to_fetch:
        scroll_to_end(wd)

        # get all image thumbnail results
        thumbnail_results = wd.find_elements_by_css_selector("img.Q4LuWd")
        number_results = len(thumbnail_results)

        print(f"Found: {number_results} search results. Extracting links from {results_start}:{number_results}")

        for img in thumbnail_results[results_start:number_results]:
            # try to click every thumbnail such that we can get the real image behind it
            try:
                img.click()
                time.sleep(sleep_between_interactions)
            except Exception:
                continue

            # extract image urls
            actual_images = wd.find_elements_by_css_selector('img.n3VNCb')
            for actual_image in actual_images:
                if actual_image.get_attribute('src') and 'http' in actual_image.get_attribute('src'):
                    image_urls.add(actual_image.get_attribute('src'))

            image_count = len(image_urls)

            if len(image_urls) >= max_links_to_fetch:
                print(f"Found: {len(image_urls)} image links, done!")
                break
        else:
            print("Found:", len(image_urls), "image links, looking for more ...")
            # time.sleep(30)
            # return
            load_more_button = wd.find_element_by_css_selector(".mye4qd")
            if load_more_button:
                wd.execute_script("document.querySelector('.mye4qd').click();")

        # move the result startpoint further down
        results_start = len(thumbnail_results)

    return image_urls


def persist_image(folder_path: str, url: str):
    os.makedirs(folder_path, exist_ok=True)

    image_content = None
    try:
        image_content = requests.get(url).content
    except Exception as e:
        print(f"ERROR - Could not download {url} - {e}")
    try:
        image_file = io.BytesIO(image_content)
        image = Image.open(image_file).convert('RGB')
        file_path = os.path.join(folder_path, hashlib.sha1(image_content).hexdigest()[:10] + '.jpg')
        with open(file_path, 'wb') as f:
            image.save(f, "JPEG", quality=85)
        print(f"SUCCESS - saved {url} - as {file_path}")
    except Exception as e:
        print(f"ERROR - Could not save {url} - {e}")


# must match your chrome version
# https://chromedriver.chromium.org/downloads
chromedriver_path = 'chromedriver.exe'

query = 'haha'  # image keyword
folder_path = 'images'  # folder path to store images
max_links_to_fetch = 200  # max image urls to fetch

# date prefix for folder
folder_date_prefix = datetime.datetime.now().strftime('%y%m%d_%H%M%S')

# create selenium chromedriver
wd = webdriver.Chrome(chromedriver_path)

# fetch all image urls at 1second interval
urls = fetch_image_urls(query, max_links_to_fetch, wd)

# download images
for url in urls:
    persist_image(os.path.join(folder_path, f'{folder_date_prefix}_{query}'), url)

# shutdown selenium chromedriver
wd.quit()
