#!/usr/bin/env python3
# coding=utf-8
# Copyright (c) 2019 Artem Hotenov (@hotenov). Available under the MIT License.
"""
    DRAFT_4:    Re-written with urllib only (without requests)
                Renamed parsed database file from "lep-db.json" to "raw-lep-db.json"
    DRAFT_5:    Improve help messages and args
                Added sys.exit(0) instead of quit() (for PyInstaller executable file)
                
"""

# Using pure urllib in order to avoid 'requests' installing
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

import sys
import json
from pathlib import Path
import re
from collections import OrderedDict, namedtuple
import argparse
from operator import itemgetter

import ssl          # For macOS terminal users
import platform     # For Windows cmd users

# If script was executed on Windows
# enable ANSI color codes on Windows using 'ctypes'
if platform.platform(aliased=0, terse=1).find("Windows") > -1:
    import ctypes
    #print(platform.platform(aliased=0, terse=1))
    # enable ANSI color codes on Windows
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

__version__ = "2.0.5"

# URLs to json database file and its extends file
url_to_downloads_location = "https://hotenov.com/d/lep/"
url_to_raw_lep_db = url_to_downloads_location + "raw-lep-db.json"
url_to_lep_db_extends = url_to_downloads_location + "lep-db-extends.json"

# Set default values for variables:
# result database
lep_db = OrderedDict()
# episode interval
ep = "0-xxx"
# Start Date for filtering
start_date = "2000-01-01"
# End Date for filtering
end_date = "2999-12-31"

# Default folder path for downloading (where script is located)
downloads_folder = Path(".")

keys_for_json = [
    "postId", "seqNumber", "date", "title",
    "episode", "postUrl", "postType", "pdfUrl",
    "newName", "oldName", "hasAudio",
    "audioFiles", "videoFiles", "audioTracks",
    "addons", "isUrl404", "pageParsingStatus",
    "originalFileName", "originalFileUrl", "fileExtension",
    "fileOldName", "fileNewName", "fileStorageUrl"]

MainKeys = namedtuple("MainKeys", keys_for_json)
# Dictionary keys 'dk' for treatment via dot
dk  = MainKeys(
    postId = "postId", seqNumber = "seqNumber", date = "date", title = "title",
    episode = "episode", postUrl = "postUrl", postType = "postType", pdfUrl = "pdfUrl",
    newName = "newName", oldName = "oldName", hasAudio = "hasAudio",
    audioFiles = "audioFiles", videoFiles = "videoFiles", audioTracks = "audioTracks",
    addons = "addons", isUrl404 = "isUrl404", pageParsingStatus = "pageParsingStatus",
    originalFileName = "originalFileName", originalFileUrl = "originalFileUrl", fileExtension = "fileExtension",
    fileOldName = "fileOldName", fileNewName = "fileNewName", fileStorageUrl = "fileStorageUrl"
)

# post type dictionary (using via dot)
PostType = namedtuple("PostType", "audio text video")
pt = PostType(audio="AUDIO", text="TEXT", video="VIDEO")

# ---------- [Text colorize functions] ----------------
fg = lambda text, color: "\33[38;5;" + str(color) + "m" + text + "\33[0m"
bg = lambda text, color: "\33[48;5;" + str(color) + "m" + text + "\33[0m"
# ---------- [END: Text colorize functions] -----------


def get_dict_from_json(url_to_json):
    """
    Return OrderedDict from json file
    """
    ordered_dict_from_json = OrderedDict()
    if args.verbose:
        print(fg("Read json file from web.", 8))
    # Tell macOS terminal that our SSL context will be unverified
    ssl._create_default_https_context = ssl._create_unverified_context
    # Get json file from web
    req = Request(url_to_json)
    try:
        response = urlopen(req)
    except HTTPError:
        pass
        #print('The server couldn\'t fulfill the request.')
        #print('Error code: ', e.code)
    except URLError:
        pass
        #print('We failed to reach a server.')
        #print('Reason: ', e.reason)
    else:
        with response as f:
            res_body = f.read()
            data = json.loads(res_body.decode("utf-8"))
            ordered_dict_from_json = OrderedDict(data)
    return ordered_dict_from_json


def save_dict_to_json(dictionary, path_to_file):
    """ 
    Save dictionary to json file
    """
    print(fg("\nWriting", 228) + " merged database file \"" + str(path_to_file) + "\" ...")
    try:
        with open(path_to_file, 'w', encoding='utf-8') as f:
            json.dump(dictionary, f, ensure_ascii=False, indent=4)
            print(fg("Done.", 8))
    except PermissionError:
        print(fg("Access denied!", 160) + " No permission to write the file.")
    except FileNotFoundError:
        print(fg("File Not Found!", 160) + " File or directory doesn't exists. Check your full path.")
    except:
        print(fg("No possibility to write a file. ", 160))


def get_max_episode_number(lep_dictionary):
    """
    Return max episode number
    """
    max_episode = 0
    for v in lep_dictionary.values():
        if v['episode'] > max_episode:
            max_episode = v['episode']
    return max_episode


def print_post_titles(full_dict):
    """
    Print list of posts' titles in passed dictionary
    """
    for k,v in full_dict.items():
        print("› " + v['title'] + " (ID=\'" + k + "\')")


def stop_execution_and_exit(msg=""):
    """
    Wait user pressing Enter and exit from the script
    """
    try:
        input(bg(fg(msg + " Press \"Enter\" key to exit: ", 16), 136))
        print()
        sys.exit(0)
    except EOFError:
        sys.exit(0)


def get_items_by_episode_num(full_dict, episode_str):
    """
    Get filtered items by episode number from main database
    Episode param as string, with parsing start and end episodes
    """
    items_by_episode_num = OrderedDict()
    parse_str = str(episode_str).strip()
    start_num = 0
    end_num = 0

    if parse_str != "":
        match = re.match(r"(?P<g_start>^\d{0,5})(?P<g_delimiter>-)?(?P<g_infinity>xxx)?(?P<g_end>\d{0,5})", parse_str)
        g_start = match.group('g_start')
        g_delimiter = match.group('g_delimiter')
        g_infinity = match.group('g_infinity')
        g_end = match.group('g_end')
        if g_start and g_delimiter == "-" and g_end:
            start_num = int(g_start)
            end_num = int(g_end)
        elif g_start and g_delimiter == "-" and g_infinity == "xxx":
            start_num = int(g_start)
            end_num = get_max_episode_number(full_dict)
        elif g_start:
            start_num = int(g_start)
            end_num = int(g_start)
        else:
            print("Incorrect episode number")
            return items_by_episode_num

        if start_num > end_num:
            start_num, end_num = end_num, start_num
        
        items_by_episode_num = {
            k: v
            for k,v in full_dict.items() if start_num <= v[dk.episode] <= end_num}
        return items_by_episode_num
    else:
        return items_by_episode_num


def is_valid_date(date_string):
    """
    Validate if the passed date string has format "YYYY-MM-DD"
    """
    regex = re.compile(r"(2[0-9]\d\d)[-](0[1-9]|1[012])[-](0[1-9]|[12][0-9]|3[01])")
    match = regex.match(str(date_string))
    return bool(match)

def get_items_by_date(full_dict, start_date, end_date):
    """
    Get filtered items by publish date from main database
    Dates params as string "YYYY-MM-DD"
    """
    date_start = start_date
    date_end = end_date
    if date_start > date_end:
        date_start, date_end = date_end, date_start
    items_filtered_by_date = OrderedDict()
    items_filtered_by_date = {
        k: v
        for k,v in full_dict.items() if date_start <= v[dk.date] <= date_end}
    return items_filtered_by_date

def get_audio_items(full_dict):
    """
    Return new OrderedDict filtered by hasaudio attribute
    """
    items_by_has_audio = {
        k: v
        for k,v in full_dict.items() if v[dk.hasAudio]}
    return items_by_has_audio

def get_audiotrack_items(full_dict):
    """
    Return new OrderedDict filtered by having audioTracks elements
    """
    items_by_has_audiotracks = {
        k: v
        for k,v in full_dict.items() if v[dk.audioTracks]}
    return items_by_has_audiotracks


def get_only_text_items(full_dict):
    """
    Return new OrderedDict filtered by postType = TEXT
    """
    items_text = {
        k: v
        for k,v in full_dict.items() if v[dk.postType] == "TEXT"}
    return items_text


def get_only_video_items(full_dict):
    """
    Return new OrderedDict filtered by postType = VIDEO
    """
    items_video = {
        k: v
        for k,v in full_dict.items() if v[dk.postType] == "VIDEO"}
    return items_video


def get_text_and_video_items(full_dict):
    """
    Return new OrderedDict filtered by hasaudio attribute = False
    """
    items_by_has_not_audio = {
        k: v
        for k,v in full_dict.items() if not v[dk.hasAudio]}
    return items_by_has_not_audio

def get_list_with_all_files(full_dict, file_section):
    """
    Return new list of files in passed section (audioFiles, videoFiles, audioTracks or addons)
    """
    all_files_in_section = OrderedDict()
    all_files_in_section = [
        file_item
        for k,v in full_dict.items()
        for file_item in v[file_section]]
    return all_files_in_section

def get_pdf_list(full_dict):
    """
    Return list of pdf files
    """
    pdf_files = []
    for v in full_dict.values():
        # Make dict with pdf file as other files
        # For using one method of getting files
        item_iter = {
            "fileOldName": "",
            "fileNewName": v['newName'],
            "fileStorageUrl": v['pdfUrl'],
            "fileExtension": ".pdf"}
        pdf_files.append(item_iter)
    return pdf_files


def get_length(collection):
    """
    Return length of collection as str
    """
    return str(len(collection))

def get_filenames_in_folder(folder):
    """
    Return list of filenames (stem + suffix) in folder 
    """
    files_in_folder = [p for p in folder.iterdir() if p.is_file()]
    filenames_in_folder = [f.stem + f.suffix for f in files_in_folder]
    return filenames_in_folder

def get_folder_scan_info(folder, downloads):
    """
    Return list of three nested lists:
    existing_old_files, existing_files, non_exesting_files
    """
    # Get list of filenames in folder
    filenames = get_filenames_in_folder(folder)

    # Create three empty list
    existing_old_files = []
    existing_files = []
    non_exesting_files = []

    for download in downloads:
        if download['fileOldName'] + download['fileExtension'] in filenames:
            existing_old_files.append(download)
        elif download['fileNewName'] + download['fileExtension'] in filenames:
            existing_files.append(download)
        else:
            non_exesting_files.append(download)

    return [existing_old_files, existing_files, non_exesting_files]

def print_scan_dir_info(scan_info_list):
    """
    Print information from three nested list
    """
    if scan_info_list[0]:
        print("\nThere are " + get_length(scan_info_list[0]) + " existing file(s) with OLD name:")
        for df in scan_info_list[0]:
            print("› " + df['fileOldName'] + df['fileExtension'])
    
    if scan_info_list[1]:
        print("\nThere are " + get_length(scan_info_list[1]) + " existing file(s):")
        for df in scan_info_list[1]:
            print("› " + df['fileNewName'] + df['fileExtension'])
    
    if scan_info_list[2]:
        print("\n" + get_length(scan_info_list[2]) + " non-existing file(s) will be download:")
        for df in scan_info_list[2]:
            print("› " + df['fileNewName'] + df['fileExtension'])

def download_files(downloads_list, folder):
    """
    Download all files in the folder from list
    """
    if downloads_list:
        print(fg("\nDownloading...\n", 228))
        for item in downloads_list:
            filename = item['fileNewName'] + item['fileExtension']
            path_to_file = folder / filename
            if not path_to_file.exists():
                #resp = s.get(item['fileStorageUrl'])
                ssl._create_default_https_context = ssl._create_unverified_context
                req = Request(item['fileStorageUrl'])
                try:
                    response = urlopen(req)
                except HTTPError:
                    not_found_files.append(item)
                    print(" " + fg("-", 160) + " " + filename + " " + bg("404: NOT FOUND", 88))
                    pass
                    #print('The server couldn\'t fulfill the request.')
                    #print('Error code: ', e.code)
                except URLError:
                    not_found_files.append(item)
                    print(" " + fg("-", 160) + " " + filename + " " + bg("404: NOT FOUND", 88))
                    pass
                    #print('We failed to reach a server.')
                    #print('Reason: ', e.reason)
                else:
                    #bin_data = response.read()
                    try:
                        with open(path_to_file, 'wb') as f:
                            bin_data = response.read()
                            f.write(bin_data)
                            downloaded_files.append(item)
                            print(" " + fg("+", 34) + " " + filename + " " + bg(fg("DOWNLOADED", 255), 34) + fg(" +", 34))
                    except PermissionError:
                        # print(fg("Access denied!", 160) + " No permission to write the file.")
                        unsaved_files.append(item)
                        print(" " + fg("-", 160) + " " + filename + " " + bg("UNSAVED", 124) + fg(" -", 160))
                    except FileNotFoundError:
                        #print(fg("File Not Found!", 160) + " File or directory doesn't exists. Check your full path.")
                        unsaved_files.append(item)
                        print(" " + fg("-", 160) + " " + filename + " " + bg("UNSAVED", 124) + fg(" -", 160))
                    except:
                        #print(fg("No possibility to write a file. ", 160))
                        # If empty file was created - delete it
                        if path_to_file.exists():
                            path_to_file.unlink()
                        unsaved_files.append(item)
                        print(" " + fg("-", 160) + " " + filename + " " + bg("UNSAVED", 124) + fg(" -", 160))
            else:
                exesting_files.append(item)
                print(" " + fg("•", 245) + " " + filename + " " + bg(fg("ON DISC", 16), 250) + fg(" •", 245))
        print(fg("\nDownloading END.", 228))
    else:
        print("\nAll files are on the disc already. There are NO NEW files to download in selected episode(s).")
        # -TODO: Insert link to documentation page
        print("You can try another script options. For example, to download video files use option --onlyvideo ")
        print("See all them here *<link_to_docs_page>* or using --help option.")

def get_parser():
    """Return parser for args"""
    help_prog = "LEP downloader"
    help_usage = "python3 LEP-downloader.py [OPTIONS]"
    help_description = "Python 3.5+ script for downloading the all FREE episodes of Luke's ENGLISH Podcast, available on its archive webpage"
    parser = argparse.ArgumentParser(prog=help_prog, usage=help_usage, description=help_description)
    parser.add_argument("-ep", "--episode", type=str,
                        help="Specify episode number (or range of episodes) for downloading")
    parser.add_argument("-pdf", "--withpdf", action="store_true",
                        help="Download PDF files of exported webpage(s)")
    parser.add_argument("-vi", "--onlyvideo", action="store_true",
                        help="Download only video files")
    parser.add_argument("-to", "--folder", type=str, metavar="PATH",
                        help="Specify a path to custom download directory (folder)")
    parser.add_argument("-d1", "--startdate", type=str,
                        help="Start date for date range filtering. Format \"YYYY-MM-DD\"")
    parser.add_argument("-d2", "--enddate", type=str,
                        help="End date for date range filtering. Format \"YYYY-MM-DD\"")
    parser.add_argument("--last", action="store_true",
                        help="Download only the last episode. Options -ep, -d1 and -d2 will be ignored in this case.")
    parser.add_argument("-text" , "--withoutanymedia", action="store_true",
                        help="Print names list of the posts which have no any media files (only TEXT) for selected episode(s). When used along with --withpdf script downloads pdf files for these posts")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Activate verbose mode to display execution steps results")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Activate quiet mode. There is no question whether to download files or not. Immediately download them.")
    parser.add_argument("-V", "--version", action="version", version="'%(prog)s' ver. " + __version__,
                        help="Print script version and exit")
    parser.add_argument("-sj", "--savejson", action="store_true",
                        help="Save database to file \"lep-db.json\" in the same folder" )
    parser.add_argument("--withaddons", action="store_true",
                        #help=argparse.SUPPRESS,
                        help="Download all additional files (if they added by script author) for selected episode(s)")
    return parser


parser = get_parser()
args = parser.parse_args()

# Define empty objects 
filtered_items = OrderedDict()

all_audio_files = []
all_audiotracks_files = []
all_pdf_files = []
all_video_files = []
all_addons_files = []
all_downloads = []

print(fg("START script execution...\n", 208))

# Look at episode number argument
if args.episode and (not args.last or not args.withoutanymedia):
    print("Selected number(s) of episode(s): " + args.episode + "\n")
    ep = args.episode
else:
    # Ignore '--episode' argument if '--last' argument is specified
    if args.last:
        print("Selected number(s) of episode(s): " + "The last" + "\n")
    # Ignore '--episode' argument if '--withoutanymedia' argument is specified
    elif args.withoutanymedia:
        print("Selected number(s) of episode(s): " + "only TEXT posts" + "\n")
    else:
        print("Selected number(s) of episode(s): " + "ALL" + "\n")

# Load parsed (raw) database
raw_lep_db = get_dict_from_json(url_to_raw_lep_db)

# If database is unavailable (or empty)
if not raw_lep_db:
    print("\nSorry. Json file with main database " + fg("is unavailable now.", 170) + " Try again later.")
    stop_execution_and_exit()
else:
    if args.verbose:
        print(fg("Raw LEP Database was downloaded, all items = " + get_length(raw_lep_db), 8))


# Load extends with corrections and additional files
lep_db_extends = get_dict_from_json(url_to_lep_db_extends)

# If extends database is unavailable (or empty)
if not lep_db_extends:
    print("\nSorry. Json file with extends database " + fg("is unavailable now.", 170) + " Try again later if you want to deal with it.")
    print(fg("Raw database", 208) + " (without extends) " + fg("will be processed.", 208))
    lep_db = raw_lep_db
else:
    # Merge main db with extends
    lep_db = OrderedDict({**raw_lep_db, **lep_db_extends})
    if args.verbose:
        print(fg("Extends database file was downloaded, all corrected items = " + get_length(lep_db_extends), 8))
        print(fg("Databases was merged, all items = " + get_length(lep_db), 8))

# Get posts items filtered by episode number
filtered_by_episode = get_items_by_episode_num(lep_db, ep)
if args.verbose:
    print(fg("\nAll filtered by episode: " + get_length(filtered_by_episode), 8))


filtered_items = filtered_by_episode

# if --startdate OR --enddate arguments are specified
if args.startdate or args.enddate:
    if args.startdate and not args.enddate:
        start_date = args.startdate
    elif not args.startdate and args.enddate:
        end_date = args.enddate
    else:
        start_date = args.startdate
        end_date = args.enddate
    if not is_valid_date(start_date):
        print("Your start date \"" + start_date + "\" is " + fg("the wrong format!", 170) + " It was reset by default to \"2000-01-01\"")
        start_date = "2000-01-01"
    if not is_valid_date(end_date):
        print("Your end date \"" + end_date + "\" is " + fg("the wrong format!", 170) + " It was reset by default to \"2999-12-31\"")
        end_date = "2999-12-31"
    filtered_by_date = get_items_by_date(filtered_by_episode, start_date, end_date)
    if args.verbose:
        print(fg("\nPosts filtered by date \"" + start_date + "\" to \"" + end_date + "\": " + get_length(filtered_by_date), 8))
    filtered_items = filtered_by_date

# If "--last" argument is specified
if args.last:
    print(fg("\n** You specified the \"--last\" option. Only the last episode will be downloaded **", 208))
    last_item = lep_db.popitem()
    filtered_items = OrderedDict({last_item[0]: last_item[1]})
    print(fg("The last episode (post) is: ", 8) + last_item[1]['title'])

# If "--withoutanymedia" argument is specified
if args.withoutanymedia:
    items_with_text = get_only_text_items(filtered_items)
    print(fg("Total posts without any media (audio or video): " + get_length(items_with_text), 8))
    if args.withpdf:
        filtered_items = items_with_text
    else:
        print_post_titles(items_with_text)
        print(fg("\nHint:", 39) +
                "\nUse options \"-text --withpdf\" if you want to download pdf files for these posts.")
        sys.exit(0)

# Get dictionaries for statistics by post type in user query
stat_audio_posts = get_audio_items(filtered_items)
stat_video_posts = get_only_video_items(filtered_items)
stat_text_posts = get_only_text_items(filtered_items)

# If "--onlyvideo" argument is specified
if args.onlyvideo:
    print(fg("\n** You specified to process ONLY VIDEO episode(s) **", 208))
    items_with_video = get_only_video_items(filtered_items)
    if args.verbose:
        print(fg("\nAll VIDEO posts in selected episode(s): " + get_length(items_with_video), 8))
    filtered_items = items_with_video
    all_video_files = get_list_with_all_files(filtered_items, dk.videoFiles)
    print(fg("\nAll video files: " + get_length(all_video_files), 8))
else:
    items_with_audio = get_audio_items(filtered_items)
    if args.verbose:
        print(fg("\nAll AUDIO posts in selected episode(s): " + get_length(items_with_audio), 8))
    items_with_audiotracks = get_audiotrack_items(filtered_items)
    if args.verbose:
        print(fg("\nAll VIDEO posts in selected episode(s) also having audio tracks: " + get_length(items_with_audiotracks), 8))

    all_audio_files = get_list_with_all_files(items_with_audio, dk.audioFiles)
    if args.verbose:
        print(fg("\nAll audio files: " + get_length(all_audio_files), 8))

    all_audiotracks_files = get_list_with_all_files(items_with_audiotracks, dk.audioTracks)
    if args.verbose:
        print(fg("\nAll audiotracks files: " + get_length(all_audiotracks_files), 8))

# If "--withpdf" argument is specified
if args.withpdf:
    all_pdf_files = get_pdf_list(filtered_items)
    if args.verbose:
        print(fg("\nAll pdf files: " + get_length(all_pdf_files), 8))

# If "--withaddons" argument is specified
if args.withaddons:
    all_addons_files = get_list_with_all_files(filtered_items, dk.addons)
    if args.verbose:
        print(fg("\nAll addons files: " + get_length(all_addons_files), 8))

# Merge all lists with files to one
all_downloads = [*all_audio_files, *all_audiotracks_files, *all_pdf_files, *all_video_files, *all_addons_files]

# Sort list with all files for downloading by 'fileNewName'
# It looks like sorting by post publishing date ASC (the last post at the end of list)
sorted_downloads = sorted(all_downloads, key=itemgetter('fileNewName'))
# Another way to do it without itemgetter: sorted(all_downloads, key=lambda e: e['fileNewName'])

# If "--folder" argument is specified
if args.folder and all_downloads:
    # Try to make folder if it doesn't exist (check path)
    try:
        Path(args.folder).mkdir(parents=True, exist_ok=True)
    except PermissionError:
        #print(fg("Access denied!", 160) + " No permission to write in the folder \"" + str(Path(args.folder)) + "\"")
        print(fg("Access denied!", 160) + " No permission to write in the folder \"" + str(Path(args.folder)) + "\"")
        stop_execution_and_exit()
    except FileNotFoundError:
        #print(fg("File Not Found!", 160) + " File or directory doesn't exists. Check your full path.")
        print(fg("Access denied!", 160) + " No permission to write in the folder \"" + str(Path(args.folder)) + "\"")
        stop_execution_and_exit()
    except:
        #print(fg("No possibility to write a file. ", 160))
        print(fg("Access denied!", 160) + " No permission to write in the folder \"" + str(Path(args.folder)) + "\"")
        stop_execution_and_exit()
    # If folder exists or script managed to create it then change default value
    downloads_folder = Path(args.folder)

# You can save result json file if you need
# If "--savejson" argument is specified
if args.savejson:
    # Save result database to json file
    file_to_save_db = downloads_folder / "lep-db.json"
    save_dict_to_json(lep_db, file_to_save_db)

# Scan folder for downlaoding to check for the existing files
scan_dir_info = get_folder_scan_info(downloads_folder, sorted_downloads)
# If "--verbose" argument is specified print this information
if args.verbose:
    print_scan_dir_info(scan_dir_info)

# Lists for statistics
exesting_files = [*scan_dir_info[0], *scan_dir_info[1]]
downloaded_files = []
not_found_files = []
unsaved_files = []

if args.quiet:
    # Donload files from "non-existing" list
    download_files(scan_dir_info[2], downloads_folder)
else:
    if scan_dir_info[2]:
        user_input = input(fg("Would download " + get_length(scan_dir_info[2]) + " file(s). Proceed (y/n)?: ", 87))
        if user_input in ["y", "Y", "Yes", "YES"]:
            download_files(scan_dir_info[2], downloads_folder)
        else:
            stop_execution_and_exit("You canceled the file downloading.")
    else:
        print("\nAll files are on the disc already. There are NO NEW files to download in selected episode(s).")
        print("You can try another script options. For example, to download video files use option --onlyvideo ")
        print("See all them here: cutt.ly/LEP-downlaoder or using --help option.")


# Print statistics
print()
print(fg("{:-^30s}".format(" STATISTICS "), 8))
if args.verbose:
    print("All processed posts: " + bg("{:8d}".format(len(filtered_items)), 240))
    print(fg("    ••• ", 8) + bg(fg("AUDIO", 255), 34) + " = " + "{:13d}".format(len(stat_audio_posts)))
    print(fg("    ••• ", 8) + bg("VIDEO", 13) + " = " + "{:13d}".format(len(stat_video_posts)))
    print(fg("    ••• ", 8) + bg("TEXT", 18) + " = " + "{:14d}".format(len(stat_text_posts)))
    print("All processed files: " + bg("{:8d}".format(len(all_downloads)), 240))
    if not args.onlyvideo:
        print(fg("    ••• ", 8) + "audio = " + "{:13d}".format(len(all_audio_files)))
        print(fg("    ••• ", 8) + "audio tracks = " + "{:6d}".format(len(all_audiotracks_files)))
        if args.withpdf:
            print(fg("    ••• ", 8) + "pdf = " + "{:15d}".format(len(all_pdf_files)))
        if args.withaddons:
            print(fg("    ••• ", 8) + "addons = " + "{:12d}".format(len(all_addons_files)))
    else:
        print(fg("    ••• ", 8) + "video = " + "{:13d}".format(len(all_video_files)))
        if args.withpdf:
            print(fg("    ••• ", 8) + "pdf = " + "{:15d}".format(len(all_pdf_files)))
        if args.withaddons:
            print(fg("    ••• ", 8) + "addons = " + "{:12d}".format(len(all_addons_files)))

    print()
    print("Downloading results:")
print(bg(fg("DOWNLOADED", 255), 34) + " = " + "{:6d}".format(len(downloaded_files)))
print(bg(fg("ON DISC", 16), 250) + " = " + "{:9d}".format(len(exesting_files)))
if not_found_files:
    print(bg("NOT FOUND", 88) + " = " + "{:7d}".format(len(not_found_files)))
if unsaved_files:
    print(bg("UNSAVED", 124) + " = " + "{:9d}".format(len(unsaved_files)))
print(fg("{:-^30s}".format(" ********** "), 8))

print(fg("\nEND script execution.", 208))

if not args.quiet:
    stop_execution_and_exit()




