'''
Created on Dec 1, 2017
@author: Guanliang Chen
'''

import sys
reload(sys)
sys.setdefaultencoding("utf-8")


from code.functions import save_file, gather_topic_hierarchy
import urllib2, json, os, time
from selenium import webdriver
    

def collect_article_discussion(path):
    article_map = json.loads(open(path + "all_article_links", "r").read())
    print("There is a total of %d articles." % len(article_map))
    
    # Collected articles
    collected_articles= set()
    if not os.path.isdir(path + "article_discussions/"):
        os.mkdir(path + "article_discussions/")
    collected_files = os.listdir(path + "article_discussions/")
    for collected_file in collected_files:
        if collected_file not in [".DS_Store"]:
            collected_articles.add(collected_file)
    print("There are %d article discussion have been collected." % len(collected_articles))
    
    # Collect article discussions
    driver = webdriver.Chrome(executable_path='../chromedriver')
    driver.maximize_window()
    
    for article_id in article_map.keys():             
        if article_id not in collected_articles and os.path.exists(path + "articles/" + article_id):
                        
            driver.get(article_map[article_id]["ka_url"])
            time.sleep(3)
            
            more_mark = True
            while more_mark:
                try:                    
                    element = driver.find_element_by_xpath("//input[@value='Show more comments']")
                    driver.execute_script("arguments[0].scrollIntoView();", element)
                    
                    driver.find_element_by_xpath("//input[@value='Show more comments']").click()
                    time.sleep(3)
                except:
                    # print("More discussion button error...\t%s" % e)
                    more_mark = False
            
            try:                
                discussion_array = []
                questions = driver.find_elements_by_xpath('//div[@class="thread "]/div[@class="question  discussion-item"]/div[@class="discussion-content"]')
                for question in questions:
                    discussion_array.append({"question": question.text, "answers":[]})
                    
                if len(questions) != 0:
                    save_file(discussion_array, path + "article_discussions/" + article_id)
                    collected_articles.add(article_id) 
            except Exception as e:
                # print("Storing error...\t%s" % e)
                print(e)


def download_articles(path):
    article_map = json.loads(open(path + "all_article_links", "r").read())
    print("There is a total of %d articles." % len(article_map))
    
    collected_articles = set()
    if not os.path.isdir(path + "articles/"):
        os.mkdir( + "articles/")
    article_files = os.listdir(path + "articles/")
    for article_file in article_files:
        if article_file != ".DS_Store":
            collected_articles.add(article_file)
    print("There are %d articles have been collected." % len(collected_articles))
    
    for article_id in article_map.keys():
        if article_id not in collected_articles:
            try:
                article_api = "http://www.khanacademy.org/api/v1/articles/" + article_id
                response = urllib2.urlopen(article_api)
                article = json.loads(response.read())
                save_file(article, path + "articles/" + article_id)
            except:
                # print("http://www.khanacademy.org/api/v1/articles/" + article_id)
                pass
                

def gather_article_ids(path):
    topic_hierarchy = gather_topic_hierarchy(path)
    component_topic_relation = {}
    for topic in topic_hierarchy.keys():
        for component in topic_hierarchy[topic]:
            component_topic_relation[component] = topic
    
    article_map = {}
    topic_files = os.listdir(path + "topics/")
    for topic_file in topic_files:
        if topic_file != ".DS_Store":
            jsonObject = json.loads(open(path + "topics/" + topic_file, "r").read())
            for tuple in jsonObject["children"]:
                if tuple["kind"] == "Article":
                    article_map[tuple["internal_id"]] = {"ka_url":tuple["url"], "topic_category":component_topic_relation[topic_file]}
                    
    print("There is a total of %d articles." % len(article_map))
    save_file(article_map, path + "all_article_links")



######################################################################    
def main():
    data_path = '../../data/khan/khan_crawled_data/'
    
    # Step 1: gather article list
    gather_article_ids(data_path)
    
    # Step 2: download articles
    download_articles(data_path)

    # Step 3: gather discussions
    collect_article_discussion(data_path)
    


            
if __name__ == "__main__":
    main()
    print("Done.")