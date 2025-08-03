# Overview

This is a live translation web application that provides real-time translation between French, English, and Polish languages with multi-device synchronization capabilities. The application features a minimal three-column interface in light mode where users can click and type in any column to see instant translations in the other two languages. Built with Flask as the backend framework, powered by Google's Gemini AI for translation services, and enhanced with Firebase Realtime Database for instant multi-device sync, the app offers a clean, distraction-free user experience with seamless cross-device functionality.

## Recent Changes (August 3, 2025)
✓ **Fixed critical English translation bug** - English column now shows proper English translations instead of French text
✓ **Enhanced translation prompts** - Stronger, more explicit prompts prevent translation failures
✓ **Upgraded to gemini-2.5-flash** - Full model instead of lite version for better accuracy
✓ **Optimized UI for legibility** - Extremely small column titles (10px), removed all spacing, added separator lines
✓ **Fixed translation logic** - Now processes complete text instead of just first word
✓ **Implemented Firebase Realtime Database** - Multi-device sync working and tested
✓ **Removed complex WebSocket/PostgreSQL code** - Simplified architecture for reliability  
✓ **Enhanced parallel API calls** - Reduced translation time to ~3 seconds
✓ **Fixed Firebase region URL** - Using correct Europe West 1 database endpoint
✓ **Resolved mobile input issues** - Enhanced touch events and debugging for mobile compatibility
✓ **Fixed speech input truncation** - Protected active typing from Firebase sync overwrites
✓ **Optimized translation speed** - Reduced debounce to 300ms, achieving 2-3 second translations
✓ **Identified Replit network bottleneck** - 243ms base latency to Google APIs causing slowness
✓ **Implemented single-call batch translation** - Reduced API calls by 50% to combat rate limits
✓ **Added performance monitoring** - Detailed timing logs throughout the translation pipeline

# User Preferences

- Preferred communication style: Simple, everyday language
- Interface design: Minimal, clean design with no extra elements
- Visual style: Light mode interface, full-height columns
- UI elements: Remove titles, status messages, loading indicators, and decorative icons

# System Architecture

## Frontend Architecture
The frontend uses a minimal three-column layout built with Bootstrap (light mode) and vanilla JavaScript. Each column represents one of the three supported languages (French, English, Polish) with full-height interactive text areas that stretch from top to bottom of the viewport. The interface employs a single-page application approach with dynamic content updates via AJAX calls. Visual feedback is provided through subtle CSS transitions and active column highlighting, with all status messages and loading indicators removed for a clean, distraction-free experience.

## Backend Architecture
The backend follows a simple Flask application structure:
- **Main Application** (`app.py`): Handles HTTP routing and translation requests
- **Translation Service** (`gemini_translator.py`): Encapsulates all Gemini AI integration with parallel API call optimization
- **Entry Point** (`main.py`): Simple application launcher

The API design includes:
- `/translate` endpoint for translation requests
- Firebase Realtime Database for instant multi-device synchronization
- Session-based state management handled client-side with Firebase

## Translation Logic
The system implements a smart translation approach where:
- Users select an active column by clicking or focusing on a text area
- Text input in the active column triggers translation to the other two languages
- Debouncing prevents excessive API calls during rapid typing
- Error handling ensures graceful degradation when translation fails

## State Management
Simple and reliable state management system:

**Client-side tracking:**
- Currently active language column with smart scrolling per column
- Last translated text for each language to avoid redundant API calls
- Translation status to prevent overlapping requests
- Input debouncing (1000ms) for optimal responsiveness
- Firebase real-time sync with feedback loop prevention

**Firebase Realtime Database:**
- Instant multi-device synchronization
- Session-based text storage for French, English, and Polish content
- Active language tracking across devices
- Real-time updates without polling or complex WebSocket management

# External Dependencies

## AI Translation Service
- **Google Gemini AI**: Primary translation engine accessed through the `google.genai` Python client
- **API Key**: Requires `GEMINI_API_KEY` environment variable for authentication
- **Supported Languages**: French, English, and Polish with full bidirectional translation capability

## Frontend Libraries
- **Bootstrap 5**: UI framework with dark theme support via CDN
- **Font Awesome 6**: Icon library for visual enhancements
- **Replit Bootstrap Theme**: Custom dark theme optimization for Replit environment

## Backend Framework
- **Flask**: Lightweight Python web framework for API and template rendering
- **Firebase Realtime Database**: Cloud-based real-time synchronization for multi-device support
- **Environment Configuration**: Uses environment variables for sensitive configuration (session secret, API keys, Firebase credentials)

## Development Environment
- **Replit Platform**: Designed for deployment and development on Replit with appropriate CDN links and theme compatibility