'''

    This script crawls a subset of the wikipedia articles from the wikipedia title list

'''


import requests
import crawler.parse as parse
import concurrent.futures
import json
import sys

# open the page list for wikipedia articles

def title_from_line(line):
    return line[1:].replace(" ","").replace("\n","").replace("\t","")




crawl_start = int(sys.argv[1])
crawl_end = int(sys.argv[2])

in_container = True

pages_to_crawl = crawl_end - crawl_start
# moniter the amount of pages that have been crawled in the current run 
pages_crawled = 0

titles = list()

if in_container:
    titles_path = "/docker-volume/wikipedia/enwiki-titles"
    save_path = save_path = f"/docker-volume/index/image_queue/wikipedia/wikipedia_{crawl_start}-{crawl_end}.json"
else:
    titles_path = "/home/wikipedia/enwiki-titles"
    save_path = f"/home/volume/index/image_queue/wikipedia/wikipedia_{crawl_start}-{crawl_end}.json"

print("opening titles file")
# open the title file, and grab a subset of the titles without opening the entire file (there would not be enough RAM to open up the entire file)
with open(titles_path) as f:
    for i, line in enumerate(f):

        # make sure that we are just grabbing titles from the range of titles to be crawled in the current run 
        if i < crawl_start:
            continue
        if i > crawl_end:
            print("finished reading title file")
            break

        # parse and store the title 
        title = title_from_line(line)
        titles.append(title)


def process_title(title):

    # make our url from the title 
    url = "https://en.wikipedia.org/wiki/" + title

    # wikipedia treats me better
    headers = {'User-Agent': 'BaleneSearchCrawler/0.0 (http://138.68.149.96:8000/search; cjryanwashere@gmail.com'}

    # get the html for the web page
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        html_content = response.text  


        # this should work generally
        image_urls, text_sections = parse.extract_general_html(html_content, url)

        # iterate through the image urls
        for image_url in image_urls:
            if not image_url in image_set:
                image_set.add(image_url)

   

                image_upsert_request = {
                "image_url" : image_url,
                "page_url" : url
                }

                image_queue.append(image_upsert_request)
        
        global pages_crawled
        pages_crawled = pages_crawled + 1
        print(f"({pages_crawled} / {pages_to_crawl}) page: {title}, images: {len(image_urls)}") 
    else:
        print(f"failed to open page: {url}")
        #with open(f"/home/wikipedia/error_html/error_{title}.html",'w') as f:
        #    f.write(response.text)
        #print("wrote response html")

# a list of all the image upsert requests produced from the current session
image_queue = list()

# set of all images that have already been added to the queue
image_set = set()

print(f"crawling subset of wikipedia titles: {crawl_start} -> {crawl_end}")

# concurrently download each page in the web site
with concurrent.futures.ThreadPoolExecutor(max_workers=80) as executor:
  executor.map(process_title, titles)

# the path to save the crawling progress
#save_path = f"/home/volume/index/image_queue/wikipedia/wikipedia_{crawl_start}-{crawl_end}.json"
# adjusted for container volume
#save_path = f"/docker-volume/index/image_queue/wikipedia/wikipedia_{crawl_start}-{crawl_end}.json"


print(f"completed crawling with {len(image_queue)} image urls")
with open(save_path,'w') as f:
    json.dump(image_queue, f)

