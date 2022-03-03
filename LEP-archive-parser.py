#!/usr/bin/env python3
# Copyright (c) 2019 Artem Hotenov (@hotenov). Available under the MIT License.
"""
    Python 3.5+ script for parsing the all FREE episodes
    of Luke's ENGLISH Podcast, available on its archive webpage
    https://teacherluke.co.uk/archive-of-episodes-1-149/

    Prerequisite:
    Installing of packages: requests, beautifulsoup4, lxml
                
"""

# Try import required packages
# usually exception messages scare user 
try:
    import requests
    from bs4 import BeautifulSoup
    import lxml
except ImportError:
    print("This 3 package (requests, beautifulsoup4, lxml) must be installed for script execution.")
    print("You can use 'pip' for that:\n\n" +
            "pip install requests\n" +
            "pip install beautifulsoup4\n" +
            "pip install lxml\n")
    print("Quit.")
    sys.exit(0)

import urllib.parse
import json
import re
from collections import namedtuple, OrderedDict
import platform

# If script was executed on Windows
# enable ANSI color codes on Windows using 'ctypes'
if platform.platform(aliased=0, terse=1).find("Windows") > -1:
    import ctypes
    #print(platform.platform(aliased=0, terse=1))
    # enable ANSI color codes on Windows
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
import time
import sys

# Version of the parser script
__version__ = "2.0.11"


# time start marker
start_time = time.time()

# ---------- [Text colorize functions] ----------------
fg = lambda text, color: "\33[38;5;" + str(color) + "m" + text + "\33[0m"
bg = lambda text, color: "\33[48;5;" + str(color) + "m" + text + "\33[0m"
# ---------- [END: Text colorize functions] -----------

keys_for_json = [
    "postId", "seqNumber", "date", "title",
    "episode", "postUrl", "postType", "pdfUrl",
    "newName", "oldName", "hasAudio",
    "audioFiles", "videoFiles", "audioTracks",
    "addons", "isUrl404", "pageParsingStatus",
    "originalFileName", "originalFileUrl", "fileExtension",
    "fileOldName", "fileNewName", "fileStorageUrl",
    "adminComment", "wasUpdatedByAdmin"]

MainKeys = namedtuple("MainKeys", keys_for_json)
# Dictionary keys 'dk' for treatment via dot
dk  = MainKeys(
    postId = "postId", seqNumber = "seqNumber", date = "date", title = "title",
    episode = "episode", postUrl = "postUrl", postType = "postType", pdfUrl = "pdfUrl",
    newName = "newName", oldName = "oldName", hasAudio = "hasAudio",
    audioFiles = "audioFiles", videoFiles = "videoFiles", audioTracks = "audioTracks",
    addons = "addons", isUrl404 = "isUrl404", pageParsingStatus = "pageParsingStatus",
    originalFileName = "originalFileName", originalFileUrl = "originalFileUrl", fileExtension = "fileExtension",
    fileOldName = "fileOldName", fileNewName = "fileNewName", fileStorageUrl = "fileStorageUrl",
    adminComment = "adminComment", wasUpdatedByAdmin = "wasUpdatedByAdmin")

# post type dictionary (using via dot)
PostType = namedtuple("PostType", "audio text video")
pt = PostType(audio="AUDIO", text="TEXT", video="VIDEO")

def get_utf8_response(session, page_url):
    """
    Get utf-8 Response from URL
    """
    # Create 'bad' Response for handling exceptions
    bad_req = requests.Response()
    bad_req.status_code = 404
    try:
        # By default 'allow_redirects' = True for wp.me links
        response = session.get(page_url, timeout=(6, 20))
        if response.ok:
            # Set response Encoding (speeds up the parsing process)
            response.encoding = "utf-8"
            return response
        else:
            return bad_req
    except requests.exceptions.ConnectionError:
        print(fg("Exception! ", 160) + "Bad Response for URL: " + page_url)
        return bad_req
    except requests.exceptions.Timeout:
        print(fg("Exception! ", 160) + "Timeout for URL: " + page_url)
        return bad_req
    except:
        print(fg("Unknown Exception!: ", 160) + page_url)
        return bad_req


def get_bs_object(page_content):
    """ Return Beautiful Soap object from text with lxml parser"""
    return BeautifulSoup(page_content, features="lxml")

def get_date_from_url(url):
    """ Return date as string "YYYY-MM-DD" """
    # Parse Date from URL
    YYYY_MM_DD = re.findall(r'(20\d\d)[- /.](0[1-9]|1[012])[- /.](0[1-9]|[12][0-9]|3[01])', url)
    if YYYY_MM_DD:
        date = "-".join(YYYY_MM_DD[0])
    else:
        date = "NO DATE"
    return date

# ---------- [Boolean functions (filters for arguments)] ----------------
def find_appropriate_tag_a(tag):
    """
    Return True if all conditions are met
    """
    if tag.string != None:
        return tag.has_attr('href') and (
            re.compile(r"^https?://teacherluke\.co\.uk|wp\.me|teacherluke\.wordpress\.com").search(tag.attrs['href'])
            and not (re.compile("phrasal-verb-a-day").search(tag.attrs['href'])
            or re.compile(r"^.{0,2}\[VIDEO\]", re.I).search(tag.string)
            or re.compile(r"Website content\].?$").search(tag.string)
            or re.compile(r"all Premium").search(tag.string)
            or re.compile(r"LEP App").search(tag.string)
            or re.compile(r"episode 522").search(tag.string)))
    else:
        return tag.has_attr('href') and re.compile(r'rock-n-roll-english-podcast|dvd-commentary|british-pop').search(tag.attrs['href'])
# ---------- [END: Boolean functions (filters for arguments)] -----------

def new_data_item(
        post_id, seq_number,  post_title, post_url, old_name, new_name = "",
        post_date = "NO DATE", episode_num = 0, post_type = "POST", pdf_url = "",
        has_audio = False, mp3_list = [],
        videos = [], audio_tracks = [], addons = [],
        is_broken_url = False, parsing_status = "OK",
        admin_comment = "", was_updated_by_admin = False):
    """
    Return data_info item as dict
    """
    return {
        dk.postId: post_id,
        dk.seqNumber: seq_number,
        dk.date: post_date,
        dk.title: post_title,
        dk.episode: episode_num,
        dk.postUrl: post_url,
        dk.postType: post_type,
        dk.pdfUrl: pdf_url,
        dk.oldName: old_name,
        dk.newName: new_name,
        dk.hasAudio: has_audio,
        dk.audioFiles: mp3_list,
        dk.videoFiles: videos,
        dk.audioTracks: audio_tracks,
        dk.addons: addons,
        dk.isUrl404: is_broken_url,
        dk.pageParsingStatus: parsing_status,
        dk.adminComment: admin_comment,
        dk.wasUpdatedByAdmin: was_updated_by_admin}

def ask_uer_to_print_json():
    """
    Asking user to print or not resulting json file
    If an exception occurred while writing a file
    """
    user_input = input(fg("Would you like to print it on screen? (Y/N): ", 87))
    if user_input in ["Y", "Yes", "YES"]:
        print(json.dumps(result_db, ensure_ascii=False, indent=4))
    else:
        print(bg(fg("Database file was NOT saved or printed.", 16), 136))
        pass


def get_stat_dict(data_dict, result_key, result_val, has_key, negation = False):
    """Return filtered dict for statistics"""
    if negation:
        filtered_dict = {
            v[result_key] : v[result_val]
            for k, v in data_dict.items() if not v[has_key]
        }
    else:
        filtered_dict = {
            v[result_key] : v[result_val]
            for k, v in data_dict.items() if v[has_key]
        }
    return filtered_dict



# Open session
s = requests.Session()
s.max_redirects = 10


# Get page content with list of posts
archive_page_url = "https://teacherluke.co.uk/archive-of-episodes-1-149/"
resp = get_utf8_response(s, archive_page_url)

if not resp.ok:
    print("\n- - - - - -\n" + bg("FAILED", 88)+ ": Script cannot get content of this URL:\n" 
        + archive_page_url + "\n- - - - - -\n")
    sys.exit(0) # is equivalent to exit(0)

soup = get_bs_object(resp.text)

# Get only main div container
posts_div = soup.find('div', {'class': 'entry-content'})
if posts_div == None:
    print(bg("\nEMPTY", 88) +": Cannot find div container with class='entry-content' on this URL:\n"
        + archive_page_url
        + fg("\nQuit.\n", 228))
    sys.exit(0)

print(fg("\n... Parsing START ... \n\n", 208))

# Replace href in tag 'a' with typo in URL "...luke.co.ukm"
try:
    tag_for_replace = posts_div.find('a', href=re.compile("london-olympics-2012"))
except AttributeError:
    print(fg("Not a soup object! Cannot replace tag here. Skip", 225))
    pass
if tag_for_replace == None:
    print(fg("Cannot find tag for replacing! Skip.", 225))
    pass
else:
    tag_for_replace['href'] = r'https://teacherluke.co.uk/2012/08/06/london-olympics-2012/'

#--IMPORTANT: Broke the URL if you need parse all posts again
url_to_lep_db = "https://hotenov.com/d/lep/raw-lep-db.json"
# Read dirty database file from web
print(fg("Getting database file from web.", 8))
resp = s.get(url_to_lep_db)
resp.encoding = "utf-8"
# Load data from json to dict
if resp.ok:
    web_lep_db = OrderedDict(resp.json())
    items_in_lep_db = len(web_lep_db)
    print(fg("Database from server was downloaded, all items = ", 8) + str(items_in_lep_db))
else:
    print(bg("404", 88) + ": Database is unavailable, "+ fg("parsing all pages...", 228))
    items_in_lep_db = 0
    web_lep_db = OrderedDict()


# Filter only appropriate links to post
cleaned_posts = posts_div.find_all(find_appropriate_tag_a)
all_post_number = len(cleaned_posts)
print(fg("There are: ", 8) + str(all_post_number) + fg(" posts on the website now.", 8))

if items_in_lep_db < all_post_number:
    updates_delta = all_post_number - items_in_lep_db
    # Get only new posts
    cleaned_posts = posts_div.find_all(find_appropriate_tag_a, limit=updates_delta)
    print(fg(str(updates_delta), 228) + " new posts " + fg("will be processed...", 228))
else:
    print(fg("There are NO NEW posts from the last website parsing.", 34) + fg("\nQuit.", 228))
    sys.exit(1)

# Iterate all tags with filtered links
# and populate dict 'all_links'
if cleaned_posts:
    # Dictionary "Title - URL" from list using "dictionary comprehension"
    all_links = {tag_a.text: tag_a['href'] for tag_a in cleaned_posts}
else:
    print(fg("No appropriate links on this page", 160))
    print(fg("\nQuit.\n", 228))
    sys.exit(0)

# Create main dictionary with link info
info_data = OrderedDict()

# Iteration counter for getting seqNumber
iter_counter = 0

# Iterate each URL and parse information from page
for link_text, link_url in all_links.items():
    # Get seqNumber in reverse order
    seq_number = all_post_number - iter_counter
    iter_counter += 1

    prefix_id = "P" + str(seq_number).zfill(4) + "-"

    # Getting title from post list (NOT from page title),
    # because several old posts have one URL
    post_title = str(link_text).strip()

    # Get Response by URL, 
    post_resp = get_utf8_response(s, link_url)

    post_date = get_date_from_url(post_resp.url) if post_resp.url else "NO DATE"

    # Set old and new file names (without extension)
    old_file_name = re.sub('[@,\"^:;*|\\/?><=\\\\/]', '_', post_title).strip()
    new_file_name = "[" + post_date + "]" + " # " + old_file_name.strip()
    
    # For unavailable pages (404)
    if post_resp.status_code == 404 or not post_resp.ok:
        post_id_404 = prefix_id + "c404"
        post_url_404 = link_url
        post_date = get_date_from_url(link_url)
        # if was redirect before bad status
        if resp.history:
            # Get last distenetion URL from redirects history
            post_url_404 = resp.history[-1].next.url
            post_date = get_date_from_url(resp.history[-1].next.url) 
        new_file_name = "[" + post_date + "]" + " # " + old_file_name.strip()    
        # Add info about this page
        info_data[post_id_404] = new_data_item(
            post_id = post_id_404,
            seq_number = seq_number,
            post_date = post_date,
            post_title = link_text,
            post_url = post_url_404,
            old_name = old_file_name,
            new_name = new_file_name,
            is_broken_url = True,
            parsing_status = "UNKNOWN"
            )
        # Go to next link
        print(bg("404", 88) + ": Page is unavailable: " + post_title)
        continue

    # Get final post URL (mostly for wp.me links)
    post_url = post_resp.url

    # Create BeautifulSoup object for one page
    post_soap = get_bs_object(post_resp.text)
    
    # Getting episode number, and postId
    ep_num = 0
    post_id = str(ep_num)
    if re.search(r'^\d+(?=.)', post_title):
        ep_num = int(re.search(r'^\d+(?=.)', post_title).group(0))
        # Combine post_id as "P0001-0001"
        post_id = prefix_id + str(ep_num).zfill(4)
    else:
        # if there is no episode number get 32 leading characters from title
        post_id = prefix_id + post_title[:32].strip()

    # Mark default post type as "TEXT" using named tuple
    has_audio, post_type = False, pt.text

    # Get all mp3 links with 'Download' keyword
    audio_mp3_links = []
    entry_div = post_soap.find('div', {'class': 'entry-content'})
    if entry_div == None:
        print(bg(fg("NOT VALID.", 16), 136) + " Cannot parse the page: " + post_title +" --> Post marked as \"NOT VALID\"\n")
            # Populate main dictionary
        info_data[post_id] = new_data_item(
            post_id = post_id,
            seq_number = seq_number,
            post_date = post_date,
            post_title = post_title,
            post_url = post_url,
            old_name = old_file_name,
            new_name = new_file_name,
            parsing_status = "NOT VALID"
        )
        # Go to next link
        continue
    else:
        tag_a_mp3 = entry_div.find_all('a', href=re.compile(".mp3$"))
        for tag_item in tag_a_mp3:
            if re.search(r'download|right[-.]click', tag_item.text, re.I):
                audio_mp3_links.append(tag_item['href']) 
        
        # Collect info about mp3 downloads into list
        mp3_files_info = []

        if audio_mp3_links:
            # Mark post as "AUDIO"
            has_audio, post_type = True, pt.audio
            
            # File part suffix
            file_part = ""

            for ind, dlink in enumerate(audio_mp3_links, 1):
                # Add "[Part X]" to file name if there are more than one link
                if ind > 1:
                    file_part = " [Part " + str(ind) + "]"
                # One line
                #file_part = " [Part " + str(ind+1) + "]" if ind > 0 else ""

                # Getting original file name from url:
                download_url = dlink
                origin_file_name = re.compile(r'[^/]*$').search(download_url).group(0)

                # Get extension (file format)
                extension = re.compile(r'\.[^.]*$').search(origin_file_name).group(0)

                # Form filename for saving on disc
                old_file_name_with_part = old_file_name + file_part
                new_file_name_with_part = new_file_name + file_part

                d_nested_info = {}
                d_nested_info[dk.originalFileName] = origin_file_name
                d_nested_info[dk.originalFileUrl] = download_url
                d_nested_info[dk.fileOldName] = old_file_name_with_part
                d_nested_info[dk.fileNewName] = new_file_name_with_part
                d_nested_info[dk.fileStorageUrl] = download_url
                d_nested_info[dk.fileExtension] = extension
                mp3_files_info.append(d_nested_info)
        else:
            print(bg("No downloads.", 18) + " For page: " + post_title)

    # Generate pdf url (files must be be added on server manually)
    server_dowload_url = "https://hotenov.com/d/lep/"
    file_name_to_URL = urllib.parse.quote(new_file_name)
    url_to_pdf = server_dowload_url + file_name_to_URL + ".pdf"

    # Populate main dictionary
    info_data[post_id] = new_data_item(
        post_id = post_id,
        seq_number = seq_number,
        post_date = post_date,
        post_title = post_title,
        episode_num = ep_num,
        post_url = post_url,
        post_type = post_type,
        pdf_url = url_to_pdf,
        old_name = old_file_name,
        new_name = new_file_name,
        has_audio = has_audio,
        mp3_list = mp3_files_info
    )


# Reverse dict for following convenience
reversed_info_data = OrderedDict(reversed(info_data.items()))

# Merge two dictionaries (new posts and existing from database)
print(fg("\nAppending new " + str(len(reversed_info_data)) + " posts " +
    "to " + str(items_in_lep_db) + " existing items...", 8))

result_db = {**web_lep_db, **reversed_info_data}
print(fg("Done.", 8))

print(fg("\n... Parsing END ...", 208))

# time end marker
elapsed_time = time.time() - start_time

# Save parsed database to json file
result_json_file = "raw-lep-db.json"
print(fg("\nWriting", 228) + " merged items to \"" + str(result_json_file) + "\" file...")
try:
    with open(result_json_file, 'w', encoding='utf-8') as f:
        json.dump(result_db, f, ensure_ascii=False, indent=4)
        print(fg("Done.", 8))
except PermissionError:
    print(fg("Access denied!", 160) + " No permission to write the file.")
    ask_uer_to_print_json()
except:
    print(fg("No possibility to write a file. ", 160))
    ask_uer_to_print_json()


print("\n---------- STATISTICS -----------")
# Statistics information
print("All parsed posts: " + str(len(result_db)))

# Get dict with all AUDIO posts
posts_with_audio = get_stat_dict(result_db, dk.title, dk.postUrl, dk.hasAudio)
if posts_with_audio:
    print("    -- with audio: " + str(len(posts_with_audio)))
    # Print dict if you need
    #for k,v in posts_with_audio.items():
    #    print("\n  " + k + "\n  " + v)

# Get dict with all not AUDIO posts
posts_without_audio = get_stat_dict(result_db, dk.title, dk.postUrl, dk.hasAudio, True)
if posts_without_audio:
    print("    --   NO audio: " + str(len(posts_without_audio)))
    # Print dict if you need
    #for k,v in posts_without_audio.items():
    #    print("\n  " + k + "\n  " + v)

# Get dict with all NOT available pages
not_available_pages = get_stat_dict(result_db, dk.title, dk.postUrl, dk.isUrl404)
if not_available_pages:
    print("\nNOT available pages: " + str(len(not_available_pages)))
    # Print them
    for k,v in not_available_pages.items():
        print("\n  " + k + "\n  " + v)

# Get dict with all NOT recognizable pages
not_recognizable_pages = {
    v[dk.title] : v[dk.postUrl]
    for k, v in result_db.items() if v[dk.pageParsingStatus] == "NOT VALID"
}
if not_recognizable_pages:
    print("\nNot recognizable pages: " + str(len(not_recognizable_pages)))
    # Print them
    for k,v in not_recognizable_pages.items():
        print("\n  " + k + "\n  " + v)

print("\n  -- Execution time: " + str(elapsed_time) + " --")
print("---------- ********** -----------")

