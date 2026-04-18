"""
Database Schema and User Management
Production-ready authentication database
"""
import sqlite3
import hashlib
import secrets
import os
from datetime import datetime
from pathlib import Path

DB_PATH = Path('auth_database.db')

class AuthDB:
    """Authentication Database Manager"""
    
    def __init__(self, db_file='auth_database.db'):
        self.db_file = db_file
        self.init_db()
        self._create_admin()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cur = conn.cursor()
        import sys
        if sys.platform == 'win32':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        
        # Users table
        cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        )
        ''')
        
        # Audit log table
        cur.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            user_id INTEGER,
            username TEXT,
            details TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        ''')
        
        # Sessions table
        cur.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✓ Database initialized: {self.db_file}")
    
    @staticmethod
    def hash_password(password):
        """Hash password with salt"""
        salt = secrets.token_hex(32)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), 
                                       salt.encode(), 100000)
        return f"{salt}${pwd_hash.hex()}"
    
    @staticmethod
    def verify_password(password, password_hash):
        """Verify password against hash"""
        try:
            salt, pwd_hash = password_hash.split('$')
            new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(),
                                          salt.encode(), 100000)
            return new_hash.hex() == pwd_hash
        except Exception:
            return False
    
    def _create_admin(self):
        """Create default admin user if not exists"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute('SELECT id FROM users WHERE username = ?', ('admin',))
            if cur.fetchone() is None:
                pwd_hash = self.hash_password('admin1432')
                cur.execute('''
                INSERT INTO users (username, email, password_hash, role, status, approved_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', ('admin', 'admin@election.local', pwd_hash, 'admin', 'approved'))
                conn.commit()
                print("✓ Admin user created (username: admin, password: admin1432)")
        except Exception as e:
            print(f"⚠ Admin user already exists or error: {e}")
        finally:
            conn.close()
    
    def create_user(self, username, email, password):
        """Create new user (pending approval)"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            pwd_hash = self.hash_password(password)
            cur.execute('''
            INSERT INTO users (username, email, password_hash, role, status)
            VALUES (?, ?, ?, ?, ?)
            ''', (username, email, pwd_hash, 'user', 'pending'))
            conn.commit()
            user_id = cur.lastrowid
            
            # Log
            self.log_action('user_registration', user_id, username, 
                           f'User registered: {email}')
            
            return {'success': True, 'user_id': user_id, 
                   'message': 'Registration successful! Awaiting admin approval.'}
        except sqlite3.IntegrityError as e:
            if 'username' in str(e):
                return {'success': False, 'error': 'Username already exists'}
            elif 'email' in str(e):
                return {'success': False, 'error': 'Email already registered'}
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def authenticate(self, username, password):
        """Authenticate user"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        cur.execute('''
        SELECT id, username, role, status, is_active FROM users 
        WHERE username = ? AND is_active = 1
        ''', (username,))
        
        user = cur.fetchone()
        conn.close()
        
        if not user:
            return None, "User not found"
        
        if user['status'] != 'approved':
            return None, f"Account status: {user['status']}. Awaiting admin approval."
        
        # Get password hash for verification
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('SELECT password_hash FROM users WHERE id = ?', (user['id'],))
        pwd_row = cur.fetchone()
        conn.close()
        
        if not self.verify_password(password, pwd_row['password_hash']):
            self.log_action('login_failed', user['id'], username, 'Invalid password')
            return None, "Invalid password"
        
        # Log successful login
        self.log_action('login_success', user['id'], username, 'Login successful')
        
        # Update last login
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                   (user['id'],))
        conn.commit()
        conn.close()
        
        return dict(user), None
    
    def get_user(self, user_id):
        """Get user by ID"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, username, email, role, status FROM users WHERE id = ?',
                   (user_id,))
        user = cur.fetchone()
        conn.close()
        return dict(user) if user else None
    
    def get_all_users(self):
        """Get all users"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
        SELECT id, username, email, role, status, created_at, approved_at, last_login
        FROM users ORDER BY created_at DESC
        ''')
        users = [dict(row) for row in cur.fetchall()]
        conn.close()
        return users
    
    def get_pending_users(self):
        """Get pending user registrations"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
        SELECT id, username, email, created_at FROM users 
        WHERE status = 'pending' ORDER BY created_at ASC
        ''')
        users = [dict(row) for row in cur.fetchall()]
        conn.close()
        return users
    
    def approve_user(self, user_id, admin_username):
        """Admin approves user"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        cur.execute('''
        UPDATE users SET status = 'approved', approved_at = CURRENT_TIMESTAMP,
                        approved_by = ?
        WHERE id = ? AND status = 'pending'
        ''', (admin_username, user_id))
        
        conn.commit()
        success = cur.rowcount > 0
        
        if success:
            cur.execute('SELECT username FROM users WHERE id = ?', (user_id,))
            user = cur.fetchone()
            self.log_action('user_approved', user_id, user['username'],
                           f'Approved by {admin_username}')
        
        conn.close()
        return success
    
    def reject_user(self, user_id, admin_username, reason=''):
        """Admin rejects user"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        cur.execute('''
        UPDATE users SET status = 'rejected', is_active = 0
        WHERE id = ? AND status = 'pending'
        ''', (user_id,))
        
        conn.commit()
        success = cur.rowcount > 0
        
        if success:
            cur.execute('SELECT username FROM users WHERE id = ?', (user_id,))
            user = cur.fetchone()
            self.log_action('user_rejected', user_id, user['username'],
                           f'Rejected by {admin_username}. Reason: {reason}')
        
        conn.close()
        return success
    
    def deactivate_user(self, user_id, admin_username):
        """Admin deactivates user"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('UPDATE users SET is_active = 0 WHERE id = ?', (user_id,))
        conn.commit()
        
        cur.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        user = cur.fetchone()
        self.log_action('user_deactivated', user_id, user['username'],
                       f'Deactivated by {admin_username}')
        
        conn.close()
    
    def reactivate_user(self, user_id, admin_username):
        """Admin reactivates user"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('UPDATE users SET is_active = 1 WHERE id = ?', (user_id,))
        conn.commit()
        
        cur.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        user = cur.fetchone()
        self.log_action('user_reactivated', user_id, user['username'],
                       f'Reactivated by {admin_username}')
        
        conn.close()
    
    def log_action(self, action, user_id, username, details, ip='127.0.0.1'):
        """Log action to audit trail"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
        INSERT INTO audit_log (action, user_id, username, details, ip_address)
        VALUES (?, ?, ?, ?, ?)
        ''', (action, user_id, username, details, ip))
        conn.commit()
        conn.close()
    
    def get_audit_log(self, limit=100):
        """Get audit log"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
        SELECT action, username, details, timestamp FROM audit_log
        ORDER BY timestamp DESC LIMIT ?
        ''', (limit,))
        logs = [dict(row) for row in cur.fetchall()]
        conn.close()
        return logs


if __name__ == '__main__':
    db = AuthDB()
    print("\n✓ Database ready for use")
    print("  Admin: admin / admin1432")
