import os
from dotenv import load_dotenv
from collections import Counter
from flask import Flask, session, redirect, request, url_for,render_template
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_COOKIE_NAME'] = 'your_session_cookie_name'

client_id = os.getenv('Client_id')
client_secret = os.getenv('Client_secret')
redirect_uri = 'https://yash-spotify-api.onrender.com/callback'
scope = 'user-library-read user-top-read user-read-private'

cache_handler = FlaskSessionCacheHandler(session)
sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    cache_handler=cache_handler,
    show_dialog=True
)

@app.route('/')
def home():
    token_info = sp_oauth.get_cached_token()
    if not token_info:
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    return redirect(url_for('callback'))

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect(url_for('button_clicked'))
    

@app.route('/button_clicked', methods=['GET','POST'])
def button_clicked():
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect('home')
    
    if sp_oauth.is_token_expired(token_info):
        token_info= sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info']= token_info
    
    sp = Spotify(auth=token_info['access_token'])
    #genre = sp.recommendation_genre_seeds()
    #print(genre)
    user = sp.current_user()
    user= user.get('display_name')
    if request.method =='POST':
        print("form recieved: ", request.form)
        button_type =request.form['button_type']
        if button_type=='recommend':
            user_choice = request.form['user_choice']
            recommendations = sp.recommendations(seed_artists=None, seed_genres=[user_choice], seed_tracks=None, limit=10)
            songs_info = [(track['name'], track['external_urls']['spotify'],track['id']) for track in recommendations['tracks']]
            return render_template('songs.html', songs=songs_info,dname = user)
        
        elif button_type=='top_tracks':
            top_tracks = sp.current_user_top_tracks(limit=10, offset=0, time_range='medium_term')
            tracks_info = [(track['name'],track['external_urls']['spotify'],track['id']) for track in top_tracks['items']]
            return render_template('songs.html', songs = tracks_info, dname = user)
        elif button_type=='top_artist':
            top_artists =sp.current_user_top_artists(limit=10, offset=0, time_range='medium_term')
            artists_info = [(artist['name'], artist['external_urls']['spotify'],None) for artist in top_artists['items']]
            return render_template('songs.html', songs = artists_info,dname = user)
    return render_template('songs.html', dname = user)


@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect(url_for('/'))

port = int(os.environ.get('PORT', 5000))


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port=port)
