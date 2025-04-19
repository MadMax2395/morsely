# morsely 🚀🔡↔️📡

morsely is a simple yet powerful Python library that allows easy 
conversion between Morse code and alphanumeric text. 
It also supports decoding `.wav` audio files containing Morse signals! 🎵↔️🔤

## 📦 Installation

Install Morsely directly from PyPI (https://pypi.org/project/morsely/):

```bash
pip install morsely
```

## 🚀 Features

- 🔡 **Convert text to Morse**
- 📡 **Convert Morse to text**
- 🎵 **Decode WAV files containing Morse signals**
- ⚡ **Easy to use, configurable, and reliable**

## 🚀 Usage

### 🔡 Convert text to Morse
```python
from morsely import MorseEncoder

message = "Hello, World!"
encoder = MorseEncoder()
morse_code = encoder.convert_text_to_morse_text(
    original_string=message
)
print(morse_code)  # .... . .-.. .-.. --- --..-- / .-- --- .-. .-.. -.. -.-.--
```

### 📡 Convert Morse to text
```python
from morsely import MorseDecoder

morse = ".... . .-.. .-.. --- --..-- / .-- --- .-. .-.. -.. -.-.--"
decoder = MorseDecoder()
text = decoder.decode_morse_text(text=morse)
print(text)  # HELLO, WORLD!
```

### 🎵 Encode a text to a WAV audio file
```python
from morsely import MorseEncoder

message = "Hello, World!"
encoder = MorseEncoder()
encoding_results = encoder.convert_text_to_morse_complete(
    original_string=message, 
    folder_path='',
    file_prefix='morse_audio'
)
print(encoding_results.morse_encoded_text) #.... . .-.. .-.. --- --..-- / .-- --- .-. .-.. -.. -.-.--
print(encoding_results.path_to_file) #<folder_path>/<file_prefix>_<unique_id>.wav
```



### 🎵 Decode a WAV audio file to text
```python
from morsely import MorseDecoder

decoder = MorseDecoder()
decoding_results = decoder.decode_wav_file("morse_signal.wav")
print(decoding_results.morse_decoded_text) #.... . .-.. .-.. --- --..-- / .-- --- .-. .-.. -.. -.-.--
print(decoding_results.latin_decoded_text) #HELLO, WORLD!
```

### ✨ Morsely in Production: the Telegram Bot
The Morsely library is not just an open-source project: it also powers the Morsely Telegram Bot.

The bot allows users to:

Convert natural language text to Morse code and vice versa,

Upload audio files containing Morse signals and automatically decode them,

Generate audio files from text or Morse code.

The core functionality of the bot relies entirely on morsely, demonstrating the library’s reliability, flexibility, and lightweight performance in real-world production environments.

If you want to see Morsely in action, try the bot directly on Telegram:
👉 https://t.me/MorselyBot

## 🛠️ Requirements

- Python 3.11+
- `numpy`, `scipy` for audio processing

## 📜 License

morsely is released under the Apache License.

---

🔥 **Try morsely today and make Morse code conversion effortless!** 🔥

