from app import db
from datetime import datetime
import uuid

class TranslationSession(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    french_text = db.Column(db.Text, default='')
    english_text = db.Column(db.Text, default='')
    polish_text = db.Column(db.Text, default='')
    active_language = db.Column(db.String(10), default='english')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'french_text': self.french_text,
            'english_text': self.english_text,
            'polish_text': self.polish_text,
            'active_language': self.active_language,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def update_text(self, language, text):
        """Update text for a specific language"""
        if language == 'french':
            self.french_text = text
        elif language == 'english':
            self.english_text = text
        elif language == 'polish':
            self.polish_text = text
        
        self.active_language = language