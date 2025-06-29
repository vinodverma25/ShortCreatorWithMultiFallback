from datetime import datetime, timezone
from enum import Enum
from app import db
from sqlalchemy import JSON

class ProcessingStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    EDITING = "editing"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"

class UploadStatus(Enum):
    NOT_UPLOADED = "not_uploaded"
    PENDING = "pending"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    FAILED = "failed"

class VideoJob(db.Model):
    __tablename__ = 'video_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    youtube_url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(200))
    duration = db.Column(db.Integer)  # in seconds
    status = db.Column(db.Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    progress = db.Column(db.Integer, default=0)  # Percentage 0-100
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # File paths
    video_path = db.Column(db.String(500))
    audio_path = db.Column(db.String(500))
    transcript_path = db.Column(db.String(500))
    
    # Processing metadata
    video_info = db.Column(JSON)  # Store yt-dlp extracted info
    
    # YouTube authentication
    user_email = db.Column(db.String(200))  # Track which user's YouTube account
    
    # Video processing preferences
    video_quality = db.Column(db.String(20), default='1080p')  # 1080p, 720p, 480p, best
    aspect_ratio = db.Column(db.String(10), default='9:16')    # 9:16, 16:9, 1:1, 4:5
    
    # Relationships
    shorts = db.relationship('VideoShort', backref='job', lazy=True, cascade='all, delete-orphan')
    transcript_segments = db.relationship('TranscriptSegment', backref='job', lazy=True, cascade='all, delete-orphan')

class TranscriptSegment(db.Model):
    __tablename__ = 'transcript_segments'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('video_jobs.id'), nullable=False)
    start_time = db.Column(db.Float, nullable=False)
    end_time = db.Column(db.Float, nullable=False)
    text = db.Column(db.Text, nullable=False)
    
    # AI analysis scores
    engagement_score = db.Column(db.Float, default=0.0)
    emotion_score = db.Column(db.Float, default=0.0)
    viral_potential = db.Column(db.Float, default=0.0)
    quotability = db.Column(db.Float, default=0.0)
    overall_score = db.Column(db.Float, default=0.0)
    
    # Analysis metadata
    emotions_detected = db.Column(JSON)  # List of detected emotions
    keywords = db.Column(JSON)  # Extracted keywords
    analysis_notes = db.Column(db.Text)

class VideoShort(db.Model):
    __tablename__ = 'video_shorts'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('video_jobs.id'), nullable=False)
    
    # Video details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    tags = db.Column(JSON)  # List of tags
    start_time = db.Column(db.Float, nullable=False)
    end_time = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Float, nullable=False)
    
    # File paths
    output_path = db.Column(db.String(500))
    thumbnail_path = db.Column(db.String(500))
    
    # AI scores and metadata
    engagement_score = db.Column(db.Float, default=0.0)
    viral_potential = db.Column(db.Float, default=0.0)
    clip_reason = db.Column(db.Text)  # Why this segment was selected
    
    # YouTube upload status
    upload_status = db.Column(db.Enum(UploadStatus), default=UploadStatus.NOT_UPLOADED)
    youtube_video_id = db.Column(db.String(50))
    youtube_url = db.Column(db.String(500))
    upload_error = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    file_size = db.Column(db.Integer)  # in bytes
    
    # Relationship to access parent job (defined in VideoJob already)

class YouTubeCredentials(db.Model):
    __tablename__ = 'youtube_credentials'
    
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(200), unique=True, nullable=False)
    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text, nullable=False)
    token_expires = db.Column(db.DateTime, nullable=False)
    scope = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Channel info
    channel_id = db.Column(db.String(100))
    channel_title = db.Column(db.String(200))
    channel_thumbnail = db.Column(db.String(500))
    
    # Channel configuration settings
    default_privacy = db.Column(db.String(20), default='private')  # private, unlisted, public
    default_category = db.Column(db.Integer, default=24)  # 24 = Entertainment
    auto_add_hashtags = db.Column(db.Boolean, default=True)
    brand_watermark_enabled = db.Column(db.Boolean, default=False)
