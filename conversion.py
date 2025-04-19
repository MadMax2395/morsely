from pydub import AudioSegment
from scipy.io.wavfile import read
#audio = AudioSegment.from_ogg("/Users/massimomaddaluno/Desktop/Massimo/ProgettiPython/morsely/tests/resources/voice.ogg")

# Salva come WAV
#audio.export("/Users/massimomaddaluno/Desktop/Massimo/ProgettiPython/morsely/tests/resources/voice.wav", format="wav")


sr, audio = read('/Users/massimomaddaluno/Desktop/Massimo/ProgettiPython/morsely/tests/resources/voice.ogg')
print(sr)