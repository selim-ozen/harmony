# Discord Music Recommendation Bot

## Overview

This is a comprehensive Discord bot that integrates with Spotify to provide personalized music recommendations, playlist creation, and music discovery features. The bot uses OAuth2 to connect users' Spotify accounts, analyzes their listening data, and generates intelligent music recommendations both individually and for the entire Discord server community.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Architecture
The bot follows a modular architecture with clear separation of concerns:

- **Discord Bot Layer**: Built using discord.py with both slash commands and traditional prefix commands
- **Authentication Layer**: OAuth2 integration with Spotify using the Authorization Code Flow
- **Data Layer**: SQLite database for persistent storage of user data and music information
- **Web Server Layer**: Flask-based keep-alive server that handles OAuth callbacks and provides health endpoints
- **Recommendation Engine**: Simple recommendation system for generating music suggestions

### Security Model
- OAuth2 secure authentication flow with Spotify
- Token management with automatic refresh handling
- Environment variable-based secret management
- GDPR compliance with user data deletion capabilities
- Secure token storage with expiration handling

## Key Components

### Bot Core (`bot.py`, `main.py`)
- Main bot class inheriting from `commands.Bot`
- Slash command synchronization
- Cog loading system for modular command organization
- Integration with database and web server components

### Authentication System (`spotify_auth.py`)
- Spotify OAuth2 flow implementation using Authorization Code Flow
- State parameter generation for CSRF protection
- Token refresh mechanism for expired access tokens
- Scopes management for required Spotify permissions

### Database Layer (`database.py`)
- SQLite-based storage for user authentication tokens
- User listening data storage (tracks, artists, preferences)
- Async database operations with connection pooling
- Schema management with proper indexing

### Web Server (`keep_alive.py`)
- Flask application for OAuth callback handling
- Health check endpoints for monitoring
- Replit deployment compatibility
- Bot status API endpoints

### Command Modules (`cogs/`)
- **Admin Cog**: Bot management, statistics, and administrative commands
- **Music Cog**: Core music functionality including Spotify connection and recommendations
- Modular design allows easy addition of new feature sets

### Utilities
- **Logger (`utils/logger.py`)**: Comprehensive logging with rotation and different log levels
- **Recommendations (`utils/recommendations.py`)**: Simple recommendation engine with multiple algorithm support

## Data Flow

### User Authentication Flow
1. User runs `/connect` command
2. Bot generates OAuth2 authorization URL with state parameter
3. User authorizes application on Spotify
4. Spotify redirects to callback URL with authorization code
5. Bot exchanges code for access/refresh tokens
6. Tokens stored in database with expiration tracking

### Music Data Collection
1. Authenticated users' Spotify data is fetched periodically
2. Top tracks, artists, and listening history stored in database
3. Data aggregated for both individual and community-wide analysis
4. Recommendation engine processes listening patterns

### Recommendation Generation
1. User requests recommendations via slash commands
2. Engine analyzes user's listening history and preferences
3. Algorithms generate personalized suggestions
4. Results presented through Discord embeds and interactive UI
5. Optional playlist creation directly in user's Spotify account

## External Dependencies

### Core Libraries
- **discord.py**: Discord API interaction and bot framework
- **spotipy**: Spotify Web API wrapper for Python
- **Flask**: Web server for OAuth callbacks and health checks
- **sqlite3**: Database operations (built into Python)
- **requests**: HTTP client for API calls

### Authentication & Security
- **secrets**: Cryptographically secure random number generation
- **base64**: Token encoding/decoding
- **urllib.parse**: URL manipulation for OAuth flows

### Deployment & Monitoring
- **logging**: Comprehensive application logging
- **threading**: Background web server operation
- **asyncio**: Asynchronous operation support

## Deployment Strategy

### Replit Deployment
- **Environment Variables**: All secrets managed through Replit's Secrets Manager
- **Keep-Alive Server**: Flask server prevents Replit from sleeping
- **HTTPS Support**: Replit's built-in HTTPS for OAuth2 callbacks
- **Persistent Storage**: SQLite database stored in Replit's persistent filesystem

### Configuration Management
- Environment-based configuration through `config.py`
- Validation of required environment variables on startup
- Feature flags for optional functionality
- Rate limiting and API quota management

### Monitoring & Maintenance
- Comprehensive logging with rotation to prevent disk space issues
- Health check endpoints for external monitoring
- Bot status commands for real-time diagnostics
- Automatic error reporting and recovery mechanisms

### Security Considerations
- Secure token storage with proper encryption
- GDPR compliance with data deletion capabilities
- Rate limiting to prevent API abuse
- State parameter validation for OAuth2 CSRF protection
- Environment variable isolation for sensitive data