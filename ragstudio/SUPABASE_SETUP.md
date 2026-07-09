# RAG Studio - Supabase Integration Guide

## Overview

RAG Studio now features a complete Supabase backend for cloud synchronization, multi-device support, and realtime updates. This guide explains the architecture and how to use it.

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Desktop Agent  │────▶│   Supabase   │◀────│  Web/Mobile UI  │
│  (Local Processing)│  │  (Cloud Sync) │     │  (Control Panel)│
└─────────────────┘     └──────────────┘     └─────────────────┘
       │                       │                       │
       ├─ PDF Processing       ├─ Auth                 ├─ Real-time Updates
       ├─ OCR                  ├─ Metadata             ├─ Job Control
       ├─ Embeddings           ├─ Job Queue            ├─ Device Management
       └─ Vector Index         └─ Realtime             └─ Notifications
```

## Key Components

### 1. Database Schema (`supabase/migrations/001_initial_schema.sql`)

Complete normalized schema with:
- **Authentication**: User profiles with Supabase Auth
- **Devices**: Multi-device registration with heartbeat
- **Books & Chapters**: Document metadata (files stored locally)
- **Jobs**: Resumable pipeline jobs with stage tracking
- **Pipeline Stages**: Individual stage checkpoints
- **Logs**: Structured logging with realtime streaming
- **API Keys**: Encrypted storage with rotation support
- **Settings**: User-configurable performance parameters
- **Benchmarks**: Performance comparison history

### 2. Desktop Agent Client (`desktop_agent/supabase_client.py`)

Python client for desktop agent synchronization:
```python
from desktop_agent.supabase_client import create_desktop_agent_client

client = create_desktop_agent_client(
    supabase_url="your-supabase-url",
    supabase_key="your-supabase-key",
    device_name="My Workstation"
)

# Authenticate
await client.authenticate("user@example.com", "password")

# Register device
device_id = await client.register_device()

# Create job
job_id = await client.create_job(book_id="...")

# Update progress
await client.update_job_status(job_id, "running", progress=45)
await client.update_pipeline_stage(job_id, "ocr", 2, "completed", 100)

# Stream logs
await client.log("OCR completed", "info", job_id=job_id)
```

### 3. Frontend Store (`src/frontend/lib/store.ts`)

Zustand store with Supabase integration:
- Authentication state
- Device management
- Job tracking with realtime updates
- Automatic reconnection

### 4. Realtime Subscriptions

Automatic updates without polling:
```typescript
// Subscribe to job updates
subscribeToJobUpdates(jobId, (data) => {
  console.log('Job updated:', data);
});

// Subscribe to notifications
subscribeToNotifications(userId, (notification) => {
  toast.show(notification.message);
});
```

## Setup Instructions

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Note your project URL and anon key

### 2. Run Database Migrations

```bash
# In Supabase Dashboard > SQL Editor
# Copy and paste contents of:
# supabase/migrations/001_initial_schema.sql
```

Or use Supabase CLI:
```bash
npm install -g supabase
supabase link --project-ref your-project-ref
supabase db push
```

### 3. Configure Environment Variables

Create `.env.local` in the frontend directory:
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

Create `.env` for the backend:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
```

### 4. Install Dependencies

Frontend:
```bash
cd ragstudio
npm install
```

Desktop Agent:
```bash
pip install supabase psutil
```

### 5. Start Development

Frontend:
```bash
npm run dev
```

Backend API:
```bash
python -m uvicorn api.main:app --reload
```

Desktop Agent:
```bash
python desktop_agent/main.py
```

## Features

### Authentication
- Email/password login
- Google OAuth (configure in Supabase)
- GitHub OAuth (configure in Supabase)
- Secure session management

### Device Registration
Each desktop agent automatically:
- Generates unique device UUID
- Registers with system info (OS, CPU, RAM, GPU)
- Sends heartbeat every 30 seconds
- Reports status (online/busy/offline)

### Job Management
- Create jobs from any device
- Track progress in realtime
- Pause/resume/cancel remotely
- View detailed stage progress
- Automatic retry on failure

### Realtime Updates
- Job status changes
- New log entries
- Device status updates
- Notifications
- No polling required

### Security
- Row Level Security (RLS) on all tables
- Users can only access their own data
- API keys encrypted at rest
- Secure authentication tokens

## Responsive Design

The frontend is fully responsive:
- **Desktop**: Full sidebar navigation, multi-column layouts
- **Tablet**: Collapsible sidebar, optimized grids
- **Mobile**: Hamburger menu, single column, touch-friendly

### Breakpoints
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

## API Endpoints

The backend exposes REST APIs that work with Supabase:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login` | POST | User authentication |
| `/api/v1/devices` | GET/POST | List/register devices |
| `/api/v1/jobs` | GET/POST | List/create jobs |
| `/api/v1/jobs/:id` | GET | Job details |
| `/api/v1/jobs/:id/pause` | POST | Pause job |
| `/api/v1/jobs/:id/resume` | POST | Resume job |
| `/api/v1/jobs/:id/cancel` | POST | Cancel job |
| `/api/v1/logs` | GET | Stream logs |
| `/api/v1/settings` | GET/PUT | User settings |

## Best Practices

### 1. Local-First Architecture
- Files stay on the desktop agent
- Only metadata syncs to cloud
- Optional cloud sync for backups

### 2. Checkpointing
- Save state after each stage
- Resume from last successful checkpoint
- Never redo completed work

### 3. Error Handling
- Automatic retries with backoff
- Fallback providers for critical operations
- Detailed error logging

### 4. Performance
- Tune worker count based on CPU cores
- Set RAM limits to prevent OOM
- Use GPU acceleration when available
- Cache embeddings by text hash

## Troubleshooting

### Device Not Showing
1. Check device registration logs
2. Verify Supabase credentials
3. Ensure outbound HTTPS connectivity

### Realtime Not Updating
1. Check browser console for errors
2. Verify Supabase realtime is enabled
3. Ensure publication includes target tables

### Authentication Fails
1. Verify user exists in Supabase Auth
2. Check email confirmation status
3. Review RLS policies

## Next Steps

1. **Configure OAuth Providers**: Add Google/GitHub login in Supabase dashboard
2. **Set Up Storage**: Enable Supabase Storage for optional file backups
3. **Configure Email**: Set up transactional emails for notifications
4. **Enable pg_cron**: Schedule automatic log cleanup
5. **Deploy**: Use Docker for production deployment

## Support

For issues or questions:
- Check the documentation in `/docs`
- Review Supabase logs in the dashboard
- Inspect browser console for frontend errors
- Check `logs/` directory for backend errors
