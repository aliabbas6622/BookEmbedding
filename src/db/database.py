"""
Database layer for RAG Studio using SQLite
Handles metadata storage for documents, chunks, and pipeline status
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import json


class Database:
    """SQLite database manager for RAG Studio metadata"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self._initialize()
    
    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def _initialize(self):
        """Create database tables if they don't exist"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'uploaded',
                metadata JSON,
                session_id TEXT NOT NULL
            )
        """)
        
        # Chunks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                metadata JSON,
                embedding_id TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)
        
        # Pipeline sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'pending',
                current_stage TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                config JSON
            )
        """)
        
        # Indexes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vector_indexes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                index_name TEXT UNIQUE NOT NULL,
                provider TEXT NOT NULL,
                dimension INTEGER,
                document_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata JSON
            )
        """)
        
        conn.commit()
        self.close()
    
    def create_session(self, session_id: str, config: Dict[str, Any]) -> int:
        """Create a new pipeline session"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pipeline_sessions (session_id, config) VALUES (?, ?)",
            (session_id, json.dumps(config))
        )
        session_id_db = cursor.lastrowid
        conn.commit()
        self.close()
        return session_id_db
    
    def update_session_status(self, session_id: str, status: str, current_stage: Optional[str] = None):
        """Update pipeline session status"""
        conn = self.connect()
        cursor = conn.cursor()
        if current_stage:
            cursor.execute(
                "UPDATE pipeline_sessions SET status = ?, current_stage = ?, updated_at = ? WHERE session_id = ?",
                (status, current_stage, datetime.now(), session_id)
            )
        else:
            cursor.execute(
                "UPDATE pipeline_sessions SET status = ?, updated_at = ? WHERE session_id = ?",
                (status, datetime.now(), session_id)
            )
        conn.commit()
        self.close()
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get pipeline session by ID"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pipeline_sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        self.close()
        if row:
            return dict(row)
        return None
    
    def add_document(self, filename: str, file_path: str, file_size: int, 
                     session_id: str, metadata: Optional[Dict] = None) -> int:
        """Add a document to the database"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO documents (filename, file_path, file_size, session_id, metadata) 
               VALUES (?, ?, ?, ?, ?)""",
            (filename, file_path, file_size, session_id, json.dumps(metadata or {}))
        )
        doc_id = cursor.lastrowid
        conn.commit()
        self.close()
        return doc_id
    
    def update_document_status(self, doc_id: int, status: str):
        """Update document status"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE documents SET status = ? WHERE id = ?",
            (status, doc_id)
        )
        conn.commit()
        self.close()
    
    def get_document(self, doc_id: int) -> Optional[Dict]:
        """Get document by ID"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        self.close()
        if row:
            return dict(row)
        return None
    
    def get_documents_by_session(self, session_id: str) -> List[Dict]:
        """Get all documents for a session"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE session_id = ?", (session_id,))
        rows = cursor.fetchall()
        self.close()
        return [dict(row) for row in rows]
    
    def add_chunk(self, document_id: int, chunk_index: int, content: str, 
                  metadata: Optional[Dict] = None, embedding_id: Optional[str] = None) -> int:
        """Add a chunk to the database"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO chunks (document_id, chunk_index, content, metadata, embedding_id) 
               VALUES (?, ?, ?, ?, ?)""",
            (document_id, chunk_index, content, json.dumps(metadata or {}), embedding_id)
        )
        chunk_id = cursor.lastrowid
        conn.commit()
        self.close()
        return chunk_id
    
    def get_chunks_by_document(self, document_id: int) -> List[Dict]:
        """Get all chunks for a document"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index",
            (document_id,)
        )
        rows = cursor.fetchall()
        self.close()
        return [dict(row) for row in rows]
    
    def create_vector_index(self, index_name: str, provider: str, 
                           dimension: int, metadata: Optional[Dict] = None) -> int:
        """Create a vector index record"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO vector_indexes (index_name, provider, dimension, metadata) 
               VALUES (?, ?, ?, ?)""",
            (index_name, provider, dimension, json.dumps(metadata or {}))
        )
        index_id = cursor.lastrowid
        conn.commit()
        self.close()
        return index_id
    
    def update_index_document_count(self, index_name: str, count: int):
        """Update document count for a vector index"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE vector_indexes SET document_count = ? WHERE index_name = ?",
            (count, index_name)
        )
        conn.commit()
        self.close()
    
    def get_vector_index(self, index_name: str) -> Optional[Dict]:
        """Get vector index by name"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vector_indexes WHERE index_name = ?", (index_name,))
        row = cursor.fetchone()
        self.close()
        if row:
            return dict(row)
        return None
