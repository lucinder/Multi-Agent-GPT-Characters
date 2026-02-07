# This code runs a thread that manages the frontend code, a thread that listens for keyboard presses from the human, and then threads for the 3 agents
# Once running, the human can activate a single agent and then let the agents continue an ongoing conversation.
# Each thread has the following core logic:

# Main Thread
    # Runs the web app

# Agent X
    # Waits to be activated
    # Once it is activated (by Doug or by another agent):
        # Acquire conversation lock
            # Get response from the AI
            # Add this new response to all other agents' chat histories
        # Creates TTS with ElevenLabs
        # Acquire speaking lock (so only 1 speaks at a time)
            # Pick another thread randomly, activate them
                # Because this happens within the speaking lock, we are guaranteed that the other agents are inactive when this called.
                # But, we start this now so that the next speaker can have their answer and audio ready to go the instant this agent is done talking.
            # Update client and OBS to display stuff
            # Play the TTS audio
            # Release speaking lock (Other threads can now talk)
    
# Human Input Thread
    # Listens for keypresses:

    # If 7 is pressed:
        # Toggles "pause" flag - stops other agents from activating additional agents

        # Record mic audio (until you press 8)

        # Get convo lock (but not speaking lock)
            # In theory, wait until everyone is done speaking, and because the agents are "paused" then no new ones will add to the convo
            # But to be safe, grab the convo lock to ensure that all agents HAVE to wait until my response is added into the convo history
        
        # Transcribe mic audio into text with Whisper
        # Add Doug's response into all agents' chat history
        
        # Release the convo lock
        # (then optionally press a key to trigger a specific bot)

    # If F4 pressed:
        # Toggles "pause" flag - stops all other agents from activating additional agents
    
    # If Numpad 1, 2, 3, 4, 5, or 6 pressed:
        # Turns off "pause" flag
        # Activates Agent of that #

    # If 9 pressed:
        # Sets shutdown event, which all threads are listening for, to end the program

from flask import Flask, render_template, session, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import time
import keyboard
import random
import logging, signal
import os, sys, json
from rich import print

from audio_player import AudioManager
from tts_manager import TTSManager
from ollama_chat import OllamaManager
from whisper_openai import WhisperManager
# from obs_websockets import OBSWebsocketsManager
from ai_prompts import *
import requests as _requests

# Private global DEBUG flag inherited from OPTIONS.json
_options_path = os.path.join(os.path.dirname(__file__), "OPTIONS.json")
options = {}
DEBUG = False
# Optional features that can be toggled on and off in OPTIONS.json, but are disabled by default for simplicity. These features are:
OBS_ENABLED = False
TTS_ENABLED = False
MICROPHONE_ENABLED = False
AGENTS_SPEAK_AUTOMATICALLY = False
try:
    with open(_options_path, "r") as _f:
        options = json.load(_f)
    DEBUG = options.get("DEBUG", False)
    OBS_ENABLED = options.get("OBS_WEBSOCKETS_ENABLED", False)
    TTS_ENABLED = options.get("TTS_ENABLED", False)
    MICROPHONE_ENABLED = options.get("MICROPHONE_ENABLED", False)
    AGENTS_SPEAK_AUTOMATICALLY = options.get("AGENTS_SPEAK_AUTOMATICALLY", False)
except Exception:
    pass

# --- OLLAMA API PROXY ENDPOINT ---
OLLAMA_HOST = options.get("WEBSOCKET_HOST", "127.0.0.1")
OLLAMA_PORT = options.get("OLLAMA_PORT", 11434)
OLLAMA_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/chat"

socketio = SocketIO
app = Flask(__name__)
FLASK_PORT = options.get("FLASK_PORT", 5000)
FLASK_SERVER_NAME = f"{OLLAMA_HOST}:{FLASK_PORT}"
app.config['SERVER_NAME'] = FLASK_SERVER_NAME
socketio = SocketIO(app, async_mode="threading")


log = logging.getLogger('werkzeug') # Sets flask app to only print error messages, rather than all info logs
log.setLevel(logging.ERROR)


# Global shutdown event for all threads
shutdown_event = threading.Event()

@app.route("/")
def home():
    return render_template('index.html')

@socketio.event
def connect():
    print("[green]The server connected to client!")

# OBSWS is deactivated for now
# obswebsockets_manager = OBSWebsocketsManager()
whisper_manager = WhisperManager()
tts_manager = TTSManager()
audio_manager = AudioManager()

speaking_lock = threading.Lock()
conversation_lock = threading.Lock()

def _acquire_lock_or_shutdown(lock, poll_interval=0.5):
    """Try to acquire a lock, but give up if shutdown_event is set. Returns True if lock acquired, False if shutting down."""
    while not shutdown_event.is_set():
        if lock.acquire(timeout=poll_interval):
            return True
    return False

agents_paused = False

# Class that represents a single ChatGPT Agent and its information
class Agent():
    
    def __init__(self, agent_name, agent_id, filter_name, all_agents, system_prompt, tts_voice):
        # Flag of whether this agent should begin speaking
        self.activated = False 
        # Used to identify each agent in the conversation history
        self.name = agent_name 
        # an int used to ID this agent to the frontend code
        self.agent_id = agent_id 
        # the name of the OBS filter to activate when this agent is speaking
        # You don't need to use OBS filters as part of this code, it's optional for adding extra visual flair
        self.filter_name = filter_name 
        # A list of the other agents, so that you can pick one to randomly "activate" when you finish talking
        self.all_agents = all_agents
        # The name of the Elevenlabs voice that you want this agent to speak with
        self.voice = tts_voice
        # The name of the txt backup file where this agent's conversation history will be stored
        backup_file_name = f"backup/backup_history_{agent_name}.txt"
        # Initialize the Ai manager with a system prompt and a file that you would like to save your conversation too
        # If the backup file isn't empty, then it will restore that backed up conversation for this agent
        self.ai_manager = OllamaManager(system_prompt, backup_file_name)
        # Optional - tells the nAi manager not to print as much
        self.ai_manager.logging = False

    def run(self):
        while True:
            if shutdown_event.is_set():
                break
            # Wait until we've been activated
            if not self.activated:
                time.sleep(0.1)
                continue
            self.activated = False
            print(f"[italic purple] {self.name} has STARTED speaking.")
            # This lock isn't necessary in theory, but for safety we will require this lock whenever updating any agent's convo history
            if not _acquire_lock_or_shutdown(conversation_lock):
                break
            try:
                # Generate a response to the conversation
                ai_answer = self.ai_manager.chat_with_history("Okay what is your response? Try to be as chaotic and bizarre and adult-humor oriented as possible. Again, 3 sentences maximum.")
                ai_answer = ai_answer.replace("*", "")
                print(f'[magenta]Got the following response:\n{ai_answer}')
                # Add your new response into everyone else's chat history, then have them save their chat history
                # This agent's responses are marked as "assistant" role to itself, so everyone elses messages are "user" role.
                for agent in self.all_agents:
                    if agent is not self:
                        agent.ai_manager.chat_history.append({"role": "user", "content": f"[{self.name}] {ai_answer}"})
                        agent.ai_manager.save_chat_to_backup()
            finally:
                conversation_lock.release()
            if TTS_ENABLED:
                # Create audio response
                tts_file = tts_manager.text_to_audio(ai_answer, self.voice, False)

                # Process the audio to get subtitles (DISABLED)
                # audio_and_timestamps = whisper_manager.audio_to_text(tts_file, "sentence")

            # Wait here until the current speaker is finished
            if not _acquire_lock_or_shutdown(speaking_lock):
                break
            try:
                # If we're "paused", then simply finish speaking without activating another agent
                # Likewise if AGENTS_SPEAK_AUTOMATICALLY is disabled
                # Otherwise, pick another agent randomly, then activate it
                if (not agents_paused) and AGENTS_SPEAK_AUTOMATICALLY:
                    other_agents = [agent for agent in self.all_agents if agent is not self]
                    random_agent = random.choice(other_agents)
                    random_agent.activated = True
                # Activate move filter on the image (DISABLED)
                # obswebsockets_manager.set_filter_visibility("Line In", self.filter_name, True)
                if TTS_ENABLED:
                    # Play the TTS audio (without pausing)
                    audio_manager.play_audio(tts_file, sleep_during_playback=False, delete_file=True, play_using_music=True)

                    # While the audio is playing, display each sentence on the front-end (DISABLED)
                    # Each dictionary will look like: {'text': 'here is my speech', 'start_time': 11.58, 'end_time': 14.74}
                    '''
                    socketio.emit('start_agent', {'agent_id': self.agent_id})
                    try:
                        for i in range(len(audio_and_timestamps)):
                            current_sentence = audio_and_timestamps[i]
                            duration = current_sentence['end_time'] - current_sentence['start_time']
                            socketio.emit('agent_message', {'agent_id': self.agent_id, 'text': f"{current_sentence['text']}"})
                            time.sleep(duration)
                            # If this is not the final sentence, sleep for the gap of time inbetween this sentence and the next one starting
                            if i < (len(audio_and_timestamps) - 1):
                                time_between_sentences = audio_and_timestamps[i+1]['start_time'] - current_sentence['end_time']
                                time.sleep(time_between_sentences)
                    except Exception:
                        print(f"[magenta] Whoopsie! There was a problem and I don't know why. This was the current_sentence it broke on: {current_sentence}")
                    socketio.emit('clear_agent', {'agent_id': self.agent_id})
                    '''
                time.sleep(1) # Wait one second before the next person talks, otherwise their audio gets cut off

                # Turn off the filter in OBS (DISABLED)
                # obswebsockets_manager.set_filter_visibility("Line In", self.filter_name, False)
            finally:
                speaking_lock.release()
            print(f"[italic purple] {self.name} has FINISHED speaking.")


# Class that handles human input, this thread is how you can manually activate or pause the other agents
class Human():
    
    def __init__(self, name, all_agents):
        self.name = name # This will be added to the beginning of the response
        self.all_agents = all_agents
        self.agent_count = len(all_agents)

    def run(self):
        global agents_paused, MICROPHONE_ENABLED
        while True:
            if shutdown_event.is_set():
                break

            # Force shutdown
            if keyboard.is_pressed('num 9'):
                print("[bold red] Shutdown requested. Exiting all threads...")
                os.kill(os.getpid(), signal.SIGINT)
                shutdown_event.set()
                break

            # Speak into mic and add the dialogue to the chat history
            if keyboard.is_pressed('num 7'):
                try:
                    # Toggles "pause" flag - stops other agents from activating additional agents
                    agents_paused = True
                    print(f"[italic red] Agents have been paused")

                    # Record mic audio from human (until they press '=')
                    print(f"[italic green] {self.name} has STARTED speaking.")
                    mic_audio = None
                    text_input = None
                    if MICROPHONE_ENABLED:
                        mic_audio = audio_manager.record_audio(end_recording_key='num 8')
                    else:
                        text_input = input("Enter your message for the agents: ")

                    if not _acquire_lock_or_shutdown(conversation_lock):
                        break
                    try:
                        if MICROPHONE_ENABLED:
                            # Transcribe mic audio into text with Whisper
                            message = whisper_manager.audio_to_text(mic_audio)
                        else:
                            message = text_input
                        print(f"[teal]Got the following text from {self.name}:\n{message}")
                        # Add human's response into all agents chat history
                        for agent in self.all_agents:
                            agent.ai_manager.chat_history.append({"role": "user", "content": f"[{self.name}] {message}"})
                            agent.ai_manager.save_chat_to_backup() # Tell the other agents to save their chat history to their backup file
                    finally:
                        conversation_lock.release()
                    
                    print(f"[italic magenta] {self.name} has FINISHED speaking.")

                    # Activate another agent randomly
                    if AGENTS_SPEAK_AUTOMATICALLY:
                        agents_paused = False
                        random_agent = random.randint(0, len(self.all_agents)-1)
                        print(f"[cyan]Activating Agent {random_agent+1}")
                        self.all_agents[random_agent].activated = True
                except Exception as e:
                    print("[bold red] Exception in human thread. Exiting all threads...")
                    shutdown_event.set()
                    break
            
            # "Pause" the other agents.
            # Whoever is currently speaking will finish, but no future agents will be activated
            if keyboard.is_pressed('f4'):
                print("[italic red] Agents have been paused")
                agents_paused = True
                time.sleep(1) # Wait for a bit to ensure you don't press this twice in a row
            
            for idx in range(self.agent_count):
                agent_number = idx + 1
                # Activate Agent N
                if keyboard.is_pressed('num {agent_number}') and self.agent_count >= agent_number:
                    print("[cyan]Activating Agent {agent_number}")
                    agents_paused = False
                    self.all_agents[idx].activated = True
                    time.sleep(1) # Wait for a bit to ensure you don't press this twice in a row
                    
            time.sleep(0.05)
                


def start_bot(bot):
    try:
        bot.run()
    except Exception as e:
        import traceback
        print(f"[bold red] Exception in {getattr(bot, 'name', repr(bot))} thread: {e}")
        traceback.print_exc()
        # Optionally, set shutdown_event if you want all threads to stop on any bot failure
        # shutdown_event.set()

if __name__ == '__main__':

    # Read agent and human names from OPTIONS.json
    agent_names = options.get("AGENT_NAMES", ["Agent1", "Agent2", "Agent3"])
    human_name = options.get("HUMAN_SPEAKER_NAME", "Human")

    all_agents = []
    agent_prompts = [AGENT_1, AGENT_2, AGENT_3]
    agent_voices = ["Microsoft David Desktop - English (United States)", \
                    "Microsoft Mark Desktop - English (United States)", \
                    "Microsoft Zira Desktop - English (United States)"]
    agent_filters = ["Audio Move - Wario Pepper", "Audio Move - Waluigi Pepper", "Audio Move - Gamer Pepper"]

    try:
        for idx, name in enumerate(agent_names):
            agent = Agent(
                name,
                idx + 1,
                agent_filters[idx] if idx < len(agent_filters) else f"Filter{idx+1}",
                all_agents,
                agent_prompts[idx] if idx < len(agent_prompts) else "",
                agent_voices[idx] if idx < len(agent_voices) else name
            )
            all_agents.append(agent)
            thread = threading.Thread(target=start_bot, args=(agent,), daemon=True)
            thread.start()

        # Human thread
        human = Human(human_name, all_agents)
        human_thread = threading.Thread(target=start_bot, args=(human,), daemon=True)
        human_thread.start()

        print(f"[italic green]!!AGENTS ARE READY TO GO!!\nPress Num 1, Num 2, or Num3 to activate an agent.\nPress F7 to speak to the agents.")

        socketio.run(app)

        print("[bold red] Program shutdown complete.")
        sys.exit(0)
    except KeyboardInterrupt:
        print("[bold red] KeyboardInterrupt received. Shutting down...")
        shutdown_event.set()
    finally:
        print("[bold red] Program shutdown complete.")
        os._exit(0)