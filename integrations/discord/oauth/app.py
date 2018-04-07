import state.storage
import local_config

import os
from flask import Flask, session, redirect, request, url_for, jsonify
from requests_oauthlib import OAuth2Session
from werkzeug.exceptions import HTTPException

OAUTH2_CLIENT_ID = local_config.DISCORD_BOT_CLIENT_ID
OAUTH2_CLIENT_SECRET = local_config.DISCORD_BOT_CLIENT_SECRET
OAUTH2_REDIRECT_URI = 'http://localhost:5005/dota_stalker_callback'

API_BASE_URL = os.environ.get('API_BASE_URL', 'https://discordapp.com/api')
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'

app = Flask(__name__)
app.debug = False
app.config['SECRET_KEY'] = OAUTH2_CLIENT_SECRET

if 'http://' in OAUTH2_REDIRECT_URI:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'


def token_updater(token):
    session['oauth2_token'] = token


class SteamNotConnected(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=OAUTH2_CLIENT_ID,
        token=token,
        state=state,
        scope=scope,
        redirect_uri=OAUTH2_REDIRECT_URI,
        auto_refresh_kwargs={
            'client_id': OAUTH2_CLIENT_ID,
            'client_secret': OAUTH2_CLIENT_SECRET,
        },
        auto_refresh_url=TOKEN_URL,
        token_updater=token_updater)


@app.route('/dota_stalker_add')
def index():
    discord = make_session(scope='connections')
    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth2_state'] = state
    return redirect(authorization_url)


@app.route('/dota_stalker_callback')
def callback():
    print("DEBUG: in callback")
    if request.values.get('error'):
        print("ERROR: there was an error in the request")
        return request.values['error']

    discord = make_session(state=session.get('oauth2_state'))
    token = discord.fetch_token(
        TOKEN_URL,
        client_secret=OAUTH2_CLIENT_SECRET,
        authorization_response=request.url)
    session['oauth2_token'] = token
    connections = discord.get(API_BASE_URL + '/users/@me/connections').json()
    user = discord.get(API_BASE_URL + '/users/@me').json()
    steam_id = None # base64 steam ID
    print("DEBUG: about to check %d connections", len(connections))
    for connection in connections:
        if connection['type'] == 'steam':
            steam_id = connection['id']
            print("DEBUG: got steam ID!")
            break
    if steam_id is None:
        print("!!! no steam account connected for user %s" % user)
        raise SteamNotConnected(message="no steam account connected for user %s" % user)

    state.storage.steam_ids[user['id']] = steam_id
    print("DEBUG: successfully stored steam ID %s for user %s" % (steam_id, user))
    return redirect(url_for('.steam_id_success'))


@app.route('/steam_id_success')
def steam_id_success():
    return jsonify(message="Successfully added your steam ID")


@app.errorhandler(SteamNotConnected)
def handle_steam_not_connected(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(Exception)
def oops(error):
    response = jsonify(
        error="Sorry, something went wrong, probably because I'm bad and everything is hacky.  Message me!")
    if isinstance(error, HTTPException):
        response.status_code = error.code
    else:
        response.status_code = 500
    return response


def run_steam_id_getter():
    app.run(port=5005)
