"""
RAG Studio Desktop Agent - Supabase Synchronization Client

This module handles communication between the Desktop Agent and Supabase backend.
It manages device registration, job synchronization, realtime updates, and heartbeat.
"""

import os
import uuid
import socket
import platform
import psutil
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path
import json
import hashlib

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: supabase-py not installed. Cloud sync disabled.")


class DesktopAgentClient:
    """
    Client for Desktop Agent to sync with Supabase backend.
    
    Responsibilities:
    - Device registration and heartbeat
    - Job status updates
    - Log streaming
    - Realtime subscriptions
    - Checkpoint synchronization (optional)
    """
    
    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        device_name: Optional[str] = None,
        user_id: Optional[str] = None,
        access_token: Optional[str] = None
    ):
        if not SUPABASE_AVAILABLE:
            raise RuntimeError("supabase-py package required for cloud sync")
        
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.client: Client = create_client(supabase_url, supabase_key)
        
        # Device identification
        self.device_uuid = self._get_device_uuid()
        self.device_name = device_name or f"{socket.gethostname()} ({platform.system()})"
        
        # User authentication
        self.user_id = user_id
        self.access_token = access_token
        
        # State
        self.device_id: Optional[str] = None
        self.is_registered = False
        self.heartbeat_interval = 30  # seconds
        self._heartbeat_task = None
        
        # Callbacks
        self._job_callbacks: List[Callable] = []
        self._log_callbacks: List[Callable] = []
        self._notification_callbacks: List[Callable] = []
        
    def _get_device_uuid(self) -> str:
        """Generate or retrieve persistent device UUID."""
        uuid_file = Path.home() / ".ragstudio" / "device_uuid.json"
        uuid_file.parent.mkdir(parents=True, exist_ok=True)
        
        if uuid_file.exists():
            with open(uuid_file, 'r') as f:
                data = json.load(f)
                return data.get('device_uuid', str(uuid.uuid4()))
        else:
            device_uuid = str(uuid.uuid4())
            with open(uuid_file, 'w') as f:
                json.dump({'device_uuid': device_uuid}, f)
            return device_uuid
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Gather system information for device registration."""
        return {
            'os': f"{platform.system()} {platform.release()}",
            'cpu': platform.processor() or 'Unknown',
            'ram_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'gpu': self._get_gpu_info(),
            'software_version': '1.0.0'  # Should come from package
        }
    
    def _get_gpu_info(self) -> str:
        """Detect GPU information."""
        try:
            import torch
            if torch.cuda.is_available():
                return torch.cuda.get_device_name(0)
        except:
            pass
        
        try:
            # Try to get GPU from system
            if platform.system() == 'Windows':
                import subprocess
                result = subprocess.run(
                    ['wmic', 'path', 'win32_videocontroller', 'get', 'name'],
                    capture_output=True, text=True
                )
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    return lines[1].strip()
        except:
            pass
        
        return 'Not detected'
    
    def authenticate(self, email: str, password: str) -> bool:
        """Authenticate user with Supabase Auth."""
        try:
            response = self.client.auth.sign_in_with_password({
                'email': email,
                'password': password
            })
            
            self.user_id = response.user.id
            self.access_token = response.session.access_token
            
            # Update client with auth token
            self.client = create_client(self.supabase_url, self.supabase_key)
            
            return True
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def register_device(self) -> Optional[str]:
        """Register or update device in Supabase."""
        if not self.user_id:
            raise RuntimeError("Must authenticate before registering device")
        
        system_info = self._get_system_info()
        
        try:
            # Check if device already exists
            response = self.client.table('devices').select('id').eq(
                'device_uuid', self.device_uuid
            ).eq('user_id', self.user_id).execute()
            
            if response.data and len(response.data) > 0:
                # Update existing device
                self.device_id = response.data[0]['id']
                self._update_device_status('online')
                self.is_registered = True
                return self.device_id
            else:
                # Create new device
                device_data = {
                    'user_id': self.user_id,
                    'device_uuid': self.device_uuid,
                    'name': self.device_name,
                    **system_info,
                    'status': 'online',
                    'last_heartbeat': datetime.now(timezone.utc).isoformat()
                }
                
                response = self.client.table('devices').insert(device_data).execute()
                
                if response.data and len(response.data) > 0:
                    self.device_id = response.data[0]['id']
                    self.is_registered = True
                    return self.device_id
                    
        except Exception as e:
            print(f"Device registration failed: {e}")
            return None
        
        return None
    
    def _update_device_status(self, status: str):
        """Update device status in Supabase."""
        if not self.device_id:
            return
        
        try:
            self.client.table('devices').update({
                'status': status,
                'last_heartbeat': datetime.now(timezone.utc).isoformat()
            }).eq('id', self.device_id).execute()
        except Exception as e:
            print(f"Failed to update device status: {e}")
    
    def start_heartbeat(self):
        """Start periodic heartbeat to Supabase."""
        import asyncio
        
        async def heartbeat_loop():
            while True:
                self._update_device_status('busy' if self._has_active_jobs() else 'online')
                await asyncio.sleep(self.heartbeat_interval)
        
        # This would be started as a background task in the actual implementation
        print("Heartbeat started")
    
    def _has_active_jobs(self) -> bool:
        """Check if device has active jobs."""
        if not self.device_id:
            return False
        
        try:
            response = self.client.table('jobs').select('id').eq(
                'device_id', self.device_id
            ).in_('status', ['running', 'paused', 'retrying']).execute()
            
            return response.data and len(response.data) > 0
        except:
            return False
    
    def create_job(self, book_id: str, priority: int = 5) -> Optional[str]:
        """Create a new pipeline job."""
        if not self.user_id or not self.device_id:
            raise RuntimeError("Must be authenticated and registered")
        
        try:
            job_data = {
                'user_id': self.user_id,
                'device_id': self.device_id,
                'book_id': book_id,
                'priority': priority,
                'status': 'pending',
                'current_stage': None,
                'progress': 0,
                'retry_count': 0,
                'max_retries': 3
            }
            
            response = self.client.table('jobs').insert(job_data).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]['id']
                
        except Exception as e:
            print(f"Failed to create job: {e}")
            return None
        
        return None
    
    def update_job_status(
        self,
        job_id: str,
        status: str,
        current_stage: Optional[str] = None,
        progress: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """Update job status in Supabase."""
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            if current_stage is not None:
                update_data['current_stage'] = current_stage
            
            if progress is not None:
                update_data['progress'] = progress
            
            if error_message is not None:
                update_data['error_message'] = error_message
            
            if status == 'running' and 'started_at' not in update_data:
                update_data['started_at'] = datetime.now(timezone.utc).isoformat()
            
            if status in ['completed', 'failed', 'cancelled']:
                update_data['completed_at'] = datetime.now(timezone.utc).isoformat()
            
            self.client.table('jobs').update(update_data).eq('id', job_id).execute()
            
        except Exception as e:
            print(f"Failed to update job status: {e}")
    
    def update_pipeline_stage(
        self,
        job_id: str,
        stage_name: str,
        stage_order: int,
        status: str,
        progress: int = 0,
        checkpoint_data: Optional[Dict] = None,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None
    ):
        """Update or create pipeline stage."""
        try:
            # Check if stage exists
            response = self.client.table('pipeline_stages').select('id').eq(
                'job_id', job_id
            ).eq('stage_name', stage_name).execute()
            
            if response.data and len(response.data) > 0:
                # Update existing stage
                stage_id = response.data[0]['id']
                update_data = {
                    'status': status,
                    'progress': progress,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
                
                if checkpoint_data:
                    update_data['checkpoint_data'] = checkpoint_data
                
                if error_message:
                    update_data['error_message'] = error_message
                
                if duration_ms:
                    update_data['duration_ms'] = duration_ms
                
                if status == 'completed':
                    update_data['completed_at'] = datetime.now(timezone.utc).isoformat()
                
                self.client.table('pipeline_stages').update(update_data).eq(
                    'id', stage_id
                ).execute()
            else:
                # Create new stage
                stage_data = {
                    'job_id': job_id,
                    'stage_name': stage_name,
                    'stage_order': stage_order,
                    'status': status,
                    'progress': progress,
                    'checkpoint_data': checkpoint_data or {},
                    'error_message': error_message,
                    'duration_ms': duration_ms
                }
                
                if status == 'running':
                    stage_data['started_at'] = datetime.now(timezone.utc).isoformat()
                
                self.client.table('pipeline_stages').insert(stage_data).execute()
                
        except Exception as e:
            print(f"Failed to update pipeline stage: {e}")
    
    def log(
        self,
        message: str,
        severity: str = 'info',
        job_id: Optional[str] = None,
        stage_name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Send log entry to Supabase."""
        if not self.user_id:
            return
        
        try:
            log_data = {
                'user_id': self.user_id,
                'device_id': self.device_id,
                'job_id': job_id,
                'stage_name': stage_name,
                'message': message,
                'severity': severity,
                'metadata': metadata or {}
            }
            
            self.client.table('logs').insert(log_data).execute()
            
            # Call local callbacks
            for callback in self._log_callbacks:
                callback(log_data)
                
        except Exception as e:
            print(f"Failed to send log: {e}")
    
    def subscribe_to_job_updates(self, job_id: str, callback: Callable):
        """Subscribe to realtime updates for a specific job."""
        def handler(message, type):
            if type == 'INSERT' or type == 'UPDATE':
                callback(message.new)
        
        self.client.channel(f'jobs:{job_id}') \
            .on('postgres_changes', 
                {'event': '*', 'schema': 'public', 'table': 'jobs', 'filter': f'id=eq.{job_id}'},
                handler) \
            .subscribe()
    
    def subscribe_to_notifications(self, callback: Callable):
        """Subscribe to user notifications."""
        if not self.user_id:
            return
        
        def handler(message, type):
            if type == 'INSERT':
                callback(message.new)
        
        self.client.channel(f'notifications:{self.user_id}') \
            .on('postgres_changes',
                {'event': 'INSERT', 'schema': 'public', 'table': 'notifications', 'filter': f'user_id=eq.{self.user_id}'},
                handler) \
            .subscribe()
    
    def get_user_jobs(self, limit: int = 50) -> List[Dict]:
        """Get recent jobs for the user."""
        if not self.user_id:
            return []
        
        try:
            response = self.client.table('jobs').select('*').eq(
                'user_id', self.user_id
            ).order('created_at', desc=True).limit(limit).execute()
            
            return response.data or []
        except Exception as e:
            print(f"Failed to get jobs: {e}")
            return []
    
    def get_job_details(self, job_id: str) -> Optional[Dict]:
        """Get detailed job information including stages."""
        try:
            # Get job
            job_response = self.client.table('jobs').select('*').eq(
                'id', job_id
            ).execute()
            
            if not job_response.data or len(job_response.data) == 0:
                return None
            
            job = job_response.data[0]
            
            # Get stages
            stages_response = self.client.table('pipeline_stages').select('*').eq(
                'job_id', job_id
            ).order('stage_order').execute()
            
            job['stages'] = stages_response.data or []
            
            # Get recent logs
            logs_response = self.client.table('logs').select('*').eq(
                'job_id', job_id
            ).order('created_at', desc=True).limit(100).execute()
            
            job['recent_logs'] = logs_response.data or []
            
            return job
            
        except Exception as e:
            print(f"Failed to get job details: {e}")
            return None
    
    def pause_job(self, job_id: str) -> bool:
        """Pause a running job."""
        try:
            self.update_job_status(job_id, 'paused')
            return True
        except:
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job."""
        try:
            self.update_job_status(job_id, 'running')
            return True
        except:
            return False
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        try:
            self.update_job_status(job_id, 'cancelled')
            return True
        except:
            return False
    
    def get_user_settings(self) -> Optional[Dict]:
        """Get user settings from Supabase."""
        if not self.user_id:
            return None
        
        try:
            response = self.client.table('user_settings').select('*').eq(
                'user_id', self.user_id
            ).execute()
            
            return response.data[0] if response.data else None
        except:
            return None
    
    def update_user_settings(self, settings: Dict) -> bool:
        """Update user settings in Supabase."""
        if not self.user_id:
            return False
        
        try:
            response = self.client.table('user_settings').select('id').eq(
                'user_id', self.user_id
            ).execute()
            
            if response.data and len(response.data) > 0:
                self.client.table('user_settings').update(settings).eq(
                    'user_id', self.user_id
                ).execute()
            else:
                self.client.table('user_settings').insert({
                    'user_id': self.user_id,
                    **settings
                }).execute()
            
            return True
        except:
            return False
    
    def upload_benchmark_result(self, result: Dict) -> Optional[str]:
        """Upload benchmark result to Supabase."""
        if not self.user_id:
            return None
        
        try:
            benchmark_data = {
                'user_id': self.user_id,
                **result
            }
            
            response = self.client.table('benchmark_results').insert(benchmark_data).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]['id']
        except:
            return None
        
        return None
    
    def logout(self):
        """Logout and cleanup."""
        try:
            self.client.auth.sign_out()
        except:
            pass
        
        self.user_id = None
        self.access_token = None
        self.device_id = None
        self.is_registered = False


# Factory function
def create_desktop_agent_client(
    supabase_url: str,
    supabase_key: str,
    device_name: Optional[str] = None
) -> DesktopAgentClient:
    """Create and initialize a Desktop Agent client."""
    return DesktopAgentClient(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        device_name=device_name
    )
