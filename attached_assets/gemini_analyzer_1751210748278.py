import json
import logging
import os
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List, Dict, Any

class SegmentAnalysis(BaseModel):
    engagement_score: float
    emotion_score: float
    viral_potential: float
    quotability: float
    emotions: List[str]
    keywords: List[str]
    reason: str

class VideoMetadata(BaseModel):
    title: str
    description: str
    tags: List[str]

class GeminiAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        
        # Initialize Gemini client
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            try:
                self.client = genai.Client(api_key=api_key)
                self.logger.info("Gemini client initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini client: {e}")
                raise
        else:
            raise Exception("GEMINI_API_KEY not found in environment variables")

    def analyze_segment(self, text: str) -> Dict[str, Any]:
        """Analyze a text segment for engagement and viral potential using Gemini"""
        try:
            system_prompt = """You are an expert content analyst specializing in viral social media content and YouTube Shorts.
            
            Analyze the given text segment for its potential to create engaging short-form video content.
            
            Consider these factors:
            - Engagement Score (0.0-1.0): How likely this content is to engage viewers
            - Emotion Score (0.0-1.0): Emotional impact and intensity
            - Viral Potential (0.0-1.0): Likelihood to be shared and go viral
            - Quotability (0.0-1.0): How memorable and quotable the content is
            - Emotions: List of emotions detected (humor, surprise, excitement, inspiration, etc.)
            - Keywords: Important keywords that make this content engaging
            - Reason: Brief explanation of why this segment is engaging
            
            Focus on content that has:
            - Strong emotional hooks
            - Surprising or unexpected elements
            - Humor or entertainment value
            - Inspirational or motivational content
            - Controversial or debate-worthy topics
            - Clear storytelling elements
            - Quotable phrases or moments"""

            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=f"Analyze this content segment for YouTube Shorts potential:\n\n{text}")])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=SegmentAnalysis,
                ),
            )

            if response.text:
                result = json.loads(response.text)
                return {
                    'engagement_score': max(0.0, min(1.0, result.get('engagement_score', 0.5))),
                    'emotion_score': max(0.0, min(1.0, result.get('emotion_score', 0.5))),
                    'viral_potential': max(0.0, min(1.0, result.get('viral_potential', 0.5))),
                    'quotability': max(0.0, min(1.0, result.get('quotability', 0.5))),
                    'emotions': result.get('emotions', [])[:5],  # Limit to 5 emotions
                    'keywords': result.get('keywords', [])[:10],  # Limit to 10 keywords
                    'reason': result.get('reason', 'Content has potential for engagement')[:500]
                }
            else:
                raise Exception("Empty response from Gemini")

        except Exception as e:
            self.logger.error(f"Gemini segment analysis failed: {e}")
            # Fallback analysis
            return self._fallback_analysis(text)

    def _fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback analysis when Gemini is unavailable"""
        text_lower = text.lower()
        
        # Simple keyword-based scoring
        engagement_keywords = ['amazing', 'incredible', 'wow', 'shocking', 'unbelievable', 'funny', 'hilarious']
        emotion_keywords = ['love', 'hate', 'excited', 'surprised', 'happy', 'angry', 'scared']
        viral_keywords = ['viral', 'trending', 'share', 'like', 'subscribe', 'follow']
        
        engagement_score = min(1.0, sum(1 for word in engagement_keywords if word in text_lower) * 0.2)
        emotion_score = min(1.0, sum(1 for word in emotion_keywords if word in text_lower) * 0.2)
        viral_score = min(1.0, sum(1 for word in viral_keywords if word in text_lower) * 0.3)
        
        # Base scores to ensure content has some potential
        engagement_score = max(0.4, engagement_score)
        emotion_score = max(0.3, emotion_score)
        viral_score = max(0.3, viral_score)
        
        return {
            'engagement_score': engagement_score,
            'emotion_score': emotion_score,
            'viral_potential': viral_score,
            'quotability': min(1.0, len(text.split()) / 20),  # Based on length
            'emotions': ['general'],
            'keywords': text.split()[:5],
            'reason': 'Content analyzed with fallback method'
        }

    def generate_metadata(self, segment_text: str, original_title: str) -> Dict[str, Any]:
        """Generate title, description, and tags for a video short using Gemini"""
        try:
            system_prompt = """You are an expert YouTube content creator specializing in viral Shorts.
            
            Generate engaging metadata for a YouTube Short based on the content segment and original video title.
            
            Guidelines:
            - Title: Create a catchy, clickable title (50-60 characters) that hooks viewers
            - Description: Write an engaging description (100-200 words) with relevant hashtags
            - Tags: Generate 10-15 relevant tags for discoverability
            
            Focus on:
            - Using emotional triggers and curiosity gaps
            - Including trending keywords and hashtags
            - Making titles that encourage clicks
            - Creating descriptions that encourage engagement
            - Using tags that help with YouTube algorithm"""

            prompt = f"""Original video title: {original_title}
            
Content segment: {segment_text}

Generate optimized YouTube Shorts metadata for this content."""

            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=prompt)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=VideoMetadata,
                ),
            )

            if response.text:
                result = json.loads(response.text)
                return {
                    'title': result.get('title', f"Viral Moment from {original_title}")[:100],
                    'description': result.get('description', f"Amazing clip from {original_title}\n\n#Shorts #Viral #Trending"),
                    'tags': result.get('tags', ['shorts', 'viral', 'trending', 'entertainment'])[:15]
                }
            else:
                raise Exception("Empty response from Gemini")

        except Exception as e:
            self.logger.error(f"Gemini metadata generation failed: {e}")
            return self._fallback_metadata(segment_text, original_title)

    def _fallback_metadata(self, segment_text: str, original_title: str) -> Dict[str, Any]:
        """Fallback metadata generation"""
        # Extract key words from segment
        words = segment_text.split()
        key_words = [word for word in words[:5] if len(word) > 3]
        
        title = f"Must See: {' '.join(key_words[:3])}"[:60]
        
        description = f"Incredible moment from {original_title}\n\n"
        description += f"Content: {segment_text[:100]}...\n\n"
        description += "#Shorts #Viral #MustWatch #Trending #Entertainment"
        
        tags = ['shorts', 'viral', 'trending', 'entertainment', 'mustsee'] + key_words[:5]
        
        return {
            'title': title,
            'description': description,
            'tags': tags
        }

    def analyze_video_file(self, video_path: str) -> Dict[str, Any]:
        """Analyze video file directly with Gemini vision capabilities"""
        try:
            with open(video_path, "rb") as f:
                video_bytes = f.read()
                
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[
                    types.Part.from_bytes(
                        data=video_bytes,
                        mime_type="video/mp4",
                    ),
                    "Analyze this video for engaging moments, emotional highlights, and viral potential. "
                    "Identify the most interesting segments that would work well as YouTube Shorts."
                ],
            )

            return {'analysis': response.text if response.text else 'No analysis available'}

        except Exception as e:
            self.logger.error(f"Video file analysis failed: {e}")
            return {'analysis': 'Video analysis not available'}
