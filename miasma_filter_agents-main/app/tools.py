import json
import re
import redis
import datetime
from redis.commands.json.path import Path
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional

import requests

def _extract_topic_from_plan(research_plan: str) -> str:
    """
    Extracts a primary topic from the research plan to use as a Redis key.
    Searches for known topics and falls back to a timestamped generic key if none are found.
    """
   
    known_topics = ["maharashtra", "karnataka", "punjab", "delhi", "business", "breaking"]
    for topic in known_topics:
        if re.search(r'\b' + re.escape(topic) + r'\b', research_plan, re.IGNORECASE):
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            return f"{topic.lower()}:{timestamp}"
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"general_report:{timestamp}"

def save_report_to_redis(report_content: str, research_plan: str, sources: Dict[str, Any]) -> str:
    """
    Saves the final research report and its metadata to Redis using the RedisJSON module.
    The key is determined by the topic of the research (e.g., 'maharashtra:20250920-143000').

    Args:
        report_content: The final Markdown report string.
        research_plan: The research plan that generated the report.
        sources: A dictionary of citation sources used in the report.

    Returns:
        A confirmation message indicating success or failure.
    """
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping() 

        report_key = _extract_topic_from_plan(research_plan)
        report_data = {
            "content": report_content,
            "created_at": datetime.datetime.now().isoformat()
        }
        r.json().set(report_key, Path.root_path(), report_data)

        print(f"Successfully saved report to RedisJSON with key: {report_key}")
        return f"Success: Report saved to Redis as JSON with key {report_key}"

    except redis.exceptions.ConnectionError as e:
        error_message = f"Error: Could not connect to Redis. {e}"
        print(error_message)
        return error_message
    except Exception as e:
        error_message = f"An unexpected error occurred while saving to Redis. {e}"
        print(error_message)
        return error_message
    

class YouTubeLiveNewsScraper:
    """
    Agent tool for extracting live news streams from YouTube
    Returns structured data for easy consumption by agents
    """
    
    CATEGORIES = {
        "business": "business news live stream", 
        "breaking": "breaking news live stream",
        "maharashtra": "Maharashtra news live stream",
        "karnataka": "Karnataka news live stream",
        "punjab": "Punjab news live stream",
        "delhi": "Delhi news live stream"
    }
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

    def get_live_streams(self, category: str = "sports", limit: int = 10) -> Dict:
        """
        Main tool function - returns structured live stream data
        
        Args:
            category: News category to search for
            limit: Maximum number of streams to return
            
        Returns:
            Structured dict with live streams data
        """
        try:
            if category.lower() in self.CATEGORIES:
                search_query = self.CATEGORIES[category.lower()]
            else:
                search_query = f"{category} news live stream"

            live_streams = self._fetch_live_streams(search_query, limit)
            
            return {
                "success": True,
                "category": category,
                "search_query": search_query,
                "count": len(live_streams),
                "streams": live_streams,
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "category": category,
                "count": 0,
                "streams": [],
                "timestamp": self._get_timestamp()
            }

    def _fetch_live_streams(self, search_query: str, limit: int) -> List[Dict]:
        """Fetch and parse live streams from YouTube"""
        query = search_query.replace(" ", "+")
        url = f"https://www.youtube.com/results?search_query={query}"
        
        response = requests.get(url, headers=self.HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        live_streams = []
        
        # Extract YouTube initial data
        for script in soup.find_all('script'):
            if script.string and 'var ytInitialData' in script.string:
                json_text = script.string
                start = json_text.find('{')
                end = json_text.rfind('}') + 1
                
                if start != -1 and end != -1:
                    try:
                        data = json.loads(json_text[start:end])
                        live_streams = self._parse_video_data(data, limit)
                        break
                    except json.JSONDecodeError:
                        continue
        
        return live_streams

    def _parse_video_data(self, data: Dict, limit: int) -> List[Dict]:
        """Parse YouTube data and extract live streams only"""
        streams = []
        
        try:
            # Navigate YouTube's data structure
            contents = data.get('contents', {})
            search_results = None
            
            if 'twoColumnSearchResultsRenderer' in contents:
                primary = contents['twoColumnSearchResultsRenderer']['primaryContents']
                if 'sectionListRenderer' in primary:
                    for section in primary['sectionListRenderer']['contents']:
                        if 'itemSectionRenderer' in section:
                            search_results = section['itemSectionRenderer']['contents']
                            break
            
            if not search_results:
                return streams
            
            for item in search_results:
                if 'videoRenderer' not in item:
                    continue
                    
                video_info = item['videoRenderer']
                stream = self._extract_stream_info(video_info)
                
                # Only include if it's actually live
                if stream and stream['is_live']:
                    streams.append(stream)
                    
                if len(streams) >= limit:
                    break
                    
        except Exception as e:
            print(f"Parse error: {e}")
            
        return streams

    def _extract_stream_info(self, video_info: Dict) -> Optional[Dict]:
        """Extract structured info from a single video"""
        try:
            stream = {
                'title': self._safe_extract_text(video_info.get('title', {})),
                'channel': self._safe_extract_channel(video_info.get('ownerText', {})),
                'view_count': self._safe_extract_text(video_info.get('viewCountText', {})),
                'url': f"https://www.youtube.com/watch?v={video_info.get('videoId', '')}",
                'thumbnail': self._extract_thumbnail(video_info.get('thumbnail', {})),
                'is_live': False
            }
            
            published_time = self._safe_extract_text(video_info.get('publishedTimeText', {}))
            duration = self._safe_extract_text(video_info.get('lengthText', {}))
            
            if not published_time.strip() and not duration.strip():
                stream['is_live'] = True
            
            return stream if stream['is_live'] else None
            
        except Exception:
            return None

    def _safe_extract_text(self, text_obj: Dict) -> str:
        """Safely extract text from YouTube's text objects"""
        if not text_obj:
            return ""
        
        if 'simpleText' in text_obj:
            return text_obj['simpleText']
        elif 'runs' in text_obj:
            return ''.join([run.get('text', '') for run in text_obj['runs']])
        
        return ""

    def _safe_extract_channel(self, owner_obj: Dict) -> str:
        """Extract channel name safely"""
        if 'runs' in owner_obj and owner_obj['runs']:
            return owner_obj['runs'][0].get('text', '')
        return ""

    def _extract_thumbnail(self, thumb_obj: Dict) -> str:
        """Extract highest quality thumbnail URL"""
        thumbnails = thumb_obj.get('thumbnails', [])
        if thumbnails:
            return thumbnails[-1].get('url', '')
        return ""

    def _get_timestamp(self) -> str:
        """Get current timestamp for response"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_available_categories(self) -> List[str]:
        """Return list of available categories"""
        return list(self.CATEGORIES.keys())


def get_live_news_streams(category: str = "sports", limit: int = 10) -> Dict:
    """
    Tool function for agent use
    
    Args:
        category: News category (business, breaking, Maharashtra, Karnataka, Punjab, Delhi etc.)
        limit: Max streams to return (default: 10)
        
    Returns:
        Structured dict with live stream data
    """
    scraper = YouTubeLiveNewsScraper()
    return scraper.get_live_streams(category, limit)