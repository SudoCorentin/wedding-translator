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
        Sentence-by-sentence translation for accuracy
        
        Args:
            text: Text to translate
            source_language: Source language ('french', 'english', or 'polish')
            
        Returns:
            Dict with translations for all three languages
        """
        import time
        start_time = time.time()
        logging.info(f"🕐 TIMING: Server translation started for {source_language}")
        logging.info(f"Processing translation: {len(text)} characters")
        
        translations = {'french': '', 'english': '', 'polish': ''}
        translations[source_language] = text

        # Always use sentence-based translation for accuracy
        logging.info(f"Text is {len(text)} chars, using sentence-based translation")
        sentence_translations = self._translate_sentence_by_sentence(text, source_language)
        translations.update(sentence_translations)
        
        total_time = time.time() - start_time
        logging.info(f"🕐 TIMING: Total server translation time: {total_time*1000:.0f}ms")
        return translations
    
    def _translate_sentence_by_sentence(self, text: str, source_language: str) -> dict:
        """
        Translate text sentence by sentence for accuracy and speed
        """
        import time
        import re
        
        start_time = time.time()
        logging.info("🔄 Starting sentence-by-sentence translation")
        
        # Split into sentences at punctuation boundaries
        sentences = self._split_into_sentences(text)
        logging.info(f"Split text into {len(sentences)} sentences")
        
        # Get target languages
        target_languages = [
            lang for lang in self.language_codes.keys()
            if lang != source_language
        ]
        
        # Initialize result storage
        sentence_results = {lang: [] for lang in target_languages}
        
        # Translate each sentence individually
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
                
            logging.info(f"Translating sentence {i+1}/{len(sentences)}: '{sentence[:50]}...'")
            
            try:
                sentence_translation = self._translate_batch(sentence, source_language, target_languages)
                for lang in target_languages:
                    sentence_results[lang].append(sentence_translation[lang])
            except Exception as e:
                logging.error(f"Sentence {i+1} translation failed: {e}")
                # Add original sentence to maintain flow
                for lang in target_languages:
                    sentence_results[lang].append(sentence)
        
        # Reassemble chunks maintaining original structure
        final_translations = {}
        for lang in target_languages:
            # Join with line breaks if original text had line breaks
            if '\n' in text:
                final_translations[lang] = '\n\n'.join(sentence_results[lang])
            else:
                final_translations[lang] = ' '.join(sentence_results[lang])
        
        end_time = time.time()
        logging.info(f"🕐 TIMING: Sentence-by-sentence translation completed in {(end_time - start_time)*1000:.0f}ms")
        
        return final_translations
    
    def _split_into_sentences(self, text: str) -> list:
        """
        Split text into logical chunks - sentences OR line breaks
        """
        import re
        
        # Split on both sentence punctuation AND line breaks
        # This handles real-world text with bullet points, line breaks, etc.
        
        # First split on line breaks (newlines)
        lines = text.strip().split('\n')
        
        chunks = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Further split each line on sentence punctuation if it's long
            if len(line) > 100:  # Only split long lines
                sentence_pattern = r'(?<=[.!?])\s+'
                sub_sentences = re.split(sentence_pattern, line)
                for sub in sub_sentences:
                    sub = sub.strip()
                    if sub:
                        chunks.append(sub)
            else:
                chunks.append(line)
        
        logging.info(f"Split into {len(chunks)} chunks: {[s[:30] + '...' for s in chunks]}")
        return chunks
    
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
                model="gemini-2.5-flash-lite", contents=prompt)
            
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
                model="gemini-2.5-flash-lite", contents=prompt)

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