class LiveTranslator {
    constructor() {
        this.activeLanguage = null;
        this.translationTimeout = null;
        this.lastTranslatedText = {};
        this.isTranslating = false;
        this.scrollPositions = {}; // Track scroll positions for each column
        
        this.init();
    }

    init() {
        this.inputs = document.querySelectorAll('.translation-input');
        this.columns = document.querySelectorAll('.translation-column');
        
        // Initialize tracking for each language
        this.inputs.forEach(input => {
            const language = input.dataset.language;
            this.lastTranslatedText[language] = '';
            this.scrollPositions[language] = 0;
        });
        
        this.setupEventListeners();
        
        // Auto-select first column (English by default)
        this.selectColumn('english');
    }

    setupEventListeners() {
        this.inputs.forEach(input => {
            const language = input.dataset.language;
            
            // Handle column selection on click/focus
            input.addEventListener('click', () => {
                this.selectColumn(language);
            });
            
            input.addEventListener('focus', () => {
                this.selectColumn(language);
            });
            
            input.addEventListener('input', (e) => {
                if (this.activeLanguage === language) {
                    this.handleInput(e.target.value, language);
                    // For active typing, always keep at bottom
                    this.scrollToBottomIfTyping(e.target);
                }
            });
            
            // Prevent editing non-active columns
            input.addEventListener('keydown', (e) => {
                if (this.activeLanguage !== language) {
                    e.preventDefault();
                }
            });
            
            // Track scroll position for each column
            input.addEventListener('scroll', () => {
                this.scrollPositions[language] = input.scrollTop;
            });
        });
    }

    selectColumn(language) {
        // Remove active class from all columns
        this.columns.forEach(col => {
            col.classList.remove('active');
        });
        
        // Add active class to selected column
        const activeColumn = document.querySelector(`.translation-column[data-language="${language}"]`);
        if (activeColumn) {
            activeColumn.classList.add('active');
        }
        
        // Set active language and focus
        this.activeLanguage = language;
        const input = document.querySelector(`.translation-input[data-language="${language}"]`);
        if (input) {
            input.focus();
        }
        
        console.log('Selected column:', language); // Debug log
    }
    
    handleInput(text, sourceLanguage) {
        // Clear existing timeout
        if (this.translationTimeout) {
            clearTimeout(this.translationTimeout);
        }
        
        // Hide error alert
        this.hideError();
        
        // If text is empty, clear other columns
        if (!text.trim()) {
            this.clearOtherColumns(sourceLanguage);
            return;
        }
        
        // Check if text has changed significantly (only skip if exactly the same)
        if (this.lastTranslatedText[sourceLanguage] === text.trim()) {
            return;
        }
        
        // Set debounced translation - increased timeout to reduce API spam
        this.translationTimeout = setTimeout(() => {
            console.log('Starting translation for full text:', text.substring(0, 100) + '...');
            this.translateText(text.trim(), sourceLanguage);
        }, 1000); // Increased to 1 second to ensure full text input
    }

    async translateText(text, sourceLanguage) {
        if (this.isTranslating) {
            return; // Prevent concurrent translations
        }
        
        this.isTranslating = true;
        
        try {
            const response = await fetch('/translate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    source_language: sourceLanguage
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update last translated text
                this.lastTranslatedText[sourceLanguage] = text;
                
                // Update translations in other columns
                this.updateTranslations(data.translations, sourceLanguage);
            } else {
                this.showError(data.error || 'Translation failed');
            }
        } catch (error) {
            console.error('Translation error:', error);
            this.showError('Network error. Please check your connection.');
        } finally {
            this.isTranslating = false;
        }
    }

    updateTranslations(translations, sourceLanguage) {
        Object.keys(translations).forEach(language => {
            if (language !== sourceLanguage) {
                const input = document.querySelector(`.translation-input[data-language="${language}"]`);
                if (input) {
                    input.value = translations[language];
                    this.lastTranslatedText[language] = translations[language];
                    
                    // Smart scroll for non-active columns
                    this.autoScrollToBottomForLanguage(input, language);
                }
            }
        });
    }

    clearOtherColumns(sourceLanguage) {
        this.inputs.forEach(input => {
            const language = input.dataset.language;
            if (language !== sourceLanguage) {
                input.value = '';
                this.lastTranslatedText[language] = '';
            }
        });
    }

    showError(message) {
        console.error('Translation error:', message);
        // Could add UI error display here if needed
    }

    hideError() {
        // Could hide UI error display here if needed
    }

    autoScrollToBottomForLanguage(input, language) {
        // Only auto-scroll if user was already near the bottom or if it's a non-active column
        const isNearBottom = input.scrollTop >= (input.scrollHeight - input.clientHeight - 50);
        const isActiveColumn = language === this.activeLanguage;
        
        if (!isActiveColumn || isNearBottom) {
            // Small delay to ensure content is rendered
            setTimeout(() => {
                if (input.scrollHeight > input.clientHeight) {
                    input.scrollTop = input.scrollHeight;
                }
            }, 50);
        }
    }
    
    scrollToBottomIfTyping(textarea) {
        // For the active typing area, always keep cursor visible at bottom
        if (textarea && textarea.scrollHeight > textarea.clientHeight) {
            textarea.scrollTop = textarea.scrollHeight;
        }
    }
}

// Initialize the translator when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new LiveTranslator();
});