import streamlit as st
import pandas as pd
from semantly import similarity

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

# Read game configurations from CSV
game_configurations = pd.read_csv('game_configurations.csv')

# Get URL parameters
query_params = st.query_params
version = query_params.get('version', [1])[0]

# Set default line to read from the CSV
config = game_configurations[game_configurations['version'] == int(version)].iloc[0]

# Extract game configuration
secret_word = config['secret_word']
preset_guesses = config['preset_guesses'].split(',')
max_guesses = int(config['max_guesses'])

# Initialize the session state for guesses and the secret word
if 'user_guesses' not in st.session_state:
    st.session_state.user_guesses = []

if 'secret_word' not in st.session_state:
    st.session_state.secret_word = secret_word

# Preset initial guesses
preset_guesses_scores = [{'Guess': word, 'Similarity': f"{round(similarity(word, st.session_state.secret_word) * 100, 0):.0f}%"} for word in preset_guesses]
preset_guesses_scores = sorted(preset_guesses_scores, key=lambda x: float(x['Similarity'][:-1]), reverse=True)

# Function to add a user guess
def add_user_guess(guess, score):
    st.session_state.user_guesses.append({'Guess': guess, 'Similarity': f"{round(score * 100, 0):.0f}%"})
    st.session_state.user_guesses = sorted(st.session_state.user_guesses, key=lambda x: float(x['Similarity'][:-1]), reverse=True)

# Manage the state of the text input field
if 'my_guess' not in st.session_state:
    st.session_state.my_guess = ""

def submit():
    st.session_state.my_guess = st.session_state.widget
    st.session_state.widget = ""

# Display the table of preset guesses
st.write("### Hints:")
st.table(preset_guesses_scores)

# Check if the user has remaining guesses
if len(st.session_state.user_guesses) < (max_guesses):
    # User input for guessing with submit functionality
    st.text_input("Enter your guess:", key="widget", on_change=submit)

    guess = st.session_state.my_guess

    if guess:
        st.write("### Number of guesses remaining:")
        st.write(max_guesses - len(st.session_state.user_guesses) - 1)
        score = similarity(guess, st.session_state.secret_word)
        add_user_guess(guess, score)

        if score > 0.95:  # Set a threshold for winning
            st.write("🎉 You found the secret word!")
            st.stop()

        # Clear the input field after submission
        st.session_state.my_guess = ""
else:
    st.write("Game Over! You've reached the maximum number of guesses.") 
    st.write(f"We were looking for the word: {st.session_state.secret_word}")

# Display the table of user guesses
if st.session_state.user_guesses:
    st.write("### Your guesses:")
    st.table(st.session_state.user_guesses)