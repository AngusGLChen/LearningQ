'''
Created on Nov 30, 2017
@author: Guanliang Chen
'''

import os, json, urlparse

def main():
    path = '../../data/khan/khan_crawled_data/'
    
    collected_transcripts = set()
    if not os.path.isdir(path + "transcripts/"):
        os.mkdir(path + "transcripts/")
    transcript_files = os.listdir(path + "transcripts/")
    for transcript_file in transcript_files:
        collected_transcripts.add(transcript_file)    
    
    video_files = os.listdir(path + "videos/")    
    for video_file in video_files:
        video_jsonObject = json.loads(open(path + "videos/" + video_file, "r").read())
        video_youtube_link = video_jsonObject["video_youtube_link"]
        
        parsed = urlparse.urlparse(video_youtube_link)
        video_youtube_id = str(urlparse.parse_qs(parsed.query)['v'][0])
        
        if video_youtube_id not in collected_transcripts:            
            command = "python ./get_transcript.py " + video_youtube_link + " --file " + path + "transcripts/" + video_youtube_id
            os.system(command)           
                    
if __name__ == "__main__":
    main()
    print("Done.")