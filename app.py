import json
import streamlit as st
import pandas as pd
import requests
import websockets
import asyncio
import threading
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.title('Semantly')

# Explanation text
st.write("""
### How to Play
Your goal is to guess the secret word.

**How It Works:**
- Each guess you make will receive a score showing how close it is to the secret word. 
- The score is shown as a percentage. The higher the percentage, the closer your guess is to the secret word.
- Use the hints to guide your guesses.

**Good Luck!**
""")

# Get URL parameters
query_params = st.query_params
game_code = query_params.get('code', [None])
player_name = query_params.get('player', [None])

# API settings
api_url = "https://semantlyapi-352e1ba2b5fd.herokuapp.com"
api_key = st.secrets["api_key"]
headers = {"x-api-key": api_key}

if not game_code or not player_name:
    st.error("Game code and player name must be provided as URL parameters.")
    st.stop()

# Fetch game configuration from the API
response = requests.get(f"{api_url}/game/{game_code}", headers=headers)
if response.status_code != 200:
    st.error("Error fetching game configuration.")
    st.stop()

game_config = response.json()

secret_word = game_config['secret_word']
preset_guesses = game_config['preset_guesses']
max_guesses = game_config['max_guesses']

# Initialize the session state for guesses and the secret word
if 'user_guesses' not in st.session_state:
    st.session_state.user_guesses = []

if 'secret_word' not in st.session_state:
    st.session_state.secret_word = secret_word

# Fetch current user guesses
response = requests.get(f"{api_url}/game/{game_code}/guesses", headers=headers)
if response.status_code == 200:
    st.session_state.user_guesses = response.json()["user_guesses"]

# Function to add a user guess
def add_user_guess(guess, score):
    st.session_state.user_guesses.append({'player': player_name, 'Guess': guess, 'score': score})
    st.session_state.user_guesses = sorted(st.session_state.user_guesses, key=lambda x: float(x['score']), reverse=True)

# WebSocket listener
def listen_for_updates():
    logger.info("Starting WebSocket listener thread.")
    async def websocket_listener():
        try:
            async with websockets.connect(f"wss://semantlyapi-352e1ba2b5fd.herokuapp.com/ws/{game_code}") as websocket:
                logger.info("WebSocket connection established.")
                while True:
                    message = await websocket.recv()
                    logger.info(f"Received message: {message}")
                    game_data = json.loads(message)
                    st.session_state.user_guesses = game_data['user_guesses']
                    st.experimental_rerun()
        except Exception as e:
            logger.error(f"Error in WebSocket connection: {e}")
    asyncio.run(websocket_listener())

# Start WebSocket listener in a separate thread
thread = threading.Thread(target=listen_for_updates)
thread.start()

st.write("Made it here! 3")

# Manage the state of the text input field
if 'my_guess' not in st.session_state:
    st.session_state.my_guess = ""

def submit():
    st.session_state.my_guess = st.session_state.widget
    st.session_state.widget = ""

# Display the table of preset guesses
st.write("### Hints:")
st.table(preset_guesses)

# Display the table of user guesses
st.write("### All Guesses:")
st.table(st.session_state.user_guesses)

# Ensure all players have the maximum number of guesses by default
player_guess_count = {player: 0 for player in game_config['players']}
for guess in st.session_state.user_guesses:
    player_guess_count[guess['player']] += 1

remaining_guesses = {player: max_guesses - count for player, count in player_guess_count.items()}

st.write("### Remaining Guesses:")
st.table(pd.DataFrame(remaining_guesses.items(), columns=['Player', 'Remaining Guesses']))

# Check if the user has remaining guesses
if player_name not in remaining_guesses or remaining_guesses[player_name] <= 0:
    st.write("You have no guesses left.")
elif all(count <= 0 for count in remaining_guesses.values()):
    st.write("Game Over! All players have used their guesses.")
else:
    # User input for guessing with submit functionality
    st.text_input("Enter your guess:", key="widget", on_change=submit)

    guess = st.session_state.my_guess

    if guess:
        response = requests.post(f"{api_url}/game/{game_code}/guess", json={"player": player_name, "guess": guess}, headers=headers)
        if response.status_code == 200:
            #score = response.json()["game"]["user_guesses"]["score"]
            score = 0.55
            add_user_guess(guess, score)

            if float(score) > 95.0:  # Set a threshold for winning
                st.write("🎉 You found the secret word!")
                st.stop()

            # Clear the input field after submission
            st.session_state.my_guess = ""
        else:
            st.write("Error adding guess. Please try again.")