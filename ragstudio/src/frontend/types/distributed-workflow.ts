/**
 * RAG Studio V2.5 - Distributed Workflow Types
 * TypeScript definitions for collaborative processing system
 */

// ============================================
// Enums
// ============================================

export enum WorkerStatus {
  ONLINE = 'online',
  OFFLINE = 'offline',
  BUSY = 'busy',
  MAINTENANCE = 'maintenance',
  UNHEALTHY = 'unhealthy'
}

export enum StageStatus {
  PENDING = 'pending',
  QUEUED = 'queued',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  REJECTED = 'rejected',
  CANCELLED = 'cancelled'
}

export enum TaskGranularity {
  PIPELINE = 'pipeline',
  CHAPTER = 'chapter',
  PAGE_RANGE = 'page_range',
  CHUNK_BATCH = 'chunk_batch'
}

export enum TaskPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export enum WorkspaceRole {
  OWNER = 'owner',
  ADMIN = 'admin',
  PROJECT_MANAGER = 'project_manager',
  RESEARCHER = 'researcher',
  CONTRIBUTOR = 'contributor',
  REVIEWER = 'reviewer',
  VIEWER = 'viewer'
}

export enum ArtifactType {
  PDF = 'pdf',
  CHAPTER_PDF = 'chapter_pdf',
  OCR_TEXT = 'ocr_text',
  CLEANED_TEXT = 'cleaned_text',
  CHUNKS = 'chunks',
  EMBEDDINGS = 'embeddings',
  VECTOR_INDEX = 'vector_index',
  REPORT = 'report'
}

export enum EventType {
  PIPELINE_CREATED = 'PIPELINE_CREATED',
  STAGE_COMPLETED = 'STAGE_COMPLETED',
  TASK_ASSIGNED = 'TASK_ASSIGNED',
  TASK_ACCEPTED = 'TASK_ACCEPTED',
  TASK_REJECTED = 'TASK_REJECTED',
  TASK_FAILED = 'TASK_FAILED',
  WORKER_ONLINE = 'WORKER_ONLINE',
  WORKER_OFFLINE = 'WORKER_OFFLINE',
  ARTIFACT_UPLOADED = 'ARTIFACT_UPLOADED',
  BENCHMARK_COMPLETED = 'BENCHMARK_COMPLETED',
  REVIEW_REQUESTED = 'REVIEW_REQUESTED',
  REVIEW_APPROVED = 'REVIEW_APPROVED'
}

export enum NotificationType {
  TASK_ASSIGNED = 'task_assigned',
  TASK_COMPLETED = 'task_completed',
  REVIEW_REQUIRED = 'review_required',
  WORKER_OFFLINE = 'worker_offline',
  PIPELINE_FINISHED = 'pipeline_finished',
  ERROR = 'error'
}

// ============================================
// Core Interfaces
// ============================================

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
  settings: Record<string, any>;
  crdt_state?: Record<string, any>;
}

export interface WorkspaceMember {
  workspace_id: string;
  user_id: string;
  role: WorkspaceRole;
  joined_at: string;
}

export interface HardwareSpecs {
  cpu_cores: number;
  ram_gb: number;
  gpu_model?: string;
  gpu_vram_gb?: number;
  storage_gb: number;
}

export interface Worker {
  id: string;
  workspace_id: string;
  owner_id: string;
  name: string;
  device_uuid: string;
  os_info?: {
    platform: string;
    version: string;
    arch?: string;
  };
  hardware_specs: HardwareSpecs;
  capabilities: string[];
  installed_models: string[];
  status: WorkerStatus;
  current_task_id?: string;
  last_heartbeat?: string;
  metadata: {
    temperature?: number;
    battery?: number;
    network_speed?: number;
    cpu_usage?: number;
    ram_usage?: number;
  };
  created_at: string;
  updated_at: string;
}

export interface WorkerHeartbeat {
  id: number;
  worker_id: string;
  timestamp: string;
  status: WorkerStatus;
  load_metrics: {
    cpu_usage: number;
    ram_usage: number;
    gpu_usage?: number;
    temperature?: number;
  };
  current_task_id?: string;
}

export interface PipelineTemplate {
  id: string;
  workspace_id: string;
  name: string;
  description?: string;
  definition: {
    stages: Array<{
      type: string;
      config?: Record<string, any>;
      fallback?: string;
    }>;
  };
  created_by: string;
  created_at: string;
}

export interface Pipeline {
  id: string;
  workspace_id: string;
  project_id: string;
  template_id?: string;
  status: 'draft' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  current_stage_index: number;
  created_by: string;
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
}

export interface PipelineStage {
  id: string;
  pipeline_id: string;
  stage_index: number;
  stage_type: string;
  status: StageStatus;
  config: Record<string, any>;
  assigned_worker_id?: string;
  claimed_by_worker_id?: string;
  lease_expires_at?: string;
  retry_count: number;
  max_retries: number;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  checkpoint_data?: Record<string, any>;
  artifact_version: number;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  workspace_id: string;
  stage_id: string;
  granularity: TaskGranularity;
  book_id?: string;
  chapter_ids?: string[];
  page_start?: number;
  page_end?: number;
  chunk_ids?: string[];
  priority: TaskPriority;
  status: StageStatus;
  assigned_to_user_id?: string;
  claimed_by_worker_id?: string;
  lease_token?: string;
  lease_expires_at?: string;
  requires_review: boolean;
  reviewed_by?: string;
  review_status?: 'approved' | 'rejected' | 'changes_requested';
  review_comments?: string;
  progress: number;
  retry_count: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  pipeline_stages?: PipelineStage;
}

export interface Artifact {
  id: string;
  workspace_id: string;
  stage_id: string;
  task_id?: string;
  name: string;
  type: ArtifactType;
  version: number;
  storage_provider: 'local' | 's3' | 'nas';
  storage_path: string;
  storage_url?: string;
  file_size_bytes: number;
  checksum_sha256: string;
  metadata: Record<string, any>;
  created_by: string;
  created_at: string;
}

export interface ArtifactDependency {
  parent_artifact_id: string;
  child_artifact_id: string;
  relationship: 'derived_from' | 'merged_into' | 'split_from';
  created_at: string;
}

export interface AuditLog {
  id: number;
  workspace_id: string;
  user_id?: string;
  worker_id?: string;
  event_type: EventType;
  entity_type: string;
  entity_id: string;
  details: Record<string, any>;
  created_at: string;
}

export interface EventBusEvent {
  id: string;
  workspace_id: string;
  event_type: EventType;
  payload: Record<string, any>;
  created_at: string;
}

export interface Notification {
  id: string;
  user_id: string;
  workspace_id?: string;
  type: NotificationType;
  title: string;
  message?: string;
  related_entity_type?: string;
  related_entity_id?: string;
  is_read: boolean;
  created_at: string;
}

// ============================================
// Task Leasing
// ============================================

export interface TaskLease {
  task_id: string;
  worker_id: string;
  lease_token: string;
  expires_at: Date;
  claimed_at: Date;
}

// ============================================
// Capability Scheduling
// ============================================

export interface WorkerCapabilities {
  cpu_cores: number;
  ram_gb: number;
  gpu_model?: string;
  gpu_vram_gb?: number;
  storage_gb: number;
  supported_stages: string[];
  installed_models: string[];
  ocr_engines: string[];
  embedding_models: string[];
  vector_stores: string[];
}

export interface WorkerHealthMetrics {
  cpu_usage: number;
  ram_usage: number;
  gpu_usage?: number;
  temperature?: number;
  battery_level?: number;
  network_speed_mbps: number;
  available_disk_gb: number;
}

export interface ScoredWorker extends Worker {
  score: number;
}

// ============================================
// API Request/Response Types
// ============================================

export interface ClaimTaskRequest {
  task_id: string;
  worker_id: string;
}

export interface ClaimTaskResponse {
  success: boolean;
  lease?: TaskLease;
  error?: string;
}

export interface CompleteTaskRequest {
  task_id: string;
  success: boolean;
  artifacts?: Array<{
    name: string;
    type: ArtifactType;
    storage_path: string;
    checksum: string;
    file_size: number;
    metadata?: Record<string, any>;
  }>;
  error_message?: string;
}

export interface RenewLeaseRequest {
  task_id: string;
  lease_token: string;
}

export interface AssignTaskRequest {
  task_id: string;
  assigned_to_user_id?: string;
  assigned_to_worker_id?: string;
}

export interface ReviewTaskRequest {
  task_id: string;
  approved: boolean;
  comments?: string;
}

export interface CreateWorkspaceRequest {
  name: string;
  slug: string;
}

export interface InviteMemberRequest {
  workspace_id: string;
  user_email: string;
  role: WorkspaceRole;
}

export interface RegisterWorkerRequest {
  device_uuid: string;
  name: string;
  os_info: {
    platform: string;
    version: string;
  };
  hardware_specs: HardwareSpecs;
  capabilities: string[];
  installed_models: string[];
}

export interface HeartbeatRequest {
  worker_id: string;
  metrics: WorkerHealthMetrics;
}

// ============================================
// Realtime Subscription Types
// ============================================

export interface RealtimeChannel {
  subscribe(callback: (payload: any) => void): Promise<RealtimeChannel>;
  unsubscribe(): Promise<void>;
}

export interface TaskUpdatePayload {
  new: Task;
  old: Task;
  eventType: 'INSERT' | 'UPDATE' | 'DELETE';
}

export interface WorkerUpdatePayload {
  new: Worker;
  old: Worker;
  eventType: 'INSERT' | 'UPDATE' | 'DELETE';
}

export interface EventPayload {
  new: EventBusEvent;
  eventType: 'INSERT';
}

// ============================================
// Query Parameters
// ============================================

export interface GetTasksParams {
  workspace_id: string;
  status?: StageStatus;
  assigned_to_user_id?: string;
  claimed_by_worker_id?: string;
  granularity?: TaskGranularity;
  priority?: TaskPriority;
  limit?: number;
  offset?: number;
}

export interface GetWorkersParams {
  workspace_id: string;
  status?: WorkerStatus;
  capabilities?: string[];
  min_ram_gb?: number;
  requires_gpu?: boolean;
}

export interface GetArtifactsParams {
  workspace_id: string;
  stage_id?: string;
  task_id?: string;
  type?: ArtifactType;
  limit?: number;
}

export interface GetAuditLogsParams {
  workspace_id: string;
  event_type?: EventType;
  entity_type?: string;
  entity_id?: string;
  user_id?: string;
  from_date?: string;
  to_date?: string;
  limit?: number;
}
