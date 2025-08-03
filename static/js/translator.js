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
        // Get all translation inputs
        this.inputs = document.querySelectorAll('.translation-input');
        this.columns = document.querySelectorAll('.translation-column');
        this.errorAlert = document.getElementById('error-alert');
        this.errorMessage = document.getElementById('error-message');
        this.statusInfo = document.getElementById('status-info');
        
        // Initialize event listeners
        this.setupEventListeners();
        
        // Initialize last translated text and scroll tracking for each language
        this.inputs.forEach(input => {
            const language = input.dataset.language;
            this.lastTranslatedText[language] = '';
            this.scrollPositions[language] = { isNearBottom: true };
            
            // Track scroll position for each textarea independently
            input.addEventListener('scroll', () => {
                this.updateScrollPosition(input, language);
            });
        });
    }
    
    setupEventListeners() {
        // Add click listeners to columns for selection
        this.columns.forEach(column => {
            column.addEventListener('click', (e) => {
                const language = column.dataset.language;
                this.selectColumn(language);
            });
        });
        
        // Add input listeners for real-time translation
        this.inputs.forEach(input => {
            const language = input.dataset.language;
            
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
        });
    }
    
    selectColumn(language) {
        // Remove active class from all columns
        this.columns.forEach(column => {
            column.classList.remove('active-column');
        });
        
        // Add active class to selected column
        const selectedColumn = document.querySelector(`.translation-column[data-language="${language}"]`);
        if (selectedColumn) {
            selectedColumn.classList.add('active-column');
        }
        
        // Update active language
        this.activeLanguage = language;
        
        // Enable/disable inputs
        this.inputs.forEach(input => {
            if (input.dataset.language === language) {
                input.removeAttribute('readonly');
                input.focus();
            } else {
                input.setAttribute('readonly', true);
            }
        });
        
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
        
        // Check if text has changed significantly
        if (this.lastTranslatedText[sourceLanguage] === text.trim()) {
            return;
        }
        
        // Set debounced translation
        this.translationTimeout = setTimeout(() => {
            this.translateText(text, sourceLanguage);
        }, 800); // 800ms debounce for better UX
    }
    
    async translateText(text, sourceLanguage) {
        if (this.isTranslating) {
            return;
        }
        
        this.isTranslating = true;
        console.log('Translating:', text, 'from', sourceLanguage); // Debug log
        
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
            console.log('Translation response:', data); // Debug log
            
            if (data.success) {
                this.updateTranslations(data.translations, sourceLanguage);
                this.lastTranslatedText[sourceLanguage] = text.trim();
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
        // Update the text in other columns
        console.log('Updating translations:', translations); // Debug log
        Object.keys(translations).forEach(language => {
            if (language !== sourceLanguage) {
                const input = document.querySelector(`.translation-input[data-language="${language}"]`);
                if (input) {
                    input.value = translations[language];
                    this.lastTranslatedText[language] = translations[language];
                    // Each column handles its own scrolling based on its content length
                    this.autoScrollToBottomForLanguage(input, language);
                    console.log('Updated', language, 'with:', translations[language]); // Debug log
                } else {
                    console.error('Could not find input for language:', language); // Debug log
                }
            }
        });
    }
    
    clearOtherColumns(sourceLanguage) {
        this.inputs.forEach(input => {
            if (input.dataset.language !== sourceLanguage) {
                input.value = '';
                this.lastTranslatedText[input.dataset.language] = '';
            }
        });
    }
    
    showLoadingSpinners() {
        // No spinners to show in minimal interface
    }
    
    hideLoadingSpinners() {
        // No spinners to hide in minimal interface
    }
    
    showError(message) {
        console.error('Translation error:', message);
        // In minimal interface, we'll just log errors to console
    }
    
    hideError() {
        // No error UI to hide in minimal interface
    }
    
    updateStatus(message) {
        console.log('Status:', message);
        // In minimal interface, we'll just log status to console
    }
    
    capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
    
    updateScrollPosition(textarea, language) {
        // Track if user is near bottom for this specific column
        if (textarea.scrollHeight > textarea.clientHeight) {
            const isNearBottom = textarea.scrollTop >= (textarea.scrollHeight - textarea.clientHeight - 50);
            this.scrollPositions[language].isNearBottom = isNearBottom;
        }
    }
    
    autoScrollToBottomForLanguage(textarea, language) {
        // Only auto-scroll this specific column if user was near the bottom
        if (textarea && textarea.scrollHeight > textarea.clientHeight) {
            if (this.scrollPositions[language].isNearBottom) {
                // Smooth scroll to bottom only if user was already near the bottom for this column
                textarea.scrollTo({
                    top: textarea.scrollHeight,
                    behavior: 'smooth'
                });
                // Update the position tracker
                this.scrollPositions[language].isNearBottom = true;
            }
        }
    }
    
    scrollToBottomIfTyping(textarea) {
        // For the active typing area, always keep cursor visible at bottom
        if (textarea && textarea.scrollHeight > textarea.clientHeight) {
            textarea.scrollTop = textarea.scrollHeight;
        }
    }
}

// Initialize the translator when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new LiveTranslator();
});
