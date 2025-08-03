import os
import logging
import uuid
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, join_room, leave_room
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
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

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
            # Clear translations and sync across devices
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
        
        # Save to database and broadcast to all devices
        save_and_broadcast_translations(session_id, translations, source_language)
        
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

def save_and_broadcast_translations(session_id, translations, source_language):
    """Save translations to database and broadcast to all connected devices"""
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
        
        db.session.commit()
        
        # Broadcast to all devices in this session
        socketio.emit('translation_update', {
            'translations': translations,
            'active_language': source_language
        }, room=session_id)
        
    except Exception as e:
        logging.error(f"Error saving/broadcasting translations: {str(e)}")

def clear_session_translations(session_id):
    """Clear all translations for a session"""
    try:
        from models import TranslationSession
        
        translation_session = TranslationSession.query.get(session_id)
        if translation_session:
            translation_session.french_text = ''
            translation_session.english_text = ''
            translation_session.polish_text = ''
            db.session.commit()
            
            # Broadcast clear to all devices
            socketio.emit('translation_clear', {}, room=session_id)
            
    except Exception as e:
        logging.error(f"Error clearing translations: {str(e)}")

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle new WebSocket connection"""
    session_id = session.get('session_id')
    if session_id:
        join_room(session_id)
        logging.info(f"Client connected to session: {session_id}")
        
        # Send current state to the newly connected device
        try:
            from models import TranslationSession
            translation_session = TranslationSession.query.get(session_id)
            if translation_session:
                emit('session_state', {
                    'translations': {
                        'french': translation_session.french_text,
                        'english': translation_session.english_text,
                        'polish': translation_session.polish_text
                    },
                    'active_language': translation_session.active_language
                })
        except Exception as e:
            logging.error(f"Error sending session state: {str(e)}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    session_id = session.get('session_id')
    if session_id:
        leave_room(session_id)
        logging.info(f"Client disconnected from session: {session_id}")

@socketio.on('typing_update')
def handle_typing_update(data):
    """Handle real-time typing updates"""
    session_id = session.get('session_id')
    if session_id:
        # Broadcast typing update to other devices (excluding sender)
        emit('typing_sync', data, room=session_id, include_self=False)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
