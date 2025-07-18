"""
Spotify OAuth2 authentication handler
"""

import os
import logging
import secrets
import base64
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode, parse_qs, urlparse
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth

class SpotifyAuthManager:
    """Manages Spotify OAuth2 authentication"""
    
    def __init__(self):
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:5000/callback')
        
        if not all([self.client_id, self.client_secret]):
            raise ValueError("Missing Spotify credentials in environment variables")
        
        self.logger = logging.getLogger(__name__)
        self.pending_auth = {}  # Store pending auth states
        
        # Spotify API scopes
        self.scope = [
            'user-read-private',
            'user-read-email',
            'user-top-read',
            'user-read-recently-played',
            'user-library-read',
            'playlist-modify-public',
            'playlist-modify-private',
            'playlist-read-private',
            'user-follow-read'
        ]
    
    def generate_auth_url(self, discord_id: int) -> str:
        """Generate Spotify authorization URL"""
        state = secrets.token_urlsafe(32)
        self.pending_auth[state] = {
            'discord_id': discord_id,
            'timestamp': datetime.now()
        }
        
        # Clean old pending auths (older than 10 minutes)
        cutoff = datetime.now() - timedelta(minutes=10)
        self.pending_auth = {
            k: v for k, v in self.pending_auth.items() 
            if v['timestamp'] > cutoff
        }
        
        auth_params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scope),
            'state': state,
            'show_dialog': 'true'
        }
        
        return f"https://accounts.spotify.com/authorize?{urlencode(auth_params)}"
    
    async def handle_callback(self, code: str, state: str) -> Optional[Dict[str, Any]]:
        """Handle OAuth callback"""
        # Verify state
        if state not in self.pending_auth:
            self.logger.error(f"Invalid state parameter: {state}")
            return None
        
        discord_id = self.pending_auth[state]['discord_id']
        del self.pending_auth[state]
        
        try:
            # Exchange code for tokens
            tokens = await self._exchange_code_for_tokens(code)
            if not tokens:
                return None
            
            # Get user info
            user_info = await self._get_user_info(tokens['access_token'])
            if not user_info:
                return None
            
            return {
                'discord_id': discord_id,
                'spotify_id': user_info['id'],
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token'],
                'expires_at': tokens['expires_at'],
                'user_info': user_info
            }
            
        except Exception as e:
            self.logger.error(f"Error handling OAuth callback: {e}")
            return None
    
    async def _exchange_code_for_tokens(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access tokens"""
        token_url = "https://accounts.spotify.com/api/token"
        
        # Prepare authorization header
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_str.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        
        try:
            response = requests.post(token_url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            
            # Calculate expiry time
            expires_in = token_data.get('expires_in', 3600)
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            return {
                'access_token': token_data['access_token'],
                'refresh_token': token_data['refresh_token'],
                'expires_at': expires_at.isoformat()
            }
            
        except requests.RequestException as e:
            self.logger.error(f"Error exchanging code for tokens: {e}")
            return None
    
    async def _get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get Spotify user information"""
        headers = {'Authorization': f'Bearer {access_token}'}
        
        try:
            response = requests.get(
                'https://api.spotify.com/v1/me',
                headers=headers
            )
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            self.logger.error(f"Error getting user info: {e}")
            return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token"""
        token_url = "https://accounts.spotify.com/api/token"
        
        # Prepare authorization header
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_str.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        try:
            response = requests.post(token_url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            
            # Calculate expiry time
            expires_in = token_data.get('expires_in', 3600)
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            return {
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token', refresh_token),
                'expires_at': expires_at.isoformat()
            }
            
        except requests.RequestException as e:
            self.logger.error(f"Error refreshing token: {e}")
            return None
    
    def get_spotify_client(self, access_token: str) -> Optional[spotipy.Spotify]:
        """Get authenticated Spotify client"""
        try:
            return spotipy.Spotify(auth=access_token)
        except Exception as e:
            self.logger.error(f"Error creating Spotify client: {e}")
            return None
    
    async def get_user_top_tracks(self, access_token: str, time_range: str = 'medium_term', 
                                 limit: int = 50) -> Optional[List[Dict[str, Any]]]:
        """Get user's top tracks"""
        client = self.get_spotify_client(access_token)
        if not client:
            return None
        
        try:
            results = client.current_user_top_tracks(
                time_range=time_range,
                limit=limit
            )
            return results['items']
        except Exception as e:
            self.logger.error(f"Error getting top tracks: {e}")
            return None
    
    async def get_user_top_artists(self, access_token: str, time_range: str = 'medium_term',
                                  limit: int = 50) -> Optional[List[Dict[str, Any]]]:
        """Get user's top artists"""
        client = self.get_spotify_client(access_token)
        if not client:
            return None
        
        try:
            results = client.current_user_top_artists(
                time_range=time_range,
                limit=limit
            )
            return results['items']
        except Exception as e:
            self.logger.error(f"Error getting top artists: {e}")
            return None
    
    async def get_audio_features(self, access_token: str, track_ids: List[str]) -> Optional[List[Dict[str, Any]]]:
        """Get audio features for tracks"""
        client = self.get_spotify_client(access_token)
        if not client:
            return None
        
        try:
            # Spotify API limits to 100 tracks per request
            all_features = []
            for i in range(0, len(track_ids), 100):
                batch = track_ids[i:i+100]
                features = client.audio_features(batch)
                all_features.extend(features)
            return all_features
        except Exception as e:
            self.logger.error(f"Error getting audio features: {e}")
            return None
    
    async def create_playlist(self, access_token: str, user_id: str, name: str, 
                             description: str, track_uris: List[str]) -> Optional[Dict[str, Any]]:
        """Create a playlist for the user"""
        client = self.get_spotify_client(access_token)
        if not client:
            return None
        
        try:
            # Create playlist
            playlist = client.user_playlist_create(
                user=user_id,
                name=name,
                description=description,
                public=False
            )
            
            # Add tracks to playlist
            if track_uris:
                # Spotify API limits to 100 tracks per request
                for i in range(0, len(track_uris), 100):
                    batch = track_uris[i:i+100]
                    client.playlist_add_items(playlist['id'], batch)
            
            return playlist
            
        except Exception as e:
            self.logger.error(f"Error creating playlist: {e}")
            return None
