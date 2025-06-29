import os
import logging
import json
from datetime import datetime, timezone
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from app import app, db
from models import VideoShort, YouTubeCredentials, UploadStatus
from oauth_handler import OAuthHandler

class YouTubeUploader:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.oauth_handler = OAuthHandler()

    def upload_short(self, short_id: int, user_email: str):
        """Upload a short video to YouTube"""
        with app.app_context():
            short = VideoShort.query.get(short_id)
            if not short:
                self.logger.error(f"Short {short_id} not found")
                return
            
            try:
                short.upload_status = UploadStatus.UPLOADING
                db.session.commit()
                
                # Get valid credentials
                credentials = self._get_valid_credentials(user_email)
                if not credentials:
                    raise Exception("No valid YouTube credentials found")
                
                # Build YouTube service
                youtube = build('youtube', 'v3', credentials=credentials)
                
                # Prepare upload metadata
                body = self._prepare_upload_metadata(short)
                
                # Upload the video
                media = MediaFileUpload(
                    short.output_path,
                    chunksize=-1,
                    resumable=True,
                    mimetype='video/mp4'
                )
                
                request = youtube.videos().insert(
                    part=','.join(body.keys()),
                    body=body,
                    media_body=media
                )
                
                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        self.logger.info(f"Upload progress: {int(status.progress() * 100)}%")
                
                # Update short with YouTube info
                if 'id' in response:
                    short.youtube_video_id = response['id']
                    short.youtube_url = f"https://youtube.com/shorts/{response['id']}"
                    short.upload_status = UploadStatus.UPLOADED
                    short.uploaded_at = datetime.now(timezone.utc)
                    
                    self.logger.info(f"Successfully uploaded short {short_id} to YouTube: {short.youtube_url}")
                else:
                    raise Exception("No video ID returned from YouTube")
                
            except Exception as e:
                self.logger.error(f"Failed to upload short {short_id}: {e}")
                short.upload_status = UploadStatus.FAILED
                short.upload_error = str(e)
            
            finally:
                db.session.commit()

    def _get_valid_credentials(self, user_email: str):
        """Get valid YouTube credentials for user"""
        try:
            creds_record = YouTubeCredentials.query.filter_by(user_email=user_email).first()
            if not creds_record:
                return None
            
            # Check if token is expired
            now = datetime.now(timezone.utc)
            # Ensure token_expires is timezone-aware for comparison
            if creds_record.token_expires.tzinfo is None:
                token_expires = creds_record.token_expires.replace(tzinfo=timezone.utc)
            else:
                token_expires = creds_record.token_expires
            
            if token_expires <= now:
                # Try to refresh the token
                refreshed_creds = self.oauth_handler.refresh_token(user_email)
                if not refreshed_creds:
                    return None
                creds_record = refreshed_creds
            
            # Create credentials object
            credentials = Credentials(
                token=creds_record.access_token,
                refresh_token=creds_record.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.environ.get("YOUTUBE_CLIENT_ID"),
                client_secret=os.environ.get("YOUTUBE_CLIENT_SECRET"),
                scopes=['https://www.googleapis.com/auth/youtube.upload']
            )
            
            return credentials
            
        except Exception as e:
            self.logger.error(f"Failed to get valid credentials: {e}")
            return None

    def _prepare_upload_metadata(self, short: VideoShort) -> dict:
        """Prepare video metadata for YouTube upload"""
        # Get user's default settings
        creds = YouTubeCredentials.query.filter_by(user_email=short.job.user_email).first()
        
        privacy_status = 'private'
        category_id = '24'  # Entertainment
        
        if creds:
            privacy_status = creds.default_privacy
            category_id = str(creds.default_category)
        
        # Prepare tags
        tags = short.tags or []
        if creds and creds.auto_add_hashtags:
            default_tags = ['shorts', 'viral', 'trending', 'entertainment']
            tags = list(set(tags + default_tags))  # Remove duplicates
        
        # Limit tags to 500 characters total
        tags_str = ','.join(tags)
        if len(tags_str) > 500:
            # Truncate tags to fit within limit
            cumulative_length = 0
            truncated_tags = []
            for tag in tags:
                if cumulative_length + len(tag) + 1 <= 500:  # +1 for comma
                    truncated_tags.append(tag)
                    cumulative_length += len(tag) + 1
                else:
                    break
            tags = truncated_tags
        
        body = {
            'snippet': {
                'title': short.title[:100],  # YouTube title limit
                'description': short.description[:5000],  # YouTube description limit
                'tags': tags,
                'categoryId': category_id,
                'defaultLanguage': 'en',
                'defaultAudioLanguage': 'en'
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }
        
        return body

    def get_upload_quota_usage(self, user_email: str) -> dict:
        """Get current YouTube API quota usage for user"""
        try:
            credentials = self._get_valid_credentials(user_email)
            if not credentials:
                return {'error': 'No valid credentials'}
            
            youtube = build('youtube', 'v3', credentials=credentials)
            
            # Get channel info to verify credentials work
            response = youtube.channels().list(
                part='snippet,statistics',
                mine=True
            ).execute()
            
            if response.get('items'):
                channel = response['items'][0]
                return {
                    'channel_title': channel['snippet']['title'],
                    'subscriber_count': channel['statistics'].get('subscriberCount', 0),
                    'video_count': channel['statistics'].get('videoCount', 0),
                    'status': 'connected'
                }
            else:
                return {'error': 'No channel found'}
                
        except Exception as e:
            self.logger.error(f"Failed to get quota usage: {e}")
            return {'error': str(e)}
