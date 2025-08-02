# Overview

This is a live translation web application that provides real-time translation between French, English, and Polish languages. The application features a three-column interface where users can type in any of the supported languages and see instant translations in the other two languages. Built with Flask as the backend framework and powered by Google's Gemini AI for translation services, the app offers a smooth, interactive user experience with visual feedback and error handling.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
The frontend uses a responsive three-column layout built with Bootstrap and vanilla JavaScript. Each column represents one of the three supported languages (French, English, Polish) with interactive text areas. The interface employs a single-page application approach with dynamic content updates via AJAX calls. Visual feedback is provided through CSS transitions, active column highlighting, and loading spinners during translation requests.

## Backend Architecture
The backend follows a simple Flask application structure with separation of concerns:
- **Main Application** (`app.py`): Handles HTTP routing, request processing, and response formatting
- **Translation Service** (`gemini_translator.py`): Encapsulates all Gemini AI integration logic
- **Entry Point** (`main.py`): Simple application launcher

The API design is minimal with a single `/translate` endpoint that accepts JSON payloads containing the source text and language, returning translations for the other two languages.

## Translation Logic
The system implements a smart translation approach where:
- Users select an active column by clicking or focusing on a text area
- Text input in the active column triggers translation to the other two languages
- Debouncing prevents excessive API calls during rapid typing
- Error handling ensures graceful degradation when translation fails

## State Management
Client-side state management tracks:
- Currently active language column
- Last translated text for each language to avoid redundant API calls
- Translation status to prevent overlapping requests
- Input debouncing with configurable timeout

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
- **Environment Configuration**: Uses environment variables for sensitive configuration (session secret, API keys)

## Development Environment
- **Replit Platform**: Designed for deployment and development on Replit with appropriate CDN links and theme compatibility