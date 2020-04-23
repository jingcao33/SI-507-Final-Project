import requests
import json
import secret
# from bs4 import BeautifulSoup as bs
import csv
import sqlite3

API_KEY = secret.API_KEY


API_CACHE_FILE = 'api_cache.json'


# oauth = OAuth1(API_KEY,
#                 client_secret=API_SECRET,
#                 resource_owner_key=API_TOKEN)
match_url = "https://api.yelp.com/v3/businesses/matches"
detail_url = "https://api.yelp.com/v3/businesses/"

headers = {
    'Authorization': 'Bearer ' + API_KEY
}




# # cache html
# def scrape_html(template_url):
#    # session = dryscrape.Session()
#    # session.visit(template_url)
#    # response = session.body()
#    response = requests.get(template_url)
#    text = response.text
#    soup = bs(text, 'html.parser')
#    template_list = soup.find('html')
#    return template_list


# def scrape_html_with_cache(template_url):
#    if template_url in HTML_CACHE:
#       return HTML_CACHE[template_url]
#    else:
#       HTML_CACHE[template_url] = scrape_html(template_url)
#       save_cache(HTML_CACHE, HTML_CACHE_FILE)
#       return HTML_CACHE[template_url]


def construct_unique_key(baseurl, params):
   param_strings = []
   connector = '_'
   for k in params.keys():
      param_strings.append(f'{k}_{params[k]}')
   param_strings.sort()
   unique_key = baseurl + connector + connector.join(param_strings)
   return unique_key


# cache api
def request_api(baseurl, params):
   response = requests.get(url=baseurl, params=params, headers=headers, )
   # print(response)
   body = response.text
   result = json.loads(body)
   return result

API_CACHE = {}

def request_api_with_cache(baseurl, params):
   request_key = construct_unique_key(baseurl, params)
   if request_key in API_CACHE:
      return API_CACHE[request_key]
   else:
      API_CACHE[request_key] = request_api(baseurl, params)
      save_cache(API_CACHE)
      return API_CACHE[request_key]


def open_cache(filename):
   try:
      cache_file = open(filename, 'r')
      cache_contents = cache_file.read()
      cache_dict = json.loads(cache_contents)
      cache_file.close()
   except:
      cache_dict = {}
   return cache_dict


def save_cache(cache_dict):
   dumped_json_cache = json.dumps(cache_dict)
   fw = open(API_CACHE_FILE,"w")
   fw.write(dumped_json_cache)
   fw.close()


# HTML_CACHE = open_cache(HTML_CACHE_FILE)


# scrape_html_with_cache(template_url)



DB_NAME = 'sf_restaurants.sqlite'

def create_db():
   conn = sqlite3.connect(DB_NAME)
   cur = conn.cursor()

   drop_inspection_sql = 'DROP TABLE IF EXISTS "Inspection"'

   create_inspection_sql = '''
      CREATE TABLE IF NOT EXISTS "Inspection" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "business_id" INTEGER NOT NULL,
            "business_name" varchar(255) NOT NULL,
            "business_address" varchar(255) NOT NULL,
            "business_zipcode" varchar(255) NOT NULL,
            "inspection_date" DATE,
            "inspection_score" INTEGER
      );
   '''

   drop_business_sql = 'DROP TABLE IF EXISTS "Business"'

   create_business_sql = '''
      CREATE TABLE IF NOT EXISTS "Business" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "name" varchar(255) NOT NULL,
            "zipcode" varchar(255) NOT NULL,
            "is_closed" INTEGER,
            "phone" varchar(255),
            "review_count" INTEGER,
            "rating" FLOAT,
            "price" varchar(255)
      );
   '''

   drop_cat_sql = 'DROP TABLE IF EXISTS "Cat"'

   create_cat_sql = '''
      CREATE TABLE IF NOT EXISTS "Cat" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "name" varchar(255) NOT NULL
      );
   '''

   drop_categories_sql = 'DROP TABLE IF EXISTS "Categories"'

   create_categories_sql = '''
      CREATE TABLE IF NOT EXISTS "Categories" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "business_id" INTEGER,
            "cat_id" INTEGER,
            FOREIGN KEY (business_id) REFERENCES Business (id),
            FOREIGN KEY (cat_id) REFERENCES Cat (id)
      );
   '''


   cur.execute(drop_inspection_sql)
   cur.execute(create_inspection_sql)
   cur.execute(drop_business_sql)
   cur.execute(create_business_sql)
   cur.execute(drop_cat_sql)
   cur.execute(create_cat_sql)
   cur.execute(drop_categories_sql)
   cur.execute(create_categories_sql)
   conn.commit()
   conn.close()


def load_insepction():
   file_contents = open('inspection.csv', 'r')
   csv_reader = csv.reader(file_contents)
   next(csv_reader)

   insert_inspection_sql = '''
   INSERT INTO Inspection
   VALUES (NULL, ?, ?, ?, ?, ?, ?)
   '''

   conn = sqlite3.connect(DB_NAME)
   cur = conn.cursor()
   for row in csv_reader:
      cur.execute(insert_inspection_sql, [
         row[0],
         row[1],
         row[2],
         row[3],
         row[4],
         row[5]
      ])
   conn.commit()
   conn.close()

create_db()
load_insepction()


def load_business():
   select_inspection_sql = '''
      SELECT DISTINCT business_name, business_address
      FROM Inspection
   '''

   conn = sqlite3.connect(DB_NAME)
   cur = conn.cursor()
   cur.execute(select_inspection_sql)
   business_ids = []
   for row in cur:
      business_name = row[0]
      business_address = row[1]
      params = {
      'name': business_name.lower(),
      'address1': business_address,
      'city': 'San Francisco',
      'state': 'CA',
      'country': 'US'
      }
      try:
         res = request_api_with_cache(baseurl=match_url, params=params)
         print(business_name)
         business_id = res['businesses'][0]['id']
         business_ids.append(business_id)
      except:
         print(business_name)
         pass
   return business_ids


categories = []
def insert_business(business_ids):
   insert_business_sql = '''
      INSERT INTO Business
      VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)
   '''

   conn = sqlite3.connect(DB_NAME)
   cur = conn.cursor()
   for business_id in business_ids:
      response = request_api_with_cache(baseurl=detail_url+business_id,
                                       params={'locale':'en_US'})
      if response['is_closed'] == False:
         is_closed = 0
      else:
         is_closed = 1
      name = response['name']
      phone = response['display_phone']
      review_count = response['review_count']
      rating = response['rating']
      zipcode = response['location']['zip_code']
      price = response['price']

      cur.execute(insert_business_sql, [
         name,
         zipcode,
         is_closed,
         phone,
         review_count,
         rating,
         price
      ])

      for category in response['categories']:
         if category['title'] in categories:
            pass
         else:
            categories.append(category['title'])

   conn.commit()
   conn.close()


def insert_cat():
   insert_cat_sql = '''
      INSERT INTO Cat
      VALUES (NULL, ?)
   '''
   conn = sqlite3.connect(DB_NAME)
   cur = conn.cursor()
   for category in categories:
      cur.execute(insert_cat_sql, [category])
   conn = sqlite3.connect(DB_NAME)
   cur = conn.cursor()




   #          cur.execute(select_cat_id_sql, [category])
   #          res = cur.fetchone()
   #          categories[category] = res[0]



   # select_cat_id_sql = '''
   #    SELECT id
   #    FROM Cat
   #    WHERE name = ?
   # '''

   # select_business_id_sql = '''
   #    SELECT id
   #    FROM Business
   #    WHERE name = ?
   # '''

   # insert_categories_sql = '''
   #    INSERT INTO Categories
   #    VALUES (NULL, ?, ?)
   # '''



   
   # b_id = 
   # response = requests.get(detail_url+b_id)


API_CACHE = open_cache(API_CACHE_FILE)
ids = load_business()
insert_business(ids)
insert_cat()
