'''
Created on Nov 26, 2017
@author: Guanliang Chen
'''

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import json, os, time, random, shutil
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains


def merge_gather_data(path):
    
    data_dump = []
    
    # Gather category relation
    category_file = open(path + "category_video_relation", "r")
    category_video_map = json.loads(category_file.read())
    video_set = set()
    video_category_map = {}
    
    title_link_map = {}
    title_set = set()
     
    for category in category_video_map.keys():
        videos = category_video_map[category]
        for video in videos:
            if video["url"] not in video_set:
                video_set.add(video["url"])
                video_category_map[video["url"]] = []
            video_category_map[video["url"]].append(category)
            
            url = video["url"]
            title = video["video_title_length"]
            if title not in title_set:
                title_set.add(title)
                title_link_map[title] = []
            
            title_link_map[title].append(category)
            
    
    
    # Gather collected videos
    video_files = os.listdir(path + "ted_videos/")
    for video_file in video_files:
        video_object = json.loads(open(path + "ted_videos/" + video_file, "r").read())
        video_youtube_link = video_object["video_youtube_link"]
        
        parsed = urlparse.urlparse(video_youtube_link)
        video_youtube_id = str(urlparse.parse_qs(parsed.query)['v'][0])
        
        if os.path.exists(path + "transcripts/" + video_youtube_id):
            transcript_file = open(path + "transcripts/" + video_youtube_id)
            transcript = transcript_file.read()
            lines = transcript.split("\n")
            
            index = None
            for i in range(len(lines)):
                if lines[i] == "":
                    index = i + 1
                    break
            
            processed_transcript = ""
            for i in range(index, len(lines)):
                processed_transcript += (lines[i] + " ")
            # processed_transcript = processed_transcript.lower().strip()
            
            video_object["transcript"] = processed_transcript
            if video_object["video_title_length"] in title_link_map.keys():
                video_object["categories"] = title_link_map[video_object["video_title_length"]]
            else:
                video_object["categories"] = []
            
            if "quizzes" in video_object.keys():
                data_dump.append(video_object)
    
    out_file = open(path + "data_dump", "w")
    out_file.write(json.dumps(data_dump))
    out_file.close()
 


def collect_category_relation(path):    
    driver = webdriver.Chrome(executable_path='../chromedriver')
    driver.maximize_window()
    
    home_link = "https://ed.ted.com/lessons"
    category_tuples = []
    
    driver.get(home_link)
    
    # Click "log in"
    click_action(driver, "//a[@href='/session']")
    
    # Log in
    driver.find_element_by_xpath("//input[@id='user_email']").send_keys('')
    driver.find_element_by_xpath("//input[@id='user_password']").send_keys('')
    click_action(driver, "//input[@name='commit']")
    
    # Gather subject categories
    xml_categories = driver.find_elements_by_xpath("//li[@class='parent ']/a")
    for xml_category in xml_categories:
        category = xml_category.text
        category_link = xml_category.get_attribute('href')
        category_tuples.append([category, category_link])
        
    category_videos_map = {}
        
    for category_tuple in category_tuples:
        category = category_tuple[0]
        category_link = category_tuple[1]
        
        category_videos_map[category] = []        
               
        # Click a subject category and gather the number of total pages
        driver.get(category_link)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")        
        time.sleep(3)
        try:
            driver.find_element_by_xpath("//li[@class='last next']/a").click()
            total_pages = driver.find_element_by_xpath("//li[@class='page active']").text
            total_pages = int(total_pages)
        except:
            total_pages = 1
        
        for i in range(1, total_pages + 1):            
            video_group_link = category_link + "&page=" + str(i)
            driver.get(video_group_link)
                        
            videos = driver.find_elements_by_xpath("//div[@class='video-text']/a")
            
            for video in videos:
                url = video.get_attribute('href')     
                video_title_length = video.text
                category_videos_map[category].append({"video_title_length":video_title_length, "url":url})
                
    out_file = open(path + "category_video_relation", "w")
    out_file.write(json.dumps(category_videos_map))
    out_file.close()


def click_action(driver, xpath):
    element = driver.find_element_by_xpath(xpath)
    driver.execute_script("arguments[0].click();", element)
    time.sleep(2)
    

def collect_data(path):
    driver = webdriver.Chrome(executable_path='../chromedriver')
    driver.maximize_window()
    
    home_link = "https://ed.ted.com/lessons"            
    driver.get(home_link)
    
    # Click "log in"
    click_action(driver, "//a[@href='/session']")
    
    # Log in
    driver.find_element_by_xpath("//input[@id='user_email']").send_keys('')
    driver.find_element_by_xpath("//input[@id='user_password']").send_keys('')
    click_action(driver, "//input[@name='commit']")
    
    # Gather collected video list
    collected_videos = set()
    if not os.path.isdir(path + "videos/"):
        os.mkdir( + 'videos/')
    video_files = os.listdir(path + "videos/")
    for video_file in video_files:
        if video_file != ".DS_Store":
            collected_videos.add(json.loads(open(path + "videos/" + video_file,"r").read())["video_title_length"])
    print("There are %d collected videos." % len(collected_videos))
    
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")        
    time.sleep(3)
    driver.find_element_by_xpath("//li[@class='last next']/a").click()
    total_pages = driver.find_element_by_xpath("//li[@class='page active']").text
    total_pages = int(total_pages)
        
    for i in range(1, total_pages + 1):
        print("Processing page %d" % i)
        video_group_link = home_link + "?page=" + str(i)
        driver.get(video_group_link)
                
        videos = driver.find_elements_by_xpath("//div[@class='video-text']/a")
        video_tuples = []
        for video in videos:
            video_link = video.get_attribute('href')
            video_title_length = video.text
            video_tuples.append([video_link, video_title_length])
        
        for tuple in video_tuples:
            video_link = tuple[0]
            video_title_length = tuple[1]
                        
            try:
                                                
                if video_title_length in collected_videos:
                    continue
                
                video_json_object = {"video_link":video_link, "video_title_length":video_title_length}
                                                                             
                driver.get(video_link)
                video_description = driver.find_element_by_xpath("//div[@class='lessonDescription']").text
                video_json_object["video_description"] = video_description
                
                # Click the "Think" button
                try:
                    # For some videos, there is no quiz questions
                    time.sleep(0.5)
                    driver.find_element_by_xpath("//a[@id='think-link']")
                    click_action(driver, "//a[@id='think-link']")
                except:
                    # Locate the video
                    video_iframe = driver.find_element_by_xpath("//iframe[@id='playerContainer']")
                    driver.switch_to.frame(video_iframe)
                    video_youtube_link = driver.find_element_by_xpath("//a[@class='ytp-watermark yt-uix-sessionlink']").get_attribute('href')
                    video_json_object["video_youtube_link"] = video_youtube_link
                    
                    out_file = open(path + "videos/" + video_title_length, "w")
                    out_file.write(json.dumps(video_json_object))
                    out_file.close()
                    
                    continue
                                      
                # Locate the quizzes
                num_quiz_divs = 0
                while num_quiz_divs == 0:
                    quiz_divs = driver.find_elements_by_xpath("//div[@data-position]")
                    time.sleep(0.5)
                    num_quiz_divs = len(quiz_divs)
                               
                quizzes = []
                
                for j in range(num_quiz_divs):
                    # Loop over quizzes
                    driver.get(video_link + "/review_open#question-" + str(j+1))
                    time.sleep(0.5)
                    driver.get(video_link + "/review_open#question-" + str(j+1))
                    time.sleep(0.5)
                                   
                    open_question_mark = None
                    try:
                        driver.find_element_by_xpath("//div[@data-position=" + str(j) + "]//div[@class='panel-response']")
                        open_question_mark = True
                    except:
                        open_question_mark = False
                                        
                    # Quizzes
                    quiz_description = None
                    quiz_options = []
                    
                    if open_question_mark:
                        # For open-ended questions
                        
                        # Mouse hover
                        element = driver.find_element_by_xpath("//div[@data-position=" + str(j)+ "]//div[@class='panel-response']")
                        hover = ActionChains(driver).move_to_element(element)
                        hover.perform()
                        
                        quiz_description = driver.find_element_by_xpath("//div[@data-position=" + str(j)+ "]//div[@class='panel-response']/div/h5").text
                        quizzes.append({"quiz_description": quiz_description, "question_type":"open-ended"})
                                                
                    else:
                        # For multiple-choices questions
                        
                        # Mouse hover
                        element = driver.find_element_by_xpath("(//div[@class='question scroll uiScroll text-ultralight'])[1]")
                        hover = ActionChains(driver).move_to_element(element)
                        hover.perform()
                                             
                        # Collect textual information
                        quiz_text = driver.find_element_by_xpath("(//div[@class='question scroll uiScroll text-ultralight'])[1]").text                      
                        lines = quiz_text.split("\n")
                        quiz_description = lines[0]
                        
                        for k in range(1,len(lines),2):
                            letter_id = lines[k]
                            numerical_id = k/2
                            option = lines[k+1]
                            quiz_options.append({"letter_id":letter_id, "option_text":option, "numerical_id":numerical_id})
                            
                        # Collect answer & hint
                        hint_mark = False
                        answer_mark = False
                                       
                        correct_answer_id = None
                        hint = None
                                            
                        num_options = len(quiz_options)  
                        for k in range(num_options):
                            # Loop over options
        
                            # Go back to the quiz question                            
                            driver.get(video_link + "/review_open#question-" + str(j+1))
                            time.sleep(0.5)
                            driver.get(video_link + "/review_open#question-" + str(j+1))
                            time.sleep(0.5)         
                                                        
                            # Mouse hover
                            element = driver.find_element_by_xpath("//div[@class='clearfix a answer'][1]")
                            hover = ActionChains(driver).move_to_element(element)
                            hover.perform()                            
                            time.sleep(0.5)
                                                        
                            # Select answer
                            driver.find_element_by_xpath("(//div[@class='clearfix a answer'])[1]").click()                                                           
                            # Click "Save my answer"                           
                            driver.find_element_by_xpath("(//button[@class='check'])[" + str(k+1) +"]").click()
                            time.sleep(0.5)
                                                   
                            msg_mark = False
                            while not msg_mark:
                                try:                            
                                    msg_text = driver.find_element_by_xpath("//div[@class='g']").text
                                    msg_mark = True
                                except:
                                    time.sleep(0.5)                          
                            
                            if msg_text == "Correct!":
                                correct_answer_id = k
                                answer_mark = True
                                # print("correct answer %d" % correct_answer_id)                         
                            
                            if not hint_mark and "That wasn" in msg_text:
                                hint = driver.find_element_by_xpath("//button[@class='btnWhite vid']").get_attribute('data-seconds')
                                hint_mark = True
                                # print("hint is %s" % hint)
                                
                            if hint_mark and answer_mark:
                                break
                        
                        quizzes.append({"quiz_description": quiz_description, "question_type":"multiple-choices", "quiz_options":quiz_options, "hint": hint, "answer":correct_answer_id})                        
                        
                video_json_object["quizzes"] = quizzes
                
                # Locate the video
                video_iframe = driver.find_element_by_xpath("//iframe[@id='playerContainer']")
                driver.switch_to.frame(video_iframe)
                video_youtube_link = driver.find_element_by_xpath("//a[@class='ytp-watermark yt-uix-sessionlink']").get_attribute('href')
                
                video_json_object["video_youtube_link"] = video_youtube_link
                
                out_file = open(path + "videos/" + video_title_length, "w")
                out_file.write(json.dumps(video_json_object))
                out_file.close()
                
                collected_videos.add(video_title_length)                                                                      
            
            except:
                # print("Failed for %s" % video_title_length)
                pass        
    

def main():
    data_path = '../../data/teded/teded_crawled_data/'
    
    # Step 1: collect video-category information
    collect_category_relation(data_path)
    
    # Step 2: collect questions
    collect_data(data_path)
    
   
if __name__ == "__main__":
    main()
    print("Done.")
    
        
    