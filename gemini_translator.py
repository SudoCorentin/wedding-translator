import os
import logging
import asyncio
import concurrent.futures
import json
from google import genai


class GeminiTranslator:

    def __init__(self):
        """Initialize Gemini client for translation"""
        self.client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY", "default_key"))
        self.language_codes = {
            'french': 'French',
            'english': 'English',
            'polish': 'Polish'
        }

    def translate_text(self, text: str, source_language: str) -> dict:
        """
        Optimized single-call translation using batch processing
        
        Args:
            text: Text to translate
            source_language: Source language ('french', 'english', or 'polish')
            
        Returns:
            Dict with translations for all three languages
        """
        import time
        start_time = time.time()
        logging.info(f"🕐 TIMING: Server translation started for {source_language}")
        
        translations = {'french': '', 'english': '', 'polish': ''}
        translations[source_language] = text

        # Get target languages
        target_languages = [
            lang for lang in self.language_codes.keys()
            if lang != source_language
        ]
        
        if len(target_languages) == 2:
            # Single API call for both translations
            batch_start = time.time()
            try:
                batch_result = self._translate_batch(text, source_language, target_languages)
                batch_end = time.time()
                logging.info(f"🕐 TIMING: Batch API call completed in {(batch_end - batch_start)*1000:.0f}ms")
                
                translations.update(batch_result)
            except Exception as e:
                logging.error(f"Batch translation failed, falling back to parallel: {e}")
                # Fallback to parallel approach
                parallel_start = time.time()
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    future_to_lang = {
                        executor.submit(self._translate_to_language, text, self.language_codes[source_language], self.language_codes[target_lang]):
                        target_lang
                        for target_lang in target_languages
                    }
                    
                    for future in concurrent.futures.as_completed(future_to_lang):
                        target_lang = future_to_lang[future]
                        try:
                            translated_text = future.result()
                            translations[target_lang] = translated_text
                        except Exception as e:
                            logging.error(f"Failed to translate to {target_lang}: {str(e)}")
                            translations[target_lang] = f"Translation error: {str(e)}"
                parallel_end = time.time()
                logging.info(f"🕐 TIMING: Parallel fallback completed in {(parallel_end - parallel_start)*1000:.0f}ms")
        
        total_time = time.time() - start_time
        logging.info(f"🕐 TIMING: Total server translation time: {total_time*1000:.0f}ms")
        return translations
    
    def _translate_batch(self, text: str, source_language: str, target_languages: list) -> dict:
        """
        Single API call to translate to multiple languages simultaneously
        """
        source_lang_name = self.language_codes[source_language]
        target_lang_names = [self.language_codes[lang] for lang in target_languages]
        
        prompt = f"""You are a professional translator. Translate the following text from {source_lang_name} into {target_lang_names[0]} and {target_lang_names[1]}.

IMPORTANT: Provide ONLY the translations, one per line, in this exact order:
1. {target_lang_names[0]} translation
2. {target_lang_names[1]} translation

Do not include any explanations, labels, or additional text.

Text to translate: "{text}"

Translations:"""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt)
            
            if response.text:
                lines = response.text.strip().split('\n')
                # Clean up the lines
                clean_lines = []
                for line in lines:
                    line = line.strip()
                    # Remove numbering if present
                    if line and (line[0].isdigit() or line.startswith('-')):
                        line = line[1:].strip()
                        if line.startswith('.') or line.startswith(')'):
                            line = line[1:].strip()
                    if line:
                        clean_lines.append(line)
                
                if len(clean_lines) >= 2:
                    result = {}
                    result[target_languages[0]] = clean_lines[0]
                    result[target_languages[1]] = clean_lines[1]
                    return result
                else:
                    raise Exception("Insufficient translations in batch response")
            else:
                raise Exception("Empty response from Gemini API")
                
        except Exception as e:
            logging.error(f"Batch translation error: {str(e)}")
            raise Exception(f"Batch translation failed: {str(e)}")

    def _translate_to_language(self, text: str, source_lang: str,
                               target_lang: str) -> str:
        """
        Translate text from source language to target language using Gemini
        
        Args:
            text: Text to translate
            source_lang: Source language name
            target_lang: Target language name
            
        Returns:
            Translated text
        """
        # More explicit and stronger translation prompt
        prompt = f"""You are a professional translator. Translate this text from {source_lang} into {target_lang}.

IMPORTANT: You must translate the text into {target_lang}. Do not keep it in {source_lang}.

Source language: {source_lang}
Target language: {target_lang}
Text to translate: "{text}"

Translation in {target_lang}:"""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt)

            if response.text:
                translated = response.text.strip()
                # Remove any quotation marks that might wrap the translation
                if translated.startswith('"') and translated.endswith('"'):
                    translated = translated[1:-1]
                elif translated.startswith("'") and translated.endswith("'"):
                    translated = translated[1:-1]
                return translated
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
        translations = {'french': '', 'english': '', 'polish': ''}

        # Set the source text in the appropriate language
        translations[source_language] = text

        # Get target languages
        target_languages = [
            lang for lang in self.language_codes.keys()
            if lang != source_language
        ]

        if len(target_languages) == 2:
            # Create optimized prompt for batch translation
            source_lang_name = self.language_codes[source_language]
            target_lang_1 = self.language_codes[target_languages[0]]
            target_lang_2 = self.language_codes[target_languages[1]]

            # Disable batch translation temporarily and use reliable parallel method
            logging.info("Using parallel translation for reliability")
            pass  # Skip batch translation

        # Fallback to parallel translation if batch fails
        return self.translate_text(text, source_language)
