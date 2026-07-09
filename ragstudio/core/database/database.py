"""
SQLite Database for RAG Studio
Handles documents, chunks, pipeline sessions, and vector indexes
"""
import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

class Database:
    """SQLite database handler for RAG Studio"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection"""
        from config.settings import DATABASE_PATH
        
        self.db_path = Path(db_path) if db_path else DATABASE_PATH
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """Initialize database schema"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                file_hash TEXT,
                status TEXT DEFAULT 'uploaded',
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Chunks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding BLOB,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        ''')
        
        # Pipeline sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pipeline_sessions (
                id TEXT PRIMARY KEY,
                document_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                current_stage TEXT,
                completed_stages TEXT,
                failed_stage TEXT,
                error_message TEXT,
                stage_order TEXT,
                context_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        ''')
        
        # Vector indexes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vector_indexes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                provider TEXT NOT NULL,
                config TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pipeline_sessions_document_id ON pipeline_sessions(document_id)')
        
        conn.commit()
        conn.close()
    
    # ==================== Document Operations ====================
    
    def insert_document(
        self,
        filename: str,
        file_path: str,
        file_size: int,
        file_hash: Optional[str] = None,
        metadata: Optional[Dict] = None,
        status: str = "uploaded"
    ) -> int:
        """Insert a new document"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO documents (filename, file_path, file_size, file_hash, metadata, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            filename,
            file_path,
            file_size,
            file_hash,
            json.dumps(metadata) if metadata else None,
            status
        ))
        
        doc_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return doc_id
    
    def get_document(self, document_id: int) -> Optional[Dict]:
        """Get document by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM documents WHERE id = ?', (document_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def list_documents(
        self,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict]:
        """List documents with optional filtering"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute(
                'SELECT * FROM documents WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?',
                (status, limit, offset)
            )
        else:
            cursor.execute(
                'SELECT * FROM documents ORDER BY created_at DESC LIMIT ? OFFSET ?',
                (limit, offset)
            )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_document_status(self, document_id: int, status: str) -> bool:
        """Update document status"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE documents 
            SET status = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (status, document_id))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def delete_document(self, document_id: int) -> bool:
        """Delete a document and its associated chunks"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Delete chunks first (due to foreign key)
        cursor.execute('DELETE FROM chunks WHERE document_id = ?', (document_id,))
        
        # Delete document
        cursor.execute('DELETE FROM documents WHERE id = ?', (document_id,))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    # ==================== Chunk Operations ====================
    
    def insert_chunk(
        self,
        document_id: int,
        chunk_index: int,
        content: str,
        embedding: Optional[bytes] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """Insert a new chunk"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chunks (document_id, chunk_index, content, embedding, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            document_id,
            chunk_index,
            content,
            embedding,
            json.dumps(metadata) if metadata else None
        ))
        
        chunk_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return chunk_id
    
    def insert_chunks_batch(
        self,
        document_id: int,
        chunks: List[Dict]
    ) -> List[int]:
        """Insert multiple chunks in a batch"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        chunk_ids = []
        for chunk in chunks:
            cursor.execute('''
                INSERT INTO chunks (document_id, chunk_index, content, embedding, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                document_id,
                chunk.get('chunk_index', 0),
                chunk['content'],
                chunk.get('embedding'),
                json.dumps(chunk.get('metadata')) if chunk.get('metadata') else None
            ))
            chunk_ids.append(cursor.lastrowid)
        
        conn.commit()
        conn.close()
        
        return chunk_ids
    
    def get_chunks_for_document(
        self,
        document_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """Get chunks for a specific document"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM chunks 
            WHERE document_id = ? 
            ORDER BY chunk_index 
            LIMIT ? OFFSET ?
        ''', (document_id, limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def search_chunks(
        self,
        query: str,
        top_k: int = 5,
        document_id: Optional[int] = None
    ) -> List[Dict]:
        """Search chunks (basic text search - vector search handled by providers)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if document_id:
            cursor.execute('''
                SELECT *, 
                    CASE WHEN content LIKE ? THEN 1.0 ELSE 0.0 END as score
                FROM chunks 
                WHERE document_id = ? AND content LIKE ?
                ORDER BY score DESC, chunk_index
                LIMIT ?
            ''', (f'%{query}%', document_id, f'%{query}%', top_k))
        else:
            cursor.execute('''
                SELECT *, 
                    CASE WHEN content LIKE ? THEN 1.0 ELSE 0.0 END as score
                FROM chunks 
                WHERE content LIKE ?
                ORDER BY score DESC, chunk_index
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', top_k))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_chunk_embedding(self, chunk_id: int, embedding: bytes) -> bool:
        """Update chunk embedding"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE chunks SET embedding = ? WHERE id = ?',
            (embedding, chunk_id)
        )
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    # ==================== Pipeline Session Operations ====================
    
    def create_pipeline_session(
        self,
        pipeline_id: str,
        document_id: int,
        stage_order: List[str],
        context_data: Optional[Dict] = None
    ) -> str:
        """Create a new pipeline session"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO pipeline_sessions 
            (id, document_id, stage_order, context_data)
            VALUES (?, ?, ?, ?)
        ''', (
            pipeline_id,
            document_id,
            json.dumps(stage_order),
            json.dumps(context_data) if context_data else None
        ))
        
        conn.commit()
        conn.close()
        
        return pipeline_id
    
    def get_pipeline_session(self, pipeline_id: str) -> Optional[Dict]:
        """Get pipeline session by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM pipeline_sessions WHERE id = ?', (pipeline_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            result = dict(row)
            # Parse JSON fields
            if result.get('completed_stages'):
                result['completed_stages'] = json.loads(result['completed_stages'])
            if result.get('stage_order'):
                result['stage_order'] = json.loads(result['stage_order'])
            if result.get('context_data'):
                result['context_data'] = json.loads(result['context_data'])
            return result
        return None
    
    def update_pipeline_status(
        self,
        pipeline_id: str,
        status: str,
        current_stage: Optional[str] = None,
        completed_stages: Optional[List[str]] = None,
        failed_stage: Optional[str] = None,
        error_message: Optional[str] = None,
        context_data: Optional[Dict] = None
    ) -> bool:
        """Update pipeline session status"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        updates = ['status = ?', 'updated_at = CURRENT_TIMESTAMP']
        params = [status]
        
        if current_stage is not None:
            updates.append('current_stage = ?')
            params.append(current_stage)
        
        if completed_stages is not None:
            updates.append('completed_stages = ?')
            params.append(json.dumps(completed_stages))
        
        if failed_stage is not None:
            updates.append('failed_stage = ?')
            params.append(failed_stage)
        
        if error_message is not None:
            updates.append('error_message = ?')
            params.append(error_message)
        
        if context_data is not None:
            updates.append('context_data = ?')
            params.append(json.dumps(context_data))
        
        params.append(pipeline_id)
        
        # Build parameterized UPDATE query safely
        if not updates:
            return True  # Nothing to update
        
        set_clause = ', '.join(updates)
        query = f'''
            UPDATE pipeline_sessions 
            SET {set_clause}
            WHERE id = ?
        '''
        
        try:
            cursor.execute(query, params)
            affected = cursor.rowcount
            conn.commit()
            return affected > 0
        except sqlite3.Error as e:
            conn.rollback()
            raise Exception(f"Database update failed: {str(e)}")
        finally:
            conn.close()
    
    def list_pipeline_sessions(
        self,
        document_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """List pipeline sessions with optional filtering"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        conditions = []
        params = []
        
        if document_id:
            conditions.append('document_id = ?')
            params.append(document_id)
        
        if status:
            conditions.append('status = ?')
            params.append(status)
        
        where_clause = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
        
        cursor.execute(f'''
            SELECT * FROM pipeline_sessions 
            {where_clause}
            ORDER BY created_at DESC 
            LIMIT ?
        ''', [*params, limit])
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            result = dict(row)
            if result.get('completed_stages'):
                result['completed_stages'] = json.loads(result['completed_stages'])
            if result.get('stage_order'):
                result['stage_order'] = json.loads(result['stage_order'])
            if result.get('context_data'):
                result['context_data'] = json.loads(result['context_data'])
            results.append(result)
        
        return results
    
    # ==================== Vector Index Operations ====================
    
    def insert_vector_index(
        self,
        name: str,
        provider: str,
        config: Optional[Dict] = None,
        status: str = "active"
    ) -> int:
        """Insert a new vector index"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO vector_indexes (name, provider, config, status)
            VALUES (?, ?, ?, ?)
        ''', (
            name,
            provider,
            json.dumps(config) if config else None,
            status
        ))
        
        index_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return index_id
    
    def get_vector_index(self, index_id: int) -> Optional[Dict]:
        """Get vector index by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM vector_indexes WHERE id = ?', (index_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            result = dict(row)
            if result.get('config'):
                result['config'] = json.loads(result['config'])
            return result
        return None
    
    def get_vector_index_by_name(self, name: str) -> Optional[Dict]:
        """Get vector index by name"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM vector_indexes WHERE name = ?', (name,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            result = dict(row)
            if result.get('config'):
                result['config'] = json.loads(result['config'])
            return result
        return None
    
    def list_vector_indexes(self, status: Optional[str] = None) -> List[Dict]:
        """List all vector indexes"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute(
                'SELECT * FROM vector_indexes WHERE status = ? ORDER BY created_at DESC',
                (status,)
            )
        else:
            cursor.execute('SELECT * FROM vector_indexes ORDER BY created_at DESC')
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            result = dict(row)
            if result.get('config'):
                result['config'] = json.loads(result['config'])
            results.append(result)
        
        return results
    
    def update_vector_index_status(self, index_id: int, status: str) -> bool:
        """Update vector index status"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE vector_indexes SET status = ? WHERE id = ?',
            (status, index_id)
        )
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def delete_vector_index(self, index_id: int) -> bool:
        """Delete a vector index"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM vector_indexes WHERE id = ?', (index_id,))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
