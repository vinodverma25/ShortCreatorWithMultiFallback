# AI YouTube Shorts Generator

## Overview

This is a Flask-based web application that automatically generates viral YouTube Shorts from long-form YouTube videos using AI-powered content analysis. The system downloads YouTube videos, transcribes their audio content, analyzes segments for viral potential using Google Gemini AI, and creates optimized short-form video clips with automatic YouTube upload capabilities.

## System Architecture

### Backend Architecture
- **Framework**: Flask web application with SQLAlchemy ORM for database management
- **Database**: SQLite (default) with PostgreSQL support via environment configuration
- **Authentication**: OAuth 2.0 integration for secure YouTube API access
- **Processing Pipeline**: Asynchronous video processing using threading for non-blocking operations
- **AI Integration**: Google Gemini API for intelligent content analysis and viral potential scoring

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 dark theme for modern UI
- **UI Components**: Responsive design with real-time progress tracking and status updates
- **JavaScript**: Vanilla JavaScript for form validation and dynamic UI interactions
- **Styling**: Custom CSS with Bootstrap integration following Replit design guidelines

## Key Components

### Database Models
- **VideoJob**: Central entity tracking video processing status, metadata, and configuration
- **VideoShort**: Stores generated short clips with AI-calculated engagement scores
- **TranscriptSegment**: Manages transcribed text segments with timing information
- **YouTubeCredentials**: Handles OAuth tokens and user authentication for YouTube API

### Processing Pipeline Components
1. **Video Download**: yt-dlp integration for high-quality video fetching from YouTube
2. **Audio Transcription**: FFmpeg-based audio processing (with Whisper integration planned)
3. **Content Analysis**: Gemini AI analyzes transcript segments for viral potential, engagement scores, and emotional impact
4. **Video Editing**: MoviePy-based clip generation with aspect ratio conversion (9:16, 16:9, 1:1, 4:5)
5. **YouTube Upload**: Automated upload to authenticated user's YouTube channel

### External Service Integrations
- **YouTube Data API v3**: Video upload, metadata management, and channel integration
- **Google Gemini AI**: Advanced content analysis with engagement scoring and viral potential assessment
- **OAuth 2.0**: Secure authentication flow for YouTube account access

## Data Flow

1. User submits YouTube URL through web interface with quality and aspect ratio preferences
2. System validates URL format and creates VideoJob record with pending status
3. Background processor downloads video using yt-dlp with specified quality settings
4. Audio extraction and transcription (currently mock implementation, Whisper integration planned)
5. Transcript segments analyzed by Gemini AI for engagement metrics and viral scoring
6. High-scoring segments selected for clip generation based on configurable thresholds
7. Video editing pipeline creates vertical shorts with proper aspect ratio conversion
8. Generated clips stored locally with metadata and optionally uploaded to YouTube
9. Real-time status updates provided through progress tracking and web interface

## External Dependencies

### Required API Keys
- **GEMINI_API_KEY**: Google Gemini API for content analysis
- **YOUTUBE_CLIENT_ID**: YouTube OAuth client identifier
- **YOUTUBE_CLIENT_SECRET**: YouTube OAuth client secret

### Python Packages
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM and migrations
- **yt-dlp**: YouTube video downloading
- **MoviePy**: Video editing and processing
- **google-generativeai**: Gemini AI integration
- **google-api-python-client**: YouTube API client
- **requests**: HTTP client for OAuth flows

### System Dependencies
- **FFmpeg**: Audio/video processing backend
- **SQLite**: Default database (PostgreSQL supported)

## Deployment Strategy

### Environment Configuration
- **DATABASE_URL**: Database connection string (defaults to SQLite)
- **SESSION_SECRET**: Flask session encryption key
- **REPLIT_DEV_DOMAIN**: Automatic domain detection for OAuth redirects

### Directory Structure
- **uploads/**: Temporary storage for downloaded videos
- **outputs/**: Generated short clips storage
- **temp/**: Temporary processing files
- **templates/**: Jinja2 HTML templates
- **static/**: CSS, JavaScript, and asset files

### Replit-Specific Features
- Automatic domain detection for OAuth redirect URIs
- Environment variable integration
- Bootstrap dark theme compatibility
- Responsive design for various screen sizes

## Changelog

- June 29, 2025. Initial setup
- June 29, 2025. Added automatic file cleanup after successful YouTube uploads - removes shorts files, original video files, and cleans temporary directories
- June 29, 2025. Added Hindi audio prioritization - automatically detects and downloads Hindi audio tracks when multiple languages are available in videos

## User Preferences

Preferred communication style: Simple, everyday language.