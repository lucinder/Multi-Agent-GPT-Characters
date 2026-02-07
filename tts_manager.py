import win32com.client, pythoncom
import time
import os, json
# Private global DEBUG flag inherited from OPTIONS.json
_options_path = os.path.join(os.path.dirname(__file__), "OPTIONS.json")
__DEBUG = False
try:
    with open(_options_path, "r") as _f:
        _options = json.load(_f)
    __DEBUG = _options.get("DEBUG", False)
except Exception:
    pass


class TTSManager:

    def __init__(self):
        self.engine = win32com.client.Dispatch('SAPI.SpVoice')
        self.voices = self.engine.GetVoices()
        self.voice_name_to_voices = {v.GetDescription(): v for v in self.voices}

    # Convert text to speech, then save it to file. Returns the file path.
    def text_to_audio(self, input_text : str, voice=None, save_as_wave=True, subdirectory=""):
        if input_text == "":
            print("[bold red]ERROR: No text provided for TTS!")
            return None
        pythoncom.CoInitialize()
        try:
            # voice: name of the voice to use (if available)
            # save_as_wave: if True, saves as .wav, else .mp3 (pyttsx3 only supports .wav natively)
            if voice and voice in self.voice_name_to_voices:
                # self.engine.setProperty('voice', self.voice_name_to_id[voice])
                self.engine.Voice = self.voice_name_to_voices[voice]
            else:
                # Use default voice
                self.engine.Voice = self.voices[0]

            file_ext = ".wav" if save_as_wave else ".dat"
            file_name = f"___Msg{str(hash(input_text))}{time.time()}_tts{file_ext}"
            tts_file = os.path.join(os.path.abspath(os.curdir), subdirectory, file_name)

            # Save to file
            stream = win32com.client.Dispatch("SAPI.SpFileStream")
            stream.Open(tts_file, 3)
            self.engine.AudioOutputStream = stream
            self.engine.Speak(input_text, 0)
            stream.Close()
        finally:
            pythoncom.CoUninitialize()
        return tts_file