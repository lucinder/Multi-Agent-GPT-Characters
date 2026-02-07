# Multi Agent GPT Characters
Web app that allows up to 3 GPT characters and a human to talk to each other.  
Original written by DougDoug, updated to be fully FOSS-dependent and require no API calls by lucinder.

## SETUP:
1) Originally written in Python 3.9.2, verified compatible with up to Python 3.13.

2) Run `pip install -r requirements.txt` to install all modules. For pytorch and torchaudio, you MUST separately install a CUDA-compatible torch version, e.g. via `pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124` (for CUDA 12.4). Refer to https://github.com/eminsafa/pytorch-cuda-compatibility.

3) This uses Ollama for local chat AI (preferring the deepseek-r1:8b model) and pyttsx3 for local text-to-speech (TTS). Make sure you have Ollama installed and running, and a model of your choice pulled. I use deepseek-r1:8b, e.g. (run `ollama pull deepseek-r1:8b`).

4) TTS is handled locally using PyWin32's SAPI.SpVoice engine. You can select a voice available on your system by passing its name into each agent's init function in multi_agent_gpt.py. No ElevenLabs account or API key is required.

5) This app uses the open source Whisper model from OpenAi for transcribing audio into text. This means you'll be running an AI model locally on your PC, so ideally you have an Nvidia GPU to run this. This model was downloaded from Huggingface and should install automatically when you run the whisper_openai.py file. To switch to using text input, simply turn off the MICROPHONE_ENABLED flag in OPTIONS.json.

6) This code runs a Flask web app and will eventually display the agents' dialogue using HTML and javascript. The functionality of this is not fully verified with the current setup, and as such, most of the code related to dialogue display is commented out; I intend to re-implement this in the future. By default the Flask app will run the server on "127.0.0.1:5151", but you can change this in OPTIONS.json.

7) To be implemented: Optionally, you can use OBS Websockets and an OBS plugin to make images move while talking (requires OBS 28.X or later). See [the original repo](https://github.com/DougDougGithub/Multi-Agent-GPT-Characters) for instructions on setting up OBS websockets.

## Using the App

To start out, edit the prompts (AGENT_1_PROMPT.txt, AGENT_2_PROMPT.txt, etc.) in the prompts folder to design each agent's personality and the purpose of their conversation.  
By default the characters are told to discuss the greatest videogames of all time, but you can change this to anything you want. You can also change the preferred local model in OPTIONS.json, under MODEL_NAME.

Next run multi_agent_gpt.py

Once it's running you now have a number of options:

__Press Numpad7 to "talk" to the agents.__  
Numpad7 will start recording your microphone audio. Hit Numpad8 to stop recording. It will then transcribe your audio into text and add your dialogue into all 3 agents' chat history. Then it will pick a random agent to "activate" and have them start talking next.

__Numpad1 will "activate" Agent #1.__  
This means that agent will continue the conversation and start talking. Unless it has been "paused", it will also pick a random other agent and "activate" them to talk next, so that the conversation continues indefinitely.

__Numpad2 will "activate" Agent #2, Numpad3 will "activate" Agent #3.__

__F4 will "pause" all agents__   
This stops the agents from activating each other. Basically, use this to stop the conversation from continuing any further, and then you can talk to the agents again.

__Numpad9 will forcibly stop the app__
This ends all agent threads and the input thread, and defers to the main thread to shut down the Flask app. Conversation history stored in backup files will be maintained if the app is re-run.

## Miscellaneous notes:

All agents will automatically store their "chat history" into a backup txt file as the conversation continues. This is done so that when you restart the program, each agent will automatically load from their backup file and thus restore the entire conversation, letting you continue it from where you left off. If you ever want to fully reset the conversation then just delete the backup txt files in the project.

If you want to have the agent dialogue displayed in OBS, you should add a browser source and set the URL to "127.0.0.1:5151". 
