import uuid
import os
import logging
from copy import deepcopy
import datetime as dtm
from scipy.io.wavfile import write
from morsely.morse_utils import *

logger = logging.getLogger(__name__)


class MorseEncoder:
    def __init__(self, configuration: Optional[MorseEncodingConfiguration] = MorseEncodingConfiguration()):
        self._configuration = configuration
        self._morse_utils = MorseUtils()
        self._dot_duration = self._morse_utils.get_d1_duration(
            self._configuration.time_unit
        )
        self._dash_duration = self._morse_utils.get_d2_duration(
            self._configuration.time_unit
        )
        self._silence_between_morse_symbols_in_a_letter = self._morse_utils.get_d1_duration(
            self._configuration.time_unit
        )
        self._silence_between_letters = self._morse_utils.get_d2_duration(
            self._configuration.time_unit
        )
        self._silence_between_words = self._morse_utils.get_d3_duration(
            self._configuration.time_unit
        )

    def convert_text_to_morse_text(self, original_string: str) -> str:
        morse_code: List[str] = self._convert_string_to_morse_code(
            original_string,
        )
        return MorseAlphabet.SPACE_BETWEEN_CHARACTERS.value.join(morse_code)

    def convert_text_to_morse_text_and_audio_data(self, original_string: str) -> MorseEncodeResult:
        morse_code: List[str] = self._convert_string_to_morse_code(
            original_string,
        )

        morse_code_formatted = MorseAlphabet.SPACE_BETWEEN_CHARACTERS.value.join(morse_code)
        audio_signal = self._convert_morse_code_to_audio_signal(
            morse_code
        )

        return MorseEncodeResult(
            morse_code_formatted,
            audio_signal
        )

    def convert_text_to_morse_complete(self, original_string: str, folder_path: str,
                                       file_prefix: Optional[str] = '') -> MorseEncodeResult:
        result = self.convert_text_to_morse_text_and_audio_data(original_string)
        path = self._save_audio_signal_on_disk(folder_path, result.audio_signal, file_prefix)
        result.path_to_file = path
        return result

    def _generate_tone(self, duration: float) -> np.ndarray:
        """
        Generate a sound.


        Parameters
        ----------

        duration: the total duration of the sound to be reproduced. (expressed in seconds)
        """
        t = np.linspace(0, duration, int(self._configuration.sample_rate * duration), endpoint=False)
        return self._configuration.amplitude * np.sin(2 * np.pi * self._configuration.frequency * t)

    def _generate_silence(self, duration: float) -> np.ndarray:
        """
        Generate silence.

        Parameters
        ----------

        duration: the total duration of the silence to be reproduced. (expressed in seconds)
        """
        return np.zeros(int(self._configuration.sample_rate * duration))

    def _generate_silence_between_morse_symbols_in_letter(self) -> np.ndarray:
        """
        Generate the silence for the duration needed between morse symbols in a single letter.
        
        Parameters
        ----------
        """
        return self._generate_silence(self._silence_between_morse_symbols_in_a_letter)

    def _generate_silence_between_letters(self) -> np.ndarray:
        """
        Generate the silence for the duration needed between letters in a same word.

        Parameters
        ----------
        """
        return self._generate_silence(self._silence_between_letters)

    def _generate_silence_between_words(self) -> np.ndarray:
        """
        Generate the silence for the duration needed between words.

        Parameters
        ----------
        """
        return self._generate_silence(self._silence_between_words)

    def _convert_string_to_morse_code(self, string_to_convert: str) -> List[str]:
        """
        Convert a custom string to morse code.

        Parameters
        ----------
        string_to_convert: the string to convert to morse code alphabet.
        """
        string_to_convert = string_to_convert.upper().strip()
        morse_sequence: List[str] = []

        for character in string_to_convert:
            if character != LatinAlphabet.SPACE_BETWEEN_WORDS.value:
                if character in self._morse_utils.get_alphabet_to_morse_dictionary:
                    morse_sequence.append(self._morse_utils.get_alphabet_to_morse_dictionary[character])
                else:
                    if self._configuration.fail_on_unrecognized_character:
                        raise MorseEncodingException(
                            f'Received unknown character {character} in word: {string_to_convert}')
                    logger.warning(f'WARNING! IGNORING UNKNOWN CHARACTER: {character} IN WORD: {string_to_convert}')
            else:
                morse_sequence.append(MorseAlphabet.SPACE_BETWEEN_WORDS.value)

        return morse_sequence

    def _convert_morse_code_to_audio_signal(
            self,
            morse_code: List[str]
    ) -> np.ndarray:
        """
        Convert morse code to an audio signal.
        
        Parameters
        ----------
        morse_code: the morse code to transform to a .wav file.
        """
        audio_signal = []
        prev_morse_word = None

        for i, morse_word in enumerate(morse_code):
            cond1 = morse_word != MorseAlphabet.SPACE_BETWEEN_WORDS.value
            cond2 = prev_morse_word != MorseAlphabet.SPACE_BETWEEN_WORDS.value
            if i > 0 and cond1 and cond2:
                audio_signal.extend(self._generate_silence_between_letters())
            for j, morse_char in enumerate(morse_word):

                if morse_char == MorseAlphabet.DOT.value or morse_char == MorseAlphabet.DASH.value:
                    if morse_char == MorseAlphabet.DOT.value:
                        audio_signal.extend(self._generate_tone(self._dot_duration))
                    elif morse_char == MorseAlphabet.DASH.value:
                        audio_signal.extend(self._generate_tone(self._dash_duration))

                    if j != len(morse_word) - 1:
                        audio_signal.extend(self._generate_silence_between_morse_symbols_in_letter())

                elif morse_char == MorseAlphabet.SPACE_BETWEEN_WORDS.value and len(morse_word) == 1:
                    audio_signal.extend(self._generate_silence_between_words())
                else:
                    logging.error('Received unexpected character: {}', morse_char)

            prev_morse_word = deepcopy(morse_word)

        audio_signal.extend(self._generate_silence_between_morse_symbols_in_letter())
        return np.array(audio_signal, dtype=np.float32)

    def _save_audio_signal_on_disk(self, path: str, audio_signal: np.ndarray, file_prefix: str) -> str:
        """
        Save audio on disk.


        Parameters
        ----------

        path: the filesystem path where the file will be saved into.
        audio_signal: the audio signal to save as wav file.
        file_prefix: the name which will be used to save the file.

        """
        filename_complete = f'{file_prefix}.wav'

        if not self._configuration.force_filename:
            time_id = dtm.datetime.now(dtm.timezone.utc)
            time_id = int(dtm.datetime(
                time_id.year, time_id.month, time_id.day, time_id.hour, time_id.minute, time_id.second
            ).timestamp())
            entropy_id = uuid.uuid4()
            filename_complete = f'{file_prefix}_{time_id}_{entropy_id}.wav'

        complete_path = os.path.join(path, filename_complete)
        write(complete_path, self._configuration.sample_rate, audio_signal)
        return complete_path
