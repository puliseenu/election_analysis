"""
Authentication Database Module
Handles user management, password hashing, and approval workflow
"""
import sqlite3
import hashlib
import secrets
from pathlib import Path
from datetime import datetime


class AuthDB:
    """SQLite-based authentication database"""
    
    def __init__(self, db_path='auth.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP,
            approved_by TEXT,
            last_login TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY,
            action TEXT,
            user_id INTEGER,
            username TEXT,
            details TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        conn.commit()
        
        # Create default admin if doesn't exist
        c.execute("SELECT * FROM users WHERE username='admin'")
        if c.fetchone() is None:
            pwd_hash = self._hash_password('admin1432')
            c.execute('''INSERT INTO users 
                        (username, email, password_hash, role, status)
                        VALUES (?, ?, ?, ?, ?)''',
                     ('admin', 'admin@system.local', pwd_hash, 'admin', 'approved'))
            conn.commit()
            print("[LOAD] Admin user created (username: admin, password: admin1432)")
        
        conn.close()
        print("[LOAD] Database initialized: " + self.db_path)
    
    @staticmethod
    def _hash_password(password):
        """Hash password with PBKDF2"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(),
                                       salt.encode(), 100000)
        return f"{salt}${pwd_hash.hex()}"
    
    @staticmethod
    def _verify_password(password, pwd_hash):
        """Verify password against hash"""
        try:
            salt, hash_hex = pwd_hash.split('$')
            new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(),
                                          salt.encode(), 100000)
            return new_hash.hex() == hash_hex
        except:
            return False
    
    def authenticate(self, username, password):
        """Authenticate user"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        
        if user and self._verify_password(password, user['password_hash']):
            if user['status'] == 'approved':
                c.execute("UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=?",
                         (user['id'],))
                conn.commit()
                return dict(user), None
            else:
                return None, f"Account {user['status']}, awaiting admin approval"
        
        conn.close()
        return None, "Invalid credentials"
    
    def create_user(self, username, email, password):
        """Register new user"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            pwd_hash = self._hash_password(password)
            c.execute('''INSERT INTO users (username, email, password_hash)
                        VALUES (?, ?, ?)''',
                     (username, email, pwd_hash))
            conn.commit()
            return {'success': True, 'msg': 'Account created, awaiting approval'}
        except sqlite3.IntegrityError as e:
            return {'success': False, 'error': 'Username or email already exists'}
        finally:
            conn.close()
    
    def get_user(self, user_id):
        """Get user by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id=?", (user_id,))
        user = c.fetchone()
        conn.close()
        return dict(user) if user else None
    
    def get_pending_users(self):
        """Get users awaiting approval"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE status='pending'")
        users = [dict(u) for u in c.fetchall()]
        conn.close()
        return users
    
    def approve_user(self, user_id, admin_username):
        """Approve user registration"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''UPDATE users SET status='approved', approved_at=CURRENT_TIMESTAMP,
                     approved_by=? WHERE id=?''',
                 (admin_username, user_id))
        conn.commit()
        conn.close()
        return True
    
    def reject_user(self, user_id, admin_username):
        """Reject user registration"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''UPDATE users SET status='rejected', approved_at=CURRENT_TIMESTAMP,
                     approved_by=? WHERE id=?''',
                 (admin_username, user_id))
        conn.commit()
        conn.close()
        return True

    def get_all_users(self):
        """Get all users except admin"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT id, username, email, role, status, created_at, approved_at, approved_by FROM users WHERE username != 'admin' ORDER BY created_at DESC")
        users = [dict(u) for u in c.fetchall()]
        conn.close()
        return users

    def delete_user(self, user_id):
        """Delete a user"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE id=? AND username != 'admin'", (user_id,))
        conn.commit()
        conn.close()
        return True
