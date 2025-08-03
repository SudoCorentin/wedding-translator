# Overview

This is a live translation web application that provides real-time translation between French, English, and Polish languages with multi-device synchronization capabilities. The application features a minimal three-column interface in light mode where users can click and type in any column to see instant translations in the other two languages. Built with Flask as the backend framework, powered by Google's Gemini AI for translation services, and enhanced with WebSocket technology for real-time multi-device sync, the app offers a clean, distraction-free user experience with seamless cross-device functionality.

# User Preferences

- Preferred communication style: Simple, everyday language
- Interface design: Minimal, clean design with no extra elements
- Visual style: Light mode interface, full-height columns
- UI elements: Remove titles, status messages, loading indicators, and decorative icons

# System Architecture

## Frontend Architecture
The frontend uses a minimal three-column layout built with Bootstrap (light mode) and vanilla JavaScript. Each column represents one of the three supported languages (French, English, Polish) with full-height interactive text areas that stretch from top to bottom of the viewport. The interface employs a single-page application approach with dynamic content updates via AJAX calls. Visual feedback is provided through subtle CSS transitions and active column highlighting, with all status messages and loading indicators removed for a clean, distraction-free experience.

## Backend Architecture
The backend follows a Flask application structure enhanced with real-time capabilities:
- **Main Application** (`app.py`): Handles HTTP routing, WebSocket connections, session management, and real-time broadcasting
- **Database Models** (`models.py`): PostgreSQL-backed session storage for multi-device state persistence
- **Translation Service** (`gemini_translator.py`): Encapsulates all Gemini AI integration with parallel API call optimization
- **Entry Point** (`main.py`): SocketIO-enabled application launcher

The API design includes:
- `/translate` endpoint for translation requests with session persistence
- WebSocket events for real-time multi-device synchronization
- Session-based state management for device continuity

## Translation Logic
The system implements a smart translation approach where:
- Users select an active column by clicking or focusing on a text area
- Text input in the active column triggers translation to the other two languages
- Debouncing prevents excessive API calls during rapid typing
- Error handling ensures graceful degradation when translation fails

## State Management
Multi-layered state management system:

**Client-side tracking:**
- Currently active language column with smart scrolling per column
- Last translated text for each language to avoid redundant API calls
- Translation status to prevent overlapping requests
- Input debouncing (500ms) for optimal responsiveness
- WebSocket connection state and feedback loop prevention

**Server-side persistence:**
- PostgreSQL database sessions for multi-device state continuity
- Session-based text storage for French, English, and Polish content
- Active language tracking across devices
- Real-time WebSocket room management for device grouping

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
- **Flask-SocketIO**: WebSocket support for real-time multi-device synchronization
- **PostgreSQL**: Database backend for session persistence and state management
- **SQLAlchemy**: ORM for database operations and model management
- **Environment Configuration**: Uses environment variables for sensitive configuration (session secret, API keys, database URL)

## Development Environment
- **Replit Platform**: Designed for deployment and development on Replit with appropriate CDN links and theme compatibility