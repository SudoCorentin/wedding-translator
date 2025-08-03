import os
import logging
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from gemini_translator import GeminiTranslator

logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)

# Initialize Gemini translator
translator = GeminiTranslator()

with app.app_context():
    import models
    db.create_all()

@app.route('/')
def index():
    """Main page with three-column translation interface"""
    # Create or get session ID for multi-device sync
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    return render_template('index.html', session_id=session['session_id'])

@app.route('/translate', methods=['POST'])
def translate():
    """API endpoint for translation requests"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        source_language = data.get('source_language')
        session_id = session.get('session_id')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID'}), 400
        
        if not text:
            # Clear translations
            clear_session_translations(session_id)
            return jsonify({
                'success': True,
                'translations': {
                    'french': '',
                    'english': '',
                    'polish': ''
                }
            })
        
        # Get translations for the other two languages
        translations = translator.translate_text(text, source_language)
        
        # Save to database for multi-device sync
        save_translations_to_database(session_id, translations, source_language)
        
        return jsonify({
            'success': True,
            'translations': translations
        })
        
    except Exception as e:
        logging.error(f"Translation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Translation failed. Please try again.'
        }), 500

def save_translations_to_database(session_id, translations, source_language):
    """Save translations to database for multi-device sync"""
    try:
        from models import TranslationSession
        
        # Get or create session
        translation_session = TranslationSession.query.get(session_id)
        if not translation_session:
            translation_session = TranslationSession(id=session_id)
            db.session.add(translation_session)
        
        # Update translations
        translation_session.french_text = translations.get('french', '')
        translation_session.english_text = translations.get('english', '')
        translation_session.polish_text = translations.get('polish', '')
        translation_session.active_language = source_language
        translation_session.updated_at = datetime.utcnow()
        
        db.session.commit()
        
    except Exception as e:
        logging.error(f"Error saving translations: {str(e)}")

def clear_session_translations(session_id):
    """Clear all translations for a session"""
    try:
        from models import TranslationSession
        
        translation_session = TranslationSession.query.get(session_id)
        if translation_session:
            translation_session.french_text = ''
            translation_session.english_text = ''
            translation_session.polish_text = ''
            translation_session.updated_at = datetime.utcnow()
            db.session.commit()
            
    except Exception as e:
        logging.error(f"Error clearing translations: {str(e)}")

@app.route('/sync')
def sync():
    """Simple polling endpoint for multi-device sync"""
    try:
        session_id = session.get('session_id')
        last_check = request.args.get('last_check', type=float, default=0)
        
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID'}), 400
        
        from models import TranslationSession
        translation_session = TranslationSession.query.get(session_id)
        
        if translation_session and translation_session.updated_at:
            # Convert to timestamp for comparison
            updated_timestamp = translation_session.updated_at.timestamp()
            
            if updated_timestamp > last_check:
                return jsonify({
                    'success': True,
                    'translations': {
                        'french': translation_session.french_text,
                        'english': translation_session.english_text,
                        'polish': translation_session.polish_text
                    },
                    'active_language': translation_session.active_language,
                    'timestamp': updated_timestamp
                })
        
        return jsonify({
            'success': True,
            'no_changes': True
        })
        
    except Exception as e:
        logging.error(f"Sync error: {str(e)}")
        return jsonify({'success': False, 'error': 'Sync failed'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
