import requests
import json
import secret
from requests_oauthlib import OAuth1
# from requests_html import HTMLSession
import dryscrape
from bs4 import BeautifulSoup as bs
import sqlite3

API_KEY = secret.API_KEY
API_TOKEN = secret.API_TOKEN
API_SECRET = secret.API_SECRET
HTML_CACHE_FILE = "html_cache.json"
API_CACHE_FILE = 'api_cache.json'


oauth = OAuth1(API_KEY,
                client_secret=API_SECRET,
                resource_owner_key=API_TOKEN)
url = "https://api.trello.com/1/members/kevan_lee/cards"
first_url = 'https://api.trello.com/1/members/me/boards'
template_url = 'https://trello.com/templates/business'

headers = {
   "Accept": "application/json"
}

# temp_response = requests.get(template_url)
# temp_soup = bs(temp_response.text, 'html.parser')
# print(temp_soup.prettify())

# response = requests.get(url,headers=headers,auth=oauth)
# # print(response)
# body=response.text
# result=json.loads(body)
# print(result)


# cache html
def scrape_html(template_url):
   # session = dryscrape.Session()
   # session.visit(template_url)
   # response = session.body()
   response = requests.get(template_url)
   text = response.text
   soup = bs(text, 'html.parser')
   template_list = soup.find('html')
   return template_list


def scrape_html_with_cache(template_url):
   if template_url in HTML_CACHE:
      return HTML_CACHE[template_url]
   else:
      HTML_CACHE[template_url] = scrape_html(template_url)
      save_cache(HTML_CACHE, HTML_CACHE_FILE)
      return HTML_CACHE[template_url]


# cache api
def request_api(url):
   response = requests.get(url, headers=headers, auth=oauth)
   # print(response)
   body = response.text
   result = json.loads(body)
   return result

API_CACHE = {}

def request_api_with_cache(url):
   if url in API_CACHE:
      return API_CACHE[url]
   else:
      API_CACHE[url] = request_api(url)
      save_cache(API_CACHE, API_CACHE_FILE)
      return API_CACHE[url]


def open_cache(filename):
    try:
        cache_file = open(filename, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict, filename):
   dumped_json_cache = json.dumps(cache_dict)
   fw = open(filename,"w")
   fw.write(dumped_json_cache)
   fw.close()


HTML_CACHE = open_cache(HTML_CACHE_FILE)
API_CACHE = open_cache(API_CACHE_FILE)

scrape_html_with_cache(template_url)
request_api_with_cache(url)


DB_NAME = 'trello_contributor.sqlite'

def create_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    drop_contributors_sql = 'DROP TABLE IF EXISTS "Contributors"'
    drop_cards_sql = 'DROP TABLE IF EXISTS "Cards"'

    create_contributors_sql = '''
        CREATE TABLE IF NOT EXISTS "Contributors" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "url" varchar(255) NOT NULL,
            "user_name" varchar(255) NOT NULL,
            "date" DATE,
            "num_of_actions" INTEGER,
            "number_of_boards" INTEGER,
            "card_id" INTEGER
            FOREIGN KEY(card_id) REFERENCES Cards(id)
        )
    '''
    create_cards_sql = '''
        CREATE TABLE IF NOT EXISTS 'Cards'(
            'id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'content' TEXT,
            'is_template' INTEGER,
            'num_of_comments' INTEGER,
        )
    '''


    cur.execute(drop_contributors_sql)
    cur.execute(drop_cards_sql)
    cur.execute(create_contributors_sql)
    cur.execute(create_cards_sql)
    conn.commit()
    conn.close()
