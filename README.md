# Aicurate - AI Investment Platform

A revolutionary AI-powered platform that transforms how startups connect with investors. Leveraging Google's Gemini AI, Aicurate automates startup evaluation, generates comprehensive investment reports, and provides data-driven insights that accelerate funding decisions while reducing due diligence time from weeks to hours.

## Table of Contents

- [Introduction](#introduction)
- [Demo](#demo)
- [Inspiration](#inspiration)
- [What It Does](#what-it-does)
- [How We Built It](#how-we-built-it)
- [Challenges We Faced](#challenges-we-faced)
- [How to Run](#how-to-run)
- [Tech Stack](#tech-stack)
- [Team](#team)
- [Sample Dataset](#sample-dataset)
- [AI Features](#ai-features)
- [Submission Deliverables](#submission-deliverables)

---

## Introduction

Aicurate is a cutting-edge AI-powered investment platform that revolutionizes startup-investor connections through intelligent automation. Built on modern web technologies and powered by Google's Gemini AI, it transforms the traditional due diligence process by providing instant, comprehensive analysis of startup submissions.

The platform processes multimodal data (documents, videos, financial models) to generate detailed investment reports with 100+ metrics, enabling investors to make faster, more informed decisions while helping founders present their ventures more effectively. By automating the analysis pipeline, Aicurate reduces evaluation time from weeks to hours while maintaining institutional-grade accuracy.

---

## Demo

- **Live Demo**: [Link to Demo](https://aicurate.onrender.com)
- **Video Walkthrough**: [Link to Video](https://youtu.be/Mtvc1BVQ-3Q?feature=shared)
- **Pitch Deck**: [Download PDF](https://drive.google.com/file/d/123S0ZJMxMtClfJS2-RfFTm7uxHb_NfFm/view?usp=sharing)

### Screenshots Gallery

#### Homepage & Navigation
![Homepage](images/home.png)
*Clean, modern homepage with role selection and navigation*

#### Investor Experience
![Investor Dashboard](images/investor-dashboard.png)
*Comprehensive investor dashboard with AI-powered insights and analytics*

![Startup Lists](images/startup-lists.png)
*Curated startup listings with filtering and search capabilities*

![Preferences](images/preferences.png)
*Investor preference settings for personalized recommendations*

#### AI Analysis & Reports
![Deal Insights](images/dealnote.png)
*AI-generated deal insights and investment analysis*

![Charts](images/charts.png)
*Interactive charts and data visualizations*

#### Investment Decision Making
![Buy or Not](images/buyornot.png)
*Investment decision interface with AI recommendations*

---

## Inspiration

The traditional startup-investor matching process is often inefficient, time-consuming, and lacks data-driven insights. Founders struggle to present their ventures comprehensively, while investors face information overload when evaluating opportunities. Aicurate was built to address these challenges by:

- **Automating Analysis**: Using AI to process and analyze startup submissions comprehensively
- **Standardizing Information**: Creating structured, comparable data for investment decisions
- **Enhancing User Experience**: Providing intuitive interfaces for all user types
- **Enabling Data-Driven Decisions**: Offering detailed metrics and scoring systems

---

## What It Does

### For Founders
- **Startup Submission Management**: Create and manage multiple startup submissions
- **File Upload System**: Support for pitch decks, videos, financial models, and documents
- **AI-Powered Analysis**: Automated processing and report generation
- **Real-time Status Tracking**: Live updates on submission processing
- **Comprehensive Dashboards**: Track submissions, funding goals, and progress

### For Investors
- **Intelligent Startup Discovery**: AI-curated startup recommendations
- **Detailed Analysis Reports**: Comprehensive 100+ metric evaluations
- **Investment Management**: Track and manage investment portfolios
- **Advanced Filtering**: Find startups based on sector, score, and preferences
- **Deal Insights**: AI-generated insights and risk assessments

### For Administrators
- **Platform Management**: Oversee users, startups, and investments
- **Analytics Dashboard**: Platform-wide statistics and insights
- **User Management**: Manage user roles and permissions
- **Content Moderation**: Review and approve submissions

### AI-Powered Features
- **Multimodal Analysis**: Process text, images, videos, and documents
- **Intelligent Scoring**: 10+ scoring dimensions for comprehensive evaluation
- **Risk Assessment**: Automated risk identification and flagging
- **Market Analysis**: TAM/SAM/SOM calculations and competitor analysis
- **Deal Memo Generation**: Automated investment memo creation

---

## How We Built It

### Architecture Overview

```mermaid
graph TD
    %% ================== GROUPS ==================
    subgraph client["Client Layer"]
        U["User Browser (Founder / Investor / Admin)"]
    end

    subgraph edge["Edge Layer"]
        CDN["CDN / WAF"]
        LB["API Gateway / Load Balancer"]
    end

    subgraph app["Application Layer"]
        NGINX["Nginx Reverse Proxy"]
        subgraph flask["Flask App (Aicurate)"]
            direction TB
            WEB["Web Layer (Blueprints)"]
            subgraph svc["Service Layer"]
                direction TB
                AUTHZ["Auth / Session Manager"]
                SUBM["Submission Handler"]
                RECO["Recommendation Engine"]
            end
            Q["In-Memory Job Queue"]
            W["AI Worker (Async)"]
        end
    end

    subgraph ai["AI Layer"]
        GEM["Gemini / Vertex AI (Multimodal)"]
    end

    subgraph firebase["Firebase Layer"]
        FS["Firestore (Insights + Metadata)"]
        ST["Firebase Storage (Pitch Decks, XLSX, Video)"]
    end

    %% ================== FLOWS ==================
    U -->|"HTTPS Requests"| CDN --> LB --> NGINX --> WEB
    U -->|"Auth SDK"| AUTHZ

    WEB --> AUTHZ
    WEB --> SUBM
    SUBM -->|"enqueue"| Q
    Q --> W
    W -->|"AI Analysis"| GEM
    W -->|"Save Report / Metrics"| FS
    SUBM -->|"File Upload"| ST
    W -->|"Store Thumbnails / Derived"| ST
    FS --> RECO
    RECO --> FS

    %% ================== CLASSES (using old theme) ==================
    %% Blue
    classDef client   fill:#93C5FD,stroke:#1D4ED8,stroke-width:2.2,color:#0B1B32;
    %% Amber
    classDef edge     fill:#FCD34D,stroke:#B45309,stroke-width:2.2,color:#2B1D07;
    %% Teal
    classDef app      fill:#5EEAD4,stroke:#0F766E,stroke-width:2.2,color:#053A37;
    %% Blue (Flask app inner)
    classDef flask    fill:#93C5FD,stroke:#1E40AF,stroke-width:2.2,color:#0B1B32;
    %% Light Blue (service layer)
    classDef svc      fill:#DBEAFE,stroke:#1E40AF,stroke-width:2.2,color:#0B1B32;
    %% Green
    classDef ai       fill:#86EFAC,stroke:#15803D,stroke-width:2.2,color:#062812;
    %% Pink
    classDef firebase fill:#F9A8D4,stroke:#9D174D,stroke-width:2.2,color:#3B0A1E;

    class U client
    class CDN,LB edge
    class NGINX,WEB,Q,W app
    class flask flask
    class AUTHZ,SUBM,RECO svc
    class GEM ai
    class FS,ST firebase

    %% ================== GROUP STYLES (matching old look) ==================
    style client   fill:#E2E8F0,stroke:#334155,stroke-width:2
    style edge     fill:#E5E7EB,stroke:#374151,stroke-width:2
    style app      fill:#E5E7EB,stroke:#374151,stroke-width:2
    style flask    fill:#DBEAFE,stroke:#1E40AF,stroke-width:1.8,stroke-dasharray:4 3
    style svc      fill:#DBEAFE,stroke:#1E40AF,stroke-width:1.6,stroke-dasharray:4 3
    style ai       fill:#E5E7EB,stroke:#374151,stroke-width:2
    style firebase fill:#E5E7EB,stroke:#374151,stroke-width:2

    %% ================== LINKS ==================
    linkStyle default stroke:#334155,stroke-width:2,opacity:0.95
```

### Core Components

**1. AI Processing Pipeline**
- Multimodal file processing (PDF, video, audio, documents)
- Gemini AI integration for content analysis
- Structured report generation with 100+ metrics
- Automated scoring and risk assessment

**2. User Management System**
- Firebase Authentication for secure login
- Role-based access control (Founder, Investor, Admin)
- Session management and security

**3. File Upload & Processing**
- Support for multiple file types and formats
- Secure file storage and organization
- Content extraction and analysis

**4. Real-time Processing**
- Asynchronous AI processing
- Status tracking and updates
- Error handling and recovery

### Data Flow

```mermaid
graph TD
    %% ================== GROUPS ==================
    subgraph browser["User's Browser"]
        A["User (Founder / Investor / Admin)"]
    end

    subgraph cloud["Cloud Services"]
        B["Firebase Auth"]
        C["Firestore Database"]
        D["Google AI Platform (Gemini API)"]
    end

    subgraph app["Application Server (Docker)"]
        E["Nginx Web Server"]
        subgraph flaskapp["Flask Application (Aicurate)"]
            direction LR
            F["Web Layer (Blueprints)"]
            subgraph svc["Service Layer"]
                direction TB
                G["Core Services (Firebase • Files)"]
                H["Processing Pipeline"]
            end
            I["Async AI Worker (Background Thread)"]
        end
    end

    %% ================== FLOWS ==================
    A -- "(1) HTTPS Requests" --> E
    E -- "Reverse Proxy →" --> F

    A -- "(2) Auth via SDK" --> B
    F -- "Verify token / manage session" --> B

    F -- "Use" --> G
    G -- "CRUD" --> C

    F -- "(3) Queue startup submission" --> H
    H -- "Add job to in-memory queue" --> I

    I -- "(4) Upload files + prompt" --> D
    D -- "(5) Structured JSON" --> I
    I -- "(6) Save report + status" --> C

    %% ================== NODE CLASSES (darker fills + strong borders) ==================
    classDef user     fill:#93C5FD,stroke:#1D4ED8,stroke-width:2.2,color:#0B1B32;     %% Blue-300 fill, Blue-700 border
    classDef firebase fill:#FCD34D,stroke:#B45309,stroke-width:2.2,color:#2B1D07;     %% Amber-300 fill, Amber-700 border
    classDef googleai fill:#86EFAC,stroke:#15803D,stroke-width:2.2,color:#062812;     %% Green-300 fill, Green-700 border
    classDef nginx    fill:#5EEAD4,stroke:#0F766E,stroke-width:2.2,color:#053A37;     %% Teal-300 fill, Teal-700 border
    classDef flask    fill:#93C5FD,stroke:#1E40AF,stroke-width:2.2,color:#0B1B32;     %% Blue-300 fill, Indigo-800 border
    classDef worker   fill:#F9A8D4,stroke:#9D174D,stroke-width:2.2,color:#3B0A1E;     %% Pink-300 fill, Rose-800 border

    class A user;
    class B,C firebase;
    class D googleai;
    class E nginx;
    class F,G,H flask;
    class I worker;

    %% ================== GROUP BOUNDARIES (darker + solid) ==================
    style browser fill:#E2E8F0,stroke:#334155,stroke-width:2,stroke-dasharray:0
    style cloud   fill:#E5E7EB,stroke:#374151,stroke-width:2,stroke-dasharray:0
    style app     fill:#E5E7EB,stroke:#374151,stroke-width:2,stroke-dasharray:0
    style flaskapp fill:#DBEAFE,stroke:#1E40AF,stroke-width:1.8,stroke-dasharray:4 3
    style svc      fill:#DBEAFE,stroke:#1E40AF,stroke-width:1.6,stroke-dasharray:4 3

    %% ================== LINKS (clearer + darker) ==================
    linkStyle default stroke:#334155,stroke-width:2,opacity:0.95
```

## Sequence Diagram: Startup Submission & Analysis

This diagram shows the detailed, step-by-step sequence of events that occurs when a founder submits their startup for AI analysis.

```mermaid
sequenceDiagram
    participant Founder as Founder (Browser)
    participant Backend as Flask Backend
    participant Firestore as Firestore DB
    participant Queue as Processing Queue
    participant Worker as AI Worker (Thread)
    participant Gemini as Google AI (Gemini)
    participant Investor as Investor (Browser)

    Founder->>+Backend: 1. POST /founder/api/startup (with form data & files)
    Backend->>+Firestore: 2. Create submission doc (status: 'submitted')
    Firestore-->>-Backend: Returns submission_id
    Backend->>+Queue: 3. queue_submission(submission_id, data)
    Queue->>+Firestore: 4. Update submission status to 'queued'
    Firestore-->>-Queue: OK
    Queue-->>-Backend: Queued successfully
    Backend-->>-Founder: Returns { success: true }

    Note over Queue, Worker: Later, in a background thread...
    Queue->>Worker: 5. Dequeue job
    Worker->>+Firestore: 6. Update submission status to 'processing'
    Firestore-->>-Worker: OK

    Worker->>+Gemini: 7. Upload files & send prompt
    Gemini-->>-Worker: 8. Return structured JSON report

    Worker->>+Firestore: 9. Save report to 'startup_evaluation_reports'
    Firestore-->>-Worker: OK
    Worker->>+Firestore: 10. Update submission status to 'completed'
    Firestore-->>-Worker: OK

    Note over Investor, Backend: Much later...
    Investor->>+Backend: 11. GET /investor/startup/<id>
    Backend->>+Firestore: 12. Fetch submission & AI report
    Firestore-->>-Backend: Return documents
    Backend-->>-Investor: 13. Render page with report data
```

---

## Challenges We Faced

### Technical Challenges
- **Multimodal File Processing**: Handling diverse file formats and extracting meaningful content
- **AI Integration**: Managing API rate limits and ensuring reliable AI responses
- **Real-time Processing**: Implementing asynchronous processing with status updates
- **Data Structure Design**: Creating flexible schemas for varied startup data

### User Experience Challenges
- **Complex Data Presentation**: Making AI-generated insights accessible and actionable
- **File Upload Management**: Handling large files and multiple uploads efficiently
- **Cross-Platform Compatibility**: Ensuring consistent experience across devices

### Scalability Challenges
- **Database Optimization**: Efficiently querying and storing large amounts of data
- **AI Processing Queue**: Managing concurrent AI processing requests
- **File Storage**: Organizing and serving uploaded files efficiently

---

## How to Run

### Prerequisites

- Python 3.9+
- Docker & Docker Compose
- Firebase project with Authentication and Firestore enabled
- Google Gemini API key
- Git

### Quick Start with Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/Ayush-projects/aicurate.git
   cd aicurate
   ```

2. **Configure environment variables**
   ```bash
   cp env.production.example .env
   # Edit .env with your credentials
   ```

3. **Run with Docker Compose**
   ```bash
   # Development mode
   docker-compose -f docker-compose.dev.yml up --build

   # Production mode
   docker-compose up --build
   ```

4. **Access the application**
   - Open http://localhost:5001 in your browser
   - The application will be running with hot reload in development mode

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/aicurate.git
   cd aicurate
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp env_example.txt .env
   # Edit .env with your Firebase and Gemini credentials
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

### Environment Configuration

Create a `.env` file with the following variables:

   ```env
# Firebase Configuration
   FIREBASE_API_KEY=your_api_key
   FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
   FIREBASE_PROJECT_ID=your_project_id
   FIREBASE_STORAGE_BUCKET=your_project.appspot.com
   FIREBASE_MESSAGING_SENDER_ID=your_sender_id
   FIREBASE_APP_ID=your_app_id

# Firebase Admin SDK
   FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n"
   FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key

   # Flask Configuration
SECRET_KEY=your_secret_key_here
   FLASK_ENV=development
   HOST=0.0.0.0
PORT=5001

   # Admin Configuration
   ADMIN_EMAILS=admin@company.com,ceo@company.com
   ```

---

## Docker Build & Make Commands

### Quick Start with Make

The project includes a comprehensive Makefile for easy Docker management:

```bash
# Show all available commands
make help

# Start development environment
make dev

# Start production environment
make prod

# Build Docker images
make build

# Start services in background
make up

# Stop all services
make down

# View application logs
make logs

# Open shell in app container
make shell

# Run tests
make test

# Clean up containers and images
make clean
```

### Docker Commands

#### Development Environment
```bash
# Start with hot reload
make dev
# OR
docker-compose -f docker-compose.dev.yml up --build

# Run in background
docker-compose -f docker-compose.dev.yml up -d --build

# View logs
docker-compose -f docker-compose.dev.yml logs -f
```

#### Production Environment
```bash
# Start production setup
make prod
# OR
docker-compose up --build

# Run with nginx reverse proxy
docker-compose up -d --build

# Scale the application
make scale
# OR
docker-compose up --scale app=3
```

#### Advanced Docker Commands
```bash
# Build only
make build
# OR
docker-compose build

# Restart services
make restart
# OR
docker-compose restart

# Show container status
make status
# OR
docker-compose ps

# Clean up everything
make clean
# OR
docker-compose down -v
docker system prune -f
```

#### Development & Testing
```bash
# Run tests in container
make test

# Open shell for debugging
make shell

# Update dependencies
make update-deps

# Backup logs
make backup-logs

# Security scan
make security-scan

# Performance testing
make perf-test
```

### Docker Compose Files

- **`docker-compose.yml`** - Production configuration with nginx
- **`docker-compose.dev.yml`** - Development configuration with hot reload

---

## Tech Stack

### Backend
- **Python 3.9+**: Core programming language
- **Flask 2.3.3**: Web framework
- **Firebase Admin SDK**: Backend authentication and database
- **Google Gemini AI**: AI processing and analysis
- **Werkzeug**: WSGI utilities

### Frontend
- **HTML5/CSS3**: Structure and styling
- **JavaScript**: Interactive functionality
- **Tailwind CSS**: Utility-first CSS framework
- **Jinja2**: Template engine

### AI & ML
- **Google Gemini API**: Multimodal AI analysis
- **PyPDF2**: PDF processing
- **OpenPyXL**: Excel file processing
- **python-docx**: Word document processing
- **Pillow**: Image processing
- **pytesseract**: OCR capabilities

### Database & Storage
- **Firebase Firestore**: NoSQL database
- **Firebase Authentication**: User management
- **Local File System**: File storage

### DevOps & Deployment
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Reverse proxy and static file serving
- **Gunicorn**: WSGI HTTP server

### Development Tools
- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Linting
- **isort**: Import sorting

---

## Team

- **Ayush Addhyayan** – [GitHub](https://github.com/Ayush-projects) | [LinkedIn](https://www.linkedin.com/in/connectayush/)
- **Sriram B** – [GitHub](https://github.com/sriram14) | [LinkedIn](https://www.linkedin.com/in/b-sriram/)
- **Abhiram Bhimavarapu** – [GitHub](https://github.com/Abhirambvss) | [LinkedIn](https://www.linkedin.com/in/abhiram-bhimavarapu/?originalSubdomain=in)

---

## Sample Dataset

### Startup Evaluation Report Structure

The AI generates comprehensive reports with the following structure:

```json
{
  "startupId": "strp_001",
  "submission": {
    "submittedBy": "founder@example.com",
    "submittedAt": "2024-01-15T10:30:00Z",
    "startupName": "Example Startup",
    "location": {
      "city": "Bangalore",
      "state": "Karnataka", 
      "country": "India"
    },
    "foundingDate": "2023-01-01",
    "founderIds": ["user_123"],
    "uploadedAssets": [...]
  },
  "companyProfile": {
    "description": "AI-powered solution...",
    "sector": "Fintech",
    "businessModel": "B2B SaaS",
    "companyStage": "Seed",
    "teamSize": 15
  },
  "founderProfiles": [...],
  "teamStructure": {...},
  "product": {...},
  "traction": {...},
  "market": {...},
  "competitorLandscape": {...},
  "financials": {...},
  "aiInsights": {...},
  "scores": {
    "FounderMarketFit": 8.6,
    "ProductDifferentiation": 8.3,
    "GoToMarketStrategy": 7.9,
    "CXScore": 9.2,
    "Traction": 8.1,
    "FinancialHealth": 7.2,
    "TeamQuality": 8.0,
    "MarketPotential": 9.0,
    "RiskAdjustedScore": 7.8,
    "OverallScore": 8.4
  },
  "agentPipeline": [...],
  "timestamps": {...},
  "version": "1.1"
}
```

### Key Metrics Analyzed

- **Financial Metrics**: Revenue, burn rate, runway, funding requirements
- **Traction Metrics**: User growth, retention, engagement, market penetration
- **Team Metrics**: Founder experience, team composition, advisor network
- **Market Metrics**: TAM/SAM/SOM, growth rates, competitive positioning
- **Product Metrics**: Maturity, differentiation, roadmap, technical capabilities

---

## AI Features

### Multimodal Processing
- **Document Analysis**: PDF pitch decks, financial models, business plans
- **Video Processing**: Pitch videos, product demos, founder presentations
- **Audio Analysis**: Audio pitches, interview recordings
- **Image Processing**: Screenshots, diagrams, infographics

### Intelligent Analysis
- **Automated Scoring**: 10+ dimensional scoring system
- **Risk Assessment**: Automated risk identification and flagging
- **Market Analysis**: TAM/SAM/SOM calculations and growth projections
- **Competitive Analysis**: Competitor identification and positioning
- **Financial Health**: Burn rate, runway, and funding analysis

### Report Generation
- **Structured Output**: Standardized JSON format with 100+ metrics
- **Deal Memos**: Automated investment memo generation
- **Visualizations**: Charts and graphs for key metrics
- **Recommendations**: AI-generated next steps and insights

---

## Submission Deliverables

### Core Platform Features
- **Multi-role Authentication**: Founder, Investor, and Admin dashboards
- **AI-Powered Analysis**: Gemini AI integration for startup evaluation
- **File Upload System**: Support for multiple file types and formats
- **Real-time Processing**: Asynchronous AI processing with status updates
- **Comprehensive Reporting**: 100+ metric evaluation system

### Technical Implementation
- **Flask Backend**: RESTful API with modular architecture
- **Firebase Integration**: Authentication and Firestore database
- **Docker Containerization**: Complete containerization setup
- **Responsive UI**: Clean, intuitive interface optimized for all devices
- **Security Features**: Input validation, CSRF protection, role-based access

### AI & ML Capabilities
- **Multimodal Processing**: Text, image, video, and document analysis
- **Intelligent Scoring**: Comprehensive evaluation metrics
- **Risk Assessment**: Automated risk identification
- **Market Analysis**: TAM/SAM/SOM calculations
- **Deal Memo Generation**: Automated investment documentation

### Documentation & Deployment
- **Comprehensive README**: Detailed setup and usage instructions
- **API Documentation**: Complete endpoint documentation
- **Docker Configuration**: Production-ready containerization
- **Environment Setup**: Complete configuration management
- **Architecture Diagrams**: Mermaid-based system documentation

### Testing & Quality
- **Unit Tests**: Comprehensive test coverage
- **Code Quality**: Linting, formatting, and best practices
- **Error Handling**: Robust error management and logging
- **Performance Optimization**: Efficient data processing and storage

---

## API Documentation

### Authentication Endpoints
- `POST /auth/api/login` - User login
- `POST /auth/api/signup` - User registration
- `POST /auth/api/verify-token` - Verify Firebase token
- `GET /auth/logout` - User logout

### Founder Endpoints
- `GET /founder/dashboard` - Founder dashboard
- `GET /founder/profile` - Founder profile
- `GET /founder/startups` - Manage startups
- `POST /founder/api/startup` - Create startup submission
- `PUT /founder/api/startup/<id>` - Update startup
- `DELETE /founder/api/startup/<id>` - Delete startup

### Investor Endpoints
- `GET /investor/dashboard` - Investor dashboard
- `GET /investor/profile` - Investor profile
- `GET /investor/startups` - Browse startups
- `GET /investor/investments` - View investments
- `POST /investor/api/invest` - Create investment
- `GET /investor/startup/<id>` - View detailed startup analysis

### Admin Endpoints
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/users` - User management
- `GET /admin/startups` - Startup management
- `GET /admin/investments` - Investment management
- `PUT /admin/api/user/<id>/status` - Update user status

---

## Security Features

- **Input Validation**: Comprehensive validation and sanitization
- **Role-based Access Control**: Different access levels for different user types
- **CSRF Protection**: Built-in CSRF protection for forms
- **Secure Sessions**: HTTP-only, secure session cookies
- **Password Requirements**: Strong password validation
- **XSS Protection**: Input sanitization and output encoding
- **File Upload Security**: Type validation and size limits

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the logs for error details
- Contact the development team

---

## Changelog

### v2.0.0 - AI Integration & UI Overhaul
- Complete AI integration with Gemini API
- Multimodal file processing capabilities
- Comprehensive scoring and analysis system
- Clean, intuitive interface with modern design principles
- Real-time processing pipeline
- Enhanced user experience and animations

### v1.0.0 - Initial Release
- Role-based authentication system
- Firebase integration
- Basic startup submission functionality
- Investor dashboard
- Admin panel
- File upload system

---

*Built with love by the Aicurate Team*
