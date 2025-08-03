from app import db
from datetime import datetime
import uuid

class TranslationSession(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Current text content for each language
    french_text = db.Column(db.Text, default='')
    english_text = db.Column(db.Text, default='')
    polish_text = db.Column(db.Text, default='')
    
    # Track which language is currently active
    active_language = db.Column(db.String(10), default='english')
    
    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'french_text': self.french_text or '',
            'english_text': self.english_text or '',
            'polish_text': self.polish_text or '',
            'active_language': self.active_language
        }