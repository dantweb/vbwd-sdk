# VBWD-SDK Architecture

**Project:** VBWD-SDK - Express Medical Diagnostics Platform
**Status:** Initial Development
**License:** CC0 1.0 Universal (Public Domain)

---

## 1. Project Overview

VBWD-SDK is an iframed web application for express diagnostics in medical fields (e.g., dermatology). Users submit images and data through a multi-step form, which are validated, processed, and sent to a custom diagnostic API. Results are delivered via email.

---

## 2. System Architecture

### 2.1 Container Architecture (Docker)

```
┌─────────────────────────────────────────────────────────────────┐
│                        VBWD-SDK Stack                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  frontend   │    │   python    │    │    mysql    │         │
│  │  (Vue.js)   │◄──►│  (Flask)    │◄──►│    (DB)     │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│        │                  │                   │                 │
│        │                  │                   │                 │
│        ▼                  ▼                   ▼                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    data/ (volumes)                       │   │
│  │  ├── python/logs/                                        │   │
│  │  ├── frontend/logs/                                      │   │
│  │  └── mysql/ (binary data)                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

| Layer      | Technology   | Container  |
|------------|--------------|------------|
| Frontend   | Vue.js 3     | frontend   |
| Backend    | Python 3 / Flask | python |
| Database   | MySQL        | mysql      |

---

## 3. Directory Structure

```
vbwd-sdk/
├── container/                 # Docker configuration per container
│   ├── frontend/
│   ├── python/
│   └── mysql/
├── data/                      # Persistent data & logs
│   ├── python/
│   │   └── logs/
│   ├── frontend/
│   │   └── logs/
│   └── mysql/                 # MySQL binary data
├── python/                    # Python backend root
│   └── api/
│       ├── requirements.txt
│       ├── src/
│       │   ├── routes/        # API route handlers
│       │   ├── models/        # Data models
│       │   └── services/      # Business logic
│       └── tests/
│           ├── unit/          # Unit tests
│           ├── integration/   # Integration tests
│           └── fixtures/      # Test fixtures
├── frontend/                  # Vue.js applications
│   ├── admin/
│   │   └── vue/
│   │       └── package.json
│   └── user/
│       └── vue/
│           └── package.json
├── docs/
│   ├── architecture/          # This documentation
│   └── devlog/                # Development logs (by date)
├── docker-compose.yml
├── CLAUDE.md
├── README.md
└── LICENSE
```

---

## 4. Application Workflow

### 4.1 User Journey (Frontend - User App)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Step Submission Form                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PAGE 1: Data Upload                                            │
│  ├── User uploads images                                        │
│  ├── User adds text comments                                    │
│  └── User clicks "Next"                                         │
│              │                                                  │
│              ▼                                                  │
│  PAGE 2: Consent & Contact                                      │
│  ├── User sees information text                                 │
│  ├── User enters email address                                  │
│  ├── User reviews data processing agreement                     │
│  └── User clicks "Next"                                         │
│              │                                                  │
│              ▼                                                  │
│  PAGE 3: Confirmation                                           │
│  └── User sees: "Your data is submitted,                        │
│       you will receive a reply shortly"                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Backend Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Backend Processing Pipeline                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. RECEIVE DATA                                                │
│     └── Flask API receives submission                           │
│                    │                                            │
│                    ▼                                            │
│  2. VALIDATION                                                  │
│     ├── Check for injection/malware                             │
│     ├── Verify image formats                                    │
│     └── Validate data integrity                                 │
│                    │                                            │
│                    ▼                                            │
│  3. PROCESS & FORWARD                                           │
│     ├── Create data object (images + metadata)                  │
│     └── Send to custom diagnostic API endpoint                  │
│                    │                                            │
│                    ▼                                            │
│  4. POLL FOR RESULTS                                            │
│     └── Ping API endpoint every 60 seconds                      │
│         to check if result is ready                             │
│                    │                                            │
│                    ▼                                            │
│  5. DELIVER RESULTS                                             │
│     ├── Generate email from HTML template                       │
│     └── Send result email to user                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Python Backend Architecture

### 5.1 Concurrency Model (Apache/PHP-like)

The backend follows an **isolated request model** similar to Apache/PHP:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Request Isolation Model                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │ User A  │  │ User B  │  │ Admin X │  │ Admin Y │            │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘            │
│       │            │            │            │                  │
│       ▼            ▼            ▼            ▼                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              WSGI Server (Gunicorn/uWSGI)                │   │
│  │                   Multiple Workers                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│       │            │            │            │                  │
│       ▼            ▼            ▼            ▼                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │Worker 1 │  │Worker 2 │  │Worker 3 │  │Worker N │            │
│  │         │  │         │  │         │  │         │            │
│  │ Own     │  │ Own     │  │ Own     │  │ Own     │            │
│  │ Context │  │ Context │  │ Context │  │ Context │            │
│  │ Own     │  │ Own     │  │ Own     │  │ Own     │            │
│  │ Session │  │ Session │  │ Session │  │ Session │            │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘            │
│       │            │            │            │                  │
│       └────────────┴────────────┴────────────┘                  │
│                          │                                      │
│                          ▼                                      │
│              ┌─────────────────────┐                            │
│              │   MySQL (Shared)    │                            │
│              │   Connection Pool   │                            │
│              └─────────────────────┘                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Key Isolation Principles

| Principle | Implementation |
|-----------|----------------|
| **Request Isolation** | Each request runs in its own context, no shared state between requests |
| **Session Independence** | User sessions stored in DB/Redis, not in worker memory |
| **No Global State** | No mutable global variables; all state passed explicitly or via DI |
| **Stateless Workers** | Workers can be killed/restarted without affecting other users |
| **Connection Pooling** | DB connections managed via pool, not per-request connections |

### 5.3 Multi-User Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Type Separation                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FRONTEND USERS (Public)          BACKEND USERS (Admin)         │
│  ──────────────────────           ─────────────────────         │
│  │                                │                             │
│  │  - Submit diagnostic requests  │  - Review submissions       │
│  │  - View own submission status  │  - Manage configurations    │
│  │  - Receive results via email   │  - Monitor system status    │
│  │                                │  - Access all submissions   │
│  │                                │                             │
│  └────────────┬───────────────────┴────────────┬────────────────┘
│               │                                │                │
│               ▼                                ▼                │
│  ┌────────────────────────┐    ┌────────────────────────┐      │
│  │   /api/user/*          │    │   /api/admin/*         │      │
│  │   Public endpoints     │    │   Protected endpoints  │      │
│  │   Rate limited         │    │   Auth required        │      │
│  └────────────────────────┘    └────────────────────────┘      │
│               │                                │                │
│               └────────────────┬───────────────┘                │
│                                │                                │
│                                ▼                                │
│              ┌─────────────────────────────────┐                │
│              │     Shared Services Layer       │                │
│              │  (Injected per request scope)   │                │
│              └─────────────────────────────────┘                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.4 Async Submission Pattern (Fire-and-Forget)

Our app calls external LoopAI API which may take significant time. Users should not wait.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Fire-and-Forget Pattern                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FRONTEND (Vue.js)                    BACKEND (Flask)           │
│  ─────────────────                    ───────────────           │
│       │                                    │                    │
│  1. User submits form ──────────────────► │                    │
│       │                                    │                    │
│       │                               2. Validate data          │
│       │                               3. Save to DB             │
│       │                               4. Submit to ThreadPool   │
│       │                                    │                    │
│  5. ◄─────────────── 202 ACCEPTED ────────┤  (~50ms)           │
│     "Your data is submitted"               │                    │
│       │                                    │                    │
│       │                          [Background Thread]            │
│       │                               6. Call LoopAI API        │
│       │                                  (may take minutes)     │
│       │                               7. Poll for results       │
│       │                               8. Send email when ready  │
│       │                                    │                    │
│  9. ◄══════════ WebSocket/SSE ════════════╡                    │
│     (optional: if user still on page)      │                    │
│     "Your results are ready!"              │                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Principle:** HTTP response returns immediately (202 ACCEPTED). Long-running work happens in background.

### 5.5 Simple ThreadPool Implementation

```python
from concurrent.futures import ThreadPoolExecutor
from flask import current_app
import uuid

# Global executor (created once at app startup)
executor = ThreadPoolExecutor(max_workers=10)

@app.route('/api/submit', methods=['POST'])
def submit_diagnostic():
    # 1. Validate (sync, fast)
    data = request.get_json()
    errors = validate_submission(data)
    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    # 2. Save to DB (sync, fast)
    submission = Submission(
        email=data['email'],
        status='pending',
        created_at=datetime.utcnow()
    )
    db.session.add(submission)
    db.session.commit()
    submission_id = submission.id

    # 3. Submit to background thread (non-blocking)
    app = current_app._get_current_object()
    executor.submit(process_submission_background, app, submission_id, data)

    # 4. Return immediately
    return jsonify({
        "success": True,
        "message": "Your data is submitted. You will receive results via email.",
        "submission_id": submission_id
    }), 202  # 202 = Accepted

def process_submission_background(app, submission_id, data):
    """Runs in separate thread - does NOT block HTTP requests"""
    with app.app_context():
        try:
            # Call LoopAI API (may take minutes)
            response = call_loopai_api(data)

            # Poll for results
            result = poll_for_results(response['execution_id'])

            # Update DB
            submission = Submission.query.get(submission_id)
            submission.status = 'completed'
            submission.result = result
            db.session.commit()

            # Send email
            send_result_email(submission.email, result)

            # Optional: notify frontend via WebSocket
            socketio.emit('result_ready', {'submission_id': submission_id},
                         room=f'user_{submission.email}')
        except Exception as e:
            submission = Submission.query.get(submission_id)
            submission.status = 'failed'
            submission.error = str(e)
            db.session.commit()
```

### 5.6 Optional Real-Time Updates (WebSocket)

If user stays on confirmation page, show live updates:

```python
# Backend: SocketIO setup
from flask_socketio import SocketIO, join_room

socketio = SocketIO(app, async_mode='threading')

@socketio.on('subscribe')
def handle_subscribe(data):
    email = data['email']
    join_room(f'user_{email}')

# In background thread, emit updates:
socketio.emit('status_update', {
    'submission_id': submission_id,
    'status': 'processing',
    'message': 'Analyzing your images...'
}, room=f'user_{email}')
```

```javascript
// Frontend: Vue.js
import { io } from 'socket.io-client';

const socket = io();
socket.emit('subscribe', { email: userEmail });

socket.on('status_update', (data) => {
  this.statusMessage = data.message;
});

socket.on('result_ready', (data) => {
  this.showNotification('Your results are ready! Check your email.');
});
```

### 5.7 High-Load Design

- **Horizontal Scaling**: Multiple worker processes handle concurrent requests
- **ThreadPoolExecutor**: Background tasks don't block HTTP handlers
- **Connection Pooling**: DB connections managed via pool
- **Graceful Degradation**: Failed background tasks don't affect other users

---

## 6. Frontend Applications

### 6.1 User App (`frontend/user/vue/`)

- Public-facing multi-step form
- Image upload interface
- Consent management
- Submission confirmation

### 6.2 Admin App (`frontend/admin/vue/`)

- Backoffice management
- Submission review
- System monitoring
- Configuration management

---

## 6. Development Principles

### 6.1 Core Practices

- **TDD First**: Tests are written before implementation
- **SOLID Principles**: Single responsibility, Open-closed, Liskov substitution, Interface segregation, Dependency inversion
- **LSP**: Liskov Substitution Principle strictly enforced
- **DI**: Dependency Injection for loose coupling and testability
- **Clean Code**: Readable, maintainable, self-documenting code

### 6.2 Testing Strategy

- All tests run in Docker containers
- Tests must pass before any merge
- Integration tests verify container communication
- Unit tests cover business logic

### 6.3 Docker-First Development

```bash
# All test execution happens in containers
docker-compose run --rm python pytest
docker-compose run --rm frontend npm test
```

---

## 7. Security Considerations

- Input validation on all user submissions
- Image format verification before processing
- Malware/injection detection
- Secure API communication
- Data processing consent management

---

## 8. Integration Points

### 8.1 External API

- Custom diagnostic API endpoint for image analysis
- Polling mechanism for result retrieval (60-second intervals)
- Async result processing

### 8.2 Email Service

- HTML template-based emails
- Result delivery to users
- Configurable SMTP settings

---

## 9. Related Documentation

- `docs/devlog/` - Daily development logs
- `CLAUDE.md` - Claude Code guidance
- `README.md` - Project overview
