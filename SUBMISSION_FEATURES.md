# Startup Submission Features

This document describes the comprehensive startup submission system implemented for the AI Investment Platform.

## 🚀 Features Overview

### 1. Startup Submission Management
- **Create Submissions**: Founders can create detailed startup submissions with comprehensive business information
- **Multiple Submissions**: Support for multiple startup submissions per founder
- **Real-time Status Tracking**: Live processing status updates
- **Submission History**: Complete history of all submissions with timestamps

### 2. File Upload System
- **Multiple File Types**: Support for various file formats:
  - Pitch Decks (PDF, PPT, PPTX)
  - Video Pitches (MP4, AVI, MOV, WMV, WebM)
  - Audio Pitches (MP3, WAV, M4A, AAC)
  - Financial Models (XLSX, XLS, CSV)
  - Product Demos (MP4, AVI, MOV, WMV, WebM)
  - Founder Updates (DOCX, DOC, PDF, TXT)
- **File Validation**: Size limits and type validation
- **Secure Storage**: Organized file storage with unique naming
- **File Management**: Upload, view, and delete files

### 3. Video Recording
- **Browser-based Recording**: Record video pitches directly in the browser
- **Camera & Microphone Access**: Full media capture support
- **Real-time Preview**: Live video preview during recording
- **Automatic Processing**: Recorded videos are automatically processed and uploaded

### 4. AI Processing Pipeline
- **Automated Processing**: Submissions are automatically queued for AI analysis
- **Multi-stage Pipeline**: 
  - Data Ingestion
  - AI Analysis
  - Report Generation
  - Completion
- **Status Tracking**: Real-time progress updates
- **Error Handling**: Comprehensive error handling and recovery

## 📁 File Structure

```
/blueprints/founder.py              # Founder routes and API endpoints
/services/file_upload_service.py    # File upload and management
/services/processing_pipeline.py    # AI processing pipeline
/templates/founder/
  ├── dashboard.html               # Enhanced dashboard with submission modal
  └── submissions.html             # Submissions management page
/uploads/                          # File storage directory
  ├── pitch_decks/                # Pitch deck files
  ├── videos/                     # Video files
  ├── audio/                      # Audio files
  ├── financials/                 # Financial model files
  ├── demos/                      # Product demo files
  ├── updates/                    # Founder update files
  ├── images/                     # Image files
  └── documents/                  # General documents
```

## 🔧 API Endpoints

### Startup Submissions
- `POST /api/startup-submission` - Create new submission
- `GET /api/startup-submissions` - Get all submissions for founder
- `DELETE /api/startup-submission/<id>` - Delete submission

### File Upload
- `POST /api/startup-submission/<id>/upload` - Upload file to submission
- `DELETE /api/startup-submission/<id>/file/<index>` - Delete file from submission

### Static Files
- `GET /uploads/<path:filename>` - Serve uploaded files

## 🎨 User Interface

### Dashboard Enhancements
- **New Submission Modal**: Comprehensive form with all required fields
- **File Upload Interface**: Drag-and-drop file upload with preview
- **Video Recording**: Built-in video recording functionality
- **Processing Status**: Real-time processing indicators

### Submissions Page
- **Submission List**: Grid view of all submissions
- **Status Cards**: Visual status indicators
- **Progress Tracking**: Processing progress bars
- **Action Buttons**: View, edit, delete submissions

## 🗄️ Database Schema

### Startup Submissions Collection
```json
{
  "startupId": "strp_001",
  "submission": {
    "submittedBy": "founder@example.com",
    "submittedAt": "2025-01-20T14:32:15Z",
    "startupName": "Example Startup",
    "location": {
      "city": "San Francisco",
      "state": "California",
      "country": "United States"
    },
    "foundingDate": "2023-01-15",
    "founderIds": ["user_123"],
    "uploadedAssets": [
      {
        "type": "pitch_deck",
        "filename": "pitch.pdf",
        "url": "/uploads/pitch_decks/pitch.pdf",
        "file_size": 2048000,
        "mime_type": "application/pdf",
        "uploaded_at": "2025-01-20T14:35:00Z"
      }
    ]
  },
  "companyProfile": {
    "description": "Startup description...",
    "tagline": "One line description",
    "sector": "Fintech",
    "subsectors": ["Payment Gateway", "AI"],
    "businessModel": "B2B SaaS",
    "companyStage": "Seed",
    "teamSize": 8,
    "legalEntity": "Example Corp",
    "corporateStructure": "Delaware C-Corp",
    "ipAssets": ["Patent pending"]
  },
  "founderProfiles": [
    {
      "id": "user_123",
      "name": "John Doe",
      "email": "john@example.com",
      "education": "Stanford CS",
      "experience": [
        {
          "company": "Google",
          "role": "Software Engineer",
          "durationYears": 3
        }
      ],
      "commitmentLevel": {
        "fullTime": true,
        "equityHoldingPercent": 75,
        "personalCapitalInvestedINR": 500000
      },
      "founderMarketFitScore": 8.5
    }
  ],
  "status": "processing",
  "processingStage": "ai_analysis",
  "created_at": "2025-01-20T14:32:15Z",
  "updated_at": "2025-01-20T14:40:00Z",
  "founder_id": "user_123"
}
```

## 🔒 Security Features

- **File Type Validation**: Strict file type checking
- **File Size Limits**: Configurable size limits per file type
- **Secure File Names**: UUID-based unique file naming
- **Access Control**: Founder can only access their own submissions
- **Input Sanitization**: All inputs are sanitized and validated

## ⚙️ Configuration

### File Upload Limits
```python
MAX_FILE_SIZES = {
    'pitch_deck': 50,      # MB
    'video_pitch': 500,    # MB
    'audio_pitch': 100,    # MB
    'financial_model': 10, # MB
    'product_demo': 500,   # MB
    'founder_update': 20,  # MB
    'image': 10,           # MB
    'document': 20         # MB
}
```

### Allowed File Types
```python
ALLOWED_EXTENSIONS = {
    'pitch_deck': ['pdf', 'ppt', 'pptx'],
    'video_pitch': ['mp4', 'avi', 'mov', 'wmv', 'webm'],
    'audio_pitch': ['mp3', 'wav', 'm4a', 'aac'],
    'financial_model': ['xlsx', 'xls', 'csv'],
    'product_demo': ['mp4', 'avi', 'mov', 'wmv', 'webm'],
    'founder_update': ['docx', 'doc', 'pdf', 'txt'],
    'image': ['jpg', 'jpeg', 'png', 'gif', 'webp'],
    'document': ['pdf', 'doc', 'docx', 'txt', 'rtf']
}
```

## 🚀 Usage

### Creating a New Submission
1. Navigate to the founder dashboard
2. Click "New Submission" button
3. Fill in basic information (name, description, location, etc.)
4. Upload relevant files (pitch deck, videos, financials, etc.)
5. Optionally record a video pitch
6. Submit for processing

### Managing Submissions
1. Go to the submissions page
2. View all submissions with their status
3. Track processing progress
4. View, edit, or delete submissions as needed

## 🔮 Future Enhancements

### AI Processing Pipeline
The current implementation includes a placeholder processing pipeline. Future enhancements will include:

1. **Multimodal Data Ingestion**
   - PDF text extraction
   - Video transcription and analysis
   - Audio processing and sentiment analysis
   - Spreadsheet data extraction

2. **AI Analysis Agents**
   - Market analysis agent
   - Financial modeling agent
   - Team assessment agent
   - Competitive analysis agent

3. **Report Generation**
   - Comprehensive evaluation reports
   - Investment recommendations
   - Risk assessments
   - Market opportunity analysis

4. **Real-time Processing**
   - WebSocket updates
   - Live progress tracking
   - Real-time notifications

## 🧪 Testing

Run the test script to verify functionality:

```bash
python test_submission.py
```

This will test:
- Submission creation
- File upload
- Validation
- Processing status
- Error handling

## 📝 Notes

- The system is designed to be scalable and can handle multiple concurrent submissions
- File storage is organized by type for easy management
- All processing is asynchronous to avoid blocking the main application
- The AI processing pipeline is designed to be easily extensible
- Error handling is comprehensive with proper logging and user feedback
