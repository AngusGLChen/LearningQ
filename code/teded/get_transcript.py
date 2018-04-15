#!/usr/bin/env python

# -*- coding: utf-8 -*-

import urllib2
import re
import argparse
import sys
import os
import urlparse
import subprocess


# Set up argument parsing.
parser = argparse.ArgumentParser(description='Retrieve plain text transcripts from YouTube videos.')
parser.add_argument('youtube_url', metavar='url', help='The URL to the YouTube video you want to'
                                                       ' retrieve a transcript for.')
parser.add_argument('--file', help='The path to the file you want to save transcript to. '
                                   'To use the video\'s title as the filename, specify a directory.'
                                   ' Example: ~/Desktop/transcript.txt or ~/Desktop', action='store', dest='file')
parser.add_argument('--overwrite', help='Overwrites existing file at save location, if present.', action='store_true')
parser.add_argument('--open', help='Open the created transcript.', action='store_true')
parser.add_argument('--reducenewlines', help='Remove all newlines except those immediately following a period.',
                    action='store_true')
parser.add_argument('--printfilepath', help='Prints the outfile file path on console.', action='store_true')

args = parser.parse_args()

# Detect the current platform for platform-specific code later on.
if sys.platform.startswith('darwin'):
    platform = 'mac'
elif os.name == 'nt':
    platform = 'windows'
elif os.name == 'posix':
    platform = 'linux'
else:
    platform = 'unknown'


class VidProperties:
    """Get and store video attributes (ID & Title)."""
    def __init__(self):
        self.id = None
        self.title = None
        self.transcript = None
        self.filename = None
        try:
            self.id = parse_url(args.youtube_url)
        except ValueError:
            print 'ERROR: You do not appear to have entered a valid YouTube address.'
            sys.exit(1)
        self.title = get_title(self.id)
        self.filename = create_filename(self.title)


def parse_url(vid_url):
    """
    Take video URL, perform basic sanity check, then filter out video ID.
    @param vid_url: URL of the video to get transcript from.
    @type vid_url: str
    """
    if 'watch?v' in vid_url:
        vid_code = re.findall(ur'^[^=]+=([^&]+)', vid_url)
    elif 'youtu.be/' in vid_url:
        vid_code = re.findall(ur'youtu\.be/([^&]+)', vid_url)

    else:
        raise ValueError()
    return vid_code[0]


def get_title(vid_id):
    """
    Get title of video from ID.
    @param vid_id: YouTube ID for the video.
    @type vid_id: str
    """
    video_info = urllib2.urlopen('http://youtube.com/get_video_info?video_id=' + vid_id)
    video_info = video_info.read()
    if urlparse.parse_qs(video_info)['status'][0] == 'fail':
        print "WARNING: Couldn't get video title. This probably means you specified an invalid URL."
        return None
    else:
        return urlparse.parse_qs(video_info)['title'][0]


def get_transcript():
    """Retrieve XML transcript from video ID. Works for human-created transcripts only."""
    not_found_error = 'ERROR: No transcript found. This can mean one of several things:\n- There is no ' \
                      'human-created transcript for this video.\n- The video URL was entered incorrectly.\n' \
                      '- The video has "burned-on" captions, where the captions are part of the video track. ' \
                      'There is no way to extract burned-in captions.'
    try:
        transcript = urllib2.urlopen('http://video.google.com/timedtext?lang=en&v=' + vidinfo.id)
        transcript_xml = transcript.read()
    except urllib2.HTTPError as error:
        if '404' in str(error):
            print not_found_error
            sys.exit(1)
        else:
            raise error

    if '<transcript>' not in transcript_xml:
        print not_found_error
        sys.exit(1)
    return transcript_xml


def remove_extra_linebreaks(string):
    """
    Remove extraneous linebreaks from text.
    If line ends with a period, insert a linebreak.
    @param string: The transcript to remove breaks from.
    @type string: str
    @return: Formatted text.
    """
    string_by_line = string.split('\n')
    new_string = str()
    for line in string_by_line:
        if line.endswith('.'):
            new_string += line + '\n'
        else:
            new_string += line + ' '
    return new_string


def format_transcript(transcript):
    """
    Receives the full XML transcript as plain text.
    @param transcript: Transcript as XML file.
    @type transcript: str
    """
    # Remove XML tags.
    transcript = re.sub("</text>", "\n", transcript)
    transcript = re.sub("<[^>]+>", "", transcript)

    # Remove encoded HTML tags.
    transcript = re.sub("&lt;.*?&gt;", "", transcript)

    # Replace ASCII character codes with the actual character.
    rep = {"&amp;#39;": "'", "&amp;gt;": ">", "&amp;quot;": '"', "&amp;lt;": "<"}

    # Slick single-pass regex replacement.
    rep = dict((re.escape(k), v) for k, v in rep.iteritems())
    pattern = re.compile("|".join(rep.keys()))
    transcript = pattern.sub(lambda m: rep[re.escape(m.group(0))], transcript)

    # Remove all newlines except those immediately following a period to improve readability.
    if args.reducenewlines:
        transcript = remove_extra_linebreaks(transcript)

    # If text is more than 75% capitalized, we make it all lowercase for easier reading.
    num_upper_chars = len((re.findall("[A-Z]", transcript)))
    num_chars = len((re.findall("[a-zA-Z]", transcript)))
    percent_upper = (float(num_upper_chars) / float(num_chars)) * 100
    if percent_upper >= 75:
        transcript = transcript.lower()

    return transcript


def create_filename(title):
    """
    Create filename-safe version of video title.
    @param title: Title of the video.
    @type title: str
    """
    # Remove characters that will cause problems in filenames.
    rep = {"/": "-", ":": " -", "\\": '-', "<": "-", ">": "-", "|": "-", "?": "", "*": ""}

    rep = dict((re.escape(k), v) for k, v in rep.iteritems())
    pattern = re.compile("|".join(rep.keys()))

    return pattern.sub(lambda m: rep[re.escape(m.group(0))], title)


# EXECUTION START HERE.

# Collect the video, ID, transcript and title.
vidinfo = VidProperties()
raw_transcript = get_transcript()
vidinfo.transcript = format_transcript(raw_transcript)

# Validate output path.
outfile = os.path.expanduser(args.file)

# If user has not specified a filename, use the video title.
if os.path.isdir(outfile):
    outfile = os.path.join(outfile, vidinfo.filename + '.txt')

# Check if output file already exists.
if not args.overwrite:
    if os.path.isfile(outfile):
        print 'ERROR: A file already exists in the same place with the same name.\n' \
              'Please specify a different name or location.'
        sys.exit(1)

# Write transcript to file.
try:
    with open(outfile, 'w') as output_file:
        output_file.write('Title: ' + vidinfo.title + '\n\n')
        output_file.write(vidinfo.transcript)
except IOError as errtext:
    if 'No such file or directory' in str(errtext):
        print "ERROR: The destination folder you've specified does not exist. Please check the path and try again."
        sys.exit(1)
    else:
        raise errtext

# Print filename to console.
if args.printfilepath:
    print outfile

# Open created file.
if args.open:
    if platform == 'mac':
        subprocess.call(['open', outfile])
    elif platform == 'windows':
        os.startfile(outfile)
    elif platform == 'linux':
        subprocess.call(('xdg-open', outfile))
    else:
        print 'WARNING: Cannot detect your operating system. Unable to open the transcript file automatically.'
