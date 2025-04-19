from tests.t_utility import *
from morsely import *


class TestDecoder:

    def test_single_letter(self):
        conf = MorseDecodingConfiguration()
        decoder = MorseDecoder(conf)
        text = '-.-.'
        result = decoder.decode_morse_text(text)
        assert result.casefold() == 'c'.casefold()

    def test_single_word(self):
        conf = MorseDecodingConfiguration()
        decoder = MorseDecoder(conf)
        text = '-.-. .. .- ---'
        result = decoder.decode_morse_text(text)
        assert result.casefold() == 'ciao'.casefold()

    def test_words(self):
        conf = MorseDecodingConfiguration()
        decoder = MorseDecoder(conf)
        text = '-.-. .. .- --- / ... --- -. --- / -- .- ... ... .. -- ---'
        result = decoder.decode_morse_text(text)
        assert result.casefold() == 'ciao sono massimo'.casefold()

    def test_empty(self):
        conf = MorseDecodingConfiguration()
        decoder = MorseDecoder(conf)
        text = ''
        result = decoder.decode_morse_text(text)
        assert result.casefold() == ''.casefold()

    def test_decode_audio_clean(self):
        conf = MorseDecodingConfiguration()
        decoder = MorseDecoder(conf)
        morse_recorded_path = os.path.join(get_test_resources_folder(), 'morse_clean.wav')
        results = decoder.decode_wav_file(morse_recorded_path)
        assert results is not None
        assert results.morse_decoded_text is not None
        assert results.latin_decoded_text is not None
        assert results.morse_decoded_text == '-.-. .. .- ---'
        assert results.latin_decoded_text.casefold() == 'ciao'.casefold()

    def test_decode_audio_recorded(self):
        conf = MorseDecodingConfiguration()
        decoder = MorseDecoder(conf)
        morse_recorded_path = os.path.join(get_test_resources_folder(), 'morse_recorded_initial_final_pause.wav')
        results = decoder.decode_wav_file(morse_recorded_path)
        assert results is not None
        assert results.morse_decoded_text is not None
        assert results.latin_decoded_text is not None
        assert results.morse_decoded_text == '-.-. .. .- ---'
        assert results.latin_decoded_text.casefold() == 'ciao'.casefold()

    def test_decode_audio_recorded_multiple_word(self):
        conf = MorseDecodingConfiguration()
        decoder = MorseDecoder(conf)
        morse_recorded_path = os.path.join(get_test_resources_folder(), 'morse_more_words_recorded.wav')
        results = decoder.decode_wav_file(morse_recorded_path)
        assert results is not None
        assert results.morse_decoded_text is not None
        assert results.latin_decoded_text is not None
        assert results.morse_decoded_text == '.- .. ..- - .- - . -- .. / ... --- -. --- / ... --- .-.. --- / ... ..- / ..- -. .----. .. ... --- .-.. .-'
        assert results.latin_decoded_text.casefold() == "aiutatemi sono solo su un'isola".casefold()


