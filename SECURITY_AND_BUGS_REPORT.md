# Security and Bug Report for RAG Studio

## CRITICAL SECURITY ISSUES

### 1. CORS Configuration - Overly Permissive (api/main.py)
**Location:** `/workspace/ragstudio/api/main.py`, lines 29-35
**Severity:** HIGH
**Issue:** CORS is configured to allow all origins (`allow_origins=["*"]`), which exposes the API to Cross-Origin Request Forgery attacks.
**Impact:** Malicious websites can make authenticated requests on behalf of users.
**Recommendation:** Restrict `allow_origins` to specific trusted domains in production.

```python
# Current (INSECURE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # DANGEROUS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Hardcoded API Keys in Source Code (api/settings_routes.py)
**Location:** `/workspace/ragstudio/api/settings_routes.py`, lines 52-74
**Severity:** CRITICAL
**Issue:** Default configurations include placeholder API keys that could be accidentally committed or used.
**Impact:** Exposure of API credentials, potential unauthorized access to paid services.
**Files affected:**
- LLM providers (openai, gemini, anthropic) - lines 52-74
- Embedding providers (openai, cohere, huggingface) - lines 89-109
- Vector index providers (qdrant) - line 132

### 3. SQL Injection Vulnerability (core/database/database.py)
**Location:** `/workspace/ragstudio/core/database/database.py`, lines 425-431
**Severity:** HIGH
**Issue:** Dynamic SQL query construction using string formatting for UPDATE statements.
**Impact:** Potential SQL injection through the `updates` list if any field values contain malicious SQL.
**Code:**
```python
query = f'''
    UPDATE pipeline_sessions 
    SET {', '.join(updates)}
    WHERE id = ?
'''
cursor.execute(query, params)
```
**Recommendation:** Use parameterized queries for all dynamic SQL.

### 4. Insecure Pickle Deserialization (core/job_manager.py)
**Location:** `/workspace/ragstudio/core/job_manager.py`, lines 15, 168-170
**Severity:** CRITICAL
**Issue:** Using `pickle` for cache serialization which allows arbitrary code execution on deserialization.
**Impact:** If cache files are tampered with, attackers can execute arbitrary code.
**Code:**
```python
import pickle
# ...
data = await f.read()
return pickle.loads(data)  # DANGEROUS
```
**Recommendation:** Use JSON or another safe serialization format.

### 5. No Authentication on API Endpoints (api/main.py)
**Location:** `/workspace/ragstudio/api/main.py` - All endpoints
**Severity:** HIGH
**Issue:** No authentication or authorization checks on any API endpoints.
**Impact:** Anyone can upload documents, start pipelines, delete data, access settings.
**Recommendation:** Implement JWT or session-based authentication.

### 6. Path Traversal Vulnerability (api/main.py)
**Location:** `/workspace/ragstudio/api/main.py`, lines 268-273
**Severity:** MEDIUM-HIGH
**Issue:** File upload doesn't sanitize filename, allowing path traversal attacks.
**Impact:** Attacker could write files outside intended directory.
**Code:**
```python
file_path = UPLOAD_DIR / file.filename  # No sanitization!
```
**Recommendation:** Use `secure_filename()` from werkzeug or similar.

### 7. No Input Validation on File Uploads (api/main.py)
**Location:** `/workspace/ragstudio/api/main.py`, lines 258-290
**Severity:** MEDIUM
**Issue:** Only checks file extension, not actual file content (magic bytes).
**Impact:** Attackers can upload malicious files with .pdf extension.
**Recommendation:** Validate file magic bytes and implement file type detection.

### 8. Secrets Logged in Plain Text (core/logging_system.py)
**Location:** `/workspace/ragstudio/core/logging_system.py`
**Severity:** MEDIUM
**Issue:** Logger doesn't filter sensitive data before writing to logs.
**Impact:** API keys, passwords could be written to log files.
**Recommendation:** Implement secret masking in the logger.

### 9. No Rate Limiting (api/main.py)
**Location:** `/workspace/ragstudio/api/main.py`
**Severity:** MEDIUM
**Issue:** No rate limiting on any endpoints.
**Impact:** Vulnerable to brute force and DoS attacks.
**Recommendation:** Implement rate limiting using slowapi or similar.

### 10. In-Memory Session Storage (api/rag_playground.py)
**Location:** `/workspace/ragstudio/api/rag_playground.py`, line 83
**Severity:** MEDIUM
**Issue:** Conversations stored in global dictionary `_conversations`.
**Impact:** Data loss on restart, no isolation between users, memory exhaustion.
**Code:**
```python
_conversations: Dict[str, ConversationContext] = {}  # IN-MEMORY!
```

## BUGS AND CODE QUALITY ISSUES

### 11. Missing Error Handling in Database Operations (core/database/database.py)
**Location:** Multiple locations in database.py
**Severity:** MEDIUM
**Issue:** Database operations don't handle connection failures or constraint violations.
**Impact:** Unhandled exceptions crash the application.

### 12. Race Condition in Job Manager (core/job_manager.py)
**Location:** `/workspace/ragstudio/core/job_manager.py`, lines 313-314
**Severity:** MEDIUM
**Issue:** `self.jobs` dictionary accessed without locks in async context.
**Impact:** Race conditions when multiple jobs created/modified concurrently.

### 13. Missing Database Foreign Key Enforcement (core/database/database.py)
**Location:** `/workspace/ragstudio/core/database/database.py`, lines 32-97
**Severity:** LOW-MEDIUM
**Issue:** SQLite foreign keys not enabled (requires `PRAGMA foreign_keys = ON`).
**Impact:** Orphaned records possible despite FK constraints in schema.

### 14. Hardcoded Directory Paths (core/config/settings.py)
**Location:** `/workspace/ragstudio/core/config/settings.py`, lines 8-33
**Severity:** LOW
**Issue:** Directories created automatically without checking permissions.
**Impact:** Application may fail in restricted environments.

### 15. No Timeout on HTTP Requests (core/providers/llm/ollama.py)
**Location:** `/workspace/ragstudio/core/providers/llm/ollama.py`, lines 42-49
**Severity:** LOW-MEDIUM
**Issue:** While timeout is configurable, there's no connection timeout set.
**Impact:** Requests can hang indefinitely on network issues.

### 16. Missing Null Checks (core/api_key_manager.py)
**Location:** `/workspace/ragstudio/core/api_key_manager.py`, lines 145-149
**Severity:** LOW
**Issue:** Methods assume provider exists in `_keys` dict without proper validation.
**Impact:** Potential KeyError exceptions.

### 17. Unsafe File Operations in Desktop Agent (desktop_agent/supabase_client.py)
**Location:** `/workspace/ragstudio/desktop_agent/supabase_client.py`, lines 75-86
**Severity:** MEDIUM
**Issue:** Device UUID stored in world-readable location without permission checks.
**Code:**
```python
uuid_file = Path.home() / ".ragstudio" / "device_uuid.json"
```

### 18. Missing Supabase Connection Error Handling (desktop_agent/supabase_client.py)
**Location:** `/workspace/ragstudio/desktop_agent/supabase_client.py`, line 52
**Severity:** MEDIUM
**Issue:** `create_client` called without try-catch for network failures.
**Impact:** Application crashes if Supabase unavailable.

### 19. Memory Leak in TurboVec (core/providers/vector_index/turbovec.py)
**Location:** `/workspace/ragstudio/core/providers/vector_index/turbovec.py`, lines 17-21
**Severity:** LOW-MEDIUM
**Issue:** Vectors stored in memory indefinitely with no eviction policy.
**Impact:** Memory exhaustion with large datasets.

### 20. Missing Async Error Handling (pipeline/orchestrator.py)
**Location:** `/workspace/ragstudio/pipeline/orchestrator.py`, line 129
**Severity:** MEDIUM
**Issue:** `asyncio.create_task()` without error handling.
**Code:**
```python
asyncio.create_task(self.job_manager.execute_job(job_id, self.stages))
```
**Impact:** Task failures go unnoticed.

### 21. Settings Not Persisted (api/main.py)
**Location:** `/workspace/ragstudio/api/main.py`, lines 165-204
**Severity:** LOW
**Issue:** Settings updates only modify in-memory variables, comment acknowledges this.
**Code comment:** "In production, you'd want to persist these to a config file or database"
**Impact:** Settings lost on restart.

### 22. Weak File Hash Algorithm (not implemented)
**Location:** Throughout codebase
**Severity:** LOW
**Issue:** File integrity checks use SHA256 but not consistently applied.
**Impact:** Cannot detect file tampering reliably.

### 23. No CSRF Protection (api/main.py)
**Location:** `/workspace/ragstudio/api/main.py`
**Severity:** MEDIUM
**Issue:** No CSRF tokens implemented for state-changing operations.
**Impact:** Cross-site request forgery attacks possible.

### 24. Information Disclosure via Error Messages (api/main.py)
**Location:** Multiple exception handlers in api/main.py
**Severity:** LOW-MEDIUM
**Issue:** Stack traces and internal details exposed in error responses.
**Example:** Lines 289-290, 336-337
**Impact:** Attackers gain insight into internal structure.

### 25. Missing Content-Type Validation (api/main.py)
**Location:** `/workspace/ragstudio/api/main.py`, upload endpoint
**Severity:** LOW
**Issue:** Doesn't verify Content-Type header matches actual file.
**Impact:** Easier to bypass file type restrictions.

## RECOMMENDATIONS SUMMARY

### Immediate Actions Required:
1. Fix CORS configuration
2. Remove hardcoded API keys
3. Fix SQL injection vulnerability
4. Replace pickle with safe serialization
5. Add authentication to all endpoints
6. Sanitize file uploads

### Short-term Improvements:
1. Add rate limiting
2. Implement proper logging with secret masking
3. Add input validation throughout
4. Enable SQLite foreign key enforcement
5. Add error handling to all async operations

### Long-term Architecture:
1. Move from in-memory to persistent storage
2. Implement proper secrets management (e.g., HashiCorp Vault)
3. Add comprehensive audit logging
4. Implement role-based access control
5. Add monitoring and alerting

---
Report generated by security analysis
Date: Current session
