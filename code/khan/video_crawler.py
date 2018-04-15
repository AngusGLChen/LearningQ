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


def collect_video_discussion(path):
    video_link_map = json.loads(open(path + "all_video_links", "r").read())
    print("There is a total of %d video links." % len(video_link_map))
    
    # Considered topics
    considered_topic_array = ["science", "humanities", "computing", "partner-content", "economics-finance-domain", "test-prep", "college-careers-more", "math"]
    
    # Collected videos
    collected_videos= set()
    if not os.path.isdir(path + "updated_video_discussions/"):
        os.mkdir(path + "updated_video_discussions/")
    collected_files = os.listdir(path + "updated_video_discussions/")
    for collected_file in collected_files:
        if collected_file not in [".DS_Store"]:
            collected_videos.add(collected_file)
    
    # Collect video transcripts
    driver = webdriver.Chrome(executable_path='../chromedriver')
    driver.maximize_window()
    for youtube_id in video_link_map.keys():        
        if youtube_id not in collected_videos and os.path.exists(path + "transcripts/" + youtube_id):
            topic_category = video_link_map[youtube_id]["topic_category"]
            
            if topic_category not in considered_topic_array:
                continue
                        
            driver.get(video_link_map[youtube_id]["ka_url"])
            time.sleep(3)        
                                
            more_discussion_mark = True
            while more_discussion_mark:
                try:
                    element = driver.find_element_by_xpath("//input[@value='Show more comments']")
                    driver.execute_script("arguments[0].scrollIntoView();", element)
                    
                    driver.find_element_by_xpath("//input[@value='Show more comments']").click()
                    time.sleep(2)
                except Exception as e:
                    # print("More discussion button error...\t%s" % e)
                    more_discussion_mark = False
                    
            try:                
                discussion_array = []
                questions = driver.find_elements_by_xpath('//div[@class="thread "]/div[@class="question  discussion-item"]/div[@class="discussion-content"]')
                for question in questions:
                    discussion_array.append({"question": question.text, "answers":[]})
                
                if len(discussion_array) != 0:
                    save_file(discussion_array, path + "updated_video_discussions/" + youtube_id)
            except Exception as e:
                # print("Storing error...\t%s" % e)
                print(e)
                

def download_transcript_from_khan(path):
    video_link_map = json.loads(open(path + "all_video_links", "r").read())
    print("There is a total of %d video links." % len(video_link_map))
    
    # Collected videos
    collected_videos= set()
    if not os.path.isdir(path + "transcripts/"):
        os.mkdir(path + "transcripts/")         
    collected_files = os.listdir(path + "transcripts/")
    for collected_file in collected_files:
        if collected_file not in [".DS_Store"]:
            collected_videos.add(collected_file)
    print("There are %d video transcripts have been collected." % len(collected_videos))
    
    # Collect video transcripts
    driver = webdriver.Chrome(executable_path='../chromedriver')
    driver.maximize_window()
    
    for youtube_id in video_link_map.keys(): 
        if youtube_id not in collected_videos:
            driver.get(video_link_map[youtube_id]["ka_url"])
            time.sleep(2)          
            try:                
                element = driver.find_element_by_xpath("//a[contains(text(),'Transcript')]").click()     
                transcript = driver.find_element_by_xpath("//ul[@itemprop='transcript']").text        
                if transcript != "":
                    outFile = open(path + "transcripts/" + youtube_id, "w")
                    outFile.write(transcript)
                    outFile.close()                
                    collected_videos.add(youtube_id)                    
            except Exception as e:
                print(e)
            time.sleep(1)
            

def collect_video_links(path):
    # Check collected components
    collected_topics = set()
    if not os.path.isdir(path + "topic_videos/"):
        os.mkdir(path + "topic_videos/")
    files = os.listdir(path  + "topic_videos/")
    for file in files:
        collected_topics.add(file)
    print("%d topics have been processed." % len(collected_topics))
    
    # Course components (topics) => Filter out non-EN components
    course_components = set()
    topics = os.listdir(path + "topics/")
    for topic in topics:
        if topic != ".DS_Store":
            object = json.loads(open(path + "topics/" + topic, "r").read())
            if object["source_language"] == "en":
                course_components.add(topic)
    print("There are %d course components." % len(course_components))
    
    # Download video list for each topic
    for topic in course_components:
        try:
            if topic not in collected_topics:
                time.sleep(1)
                video_api = "http://www.khanacademy.org/api/v1/topic/" + topic + "/videos"
                response = urllib2.urlopen(video_api)
                videos = json.loads(response.read())
                if len(videos) != 0:
                    save_file(videos, path + "topic_videos/" + topic)
                collected_topics.add(topic)
        except:
            time.sleep(10)
    
    # Extract video links
    topic_hierarchy = gather_topic_hierarchy(path)
    component_topic_relation = {}
    for topic in topic_hierarchy.keys():
        for component in topic_hierarchy[topic]:
            component_topic_relation[component] = topic
            
    video_link_map = {}
    video_files = os.listdir(path + "topic_videos/")
    for video_file in video_files:
        if video_file != ".DS_Store":
            object = json.loads(open(path + "topic_videos/" + video_file, "r").read())
            for tuple in object:
                video_link_map[tuple["youtube_id"]] = {"ka_url":tuple["ka_url"], "component_name":video_file, "topic_category":component_topic_relation[video_file]}
    print("There is a total of %d videos." % len(video_link_map))
    save_file(video_link_map, path + "all_video_links")
    

def iterate_topictree_nodes(object, level, array):   
    if isinstance(object, dict) and "children" in object.keys():
        array.append(object["relative_url"])
        for sub_object in object["children"]:
            iterate_topictree_nodes(sub_object, level+1, array)
    elif isinstance(object, list):
        pass

  
def get_topic_links(path, url):
    # ==> Download topictrees
    response = urllib2.urlopen(url)
    topictree = response.read()
    save_file(topictree, path + 'topictree.json')
    
    # ==> Iterate over the whole topictree
    level = 0
    course_components = []
    iterate_topictree_nodes(json.loads(topictree), level, course_components)
    # save_file(course_components, path + "course_components")
    
    # ==> Collect links for each topic
    if not os.path.isdir(path + 'topics'):
        os.mkdir(path + 'topics')
    processed_topics = set()
    files = os.listdir(path  + "topics")
    for file in files:
        processed_topics.add(file)
    print("%d topics have been processed." % len(processed_topics))
    
    for component in course_components:
        try:
            topic = component.split("/")[-1]
            if topic != '' and topic not in processed_topics:
                time.sleep(1)
                exercise_api = "http://www.khanacademy.org/api/v1/topic/" + topic
                response = urllib2.urlopen(exercise_api)
                response = json.loads(response.read())
                save_file(response, path + "topics/" + topic)
                processed_topics.add(topic)
        except Exception as e:
            print(e)
            time.sleep(10)
        
   
######################################################################    
def main():
    data_path = '../../data/khan/khan_crawled_data/'

    # Step 1: retrieve and save topictree file
    url = 'http://www.khanacademy.org/api/v1/topictree'
    get_topic_links(data_path, url)
        
    # Step 2: collect video links
    collect_video_links(data_path)

    # Step 3: download video transcripts
    download_transcript_from_khan(data_path)
    
    # Step 4: gather discussion on video
    collect_video_discussion(data_path)


if __name__ == "__main__":
    main()
    print("Done.")