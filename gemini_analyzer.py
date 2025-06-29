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
        self.use_fallback_only = False
        self.api_keys = []
        self.current_key_index = 0
        
        # Collect all available API keys
        self._collect_api_keys()
        
        # Initialize Gemini client with first available key
        if self.api_keys:
            self._initialize_client()
        else:
            self.logger.warning("No Gemini API keys found in environment variables")
            self.logger.info("Will use fallback analysis methods only")
            self.use_fallback_only = True

    def _collect_api_keys(self):
        """Collect all available Gemini API keys from environment"""
        # Primary key
        primary_key = os.environ.get("GEMINI_API_KEY")
        if primary_key:
            self.api_keys.append(primary_key)
        
        # Backup keys
        for i in range(1, 5):  # Support up to 4 backup keys
            backup_key = os.environ.get(f"GEMINI_API_KEY_{i}")
            if backup_key:
                self.api_keys.append(backup_key)
        
        self.logger.info(f"Found {len(self.api_keys)} Gemini API key(s)")

    def _initialize_client(self):
        """Initialize client with current API key"""
        if self.current_key_index < len(self.api_keys):
            try:
                api_key = self.api_keys[self.current_key_index]
                self.client = genai.Client(api_key=api_key)
                self.logger.info(f"Gemini client initialized with API key #{self.current_key_index + 1}")
                return True
            except Exception as e:
                self.logger.warning(f"Failed to initialize Gemini client with key #{self.current_key_index + 1}: {e}")
                return False
        return False

    def _switch_to_next_key(self):
        """Switch to next available API key"""
        self.current_key_index += 1
        if self.current_key_index < len(self.api_keys):
            self.logger.info(f"Switching to backup API key #{self.current_key_index + 1}")
            if self._initialize_client():
                return True
        
        # No more keys available
        self.logger.warning("All Gemini API keys exhausted, switching to fallback mode")
        self.use_fallback_only = True
        self.client = None
        return False

    def _handle_api_error(self, error_msg: str):
        """Handle API errors and attempt key switching"""
        # Check for quota exceeded or rate limit errors
        if any(indicator in error_msg.lower() for indicator in ["429", "resource_exhausted", "quota", "rate limit"]):
            self.logger.warning(f"API quota/rate limit hit: {error_msg}")
            return self._switch_to_next_key()
        
        # For other errors, log but don't switch keys
        self.logger.error(f"API error: {error_msg}")
        return False

    def analyze_segment(self, text: str) -> Dict[str, Any]:
        """Analyze a text segment for engagement and viral potential using Gemini"""
        # Check if we should use fallback only
        if self.use_fallback_only or not self.client:
            self.logger.info("Using fallback analysis (no Gemini API available)")
            return self._fallback_analysis(text)
        
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
            error_msg = str(e)
            
            # Try to switch to next API key if error is quota-related
            if self._handle_api_error(error_msg) and not self.use_fallback_only:
                # Retry with new key
                try:
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
                            'emotions': result.get('emotions', [])[:5],
                            'keywords': result.get('keywords', [])[:10],
                            'reason': result.get('reason', 'Content has potential for engagement')[:500]
                        }
                except Exception as retry_e:
                    self.logger.error(f"Retry with backup key failed: {retry_e}")
            
            # Fallback analysis
            return self._fallback_analysis(text)

    def _fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Enhanced fallback analysis when Gemini is unavailable"""
        text_lower = text.lower()
        words = text.split()
        
        # Enhanced keyword categories
        engagement_keywords = ['amazing', 'incredible', 'wow', 'shocking', 'unbelievable', 'funny', 'hilarious', 
                              'awesome', 'fantastic', 'mind-blowing', 'crazy', 'insane', 'epic', 'legendary']
        emotion_keywords = ['love', 'hate', 'excited', 'surprised', 'happy', 'angry', 'scared', 'thrilled',
                           'disappointed', 'frustrated', 'overwhelmed', 'passionate', 'emotional', 'heartwarming']
        viral_keywords = ['viral', 'trending', 'share', 'like', 'subscribe', 'follow', 'must-see', 'breaking',
                         'exclusive', 'revealed', 'secret', 'exposed', 'truth', 'shocking']
        quotable_keywords = ['said', 'quote', 'tells', 'explains', 'reveals', 'admits', 'confesses', 'announces']
        
        # Calculate scores based on keyword presence
        engagement_score = min(1.0, sum(1 for word in engagement_keywords if word in text_lower) * 0.15)
        emotion_score = min(1.0, sum(1 for word in emotion_keywords if word in text_lower) * 0.15)
        viral_score = min(1.0, sum(1 for word in viral_keywords if word in text_lower) * 0.2)
        quotability_score = min(1.0, sum(1 for word in quotable_keywords if word in text_lower) * 0.2)
        
        # Length-based scoring (optimal length for shorts)
        text_length = len(words)
        if 20 <= text_length <= 50:  # Optimal length for short clips
            length_bonus = 0.2
        elif 10 <= text_length <= 80:  # Good length
            length_bonus = 0.1
        else:
            length_bonus = 0.0
        
        # Add length bonus to all scores
        engagement_score = min(1.0, engagement_score + length_bonus)
        emotion_score = min(1.0, emotion_score + length_bonus)
        viral_score = min(1.0, viral_score + length_bonus)
        quotability_score = min(1.0, quotability_score + length_bonus)
        
        # Ensure minimum scores for content viability
        engagement_score = max(0.4, engagement_score)
        emotion_score = max(0.3, emotion_score)
        viral_score = max(0.3, viral_score)
        quotability_score = max(0.2, quotability_score)
        
        # Detect emotions based on keywords
        detected_emotions = []
        if any(word in text_lower for word in ['funny', 'hilarious', 'joke', 'laugh']):
            detected_emotions.append('humor')
        if any(word in text_lower for word in ['shocking', 'surprised', 'unexpected']):
            detected_emotions.append('surprise')
        if any(word in text_lower for word in ['love', 'heartwarming', 'beautiful']):
            detected_emotions.append('inspiration')
        if any(word in text_lower for word in ['angry', 'frustrated', 'hate']):
            detected_emotions.append('controversy')
        if not detected_emotions:
            detected_emotions = ['general']
        
        # Extract meaningful keywords (longer words, excluding common words)
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'a', 'an'}
        keywords = [word for word in words if len(word) > 3 and word.lower() not in common_words][:8]
        
        return {
            'engagement_score': engagement_score,
            'emotion_score': emotion_score,
            'viral_potential': viral_score,
            'quotability': quotability_score,
            'emotions': detected_emotions[:5],
            'keywords': keywords,
            'reason': f'Fallback analysis: {len(words)} words, detected {", ".join(detected_emotions)} content'
        }

    def generate_metadata(self, segment_text: str, original_title: str) -> Dict[str, Any]:
        """Generate title, description, and tags for a video short using Gemini"""
        # Check if we should use fallback only
        if self.use_fallback_only or not self.client:
            self.logger.info("Using fallback metadata generation (no Gemini API available)")
            return self._fallback_metadata(segment_text, original_title)
            
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
            error_msg = str(e)
            
            # Try to switch to next API key if error is quota-related
            if self._handle_api_error(error_msg) and not self.use_fallback_only:
                # Retry with new key
                try:
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
                except Exception as retry_e:
                    self.logger.error(f"Retry with backup key failed: {retry_e}")
            
            return self._fallback_metadata(segment_text, original_title)

    def _fallback_metadata(self, segment_text: str, original_title: str) -> Dict[str, Any]:
        """Enhanced fallback metadata generation"""
        words = segment_text.split()
        text_lower = segment_text.lower()
        
        # Extract meaningful keywords (exclude common words)
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'a', 'an', 'this', 'that'}
        key_words = [word for word in words if len(word) > 3 and word.lower() not in common_words][:5]
        
        # Generate title based on content type
        if any(word in text_lower for word in ['funny', 'hilarious', 'joke']):
            title_prefix = "Hilarious"
        elif any(word in text_lower for word in ['shocking', 'unbelievable', 'incredible']):
            title_prefix = "Shocking"
        elif any(word in text_lower for word in ['amazing', 'awesome', 'fantastic']):
            title_prefix = "Amazing"
        elif any(word in text_lower for word in ['secret', 'revealed', 'truth']):
            title_prefix = "Revealed"
        else:
            title_prefix = "Must See"
        
        if key_words:
            title = f"{title_prefix}: {' '.join(key_words[:2])}"[:60]
        else:
            title = f"{title_prefix} Moment from {original_title.split()[0] if original_title else 'Video'}"[:60]
        
        # Generate description with relevant hashtags
        description = f"{title_prefix} moment from: {original_title}\n\n"
        
        if len(segment_text) > 100:
            description += f'"{segment_text[:100]}..."\n\n'
        else:
            description += f'"{segment_text}"\n\n'
        
        # Add relevant hashtags based on content
        hashtags = ["#Shorts", "#Viral", "#MustWatch"]
        if any(word in text_lower for word in ['funny', 'hilarious']):
            hashtags.extend(["#Funny", "#Comedy"])
        if any(word in text_lower for word in ['shocking', 'unbelievable']):
            hashtags.extend(["#Shocking", "#Unbelievable"])
        if any(word in text_lower for word in ['amazing', 'incredible']):
            hashtags.extend(["#Amazing", "#Incredible"])
        hashtags.extend(["#Trending", "#Entertainment"])
        
        description += " ".join(hashtags)
        
        # Generate tags
        base_tags = ['shorts', 'viral', 'trending', 'entertainment', 'mustsee']
        content_tags = []
        
        if any(word in text_lower for word in ['funny', 'comedy', 'hilarious']):
            content_tags.extend(['funny', 'comedy', 'humor'])
        if any(word in text_lower for word in ['music', 'song', 'dance']):
            content_tags.extend(['music', 'song', 'dance'])
        if any(word in text_lower for word in ['food', 'cooking', 'recipe']):
            content_tags.extend(['food', 'cooking', 'recipe'])
        if any(word in text_lower for word in ['travel', 'adventure']):
            content_tags.extend(['travel', 'adventure'])
        
        # Combine all tags
        all_tags = base_tags + content_tags + key_words[:3]
        
        return {
            'title': title,
            'description': description[:500],  # YouTube description limit
            'tags': list(set(all_tags))[:15]  # Remove duplicates and limit to 15
        }

    def analyze_video_file(self, video_path: str) -> Dict[str, Any]:
        """Analyze video file directly with Gemini vision capabilities"""
        # Check if we should use fallback only
        if self.use_fallback_only or not self.client:
            self.logger.info("Video file analysis not available (no Gemini API)")
            return {'analysis': 'Video analysis not available - using audio transcript analysis instead'}
        
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
