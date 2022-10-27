import requests
from csv import writer
import iso8601
from dateutil import tz
from datetime import datetime
import logging
import argparse
from urllib.parse import urlparse, parse_qs
from contextlib import suppress
import time
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import rcParams, patheffects, font_manager
from matplotlib.dates import DateFormatter
from slugify import slugify
import urllib.request
import os
import sys
# Hardcoded API key default
yt_api_key = 'Your API Key Here'

def main(url, r, gshow, gsave,  api_key = yt_api_key, filepath = os.getcwd(), healthcheck = ''):
    exception_count = 0
    os.chdir(filepath)
    # Set Logging
    logging.basicConfig(
        handlers=[logging.FileHandler("youtube_livestream_viewership_recorder.log"), logging.StreamHandler(sys.stdout)],
        # handlers=[logging.StreamHandler()],
        format='%(asctime)s | %(levelname)s: %(message)s', level=logging.INFO)

    # Set some plotting defaults
    if not os.path.exists("CJK_font.otf"):
        logging.info('CJK font file not found in directory.  Downloading one...')
        github_url = 'https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTC/NotoSansCJK-Bold.ttc'  # Get a CJK font for Asian chars
        urllib.request.urlretrieve(github_url, "CJK_font.otf")

    fprop = fm.FontProperties(family='sans-serif', fname='CJK_font.otf')
    plt.tight_layout()
    plt.gcf().set_size_inches(15, 9)
    plt.xkcd(scale=0.2)
    rcParams['font.size'] = 11
    rcParams['path.effects'] = [patheffects.withStroke(linewidth=1, foreground="w")]
    rcParams['font.family'] = ['xkcd', 'sans-serif', 'Segoe UI', 'sans-serif']


    def get_yt_id(url, ignore_playlist=False):
        # Examples:
        # - http://youtu.be/SA2iWivDJiE
        # - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
        # - http://www.youtube.com/embed/SA2iWivDJiE
        # - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
        query = urlparse(url)
        if query.hostname == 'youtu.be': return query.path[1:]
        if query.hostname == 'holodex.net': return query.path.split('/')[2]
        if query.hostname in {'www.youtube.com', 'youtube.com', 'music.youtube.com'}:
            if not ignore_playlist:
                # use case: get playlist id not current video in playlist
                with suppress(KeyError):
                    return parse_qs(query.query)['list'][0]
            if query.path == '/watch': return parse_qs(query.query)['v'][0]
            if query.path[:7] == '/watch/': return query.path.split('/')[1]
            if query.path[:7] == '/embed/': return query.path.split('/')[2]
            if query.path[:3] == '/v/': return query.path.split('/')[2]


    def append_list_as_row(file_name, list_of_elem):
        # Open file in append mode
        with open(file_name, 'a+', newline='', encoding="utf-8") as write_obj:
            # Create a writer object from csv module
            csv_writer = writer(write_obj)
            # Add contents of list as last row in the csv file
            csv_writer.writerow(list_of_elem)
            logging.info('Wrote new row to file: ' + file_name)
            if healthcheck:
                logging.info('Pinging HealthCheck URL...')
                requests.get(healthcheck)


    video_id = get_yt_id(url)
    first_loop = True
    # Refresh loop - only once unless a time is given in the cmd arguments
    while True:
        try:

            # API Call #1 for misc. video info
            if first_loop == True or video_info_response['items'][0]['snippet']['liveBroadcastContent'] == 'upcoming':
                video_info_response = requests.get(
                    'https://www.googleapis.com/youtube/v3/videos',
                    params={'part': 'snippet', 'id': video_id, 'fields': '', 'key': api_key}
                ).json()
                logging.info('Made snippet API call')
                logging.info('Live Broadcast Status: ' + video_info_response['items'][0]['snippet']['liveBroadcastContent'])
                first_loop = False

            if video_info_response['items'][0]['snippet']['liveBroadcastContent'] == 'upcoming':
                # Catch if the livestream is not live, but about to be live
                logging.info('Broadcast status is upcoming, will retry in ' + str(r) + ' secs...')
                time.sleep(r)
                continue
            if video_info_response['items'][0]['snippet']['liveBroadcastContent'] == 'none':
                # Catch if livestream is not actually a livestream
                logging.info('Broadcast status is none.  The link is not a livestream?')
                return video_info_response['items'][0]['snippet']['title'], slugify(
                    video_info_response['items'][0]['snippet']['title']) + '_graph.png', False
                break  # ends program

            # API Call #2 for livestream viewership
            livestream_response = requests.get(
                'https://www.googleapis.com/youtube/v3/videos',
                params={'part': 'liveStreamingDetails', 'id': video_id, 'fields': '', 'key': api_key}
            ).json()
            logging.info('Made liveStreamingDetails API call')

            if 'actualEndTime' in livestream_response['items'][0]['liveStreamingDetails']:
                # Catch if livestream ended using the livestreamingdetails GET and not the snippet.
                logging.info('The stream has ended.')
                return video_info_response['items'][0]['snippet']['title'], slugify(video_info_response['items'][0]['snippet']['title']) + '_graph.png', True
                break  # ends program, shouldn't be needed since we return....
            vidData = {
                "title": video_info_response['items'][0]['snippet']['title'],
                "video_id": video_id,
                "livestream_start_time": iso8601.parse_date(
                    video_info_response['items'][0]['snippet']['publishedAt']).replace(
                    tzinfo=tz.tzutc()).astimezone(tz.tzlocal()),
                "data_timestamp": iso8601.parse_date(datetime.utcnow().isoformat()).replace(
                    tzinfo=tz.tzutc()).astimezone(tz.tzlocal()),
                "livestream_viewers": int(livestream_response['items'][0]['liveStreamingDetails']['concurrentViewers'])
            }

            # Write new row to CSV (Create it with headers if it doesn't already exist
            try:
                with open(slugify(video_info_response['items'][0]['snippet']['title']) + '_video_data.csv',
                          encoding="utf-8") as f:
                    logging.info('File present: ' + slugify(video_info_response['items'][0]['snippet']['title']) + '_video_data.csv')
            except FileNotFoundError:
                logging.info('File NOT present: ' + slugify(video_info_response['items'][0]['snippet']['title']) + '_video_data.csv')
                logging.info('New file will be created')
                append_list_as_row(slugify(video_info_response['items'][0]['snippet']['title']) + '_video_data.csv',
                                   vidData)

            append_list_as_row(slugify(video_info_response['items'][0]['snippet']['title']) + '_video_data.csv',
                               vidData.values())
        except Exception as e:
            exception_count += 1
            # Catch-all for a fail in the query and data compilation process
            logging.exception("An exception was thrown!")
            if exception_count > 5:
                logging.error("Too many errors, exiting loop....")
                return video_info_response['items'][0]['snippet']['title'], slugify(
                    video_info_response['items'][0]['snippet']['title']) + '_graph.png', True
                break
            time.sleep(r)
            continue
        if gshow == True or gsave == True:
            # Creating and either showing or saving the graph
            # Currently graphs the entire history of the CSV
            # TODO: only graph last X period of data, for 24/7 livestreams
            logging.info(
                'Graphing CSV: ' + slugify(video_info_response['items'][0]['snippet']['title']) + '_video_data.csv')
            headers = ['data_timestamp', 'livestream_viewers']
            df = pd.read_csv(slugify(video_info_response['items'][0]['snippet']['title']) + '_video_data.csv',
                             parse_dates=['data_timestamp'], date_parser=iso8601.parse_date)
            video_title_fromcsv = df['title'].iat[-1]
            num_rows_fromcsv = df.shape[0]

            myFmt = DateFormatter('%Y-%m-%d %I:%M %p', tz=tz.tzlocal())

            plt.cla()
            plt.setp(plt.gca().xaxis.get_ticklabels(), rotation=30, horizontalalignment='right')
            plt.gca().xaxis.set_major_formatter(myFmt)
            plt.plot('data_timestamp', 'livestream_viewers', data=df, solid_capstyle='round')
            # plt.title("Youtube Livestream Concurrent Viewer Log\n\n" + video_title_fromcsv + "\n Plotting " + str(
            # num_rows_fromcsv) + " Data Points", fontproperties=fprop)
            plt.suptitle("Youtube Livestream Concurrent Viewer Log")
            plt.title(video_title_fromcsv, fontproperties=fprop, fontsize=14)
            plt.text(1, 1.12, 'Labtec901', transform=plt.gca().transAxes, horizontalalignment="right",
                     verticalalignment="bottom", fontsize=5)  # watermark
            plt.xlabel("Time")
            plt.ylabel("Concurrent Livestream Viewership")
            if gshow == True:
                logging.info('Drawing plot...')
                plt.draw()
                plt.pause(0.01)
            if gsave == True:
                logging.info('Saving plot to disk...')
                plt.gcf().set_size_inches(16, 8)
                plt.savefig(slugify(video_info_response['items'][0]['snippet']['title']) + '_graph.png', dpi=250,
                            bbox_inches='tight')
        if r == -1:
            logging.info('Exiting... (Was not looped)')
            return video_info_response['items'][0]['snippet']['title'], slugify(
                video_info_response['items'][0]['snippet']['title']) + '_graph.png', True
            break
        else:
            logging.info('Sleeping for ' + str(r) + ' secs...')
            time.sleep(r)

if __name__ == "__main__":

    # Command Line Arguments
    parser = argparse.ArgumentParser(description='Log viewership for a youtube livestream')
    parser.add_argument('url', metavar='url', type=str, nargs=1,
                        help='A YouTube livestream URL')
    parser.add_argument('r', default=-1, type=int, nargs='?',
                        help='How often to fetch and log viewership (sec) (default: just once)')
    parser.add_argument('--filepath', type=str, nargs='?', default=os.getcwd(),
                        help='Path to save logs and images to (default: current working directory)')
    parser.add_argument('--api_key', default=yt_api_key, type=str, nargs='?',
                        help='Youtube API Key (default: hardcoded)')
    parser.add_argument('--healthcheck', default='', type=str, nargs='?',
                        help='HealthCheck.io URL to ping on successful data write')
    parser.add_argument('-gshow', action='store_true', help="Graph and show the CSV output")
    parser.add_argument('-gsave', action='store_true', help="Graph and save a PNG of the CSV output")

    args = parser.parse_args()
    main(args.url[0],args.r,args.gshow,args.gsave, args.api_key, args.filepath, args.healthcheck)
