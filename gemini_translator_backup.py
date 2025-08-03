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
        Smart chunked translation for long texts
        
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

        # Always use sentence-based chunking for real-time translation
        logging.info(f"Text is {len(text)} chars, using sentence-based translation")
        chunk_translations = self._translate_sentence_by_sentence(text, source_language)
        translations.update(chunk_translations)
            
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
        
        # Reassemble sentences with proper spacing
        final_translations = {}
        for lang in target_languages:
            final_translations[lang] = ' '.join(sentence_results[lang])
        
        end_time = time.time()
        logging.info(f"🕐 TIMING: Sentence-by-sentence translation completed in {(end_time - start_time)*1000:.0f}ms")
        
        return final_translations
    
    def _split_into_sentences(self, text: str) -> list:
        """
        Split text into sentences using improved punctuation detection
        """
        import re
        
        # More robust sentence splitting that handles various cases
        # Split on sentence-ending punctuation (. ! ?) followed by whitespace
        # This preserves sentence boundaries without requiring capitals
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text.strip())
        
        # Clean up empty sentences and add back punctuation context
        clean_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                clean_sentences.append(sentence)
        
        logging.info(f"Split into sentences: {[s[:30] + '...' for s in clean_sentences]}")
        return clean_sentences
    
    def _group_sentences_into_chunks(self, sentences: list, max_chunk_size: int = 400) -> list:
        """
        Group sentences into chunks without breaking sentence boundaries
        """
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Check if adding this sentence would exceed the limit
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if len(potential_chunk) <= max_chunk_size:
                current_chunk = potential_chunk
            else:
                # Current chunk is full, start a new one
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
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


        
        # Get target languages only (don't include source)
        target_languages = [
            lang for lang in self.language_codes.keys()
            if lang != source_language
        ]
        
        if len(target_languages) == 2:
            try:
                # Use batch translation for chunk
                batch_result = self._translate_chunk_batch(chunk, source_language, target_languages)
                translations.update(batch_result)
                
                total_time = time.time() - start_time
                logging.info(f"🕐 TIMING: Chunk translation completed in {total_time*1000:.0f}ms")
                return translations
                
            except Exception as e:
                logging.error(f"Chunk batch translation failed: {e}")
                # Fallback to single calls for chunks
                translations = self._translate_chunk_parallel(chunk, source_language, target_languages)
        
        total_time = time.time() - start_time
        logging.info(f"🕐 TIMING: Chunk translation completed in {total_time*1000:.0f}ms")
        return translations
    
    def _translate_chunk_batch(self, chunk: str, source_language: str, target_languages: list) -> dict:
        """
        Batch translate a chunk to multiple languages
        """
        source_lang_name = self.language_codes[source_language]
        target_lang_names = [self.language_codes[lang] for lang in target_languages]
        
        # Optimized prompt for chunks
        prompt = f"""Translate this text chunk from {source_lang_name}:

"{chunk}"

Provide translations in this exact format:
{target_lang_names[0]}: [translation]
{target_lang_names[1]}: [translation]"""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite", contents=prompt)
            
            if response.text:
                lines = response.text.strip().split('\n')
                result = {}
                
                for line in lines:
                    line = line.strip()
                    for i, target_lang in enumerate(target_languages):
                        expected_prefix = f"{target_lang_names[i]}:"
                        if line.lower().startswith(expected_prefix.lower()):
                            translation = line[len(expected_prefix):].strip()
                            result[target_lang] = translation
                            break
                
                if len(result) == 2:
                    return result
                else:
                    raise Exception("Could not parse batch chunk response")
            else:
                raise Exception("Empty response from Gemini API")
                
        except Exception as e:
            logging.error(f"Chunk batch translation error: {str(e)}")
            raise Exception(f"Chunk batch translation failed: {str(e)}")
    
    def _translate_chunk_parallel(self, chunk: str, source_language: str, target_languages: list) -> dict:
        """
        Parallel translate chunk as fallback
        """
        translations = {}
        source_lang_name = self.language_codes[source_language]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_to_lang = {
                executor.submit(self._translate_to_language, chunk, source_lang_name, self.language_codes[target_lang]):
                target_lang
                for target_lang in target_languages
            }
            
            for future in concurrent.futures.as_completed(future_to_lang):
                target_lang = future_to_lang[future]
                try:
                    translated_text = future.result()
                    translations[target_lang] = translated_text
                except Exception as e:
                    logging.error(f"Failed to translate chunk to {target_lang}: {str(e)}")
                    translations[target_lang] = f"[Translation error]"
        
        return translations
