"""
RAG Studio V2.5 - Distributed Workflow Orchestrator

Core module for capability-based scheduling, task leasing, and distributed pipeline execution.
Implements artifact-centric workflow where stages can move freely between workers.
"""

import asyncio
import hashlib
import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field, asdict
from supabase import Client, PostgrestError
import logging

logger = logging.getLogger(__name__)


class WorkerStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    UNHEALTHY = "unhealthy"


class StageStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class TaskGranularity(str, Enum):
    PIPELINE = "pipeline"
    CHAPTER = "chapter"
    PAGE_RANGE = "page_range"
    CHUNK_BATCH = "chunk_batch"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class WorkerCapabilities:
    """Represents what a worker can do"""
    cpu_cores: int = 0
    ram_gb: float = 0.0
    gpu_model: Optional[str] = None
    gpu_vram_gb: float = 0.0
    storage_gb: float = 0.0
    supported_stages: List[str] = field(default_factory=list)
    installed_models: List[str] = field(default_factory=list)
    ocr_engines: List[str] = field(default_factory=list)
    embedding_models: List[str] = field(default_factory=list)
    vector_stores: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WorkerCapabilities':
        return cls(**data)


@dataclass
class WorkerHealth:
    """Real-time health metrics"""
    cpu_usage: float = 0.0
    ram_usage: float = 0.0
    gpu_usage: float = 0.0
    temperature: float = 0.0
    battery_level: Optional[float] = None
    network_speed_mbps: float = 0.0
    available_disk_gb: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Artifact:
    """Immutable versioned artifact"""
    id: str
    name: str
    type: str
    version: int
    storage_path: str
    checksum_sha256: str
    file_size_bytes: int = 0
    metadata: Dict = field(default_factory=dict)
    
    @staticmethod
    def compute_checksum(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()


@dataclass
class TaskLease:
    """Transactional lease for task execution"""
    task_id: str
    worker_id: str
    lease_token: str
    expires_at: datetime
    claimed_at: datetime = field(default_factory=datetime.utcnow)


class CapabilityScheduler:
    """
    Capability-based scheduler that matches tasks to optimal workers.
    Never assumes worker type - only considers advertised capabilities.
    """
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self._worker_cache: Dict[str, Dict] = {}
        self._cache_ttl = timedelta(seconds=30)
        self._last_cache_update: Optional[datetime] = None
    
    async def get_available_workers(
        self,
        workspace_id: str,
        required_capabilities: Optional[List[str]] = None,
        min_ram_gb: float = 0.0,
        requires_gpu: bool = False
    ) -> List[Dict]:
        """
        Find workers matching requirements using capability filtering.
        """
        query = self.supabase.table("workers").select("*").eq("workspace_id", workspace_id)
        
        # Filter by status
        query = query.in_("status", [WorkerStatus.ONLINE.value, WorkerStatus.BUSY.value])
        
        workers_response = await asyncio.to_thread(query.execute)
        workers = workers_response.data or []
        
        # Client-side filtering for complex capabilities
        filtered_workers = []
        for worker in workers:
            caps = worker.get("capabilities", [])
            specs = worker.get("hardware_specs", {})
            
            # Check required capabilities
            if required_capabilities:
                if not all(cap in caps for cap in required_capabilities):
                    continue
            
            # Check RAM
            if min_ram_gb > 0 and specs.get("ram_gb", 0) < min_ram_gb:
                continue
            
            # Check GPU
            if requires_gpu and not specs.get("gpu_model"):
                continue
            
            filtered_workers.append(worker)
        
        # Score and sort workers
        scored_workers = self._score_workers(filtered_workers, required_capabilities)
        return sorted(scored_workers, key=lambda w: w["score"], reverse=True)
    
    def _score_workers(self, workers: List[Dict], required_caps: Optional[List[str]]) -> List[Dict]:
        """Score workers based on capabilities and current load"""
        scored = []
        for worker in workers:
            score = 0.0
            specs = worker.get("hardware_specs", {})
            metadata = worker.get("metadata", {})
            
            # Base score from hardware
            score += specs.get("cpu_cores", 0) * 10
            score += specs.get("ram_gb", 0) * 5
            if specs.get("gpu_vram_gb", 0) > 0:
                score += specs.get("gpu_vram_gb", 0) * 20
            
            # Penalty for high load
            cpu_load = metadata.get("cpu_usage", 0)
            if cpu_load > 80:
                score -= 50
            elif cpu_load > 50:
                score -= 20
            
            # Bonus for low temperature
            temp = metadata.get("temperature", 0)
            if temp > 0 and temp < 70:
                score += 10
            
            worker["score"] = score
            scored.append(worker)
        
        return scored
    
    async def select_best_worker(
        self,
        workspace_id: str,
        stage_type: str,
        task_config: Dict
    ) -> Optional[Dict]:
        """
        Automatically select the best worker for a stage based on capabilities.
        """
        # Map stage types to required capabilities
        capability_map = {
            "ocr": ["ocr"],
            "llm_correction": ["llm"],
            "embedding": ["embedding"],
            "indexing": ["vector_store"],
            "chunking": [],
            "cleaning": []
        }
        
        required_caps = capability_map.get(stage_type, [])
        
        # Check if GPU is needed (for embeddings/indexing typically)
        requires_gpu = stage_type in ["embedding", "indexing"]
        
        workers = await self.get_available_workers(
            workspace_id=workspace_id,
            required_capabilities=required_caps,
            requires_gpu=requires_gpu
        )
        
        return workers[0] if workers else None


class TaskLeaseManager:
    """
    Manages transactional task leasing to prevent duplicate execution.
    Uses lease tokens and expiration for automatic failover.
    """
    
    LEASE_DURATION = timedelta(minutes=5)
    HEARTBEAT_INTERVAL = timedelta(minutes=1)
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self._active_leases: Dict[str, TaskLease] = {}
    
    async def claim_task(
        self,
        task_id: str,
        worker_id: str,
        workspace_id: str
    ) -> Optional[TaskLease]:
        """
        Attempt to claim a task with transactional leasing.
        Returns lease if successful, None if task already claimed.
        """
        lease_token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + self.LEASE_DURATION
        
        try:
            # Atomic update with condition
            response = await asyncio.to_thread(
                self.supabase.table("tasks")
                .update({
                    "claimed_by_worker_id": worker_id,
                    "lease_token": lease_token,
                    "lease_expires_at": expires_at.isoformat(),
                    "status": StageStatus.RUNNING.value
                })
                .eq("id", task_id)
                .eq("workspace_id", workspace_id)
                .is_("claimed_by_worker_id", None)  # Only if not already claimed
                .execute()
            )
            
            if response.data and len(response.data) > 0:
                lease = TaskLease(
                    task_id=task_id,
                    worker_id=worker_id,
                    lease_token=lease_token,
                    expires_at=expires_at
                )
                self._active_leases[task_id] = lease
                logger.info(f"Task {task_id} claimed by worker {worker_id}")
                return lease
            
            logger.warning(f"Failed to claim task {task_id} - already claimed")
            return None
            
        except PostgrestError as e:
            logger.error(f"Database error claiming task: {e}")
            return None
    
    async def renew_lease(self, task_id: str, worker_id: str, lease_token: str) -> bool:
        """Renew lease before expiration"""
        new_expires = datetime.utcnow() + self.LEASE_DURATION
        
        try:
            response = await asyncio.to_thread(
                self.supabase.table("tasks")
                .update({"lease_expires_at": new_expires.isoformat()})
                .eq("id", task_id)
                .eq("claimed_by_worker_id", worker_id)
                .eq("lease_token", lease_token)
                .execute()
            )
            
            if response.data:
                if task_id in self._active_leases:
                    self._active_leases[task_id].expires_at = new_expires
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error renewing lease: {e}")
            return False
    
    async def release_lease(self, task_id: str, worker_id: str, lease_token: str, success: bool = True):
        """Release lease after task completion"""
        new_status = StageStatus.COMPLETED.value if success else StageStatus.FAILED.value
        
        try:
            await asyncio.to_thread(
                self.supabase.table("tasks")
                .update({
                    "status": new_status,
                    "claimed_by_worker_id": None,
                    "lease_token": None,
                    "lease_expires_at": None,
                    "completed_at": datetime.utcnow().isoformat() if success else None
                })
                .eq("id", task_id)
                .eq("claimed_by_worker_id", worker_id)
                .eq("lease_token", lease_token)
                .execute()
            )
            
            self._active_leases.pop(task_id, None)
            logger.info(f"Task {task_id} lease released")
            
        except Exception as e:
            logger.error(f"Error releasing lease: {e}")
    
    async def reclaim_expired_leases(self, workspace_id: str) -> List[str]:
        """
        Find and reclaim tasks with expired leases.
        Returns list of reclaimed task IDs.
        """
        now = datetime.utcnow().isoformat()
        
        try:
            # Find expired leases
            response = await asyncio.to_thread(
                self.supabase.table("tasks")
                .select("id, claimed_by_worker_id")
                .eq("workspace_id", workspace_id)
                .lt("lease_expires_at", now)
                .in_("status", [StageStatus.RUNNING.value])
                .execute()
            )
            
            expired_tasks = response.data or []
            reclaimed_ids = []
            
            for task in expired_tasks:
                # Reset task to pending
                await asyncio.to_thread(
                    self.supabase.table("tasks")
                    .update({
                        "claimed_by_worker_id": None,
                        "lease_token": None,
                        "lease_expires_at": None,
                        "status": StageStatus.QUEUED.value,
                        "retry_count": (task.get("retry_count", 0) or 0) + 1
                    })
                    .eq("id", task["id"])
                    .execute()
                )
                
                reclaimed_ids.append(task["id"])
                logger.warning(f"Reclaimed expired task {task['id']} from worker {task['claimed_by_worker_id']}")
            
            return reclaimed_ids
            
        except Exception as e:
            logger.error(f"Error reclaiming leases: {e}")
            return []


class ArtifactManager:
    """
    Manages immutable versioned artifacts with integrity checking.
    Artifacts flow between stages without internal state coupling.
    """
    
    def __init__(self, supabase_client: Client, local_storage_path: str = "./artifacts"):
        self.supabase = supabase_client
        self.local_storage_path = local_storage_path
    
    async def register_artifact(
        self,
        workspace_id: str,
        stage_id: str,
        task_id: Optional[str],
        name: str,
        artifact_type: str,
        storage_path: str,
        checksum: str,
        file_size: int,
        metadata: Optional[Dict] = None,
        created_by: Optional[str] = None
    ) -> Artifact:
        """Register a new immutable artifact version"""
        artifact_id = str(uuid.uuid4())
        
        # Get next version number
        version_response = await asyncio.to_thread(
            self.supabase.table("artifacts")
            .select("version", count="exact")
            .eq("stage_id", stage_id)
            .eq("name", name)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )
        
        current_version = 0
        if version_response.data and len(version_response.data) > 0:
            current_version = version_response.data[0].get("version", 0)
        
        new_version = current_version + 1
        
        try:
            response = await asyncio.to_thread(
                self.supabase.table("artifacts")
                .insert({
                    "id": artifact_id,
                    "workspace_id": workspace_id,
                    "stage_id": stage_id,
                    "task_id": task_id,
                    "name": name,
                    "type": artifact_type,
                    "version": new_version,
                    "storage_path": storage_path,
                    "checksum_sha256": checksum,
                    "file_size_bytes": file_size,
                    "metadata": metadata or {},
                    "created_by": created_by
                })
                .execute()
            )
            
            artifact = Artifact(
                id=artifact_id,
                name=name,
                type=artifact_type,
                version=new_version,
                storage_path=storage_path,
                checksum_sha256=checksum,
                file_size_bytes=file_size,
                metadata=metadata or {}
            )
            
            logger.info(f"Registered artifact {name} v{new_version} ({artifact_id})")
            return artifact
            
        except Exception as e:
            logger.error(f"Error registering artifact: {e}")
            raise
    
    async def link_artifacts(self, parent_id: str, child_id: str, relationship: str):
        """Create artifact lineage relationship"""
        try:
            await asyncio.to_thread(
                self.supabase.table("artifact_dependencies")
                .insert({
                    "parent_artifact_id": parent_id,
                    "child_artifact_id": child_id,
                    "relationship": relationship
                })
                .execute()
            )
        except Exception as e:
            logger.error(f"Error linking artifacts: {e}")
    
    async def get_latest_artifact(self, stage_id: str, name: str) -> Optional[Artifact]:
        """Get latest version of an artifact"""
        response = await asyncio.to_thread(
            self.supabase.table("artifacts")
            .select("*")
            .eq("stage_id", stage_id)
            .eq("name", name)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )
        
        if response.data and len(response.data) > 0:
            data = response.data[0]
            return Artifact(
                id=data["id"],
                name=data["name"],
                type=data["type"],
                version=data["version"],
                storage_path=data["storage_path"],
                checksum_sha256=data["checksum_sha256"],
                file_size_bytes=data.get("file_size_bytes", 0),
                metadata=data.get("metadata", {})
            )
        
        return None
    
    async def verify_artifact_integrity(self, artifact_id: str, local_data: bytes) -> bool:
        """Verify artifact checksum matches stored value"""
        response = await asyncio.to_thread(
            self.supabase.table("artifacts")
            .select("checksum_sha256")
            .eq("id", artifact_id)
            .single()
            .execute()
        )
        
        if response.data:
            expected_checksum = response.data["checksum_sha256"]
            actual_checksum = Artifact.compute_checksum(local_data)
            return expected_checksum == actual_checksum
        
        return False


class DistributedWorkflowOrchestrator:
    """
    Main orchestrator for distributed workflow execution.
    Coordinates scheduling, leasing, and artifact management.
    """
    
    def __init__(self, supabase_client: Client, worker_id: str, workspace_id: str):
        self.supabase = supabase_client
        self.worker_id = worker_id
        self.workspace_id = workspace_id
        
        self.scheduler = CapabilityScheduler(supabase_client)
        self.lease_manager = TaskLeaseManager(supabase_client)
        self.artifact_manager = ArtifactManager(supabase_client)
        
        self._running = False
        self._heartbeat_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the orchestrator"""
        self._running = True
        
        # Register worker as online
        await self._register_worker()
        
        # Start heartbeat
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        # Start lease reclamation
        asyncio.create_task(self._lease_reclamation_loop())
        
        logger.info(f"Orchestrator started for worker {self.worker_id}")
    
    async def stop(self):
        """Stop the orchestrator gracefully"""
        self._running = False
        
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Mark worker as offline
        await asyncio.to_thread(
            self.supabase.table("workers")
            .update({"status": WorkerStatus.OFFLINE.value})
            .eq("id", self.worker_id)
            .execute()
        )
        
        logger.info(f"Orchestrator stopped for worker {self.worker_id}")
    
    async def _register_worker(self):
        """Register or update worker in database"""
        import platform
        import psutil
        
        # Gather system info
        hardware_specs = {
            "cpu_cores": psutil.cpu_count(logical=False) or 0,
            "ram_gb": psutil.virtual_memory().total / (1024**3),
            "storage_gb": psutil.disk_usage('/').total / (1024**3) if platform.system() != "Windows" else psutil.disk_usage('C:\\').total / (1024**3),
        }
        
        # Detect GPU (simplified)
        try:
            import torch
            if torch.cuda.is_available():
                hardware_specs["gpu_model"] = torch.cuda.get_device_name(0)
                hardware_specs["gpu_vram_gb"] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        except ImportError:
            pass
        
        await asyncio.to_thread(
            self.supabase.table("workers")
            .upsert({
                "id": self.worker_id,
                "workspace_id": self.workspace_id,
                "device_uuid": self.worker_id,  # Using worker_id as device UUID
                "name": f"Worker-{platform.node()}",
                "os_info": {"platform": platform.system(), "version": platform.version()},
                "hardware_specs": hardware_specs,
                "status": WorkerStatus.ONLINE.value,
                "last_heartbeat": datetime.utcnow().isoformat()
            }, on_conflict="device_uuid")
            .execute()
        )
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        while self._running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(30)  # 30-second heartbeat interval
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(5)
    
    async def _send_heartbeat(self):
        """Send heartbeat with current metrics"""
        import psutil
        
        metrics = {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "ram_usage": psutil.virtual_memory().percent,
            "available_disk_gb": psutil.disk_usage('/').free / (1024**3) if psutil.disk_usage('/').free > 0 else 0
        }
        
        # Log heartbeat
        await asyncio.to_thread(
            self.supabase.table("worker_heartbeats")
            .insert({
                "worker_id": self.worker_id,
                "status": WorkerStatus.ONLINE.value,
                "load_metrics": metrics
            })
            .execute()
        )
        
        # Update worker status
        await asyncio.to_thread(
            self.supabase.table("workers")
            .update({
                "last_heartbeat": datetime.utcnow().isoformat(),
                "metadata": metrics,
                "status": WorkerStatus.BUSY.value if self._has_active_tasks() else WorkerStatus.ONLINE.value
            })
            .eq("id", self.worker_id)
            .execute()
        )
    
    def _has_active_tasks(self) -> bool:
        """Check if worker has active tasks"""
        return len(self.lease_manager._active_leases) > 0
    
    async def _lease_reclamation_loop(self):
        """Periodically reclaim expired leases"""
        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self.lease_manager.reclaim_expired_leases(self.workspace_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Lease reclamation error: {e}")
    
    async def claim_next_task(self, stage_types: Optional[List[str]] = None) -> Optional[Dict]:
        """
        Claim the next available task matching worker capabilities.
        """
        # Build query for available tasks
        query = self.supabase.table("tasks").select("""
            *,
            pipeline_stages(
                stage_type,
                config
            )
        """).eq("workspace_id", self.workspace_id)
        
        query = query.eq("status", StageStatus.QUEUED.value)
        query = query.is_("claimed_by_worker_id", None)
        
        if stage_types:
            query = query.in_("stage_id", [
                t["id"] for t in 
                (await asyncio.to_thread(
                    self.supabase.table("pipeline_stages")
                    .select("id")
                    .in_("stage_type", stage_types)
                    .execute()
                )).data or []
            ])
        
        query = query.order("priority", desc=True).order("created_at", asc=True)
        query = query.limit(10)
        
        response = await asyncio.to_thread(query.execute)
        tasks = response.data or []
        
        # Try to claim first available task
        for task in tasks:
            stage_type = task.get("pipeline_stages", {}).get("stage_type")
            
            # Check if worker supports this stage type
            if not await self._supports_stage_type(stage_type):
                continue
            
            lease = await self.lease_manager.claim_task(
                task_id=task["id"],
                worker_id=self.worker_id,
                workspace_id=self.workspace_id
            )
            
            if lease:
                logger.info(f"Claimed task {task['id']} ({stage_type})")
                return task
        
        return None
    
    async def _supports_stage_type(self, stage_type: str) -> bool:
        """Check if worker supports a stage type"""
        # Get worker capabilities from DB
        response = await asyncio.to_thread(
            self.supabase.table("workers")
            .select("capabilities")
            .eq("id", self.worker_id)
            .single()
            .execute()
        )
        
        if not response.data:
            return False
        
        capabilities = response.data.get("capabilities", [])
        
        stage_capability_map = {
            "ocr": "ocr",
            "llm_correction": "llm",
            "embedding": "embedding",
            "indexing": "vector_store",
            "chunking": "chunking",
            "cleaning": "cleaning",
            "split": "split"
        }
        
        required_cap = stage_capability_map.get(stage_type)
        if not required_cap:
            return True  # Unknown stage type, assume supported
        
        return required_cap in capabilities
    
    async def complete_task(
        self,
        task_id: str,
        success: bool,
        artifacts: Optional[List[Artifact]] = None,
        error_message: Optional[str] = None
    ):
        """Complete a task and register artifacts"""
        lease = self.lease_manager._active_leases.get(task_id)
        
        if not lease:
            logger.error(f"No active lease found for task {task_id}")
            return
        
        # Release lease
        await self.lease_manager.release_lease(
            task_id=task_id,
            worker_id=self.worker_id,
            lease_token=lease.lease_token,
            success=success
        )
        
        if success and artifacts:
            # Get stage_id from task
            task_response = await asyncio.to_thread(
                self.supabase.table("tasks")
                .select("stage_id")
                .eq("id", task_id)
                .single()
                .execute()
            )
            
            stage_id = task_response.data.get("stage_id") if task_response.data else None
            
            # Register artifacts
            for artifact in artifacts:
                await self.artifact_manager.register_artifact(
                    workspace_id=self.workspace_id,
                    stage_id=stage_id,
                    task_id=task_id,
                    name=artifact.name,
                    artifact_type=artifact.type,
                    storage_path=artifact.storage_path,
                    checksum=artifact.checksum_sha256,
                    file_size=artifact.file_size_bytes,
                    metadata=artifact.metadata
                )
        
        # Emit event
        event_type = "TASK_COMPLETED" if success else "TASK_FAILED"
        await self._emit_event(event_type, {
            "task_id": task_id,
            "worker_id": self.worker_id,
            "success": success,
            "error": error_message
        })
    
    async def _emit_event(self, event_type: str, payload: Dict):
        """Emit event to event bus"""
        await asyncio.to_thread(
            self.supabase.table("event_bus")
            .insert({
                "workspace_id": self.workspace_id,
                "event_type": event_type,
                "payload": payload
            })
            .execute()
        )


# Factory function
def create_orchestrator(
    supabase_url: str,
    supabase_key: str,
    worker_id: str,
    workspace_id: str
) -> DistributedWorkflowOrchestrator:
    """Create a configured orchestrator instance"""
    from supabase import create_client
    
    client = create_client(supabase_url, supabase_key)
    return DistributedWorkflowOrchestrator(client, worker_id, workspace_id)
