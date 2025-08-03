import os
import logging
import asyncio
import concurrent.futures
import json
from google import genai
from google.genai import types

class GeminiTranslator:
    def __init__(self):
        """Initialize Gemini client for translation"""
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "default_key"))
        self.language_codes = {
            'french': 'French',
            'english': 'English', 
            'polish': 'Polish'
        }
    
    def translate_text(self, text: str, source_language: str) -> dict:
        """
        Translate text from source language to the other two languages
        
        Args:
            text: Text to translate
            source_language: Source language ('french', 'english', or 'polish')
            
        Returns:
            Dict with translations for all three languages
        """
        translations = {
            'french': '',
            'english': '',
            'polish': ''
        }
        
        # Set the source text in the appropriate language
        translations[source_language] = text
        
        # Get the other two languages to translate to
        target_languages = [lang for lang in self.language_codes.keys() if lang != source_language]
        
        # Use ThreadPoolExecutor to make parallel API calls
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both translation tasks simultaneously
            future_to_lang = {
                executor.submit(
                    self._translate_to_language,
                    text,
                    self.language_codes[source_language],
                    self.language_codes[target_lang]
                ): target_lang for target_lang in target_languages
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_lang):
                target_lang = future_to_lang[future]
                try:
                    translated_text = future.result()
                    translations[target_lang] = translated_text
                except Exception as e:
                    logging.error(f"Failed to translate to {target_lang}: {str(e)}")
                    translations[target_lang] = f"Translation error: {str(e)}"
        
        return translations
    
    def _translate_to_language(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text from source language to target language using Gemini
        
        Args:
            text: Text to translate
            source_lang: Source language name
            target_lang: Target language name
            
        Returns:
            Translated text
        """
        prompt = f"""Translate the following text from {source_lang} to {target_lang}. 
        Only return the translation, no explanations or additional text.
        
        Text to translate: {text}"""
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            if response.text:
                return response.text.strip()
            else:
                raise Exception("Empty response from Gemini API")
                
        except Exception as e:
            logging.error(f"Gemini API error: {str(e)}")
            raise Exception(f"Translation service unavailable: {str(e)}")
    
    def translate_text_batch(self, text: str, source_language: str) -> dict:
        """
        Translate text using a single API call with batch prompting for better speed
        
        Args:
            text: Text to translate
            source_language: Source language ('french', 'english', or 'polish')
            
        Returns:
            Dict with translations for all three languages
        """
        translations = {
            'french': '',
            'english': '',
            'polish': ''
        }
        
        # Set the source text in the appropriate language
        translations[source_language] = text
        
        # Get target languages
        target_languages = [lang for lang in self.language_codes.keys() if lang != source_language]
        
        if len(target_languages) == 2:
            # Create optimized prompt for batch translation
            source_lang_name = self.language_codes[source_language]
            target_lang_1 = self.language_codes[target_languages[0]]
            target_lang_2 = self.language_codes[target_languages[1]]
            
            prompt = f"""Translate the following {source_lang_name} text to {target_lang_1} and {target_lang_2}. 
Respond in JSON format with keys "{target_languages[0]}" and "{target_languages[1]}".

Text to translate: {text}

Response format:
{{
    "{target_languages[0]}": "translation here",
    "{target_languages[1]}": "translation here"
}}"""

            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                
                if response.text:
                    # Parse JSON response
                    batch_translations = json.loads(response.text.strip())
                    
                    # Update translations dict
                    for lang_code, translation in batch_translations.items():
                        if lang_code in translations:
                            translations[lang_code] = translation
                    
                    return translations
                    
            except Exception as e:
                logging.error(f"Batch translation failed, falling back to parallel: {e}")
        
        # Fallback to parallel translation if batch fails
        return self.translate_text(text, source_language)
