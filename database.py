"""
Database management for the Discord Music Bot
"""

import sqlite3
import asyncio
import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

class DatabaseManager:
    """Manages SQLite database operations"""
    
    def __init__(self, db_path: str = "music_bot.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize database tables"""
        async with self._lock:
            await asyncio.get_event_loop().run_in_executor(
                None, self._create_tables
            )
    
    def _create_tables(self):
        """Create database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    discord_id INTEGER PRIMARY KEY,
                    spotify_id TEXT,
                    access_token TEXT,
                    refresh_token TEXT,
                    token_expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # User listening data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id INTEGER,
                    track_id TEXT,
                    track_name TEXT,
                    artist_name TEXT,
                    album_name TEXT,
                    genres TEXT,
                    audio_features TEXT,
                    play_count INTEGER DEFAULT 1,
                    last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (discord_id) REFERENCES users (discord_id),
                    UNIQUE(discord_id, track_id)
                )
            ''')
            
            # User top artists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_artists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id INTEGER,
                    artist_id TEXT,
                    artist_name TEXT,
                    genres TEXT,
                    popularity INTEGER,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (discord_id) REFERENCES users (discord_id),
                    UNIQUE(discord_id, artist_id)
                )
            ''')
            
            # Playlists created by bot
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id INTEGER,
                    spotify_playlist_id TEXT,
                    playlist_name TEXT,
                    playlist_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (discord_id) REFERENCES users (discord_id)
                )
            ''')
            
            # Command logs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS command_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id INTEGER,
                    guild_id INTEGER,
                    command_name TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN,
                    error_message TEXT
                )
            ''')
            
            conn.commit()
            self.logger.info("Database tables initialized successfully")
    
    async def save_user_tokens(self, discord_id: int, spotify_data: Dict[str, Any]):
        """Save user's Spotify tokens"""
        async with self._lock:
            await asyncio.get_event_loop().run_in_executor(
                None, self._save_user_tokens_sync, discord_id, spotify_data
            )
    
    def _save_user_tokens_sync(self, discord_id: int, spotify_data: Dict[str, Any]):
        """Synchronous version of save_user_tokens"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (discord_id, spotify_id, access_token, refresh_token, token_expires_at, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                discord_id,
                spotify_data.get('spotify_id'),
                spotify_data.get('access_token'),
                spotify_data.get('refresh_token'),
                spotify_data.get('expires_at')
            ))
            
            conn.commit()
    
    async def get_user_tokens(self, discord_id: int) -> Optional[Dict[str, Any]]:
        """Get user's Spotify tokens"""
        async with self._lock:
            return await asyncio.get_event_loop().run_in_executor(
                None, self._get_user_tokens_sync, discord_id
            )
    
    def _get_user_tokens_sync(self, discord_id: int) -> Optional[Dict[str, Any]]:
        """Synchronous version of get_user_tokens"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT spotify_id, access_token, refresh_token, token_expires_at
                FROM users WHERE discord_id = ?
            ''', (discord_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'spotify_id': row[0],
                    'access_token': row[1],
                    'refresh_token': row[2],
                    'expires_at': row[3]
                }
            return None
    
    async def save_user_tracks(self, discord_id: int, tracks: List[Dict[str, Any]]):
        """Save user's track data"""
        async with self._lock:
            await asyncio.get_event_loop().run_in_executor(
                None, self._save_user_tracks_sync, discord_id, tracks
            )
    
    def _save_user_tracks_sync(self, discord_id: int, tracks: List[Dict[str, Any]]):
        """Synchronous version of save_user_tracks"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for track in tracks:
                cursor.execute('''
                    INSERT OR REPLACE INTO user_tracks
                    (discord_id, track_id, track_name, artist_name, album_name, 
                     genres, audio_features, last_played)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    discord_id,
                    track['id'],
                    track['name'],
                    ', '.join([artist['name'] for artist in track['artists']]),
                    track['album']['name'],
                    json.dumps(track.get('genres', [])),
                    json.dumps(track.get('audio_features', {}))
                ))
            
            conn.commit()
    
    async def get_user_tracks(self, discord_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's saved tracks"""
        async with self._lock:
            return await asyncio.get_event_loop().run_in_executor(
                None, self._get_user_tracks_sync, discord_id, limit
            )
    
    def _get_user_tracks_sync(self, discord_id: int, limit: int) -> List[Dict[str, Any]]:
        """Synchronous version of get_user_tracks"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT track_id, track_name, artist_name, album_name, genres, audio_features
                FROM user_tracks WHERE discord_id = ? 
                ORDER BY last_played DESC LIMIT ?
            ''', (discord_id, limit))
            
            tracks = []
            for row in cursor.fetchall():
                tracks.append({
                    'id': row[0],
                    'name': row[1],
                    'artists': row[2],
                    'album': row[3],
                    'genres': json.loads(row[4]) if row[4] else [],
                    'audio_features': json.loads(row[5]) if row[5] else {}
                })
            
            return tracks
    
    async def save_user_artists(self, discord_id: int, artists: List[Dict[str, Any]]):
        """Save user's top artists"""
        async with self._lock:
            await asyncio.get_event_loop().run_in_executor(
                None, self._save_user_artists_sync, discord_id, artists
            )
    
    def _save_user_artists_sync(self, discord_id: int, artists: List[Dict[str, Any]]):
        """Synchronous version of save_user_artists"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for artist in artists:
                cursor.execute('''
                    INSERT OR REPLACE INTO user_artists
                    (discord_id, artist_id, artist_name, genres, popularity, last_updated)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    discord_id,
                    artist['id'],
                    artist['name'],
                    json.dumps(artist.get('genres', [])),
                    artist.get('popularity', 0)
                ))
            
            conn.commit()
    
    async def delete_user_data(self, discord_id: int):
        """Delete all user data (GDPR compliance)"""
        async with self._lock:
            await asyncio.get_event_loop().run_in_executor(
                None, self._delete_user_data_sync, discord_id
            )
    
    def _delete_user_data_sync(self, discord_id: int):
        """Synchronous version of delete_user_data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Delete from all tables
            tables = ['users', 'user_tracks', 'user_artists', 'playlists']
            for table in tables:
                cursor.execute(f'DELETE FROM {table} WHERE discord_id = ?', (discord_id,))
            
            conn.commit()
    
    async def log_command(self, discord_id: int, guild_id: int, command_name: str, 
                         success: bool, error_message: str = None):
        """Log command usage"""
        async with self._lock:
            await asyncio.get_event_loop().run_in_executor(
                None, self._log_command_sync, discord_id, guild_id, 
                command_name, success, error_message
            )
    
    def _log_command_sync(self, discord_id: int, guild_id: int, command_name: str, 
                         success: bool, error_message: str = None):
        """Synchronous version of log_command"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO command_logs
                (discord_id, guild_id, command_name, success, error_message)
                VALUES (?, ?, ?, ?, ?)
            ''', (discord_id, guild_id, command_name, success, error_message))
            
            conn.commit()
