# Technical Architecture Documentation

## AI-Enhanced Medical Management System

**Version:** 1.0  
**Last Updated:** December 15, 2025

---

## System Architecture Overview

```mermaid
graph TB
    subgraph "Client Layer"
        Browser["Web Browser<br/>(Chrome, Firefox, Safari)"]
        Camera["Camera Device"]
        Microphone["Microphone"]
    end

    subgraph "Presentation Layer"
        Templates["HTML Templates<br/>(Jinja2)"]
        StaticAssets["CSS/JS Assets"]
        Templates --> StaticAssets
    end

    subgraph "Application Layer - Flask Blueprints"
        AuthBP["Authentication Blueprint<br/>Login, Register, Profile"]
        PatientsBP["Patients Blueprint<br/>CRUD, Face Scan, Search"]
        MainBP["Main Blueprint<br/>AI Chat, Disease Match, Skin"]
        AdminBP["Admin Blueprint<br/>Dashboard, Users, Analytics"]
    end

    subgraph "Business Logic Layer"
        DiseaseMatcher["Disease Matcher<br/>(TF-IDF + Cosine Similarity)"]
        RiskAnalyzer["Risk Analyzer<br/>(Predictive Health Scoring)"]
        AIClient["AI Client<br/>(Gemini Integration)"]
        PDFGenerator["PDF Report Generator<br/>(ReportLab)"]
        FaceRecognition["Face Recognition<br/>(dlib + face_recognition)"]
    end

    subgraph "Data Access Layer"
        ORM["SQLAlchemy ORM"]
        Models["Database Models<br/>User, Patient, Disease, etc."]
        ORM --> Models
    end

    subgraph "Data Storage"
        SQLite["SQLite Database<br/>(app.db)"]
        CSVFiles["CSV Data<br/>(diseases, synonyms)"]
        JSONFiles["JSON Data<br/>(interactions)"]
        ImageStorage["Image Storage<br/>(static/uploads/)"]
    end

    subgraph "External Services"
        GeminiAPI["Google Gemini API<br/>(gemini-2.5-flash)"]
        SpeechAPI["Google Speech API<br/>(Speech Recognition)"]
    end

    Browser --> Templates
    Camera --> Browser
    Microphone --> Browser
    
    Templates --> AuthBP
    Templates --> PatientsBP
    Templates --> MainBP
    Templates --> AdminBP

    AuthBP --> FaceRecognition
    PatientsBP --> FaceRecognition
    PatientsBP --> PDFGenerator
    PatientsBP --> RiskAnalyzer
    MainBP --> DiseaseMatcher
    MainBP --> AIClient
    MainBP --> SpeechAPI

    AuthBP --> ORM
    PatientsBP --> ORM
    MainBP --> ORM
    AdminBP --> ORM

    ORM --> SQLite
    DiseaseMatcher --> CSVFiles
    PatientsBP --> JSONFiles
    FaceRecognition --> ImageStorage
    AIClient --> GeminiAPI

    style Browser fill:#e1f5ff
    style GeminiAPI fill:#fff3cd
    style SpeechAPI fill:#fff3cd
    style SQLite fill:#d4edda
```

---

## Component Architecture

```mermaid
graph LR
    subgraph "Flask Application Factory"
        AppPy["app.py<br/>create_app()"]
    end

    subgraph "Extensions Initialization"
        DB["SQLAlchemy<br/>(db)"]
        LoginManager["Flask-Login<br/>(login_manager)"]
        Migrate["Flask-Migrate<br/>(migrate)"]
    end

    subgraph "Blueprint Registration"
        Auth["auth_bp<br/>/login, /register, /logout"]
        Patients["patients_bp<br/>/add_patient, /view_patients"]
        Main["main_bp<br/>/match, /chat, /skin"]
        Admin["admin_bp<br/>/dashboard, /users"]
    end

    AppPy --> DB
    AppPy --> LoginManager
    AppPy --> Migrate
    AppPy --> Auth
    AppPy --> Patients
    AppPy --> Main
    AppPy --> Admin

    style AppPy fill:#ff6b6b
    style DB fill:#4ecdc4
    style LoginManager fill:#4ecdc4
    style Migrate fill:#4ecdc4
```

---

## Database Schema (Entity Relationship Diagram)

```mermaid
erDiagram
    User ||--o| Patient : "has one"
    Patient ||--o{ PatientDisease : "has many"
    Patient ||--o{ Visit : "has many"
    Patient ||--o{ Appointment : "has many"
    Patient ||--o{ Prescription : "has many"
    Patient ||--o{ LabTest : "has many"

    User {
        string id PK
        string username UK
        string password_hash
        string role
    }

    Patient {
        string id PK
        string name
        string age
        string address
        string image_path
        string image_hash
        blob face_encoding
        string user_id FK
    }

    PatientDisease {
        int id PK
        string patient_id FK
        string name
        string added_date
    }

    Visit {
        int id PK
        string patient_id FK
        string date
        string time
        text notes
    }

    Appointment {
        int id PK
        string patient_id FK
        string date
        string time
        string purpose
    }

    Prescription {
        int id PK
        string patient_id FK
        string medication
        string dosage
        string duration
        text notes
    }

    LabTest {
        int id PK
        string patient_id FK
        string name
        string date
        text notes
    }
```

---

## Request Flow Diagrams

### User Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Browser
    participant AuthBP
    participant Database
    participant FlaskLogin

    User->>Browser: Enter credentials
    Browser->>AuthBP: POST /login
    AuthBP->>Database: Query User by username
    Database-->>AuthBP: User record
    AuthBP->>AuthBP: Verify password hash
    alt Valid credentials
        AuthBP->>FlaskLogin: login_user()
        FlaskLogin-->>Browser: Set session cookie
        Browser-->>User: Redirect to dashboard
    else Invalid credentials
        AuthBP-->>Browser: Flash error message
        Browser-->>User: Show login page
    end
```

### Facial Recognition Flow

```mermaid
sequenceDiagram
    participant User
    participant Browser
    participant PatientsBP
    participant FaceLib
    participant Database
    participant ImageHash

    User->>Browser: Activate camera
    Browser->>User: Show video stream
    User->>Browser: Capture photo
    Browser->>PatientsBP: POST /scan (base64 image)
    PatientsBP->>PatientsBP: Decode base64
    
    alt face_recognition available
        PatientsBP->>FaceLib: Extract face encoding
        FaceLib-->>PatientsBP: 128-dim vector
        PatientsBP->>Database: Query all patients
        Database-->>PatientsBP: Patient encodings
        PatientsBP->>PatientsBP: Compare encodings
        PatientsBP-->>Browser: Match result
    else face_recognition unavailable
        PatientsBP->>ImageHash: Compute average_hash
        ImageHash-->>PatientsBP: Hash value
        PatientsBP->>Database: Query patient hashes
        Database-->>PatientsBP: All hashes
        PatientsBP->>PatientsBP: Compare hashes (threshold=15)
        PatientsBP-->>Browser: Best match
    end
    
    Browser-->>User: Show identified patient
```

### Disease Matching Flow

```mermaid
sequenceDiagram
    participant User
    participant Browser
    participant MainBP
    participant Matcher
    participant AIClient
    participant Gemini

    User->>Browser: Enter symptoms
    Browser->>MainBP: POST /match
    MainBP->>Matcher: match(symptoms, top_k=10)
    
    Matcher->>Matcher: Normalize text (lowercase)
    Matcher->>Matcher: Expand synonyms
    Matcher->>Matcher: Tokenize
    Matcher->>Matcher: Fuzzy correction
    Matcher->>Matcher: TF-IDF vectorization
    Matcher->>Matcher: Compute cosine similarity
    Matcher-->>MainBP: Top 10 matches with scores
    
    par AI Enhancement
        MainBP->>AIClient: generate_content(prompt)
        AIClient->>Gemini: API request
        Gemini-->>AIClient: AI response
        AIClient-->>MainBP: Formatted recommendations
    end
    
    MainBP-->>Browser: Render results + AI advice
    Browser-->>User: Display matches
```

### AI Chat Flow

```mermaid
sequenceDiagram
    participant User
    participant Browser
    participant MainBP
    participant AIClient
    participant Gemini
    participant Matcher

    User->>Browser: Type message
    Browser->>MainBP: POST /chat (AJAX)
    MainBP->>AIClient: Extract symptoms + generate response
    AIClient->>Gemini: Analyze intent
    
    Gemini-->>AIClient: JSON {symptoms: [...], response: "..."}
    AIClient-->>MainBP: Parsed data
    
    alt Symptoms detected
        MainBP->>Matcher: match(symptom_str, top_k=3)
        Matcher-->>MainBP: Disease matches
    end
    
    MainBP-->>Browser: JSON response
    Browser->>Browser: Update chat UI
    Browser-->>User: Show AI response + matches
```

---

## Security Architecture

```mermaid
graph TB
    subgraph "Authentication Layer"
        Login["Login Form"]
        PasswordHash["Werkzeug PBKDF2-SHA256<br/>600,000 iterations"]
        Session["Flask-Login Session<br/>Signed Cookies"]
    end

    subgraph "Authorization Layer"
        RoleCheck["Role-Based Access Control"]
        Decorator["@login_required<br/>@role_required"]
    end

    subgraph "Input Validation"
        FormValidation["Server-Side Validation"]
        Sanitization["Werkzeug secure_filename()"]
        SQLProtection["SQLAlchemy Parameterized Queries"]
        XSSProtection["Jinja2 Auto-Escaping"]
    end

    subgraph "Data Protection"
        DBEncryption["Database Encryption<br/>(Production: TDE)"]
        ImageObfuscation["UUID Filenames"]
        APIKeyEnv["Environment Variables<br/>(Planned)"]
    end

    Login --> PasswordHash
    PasswordHash --> Session
    Session --> RoleCheck
    RoleCheck --> Decorator

    FormValidation --> SQLProtection
    Sanitization --> ImageObfuscation
    XSSProtection --> DBEncryption

    style PasswordHash fill:#ff6b6b
    style RoleCheck fill:#feca57
    style SQLProtection fill:#48dbfb
    style DBEncryption fill:#1dd1a1
```

---

## Deployment Architecture

### Development Environment

```mermaid
graph LR
    Developer["Developer<br/>Workstation"]
    FlaskDev["Flask Dev Server<br/>localhost:5000"]
    SQLiteDev["SQLite DB<br/>(local file)"]
    
    Developer --> FlaskDev
    FlaskDev --> SQLiteDev

    style FlaskDev fill:#95afc0
    style SQLiteDev fill:#dfe6e9
```

### Production Environment (Recommended)

```mermaid
graph TB
    subgraph "Load Balancer"
        Nginx["Nginx<br/>Reverse Proxy<br/>SSL Termination"]
    end

    subgraph "Application Servers"
        Gunicorn1["Gunicorn<br/>Worker 1"]
        Gunicorn2["Gunicorn<br/>Worker 2"]
        Gunicorn3["Gunicorn<br/>Worker 3"]
        Gunicorn4["Gunicorn<br/>Worker 4"]
    end

    subgraph "Data Layer"
        PostgreSQL["PostgreSQL<br/>Primary Database"]
        Redis["Redis<br/>Session Store<br/>(Future)"]
        S3["AWS S3<br/>Image Storage<br/>(Future)"]
    end

    subgraph "External Services"
        Gemini["Google Gemini API"]
        Speech["Google Speech API"]
    end

    Internet["Internet"] --> Nginx
    Nginx --> Gunicorn1
    Nginx --> Gunicorn2
    Nginx --> Gunicorn3
    Nginx --> Gunicorn4

    Gunicorn1 --> PostgreSQL
    Gunicorn2 --> PostgreSQL
    Gunicorn3 --> PostgreSQL
    Gunicorn4 --> PostgreSQL

    Gunicorn1 --> Redis
    Gunicorn1 --> S3
    Gunicorn1 --> Gemini
    Gunicorn1 --> Speech

    style Nginx fill:#00d2d3
    style PostgreSQL fill:#336791
    style Redis fill:#dc382d
```

---

## Technology Stack Details

### Backend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Web Framework** | Flask | 3.0+ | Application foundation |
| **WSGI Server** | Gunicorn (prod) | 20.1+ | Production HTTP server |
| **Database** | SQLite (dev) / PostgreSQL (prod) | 3.35+ / 13+ | Data persistence |
| **ORM** | SQLAlchemy | 2.0+ | Database abstraction |
| **Migrations** | Alembic (via Flask-Migrate) | 1.12+ | Schema versioning |
| **Authentication** | Flask-Login | 0.6+ | Session management |
| **Password Hashing** | Werkzeug Security | Built-in | PBKDF2 hashing |

### AI/ML Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Generative AI** | Google Gemini | gemini-2.5-flash | Conversational AI, image analysis |
| **ML Framework** | scikit-learn | 1.3+ | TF-IDF vectorization |
| **NLP** | NLTK (implicit) | - | Text tokenization |
| **Computer Vision** | face_recognition | 1.3+ | Facial encoding |
| **Image Processing** | Pillow | 10.0+ | Image manipulation |
| **Image Hashing** | imagehash | 4.3+ | Perceptual hashing |

### Frontend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **HTML** | HTML5 | - | Semantic markup |
| **CSS Framework** | Bootstrap | 5.3+ | Responsive design |
| **Icons** | Font Awesome | 6.4+ | UI icons |
| **JavaScript** | Vanilla JS | ES6+ | Client-side interactivity |
| **AJAX Library** | Fetch API | Native | Async requests |

### Additional Libraries

| Library | Purpose |
|---------|---------|
| **ReportLab** | PDF generation |
| **SpeechRecognition** | Audio transcription |
| **pydub** | Audio format conversion |
| **pytest** | Unit testing |
| **python-dotenv** | Environment variable management (recommended) |

---

## Performance Considerations

### Database Optimization

```mermaid
graph TD
    Query["Database Query"]
    Index["Check Indexes"]
    Cache["Query Result Cache<br/>(Future: Redis)"]
    Pagination["Pagination<br/>(Limit/Offset)"]

    Query --> Index
    Index --> Cache
    Cache --> Pagination

    style Index fill:#ffeaa7
    style Cache fill:#74b9ff
```

**Current Indexes:**
- `User.username` - Unique index for fast login queries
- `Patient.user_id` - Foreign key index

**Recommended Additions:**
- `Patient.image_hash` - For image similarity search
- `PatientDisease.patient_id` - Composite index with name

### Caching Strategy (Future Enhancement)

```python
# Recommended caching layers
1. Application Cache (Flask-Caching)
   - Disease matcher TF-IDF model
   - AI responses (with TTL)
   - User session data

2. Database Query Cache (SQLAlchemy)
   - Frequently accessed patient records
   - Admin dashboard statistics

3. CDN/Static Cache
   - CSS/JS assets
   - Patient images (with privacy controls)
```

---

## Error Handling Architecture

```mermaid
graph TB
    Request["HTTP Request"]
    RouteHandler["Blueprint Route Handler"]
    BusinessLogic["Business Logic"]
    ErrorOccurs{"Error<br/>Occurs?"}
    ErrorType{"Error<br/>Type?"}
    
    ValidationError["Validation Error"]
    DatabaseError["Database Error"]
    APIError["External API Error"]
    SystemError["System Error"]
    
    FlashMessage["Flash Message to User"]
    Rollback["Database Rollback"]
    Retry["Retry with Backoff"]
    Log["Log Error"]
    ErrorPage["Error Page (500)"]

    Request --> RouteHandler
    RouteHandler --> BusinessLogic
    BusinessLogic --> ErrorOccurs
    
    ErrorOccurs -->|No| Success["Return Response"]
    ErrorOccurs -->|Yes| ErrorType
    
    ErrorType -->|User Input| ValidationError
    ErrorType -->|DB| DatabaseError
    ErrorType -->|API| APIError
    ErrorType -->|System| SystemError
    
    ValidationError --> FlashMessage
    DatabaseError --> Rollback
    DatabaseError --> Log
    APIError --> Retry
    APIError --> Log
    SystemError --> Log
    SystemError --> ErrorPage
    
    FlashMessage --> RouteHandler
    Rollback --> FlashMessage
    Retry --> BusinessLogic
    
    style ErrorOccurs fill:#ff6b6b
    style Rollback fill:#feca57
    style Log fill:#48dbfb
```

---

## Monitoring & Logging (Planned)

### Logging Levels

```python
# Recommended logging configuration
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()  # Console output
    ]
)

# Log categories:
# DEBUG: Query details, AI prompts, matcher operations
# INFO: User actions, successful operations
# WARNING: Failed logins, validation errors, rate limits
# ERROR: Database errors, API failures
# CRITICAL: System crashes, data corruption
```

### Metrics to Track (Future)

- Request latency (p50, p95, p99)
- Database query time
- AI API response time
- User registration rate
- Disease matching accuracy
- Error rates by endpoint
- Active user sessions

---

## Scaling Strategy

### Horizontal Scaling

```mermaid
graph TB
    LoadBalancer["Load Balancer<br/>(Nginx/HAProxy)"]
    
    subgraph "Application Tier"
        App1["App Server 1"]
        App2["App Server 2"]
        App3["App Server N"]
    end
    
    subgraph "Data Tier"
        DBMaster["PostgreSQL<br/>Master"]
        DBReplica1["PostgreSQL<br/>Replica 1"]
        DBReplica2["PostgreSQL<br/>Replica 2"]
    end
    
    subgraph "Cache Tier"
        RedisCluster["Redis Cluster"]
    end
    
    LoadBalancer --> App1
    LoadBalancer --> App2
    LoadBalancer --> App3
    
    App1 --> RedisCluster
    App2 --> RedisCluster
    App3 --> RedisCluster
    
    App1 --> DBMaster
    App1 --> DBReplica1
    
    DBMaster -->|Replication| DBReplica1
    DBMaster -->|Replication| DBReplica2
    
    style LoadBalancer fill:#00cec9
    style DBMaster fill:#6c5ce7
    style RedisCluster fill:#fd79a8
```

---

## File Structure

```
human/
├── app.py                          # Application factory
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables (not in repo)
│
├── instance/
│   └── app.db                     # SQLite database
│
├── migrations/                    # Alembic migrations
│   └── versions/
│
├── src/
│   ├── models.py                  # SQLAlchemy models
│   ├── ai_client.py              # Gemini API wrapper
│   ├── matcher.py                # Disease matching engine
│   ├── analysis.py               # Risk prediction
│   ├── reports.py                # PDF generation
│   │
│   └── blueprints/
│       ├── __init__.py
│       ├── auth.py               # Authentication routes
│       ├── patients.py           # Patient management
│       ├── main.py               # Core features
│       └── admin.py              # Admin panel
│
├── templates/                     # Jinja2 HTML templates
├── static/
│   ├── css/
│   ├── js/
│   └── uploads/                  # Patient images
│
├── data/
│   ├── diseases.csv              # Disease database
│   ├── symptoms_synonyms.csv    # Synonym mappings
│   └── interactions.json         # Drug interactions
│
├── tests/
│   ├── conftest.py
│   └── test_matcher.py
│
└── scripts/
    └── generate_diseases.py      # Dataset generator
```

---

## Configuration Management

### Environment Variables

```bash
# .env file (not committed to version control)
FLASK_APP=app.py
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@localhost/medical_db
GEMINI_API_KEY=AIzaSy...
APP_SECRET=random-32-character-secret
UPLOAD_FOLDER=/var/www/uploads
MAX_CONTENT_LENGTH=5242880  # 5MB
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
```

### Configuration Classes

```python
# config.py (recommended)
class Config:
    SECRET_KEY = os.environ.get('APP_SECRET')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/app.db'
    
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SESSION_COOKIE_SECURE = True
```

---

**Document Version:** 1.0  
**Last Updated:** December 15, 2025  
**Maintained By:** Development Team
