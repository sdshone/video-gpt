# Video AI Assistant

An AI-powered video assistant that helps users understand and interact with YouTube video content through natural language queries.

## Features

- **Video Processing**: Automatically transcribes YouTube videos
- **AI Interaction**: Ask questions about video content and get contextual answers
- **User Management**: Secure authentication system with registration and login
- **History Tracking**: Keep track of processed videos and previous queries
- **Responsive UI**: Clean, modern interface that works on all devices

## Tech Stack

### Frontend
- React with TypeScript
- React Query for state management
- Tailwind CSS for styling
- React Router for navigation

### Backend
- FastAPI (Python)
- SQLAlchemy for database management
- Celery for background tasks
- Google's Gemini AI for natural language processing

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 14+
- PostgreSQL
- Redis (for Celery)

### Backend Setup

1. Clone the repository

```bash
git clone https://github.com/sdshone/video-gpt.git
cd video-gpt
```

2. Create and activate virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

4. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your configurations
```

6. Start the server
```bash
uvicorn main:app --reload
```

### Frontend Setup

1. Navigate to frontend directory
```bash
cd frontend
```

2. Install dependencies
```bash
npm install
```

3. Start development server
```bash
npm run dev
```

## Environment Variables

### Backend
```env
DATABASE_URL=postgresql://user:password@localhost/dbname
GOOGLE_API_KEY=your_gemini_api_key
JWT_SECRET=your_jwt_secret
JWT_ALGORITHM=HS256
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Frontend
```env
VITE_API_URL=http://localhost:8000
```

## API Documentation

Once the backend server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
.
├── backend/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── tasks/
│   └── main.py
└── frontend/
    ├── src/
    │   ├── components/
    │   ├── api/
    │   └── App.tsx
    └── package.json
```
