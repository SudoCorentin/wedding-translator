class LiveTranslator {
    constructor() {
        this.activeLanguage = null;
        this.translationTimeout = null;
        this.lastTranslatedText = {};
        this.isTranslating = false;
        this.scrollPositions = {}; // Track scroll positions for each column
        this.sessionId = this.generateSessionId();
        this.isReceivingUpdate = false; // Prevent feedback loops
        
        this.init();
        this.initFirebaseSync();
    }

    generateSessionId() {
        // Use a fixed session ID so all devices connect to the same session
        // You can change this to create different rooms
        return 'shared_translation_session';
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
            
            // Handle column selection on click/focus with debugging
            input.addEventListener('click', () => {
                console.log('CLICK EVENT: Selecting column', language);
                this.selectColumn(language);
            });
            
            input.addEventListener('focus', () => {
                console.log('FOCUS EVENT: Selecting column', language);
                this.selectColumn(language);
            });
            
            // Add touchstart for mobile compatibility
            input.addEventListener('touchstart', () => {
                console.log('TOUCH EVENT: Selecting column', language);
                this.selectColumn(language);
            });
            
            input.addEventListener('input', (e) => {
                console.log('INPUT EVENT: Language =', language, 'Active =', this.activeLanguage, 'Text length =', e.target.value.length);
                if (this.activeLanguage === language) {
                    this.handleInput(e.target.value, language);
                    // For active typing, always keep at bottom
                    this.scrollToBottomIfTyping(e.target);
                } else {
                    console.log('INPUT BLOCKED: Not active language');
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
        
        // Set debounced translation - reduced timeout for faster response
        this.translationTimeout = setTimeout(() => {
            console.log('Starting translation for full text:', text.substring(0, 100) + '...');
            this.translateText(text.trim(), sourceLanguage);
        }, 2000); // increase to 2000 to hit the API max 30 times per minute
    }

    async translateText(text, sourceLanguage) {
        console.log('TRANSLATE REQUEST: Starting translation for', sourceLanguage, 'text length:', text.length);
        
        if (this.isTranslating) {
            console.log('TRANSLATE BLOCKED: Already translating');
            return; // Prevent concurrent translations
        }
        
        this.isTranslating = true;
        
        try {
            console.log('TRANSLATE API: Sending request to /translate');
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
            
            console.log('TRANSLATE API: Response status =', response.status);
            const data = await response.json();
            console.log('TRANSLATE API: Response data =', data);
            
            if (data.success) {
                console.log('TRANSLATE SUCCESS: Updating UI with translations');
                // Update last translated text
                this.lastTranslatedText[sourceLanguage] = text;
                
                // Update translations in other columns
                this.updateTranslations(data.translations, sourceLanguage);
                
                // Sync to Firebase for multi-device support
                this.syncToFirebase(data.translations, sourceLanguage);
                console.log('TRANSLATE COMPLETE: Translation and sync finished');
            } else {
                console.error('TRANSLATE ERROR: API returned error =', data.error);
                this.showError(data.error || 'Translation failed');
            }
        } catch (error) {
            console.error('TRANSLATE NETWORK ERROR:', error);
            this.showError('Network error. Please check your connection.');
        } finally {
            this.isTranslating = false;
            console.log('TRANSLATE DONE: isTranslating set to false');
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

    initFirebaseSync() {
        // Initialize Firebase real-time sync
        if (!window.firebase) {
            console.log('Firebase not available, multi-device sync disabled');
            return;
        }

        try {
            const { database, ref, set, onValue } = window.firebase;
            this.database = database;
            this.sessionRef = ref(database, `sessions/${this.sessionId}`);
            
            console.log('Attempting Firebase connection with SHARED session:', this.sessionId);
            console.log('Database reference:', this.sessionRef);
            console.log('All devices using this URL will sync to the same session');
            
            // Test Firebase write immediately
            const testData = {
                test: 'Firebase connection test',
                timestamp: Date.now()
            };
            
            set(this.sessionRef, testData).then(() => {
                console.log('✓ Firebase write test successful - database rules are properly configured');
            }).catch((error) => {
                console.error('✗ Firebase write test failed - check database rules:', error);
                console.error('Database rules must allow read/write access');
            });
            
            // Listen for changes from other devices
            onValue(this.sessionRef, (snapshot) => {
                const data = snapshot.val();
                console.log('Firebase onValue triggered with data:', data);
                
                if (data && data.translations && !this.isReceivingUpdate) {
                    console.log('Received Firebase sync update with translations - updating UI');
                    this.isReceivingUpdate = true;
                    
                    // Force update the UI with Firebase data
                    this.updateFromFirebase(data);
                    
                    // Brief delay to prevent feedback loops
                    setTimeout(() => {
                        this.isReceivingUpdate = false;
                    }, 2000);
                } else if (data && !data.translations) {
                    console.log('Firebase data received but no translations found');
                } else if (this.isReceivingUpdate) {
                    console.log('Skipping Firebase update - currently receiving update');
                }
            }, (error) => {
                console.error('Firebase onValue error:', error);
            });
            
            console.log('Firebase sync initialized with session:', this.sessionId);
        } catch (error) {
            console.error('Firebase sync setup failed:', error);
        }
    }

    syncToFirebase(translations, activeLanguage) {
        // Send updates to Firebase for other devices
        if (!this.database || this.isReceivingUpdate) {
            console.log('Skipping Firebase sync - database not available or receiving update');
            return;
        }

        try {
            const { ref, set } = window.firebase;
            const updateData = {
                translations: translations,
                activeLanguage: activeLanguage,
                timestamp: Date.now()
            };
            
            console.log('Syncing to Firebase:', updateData);
            
            set(this.sessionRef, updateData).then(() => {
                console.log('✓ Synced to Firebase successfully');
            }).catch((error) => {
                console.error('✗ Firebase sync failed:', error);
            });
        } catch (error) {
            console.error('Firebase sync error:', error);
        }
    }

    updateFromFirebase(data) {
        // Update translations received from other devices
        console.log('Updating UI from Firebase data:', data);
        
        if (data.translations) {
            Object.keys(data.translations).forEach(language => {
                const input = document.querySelector(`.translation-input[data-language="${language}"]`);
                if (input && data.translations[language] !== undefined) {
                    const newValue = data.translations[language];
                    
                    // CRITICAL: Don't overwrite if user is currently typing in this column
                    const isCurrentlyActive = (language === this.activeLanguage);
                    const isUserTyping = input === document.activeElement;
                    
                    if (isCurrentlyActive && isUserTyping) {
                        console.log(`Skipping Firebase update for ${language} - user is actively typing`);
                        return; // Skip this column to prevent overwriting speech input
                    }
                    
                    console.log(`Updating ${language} column with: "${newValue}"`);
                    
                    // Only update if different to avoid cursor jumping
                    if (input.value !== newValue) {
                        // Save cursor position if this is the active input
                        const isActiveInput = input === document.activeElement;
                        const cursorPosition = isActiveInput ? input.selectionStart : null;
                        
                        input.value = newValue;
                        this.lastTranslatedText[language] = newValue;
                        
                        // Restore cursor position for active input
                        if (isActiveInput && cursorPosition !== null) {
                            input.setSelectionRange(cursorPosition, cursorPosition);
                        }
                        
                        this.autoScrollToBottomForLanguage(input, language);
                        console.log(`✓ Updated ${language} column successfully`);
                    }
                }
            });
            
            // Update active language indicator
            if (data.activeLanguage && data.activeLanguage !== this.activeLanguage) {
                console.log(`Updating active language from ${this.activeLanguage} to ${data.activeLanguage}`);
                this.selectColumn(data.activeLanguage);
            }
        }
    }
}

// Initialize the translator when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new LiveTranslator();
});