import pytest
import math
from scipy.io.wavfile import *
from tests.t_utility import *
from morsely import *


class TestEncoder:

    def test_single_letter(self):
        conf = MorseEncodingConfiguration()
        encoder = MorseEncoder(conf)
        text = 'c'
        result = encoder.convert_text_to_morse_text(text)
        assert result == '-.-.'

    def test_single_word(self):
        conf = MorseEncodingConfiguration()
        encoder = MorseEncoder(conf)
        text = 'ciao'
        result = encoder.convert_text_to_morse_text(text)
        assert result == '-.-. .. .- ---'

    def test_words(self):
        conf = MorseEncodingConfiguration()
        encoder = MorseEncoder(conf)
        text = 'ciao sono massimo'
        result = encoder.convert_text_to_morse_text(text)
        assert result == '-.-. .. .- --- / ... --- -. --- / -- .- ... ... .. -- ---'

    def test_empty(self):
        conf = MorseEncodingConfiguration()
        encoder = MorseEncoder(conf)
        text = ''
        result = encoder.convert_text_to_morse_text(text)
        assert result == ''

    def test_not_raise_exception(self):
        conf = MorseEncodingConfiguration(
            fail_on_unrecognized_character=False
        )
        encoder = MorseEncoder(conf)
        text = '∞'
        result = encoder.convert_text_to_morse_text(text)
        assert result is not None
        assert result == ''

    def test_raise_exception(self):
        conf = MorseEncodingConfiguration(
            fail_on_unrecognized_character=True
        )
        encoder = MorseEncoder(conf)
        text = '∞'
        with pytest.raises(MorseEncodingException):
            encoder.convert_text_to_morse_text(text)

    def test_audio_signal(self):
        conf = MorseEncodingConfiguration()
        encoder = MorseEncoder(conf)
        text = 'ciao'
        results = encoder.convert_text_to_morse_text_and_audio_data(text)
        assert results is not None
        assert results.audio_signal is not None
        assert results.path_to_file is None
        assert results.morse_encoded_text == '-.-. .. .- ---'
        ampl = float(round(max(results.audio_signal), 2))
        assert math.isclose(ampl, conf.amplitude, abs_tol=0.01)

    def test_file_write(self):
        conf = MorseEncodingConfiguration()
        encoder = MorseEncoder(conf)
        text = 'ciao'
        results = encoder.convert_text_to_morse_complete(text, get_working_directory_test())
        assert results is not None
        assert results.audio_signal is not None
        assert results.path_to_file is not None
        assert results.morse_encoded_text == '-.-. .. .- ---'
        sample_rate, audio_signal = read(results.path_to_file)
        os.remove(results.path_to_file)
        assert sample_rate == conf.sample_rate
        ampl = float(round(max(audio_signal), 2))
        assert math.isclose(ampl, conf.amplitude, abs_tol=0.01)
