'''
Created on 1 Dec 2017
@author: Guanliang Chen
'''

import json, nltk
from langdetect import detect


def save_file(object, path):
    file = open(path, "w")
    file.write(json.dumps(object))
    file.close()
   
    
def check_language(text):
    mark = False
    try:
        if detect(text) == "en":
            mark = True
    except:
        pass
    return mark


def tokenize_text(text):
    # Lowercase, replace tabs, striping    
    text = text.lower().replace('\n', ' ').strip()
    return " ".join(nltk.word_tokenize(text))


def gather_subtopics(object, topic_hierarchy):
    if isinstance(object, dict) and "children" in object.keys():        
        main_topic = object["relative_url"].split("/")[1]
        topic = object["relative_url"].split("/")[-1]
        topic_hierarchy[main_topic].append(topic)
        for sub_object in object["children"]:
            gather_subtopics(sub_object, topic_hierarchy)            
    elif isinstance(object, list):
        pass
 
      
def gather_topic_hierarchy(path):
    topictree_object = json.loads(open(path + "topictree.json").read())
    topic_hierarchy = {}
    for element in topictree_object["children"]:
        topic = element["domain_slug"]
        topic_hierarchy[topic] = []
        for sub_element in element["children"]:
            gather_subtopics(sub_element, topic_hierarchy)
    return topic_hierarchy