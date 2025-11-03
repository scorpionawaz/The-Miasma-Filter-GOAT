import requests
from bs4 import BeautifulSoup
import json

def extract_youtube_live_streams_location(location):
    """
    Extract live stream details with pagination support
    """
    search_query = f"{location}, India News live"
    query = search_query.replace(" ", "+")
    base_url = f"https://www.youtube.com/results?search_query={query}&sp=CAMSAkAB"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    all_videos = []
    continuation_token = None
    max_pages = 1  # Adjust this to get more results
    current_page = 0
    
    while current_page < max_pages:
        try:
            if continuation_token:
                # Use continuation for subsequent pages
                url = f"https://www.youtube.com/youtubei/v1/search?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
                payload = {
                    "context": {
                        "client": {
                            "clientName": "WEB",
                            "clientVersion": "2.20230101.00.00"
                        }
                    },
                    "continuation": continuation_token
                }
                response = requests.post(url, json=payload, headers=headers)
            else:
                # First request to get initial data
                response = requests.get(base_url, headers=headers)
            
            response.raise_for_status()
            
            if continuation_token:
                # Parse JSON response for continuation requests
                data = response.json()
            else:
                # Parse HTML response for initial request
                soup = BeautifulSoup(response.content, 'html.parser')
                scripts = soup.find_all('script')
                data = None
                
                for script in scripts:
                    if script.string and 'var ytInitialData' in script.string:
                        json_text = script.string
                        start = json_text.find('{')
                        end = json_text.rfind('}') + 1
                        
                        if start != -1 and end != -1:
                            try:
                                data = json.loads(json_text[start:end])
                                break
                            except json.JSONDecodeError:
                                continue
            
            if not data:
                print("No data found")
                break
                
            # Extract videos from current page
            videos = extract_video_info(data)
            all_videos.extend(videos)
            
            print(f"Page {current_page + 1}: Found {len(videos)} videos")
            
            # Extract continuation token for next page
            continuation_token = extract_continuation_token(data)
            
            if not continuation_token:
                print("No more pages available")
                break
                
            current_page += 1
            
        except Exception as e:
            print(f"Error on page {current_page + 1}: {e}")
            break
    
    # Output results
    output = {
        "search_query": search_query,
        "results_count": len(all_videos),
        "pages_processed": current_page + 1,
        "videos": all_videos
    }
    
    print(json.dumps(output, indent=4, ensure_ascii=False))
    return output


def extract_video_info(data):
    videos = []

    try:
        contents = data.get('contents', {})
        search_results = None

        if 'twoColumnSearchResultsRenderer' in contents:
            primary_contents = contents['twoColumnSearchResultsRenderer']['primaryContents']
            if 'sectionListRenderer' in primary_contents:
                sections = primary_contents['sectionListRenderer']['contents']
                for section in sections:
                    if 'itemSectionRenderer' in section:
                        search_results = section['itemSectionRenderer']['contents']
                        break

        if not search_results:
            return videos

        for item in search_results:
            if 'videoRenderer' in item:
                video_info = item['videoRenderer']
                video = {
                    'title': '',
                    'channel': '',
                    'is_live': False,
                    'view_count': '',
                    'duration': '',
                    'published_time': '',
                    'url': '',
                    'description': ''
                }

                if 'title' in video_info and 'runs' in video_info['title']:
                    video['title'] = ''.join([run.get('text', '') for run in video_info['title']['runs']])

                if 'ownerText' in video_info and 'runs' in video_info['ownerText']:
                    video['channel'] = video_info['ownerText']['runs'][0].get('text', '')

                if 'badges' in video_info:
                    for badge in video_info['badges']:
                        if 'metadataBadgeRenderer' in badge:
                            badge_text = badge['metadataBadgeRenderer'].get('label', '')
                            if 'LIVE' in badge_text.upper():
                                video['is_live'] = True
                                break

                if 'viewCountText' in video_info:
                    if 'simpleText' in video_info['viewCountText']:
                        video['view_count'] = video_info['viewCountText']['simpleText']
                    elif 'runs' in video_info['viewCountText']:
                        video['view_count'] = ''.join([run.get('text', '') for run in video_info['viewCountText']['runs']])

                if 'lengthText' in video_info:
                    if 'simpleText' in video_info['lengthText']:
                        video['duration'] = video_info['lengthText']['simpleText']

                if 'publishedTimeText' in video_info:
                    if 'simpleText' in video_info['publishedTimeText']:
                        video['published_time'] = video_info['publishedTimeText']['simpleText']

                if 'videoId' in video_info:
                    video['url'] = f"https://www.youtube.com/watch?v={video_info['videoId']}"

                if 'detailedMetadataSnippets' in video_info:
                    snippets = video_info['detailedMetadataSnippets']
                    if snippets and 'snippetText' in snippets[0]:
                        if 'runs' in snippets[0]['snippetText']:
                            video['description'] = ''.join([run.get('text', '') for run in snippets[0]['snippetText']['runs']])

                videos.append(video)


    except Exception as e:
        print(f"Error parsing video data: {e}")

    return videos

def extract_continuation_token(data):
    """Extract continuation token for pagination"""
    try:
        # Search for continuation data in the response
        contents = data.get('contents', {})
        
        if 'twoColumnSearchResultsRenderer' in contents:
            primary_contents = contents['twoColumnSearchResultsRenderer']['primaryContents']
            if 'sectionListRenderer' in primary_contents:
                sections = primary_contents['sectionListRenderer']['contents']
                
                # Look for continuation token in the sections
                for section in sections:
                    if 'continuationItemRenderer' in section:
                        continuation_data = section['continuationItemRenderer']['continuationEndpoint']
                        if 'continuationCommand' in continuation_data:
                            return continuation_data['continuationCommand']['token']
    except Exception as e:
        print(f"Error extracting continuation token: {e}")
    
    return None


