import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from gemini_translator import GeminiTranslator
import uuid

logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False)

# Initialize Gemini translator
translator = GeminiTranslator()

@app.route('/')
def index():
    """Create a new translation session and redirect"""
    session_id = str(uuid.uuid4())
    return redirect(url_for('session', session_id=session_id))

@app.route('/session/<session_id>')
def session(session_id):
    """Main page with three-column translation interface for a specific session"""
    # Get or create session
    from models import TranslationSession
    session_obj = TranslationSession.query.get(session_id)
    if not session_obj:
        session_obj = TranslationSession(id=session_id)
        db.session.add(session_obj)
        db.session.commit()
    
    return render_template('index.html', session_id=session_id, session_data=session_obj.to_dict())

@app.route('/translate', methods=['POST'])
def translate():
    """API endpoint for translation requests"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        source_language = data.get('source_language')
        session_id = data.get('session_id')
        
        if not text:
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
        
        # Save to database if session_id provided
        if session_id:
            from models import TranslationSession
            session_obj = TranslationSession.query.get(session_id)
            if session_obj:
                # Update the session with new translations
                setattr(session_obj, f'{source_language}_text', text)
                for lang, translation in translations.items():
                    if lang != source_language:
                        setattr(session_obj, f'{lang}_text', translation)
                session_obj.active_language = source_language
                db.session.commit()
                
                # Broadcast to all devices in this session
                socketio.emit('translation_update', {
                    'translations': translations,
                    'source_language': source_language,
                    'session_id': session_id
                }, to=session_id)
        
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

@app.route('/sync', methods=['POST'])
def sync_input():
    """Fast sync endpoint for instant multi-device updates"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        language = data.get('language')
        text = data.get('text', '')
        
        if session_id and language:
            from models import TranslationSession
            session_obj = TranslationSession.query.get(session_id)
            if session_obj:
                setattr(session_obj, f'{language}_text', text)
                session_obj.active_language = language
                db.session.commit()
        
        return jsonify({'success': True})
    except Exception:
        return jsonify({'success': False}), 500

@app.route('/session/<session_id>/updates')
def get_session_updates(session_id):
    """Fast polling endpoint for multi-device sync"""
    try:
        from models import TranslationSession
        session_obj = TranslationSession.query.get(session_id)
        if session_obj:
            return jsonify({
                'french_text': session_obj.french_text or '',
                'english_text': session_obj.english_text or '',
                'polish_text': session_obj.polish_text or '',
                'active_language': session_obj.active_language,
                'updated_at': session_obj.updated_at.timestamp()
            })
        return jsonify({'error': 'Session not found'}), 404
    except Exception:
        return jsonify({'error': 'Server error'}), 500

# Create database tables
with app.app_context():
    import models  # Import models to register them
    db.create_all()

# WebSocket event handlers
@socketio.on('connect')
def on_connect():
    logging.info('Client connected')

@socketio.on('disconnect')
def on_disconnect():
    logging.info('Client disconnected')

@socketio.on('join_session')
def on_join_session(data):
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        logging.info(f'Client joined session: {session_id}')

@socketio.on('leave_session')
def on_leave_session(data):
    session_id = data.get('session_id')
    if session_id:
        leave_room(session_id)
        logging.info(f'Client left session: {session_id}')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False, log_output=False)
