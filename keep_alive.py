"""
Keep-alive web server for Replit deployment
"""

import os
import logging
from threading import Thread
from flask import Flask, request, redirect, jsonify

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Initialize Spotify auth manager (will be set later)
spotify_auth = None

def set_spotify_auth(auth_manager):
    """Set Spotify auth manager"""
    global spotify_auth
    spotify_auth = auth_manager

# Store bot instance reference
bot_instance = None

def set_bot_instance(bot):
    """Set bot instance for use in web routes"""
    global bot_instance
    bot_instance = bot

@app.route('/')
def home():
    """Home route"""
    return jsonify({
        'status': 'online',
        'message': 'Discord Music Bot is running!',
        'bot_connected': bot_instance.is_ready() if bot_instance else False
    })

@app.route('/callback')
def spotify_callback():
    """Handle Spotify OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        logging.error(f"Spotify OAuth error: {error}")
        return f"""
        <html>
            <body>
                <h1>Authorization Failed</h1>
                <p>Error: {error}</p>
                <p>Please try connecting your Spotify account again.</p>
            </body>
        </html>
        """, 400
    
    if not code or not state:
        return f"""
        <html>
            <body>
                <h1>Authorization Failed</h1>
                <p>Missing authorization code or state parameter.</p>
                <p>Please try connecting your Spotify account again.</p>
            </body>
        </html>
        """, 400
    
    if not spotify_auth:
        return f"""
        <html>
            <body>
                <h1>Service Not Ready</h1>
                <p>Spotify authentication service is not initialized yet.</p>
                <p>Please try again in a moment.</p>
            </body>
        </html>
        """, 503
    
    # Handle the callback
    try:
        import asyncio
        
        # Run async callback in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(spotify_auth.handle_callback(code, state))
        
        if result and bot_instance:
            # Save user tokens to database
            loop.run_until_complete(bot_instance.db.save_user_tokens(
                result['discord_id'],
                {
                    'spotify_id': result['spotify_id'],
                    'access_token': result['access_token'],
                    'refresh_token': result['refresh_token'],
                    'expires_at': result['expires_at']
                }
            ))
        loop.close()
        
        if result:
            return f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }}
                        .success {{ color: #28a745; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1 class="success">Success!</h1>
                        <p>Your Spotify account has been successfully connected!</p>
                        <p>You can now close this window and return to Discord.</p>
                        <p>Try using the <code>/recommend</code> command to get started!</p>
                    </div>
                </body>
            </html>
            """
        else:
            return f"""
            <html>
                <body>
                    <h1>Authorization Failed</h1>
                    <p>Failed to process your Spotify authorization.</p>
                    <p>Please try connecting your Spotify account again.</p>
                </body>
            </html>
            """, 500
            
    except Exception as e:
        logging.error(f"Error processing Spotify callback: {e}")
        return f"""
        <html>
            <body>
                <h1>Authorization Failed</h1>
                <p>An error occurred while processing your authorization.</p>
                <p>Please try connecting your Spotify account again.</p>
            </body>
        </html>
        """, 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })

def run():
    """Run the Flask server"""
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def keep_alive():
    """Start the keep-alive server in a separate thread"""
    server = Thread(target=run)
    server.daemon = True
    server.start()
    
    logging.info(f"Keep-alive server started on port {os.getenv('PORT', 5000)}")