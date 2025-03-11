from dataclasses import dataclass
from enum import StrEnum
from typing import Optional, Dict, List, Union, Set
import numpy as np

DASH_CHARACTER = '-'
DOT_CHARACTER = '.'
NO_CHARACTER = ''
SPACE_CHARACTER = ' '
SPACE_2_CHARACTER = '/'


class LatinAlphabet(StrEnum):
    EMPTY = NO_CHARACTER
    SPACE_BETWEEN_CHARACTERS = NO_CHARACTER
    SPACE_BETWEEN_WORDS = SPACE_CHARACTER


class MorseAlphabet(StrEnum):
    DASH = DASH_CHARACTER
    DOT = DOT_CHARACTER
    EMPTY = NO_CHARACTER
    SPACE_BETWEEN_CHARACTERS = SPACE_CHARACTER
    SPACE_BETWEEN_WORDS = SPACE_2_CHARACTER


@dataclass
class Interval:
    duration: float
    is_silence: bool
    start: int
    end: int
    interval_type: Optional[MorseAlphabet] = None


class MorseEncodingConfiguration:
    """
    A class which represents the configuration for the encoding process.
    """

    def __init__(
            self,
            amplitude: Optional[float] = 0.5,
            time_unit: Optional[float] = 0.1,
            frequency: Optional[float] = 1000.0,
            sample_rate: Optional[int] = 44100,
            fail_on_unrecognized_character: Optional[bool] = False,
            force_filename: Optional[bool] = False
    ):
        """
        Parameters
        ----------
        amplitude: the amplitude of the sinusoid to generate for the morse audio signal as a sinusoidal wave.

        time_unit: the time unit to consider when producing the morse audio signal, expressed in seconds.

        frequency: the frequency to consider when producing the morse audio signal as a sinusoidal wave,
        expressed in Hz.

        sample_rate: the sample rate to consider when producing the morse audio signal, expressed in Hz.

        fail_on_unrecognized_character: flag to indicate if the algorithm has to raise an exception if an unknown 
        character is detected in the string to encode, if false it will be ignored.

        force_filename: flag to indicate if after the encoding process the file has to be saved with a given name;
        if false the file will be saved with a concatenation of unique identifiers.
        """
        self._amplitude = amplitude
        self._time_unit = time_unit
        self._frequency = frequency
        self._sample_rate = sample_rate
        self._fail_on_unrecognized_character = fail_on_unrecognized_character
        self._force_filename = force_filename

    @property
    def amplitude(self):
        return self._amplitude

    @property
    def time_unit(self):
        return self._time_unit

    @property
    def frequency(self):
        return self._frequency

    @property
    def sample_rate(self):
        return self._sample_rate

    @property
    def fail_on_unrecognized_character(self):
        return self._fail_on_unrecognized_character

    @property
    def force_filename(self):
        return self._force_filename


class MorseDecodingConfiguration:
    """
    A class which represents the configuration for the decoding process.
    """

    def __init__(
            self,
            amplitude: Optional[float] = None,
            time_unit: Optional[float] = None,
            fail_on_asymmetric_signal_fronts: Optional[bool] = False,
            fail_on_unrecognized_morse_word: Optional[bool] = False,
            max_low_elements_to_consider_for_time_unit_inference: Optional[int] = 4,
            fail_on_unallowed_duration: Optional[bool] = False,
            smooth_audio_signal: Optional[bool] = True,
            smooth_window_length_perc: Optional[float] = 11.33,
            exact_match_duration: Optional[bool] = False,
            apply_noise_reduction: Optional[bool] = True,
            frequencies_deviation_tolerance_perc: Optional[float] = 4.0
    ):
        """
        Parameters
        ----------
        amplitude: the max amplitude of the audio signal to decode. If not provided the max amplitude
        will be = max signal value.

        time_unit: the time unit to consider when decoding the morse audio signal, expressed in seconds. 
        If not provided, a maximum-likelihood algorithm will try to detect the time unit.

        fail_on_asymmetric_signal_fronts: flag to indicate if the algorithm has to raise an exception
        if the audio signal for whatever reason, has a different number of fronts (between rising and falling ones).

        fail_on_unrecognized_morse_word: flag to indicate if the algorithm has to raise an exception
        if the morse code contains unrecognized morse words, if false they will be ignored.

        max_low_elements_to_consider_for_time_unit_inference: (only considered when time_unit is not provided)
        hyperparameter considered for the maximum likelihood algorithm to detect the time unit.

        fail_on_unallowed_duration: flag to indicate if the algorithm has to raise an exception if there is an
        unallowed signal duration (both logical 1 or 0) in the audio signal considering the morse time coding rules;
        if false that signal duration is ignored.

        smooth_audio_signal: flag to indicate if the algorithm has to smooth the audio signal.

        smooth_window_length_perc: the percentage which express the length of the smoothing window, compared to the
        sample rate of the audio file.

        exact_match_duration: flag to indicate if the algorithm has to match exactly
        the duration of morse alphabet, given a time unit.
        WARNING: Enable this only if an audio file is VERY clean from noise.

        apply_noise_reduction: apply the default method to reduce the noise detected in the audio signal.
        The default method extract the most frequent frequency from the signal spectrum.

        frequencies_deviation_tolerance_perc: the percentage (expressed as a number >=0 and ideally <= 100)
        of frequencies to include when applying the noise reduction function.
        After estimating the most frequent frequency, only the frequencies
        abs_dev = (most_frequent_frequency * frequencies_deviation_tolerance_perc) / 100
        which fall in the interval [most_frequent_frequency - (abs_dev / 2), most_frequent_frequency + (abs_dev / 2)]
        will be included.
        """
        self._amplitude = amplitude
        self._time_unit = time_unit
        self._fail_on_asymmetric_signal_fronts = fail_on_asymmetric_signal_fronts
        self._fail_on_unrecognized_morse_word = fail_on_unrecognized_morse_word
        self._max_low_elements_to_consider_for_time_unit_inference \
            = max_low_elements_to_consider_for_time_unit_inference
        self._fail_on_unallowed_duration = fail_on_unallowed_duration
        self._smooth_audio_signal = smooth_audio_signal
        self._smooth_window_length_perc = smooth_window_length_perc
        self._exact_match_duration = exact_match_duration
        self._apply_noise_reduction = apply_noise_reduction
        self._frequencies_deviation_tolerance_perc = frequencies_deviation_tolerance_perc

    def __repr__(self):
        dictio = {}
        for attr_name, attr_value in vars(self).items():
            if attr_name.startswith('_') and not attr_name.startswith('__'):
                attr_name_parsed = attr_name.split('_')[-1]
                dictio[attr_name_parsed] = attr_value

        return dictio

    def __str__(self):
        attr_text = ''
        i = 0
        for attr_name, attr_value in vars(self).items():
            if attr_name.startswith('_'):
                temp_text = f'{attr_name}={attr_value}'
                if i == 0:
                    attr_text = temp_text
                else:
                    attr_text = f'{attr_text},{temp_text}'

        return f'MorseDecodingConfiguration({attr_text})'

    @property
    def amplitude(self):
        return self._amplitude

    @property
    def time_unit(self):
        return self._time_unit

    @property
    def fail_on_asymmetric_signal_fronts(self):
        return self._fail_on_asymmetric_signal_fronts

    @property
    def fail_on_unrecognized_morse_word(self):
        return self._fail_on_unrecognized_morse_word

    @property
    def max_low_elements_to_consider_for_time_unit_inference(self):
        return self._max_low_elements_to_consider_for_time_unit_inference

    @property
    def fail_on_unallowed_duration(self):
        return self._fail_on_unallowed_duration

    @property
    def smooth_audio_signal(self):
        return self._smooth_audio_signal

    @property
    def smooth_window_length_perc(self):
        return self._smooth_window_length_perc

    @property
    def exact_match_duration(self):
        return self._exact_match_duration

    @property
    def apply_noise_reduction(self):
        return self._apply_noise_reduction

    @property
    def frequencies_deviation_tolerance_perc(self):
        return self._frequencies_deviation_tolerance_perc


class MorseEncodingException(Exception):
    pass


class MorseDecodingException(Exception):
    pass


class MorseUtils:
    _ALPHABET_2_MORSE_DICT = {
        'A': '.-', 'B': '-...',
        'C': '-.-.', 'D': '-..', 'E': '.',
        'F': '..-.', 'G': '--.', 'H': '....',
        'I': '..', 'J': '.---', 'K': '-.-',
        'L': '.-..', 'M': '--', 'N': '-.',
        'O': '---', 'P': '.--.', 'Q': '--.-',
        'R': '.-.', 'S': '...', 'T': '-',
        'U': '..-', 'V': '...-', 'W': '.--',
        'X': '-..-', 'Y': '-.--', 'Z': '--..',
        '1': '.----', '2': '..---', '3': '...--',
        '4': '....-', '5': '.....', '6': '-....',
        '7': '--...', '8': '---..', '9': '----.',
        '0': '-----', ',': '--..--', '.': '.-.-.-',
        '?': '..--..', '/': '-..-.', '-': '-....-',
        '(': '-.--.', ')': '-.--.-', ':': '---...',
        '"': '.-..-.', '=': '-...-', ';': '-.-.-.',
        "'": ".----.", '_': '..--.-', '+': '.-.-.',
        '@': '.--.-.', '!': '-.-.--'
    }

    _MORSE_2_ALPHABET_DICT = {
        '.-': 'A', '-...': 'B', '-.-.': 'C',
        '-..': 'D', '.': 'E', '..-.': 'F',
        '--.': 'G', '....': 'H', '..': 'I',
        '.---': 'J', '-.-': 'K', '.-..': 'L',
        '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P',
        '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T',
        '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
        '-.--': 'Y', '--..': 'Z', '.----': '1', '..---': '2',
        '...--': '3', '....-': '4', '.....': '5', '-....': '6',
        '--...': '7', '---..': '8', '----.': '9', '-----': '0',
        '--..--': ',', '.-.-.-': '.', '..--..': '?', '-..-.': '/',
        '-....-': '-', '-.--.': '(', '-.--.-': ')', '---...': ':',
        '.-..-.': '"', '-...-': '=', '-.-.-.': ';', '.----.': "'",
        '..--.-': '_', '.-.-.': '+', '.--.-.': '@', '-.-.--': '!'
    }

    _CHARACTER_BETWEEN_WORDS = '/'
    _SPACE_BETWEEN_WORDS = ' '

    @property
    def get_alphabet_to_morse_dictionary(self) -> Dict[str, str]:
        return self._ALPHABET_2_MORSE_DICT

    @property
    def get_morse_to_alphabet_dictionary(self) -> Dict[str, str]:
        return self._MORSE_2_ALPHABET_DICT

    @property
    def get_character_between_words(self) -> str:
        return self._CHARACTER_BETWEEN_WORDS

    @property
    def get_space_between_words(self) -> str:
        return self._SPACE_BETWEEN_WORDS

    @classmethod
    def __get_duration(cls, time_unit: float, multiplier: int) -> float:
        return round(multiplier * time_unit, 2)

    def get_d1_duration(self, time_unit: float) -> float:
        return self.__get_duration(time_unit, 1)

    def get_d2_duration(self, time_unit: float) -> float:
        return self.__get_duration(time_unit, 3)

    def get_d3_duration(self, time_unit: float) -> float:
        return self.__get_duration(time_unit, 7)

    def get_allowed_durations(self, time_unit: float, return_set_like: bool = True) -> Union[List[float], Set[float]]:
        allowed_durations = [
            self.get_d1_duration(time_unit),
            self.get_d2_duration(time_unit),
            self.get_d3_duration(time_unit),
        ]

        if return_set_like:
            return set(allowed_durations)
        return allowed_durations


@dataclass
class MorseEncodeResult:
    morse_encoded_text: str
    audio_signal: np.ndarray
    path_to_file: Optional[str] = None


@dataclass
class MorseDecodeResult:
    morse_decoded_text: str
    latin_decoded_text: str
