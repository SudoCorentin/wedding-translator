import os
import logging
from flask import Flask, render_template, request, jsonify
from gemini_translator import GeminiTranslator

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Initialize Gemini translator
translator = GeminiTranslator()

@app.route('/')
def index():
    """Main page with three-column translation interface"""
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate():
    """API endpoint for translation requests"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        source_language = data.get('source_language')
        
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
