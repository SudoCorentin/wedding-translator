import os
import logging
from flask import Flask, render_template, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from gemini_translator import GeminiTranslator

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize Gemini translator
translator = GeminiTranslator()

@app.route('/')
def index():
    return render_template('index.html',
                         firebase_api_key=os.environ.get("FIREBASE_API_KEY"),
                         firebase_project_id=os.environ.get("FIREBASE_PROJECT_ID"),
                         firebase_app_id=os.environ.get("FIREBASE_APP_ID"))

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        source_language = data.get('source_language', '')
        
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)