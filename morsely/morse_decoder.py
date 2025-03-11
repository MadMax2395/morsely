from copy import deepcopy
import logging
import math
from math import isclose
from typing import Tuple
from scipy.fft import fft
from scipy.io.wavfile import read
from scipy.signal import hilbert, savgol_filter, butter, filtfilt
from morsely.morse_utils import *

logger = logging.getLogger(__name__)


class MorseDecoder:
    def __init__(self, configuration: Optional[MorseDecodingConfiguration] = MorseDecodingConfiguration()):
        self._morse_utils = MorseUtils()
        self._configuration = configuration

    def decode_wav_file(self, path: str) -> MorseDecodeResult:
        sample_rate, audio_signal = self._read(path)
        audio_signal = self._preprocess_audio(audio_signal, sample_rate)
        quantized_fronts = self._convert_raw_signal_to_quantized_fronts(audio_signal, sample_rate)
        validated_rising_fronts, validated_falling_fronts = self._extract_validated_fronts_index_from_quantized_fronts(
            quantized_fronts
        )
        intervals = self._extract_intervals_from_fronts(
            sample_rate,
            validated_rising_fronts,
            validated_falling_fronts
        )
        morse_words = self._extract_morse_words_from_intervals(intervals)
        return self._extract_decoded_text_and_morse_translation(morse_words)

    def decode_morse_text(self, text: str) -> str:
        # TODO
        morse_words = text.split(sep=MorseAlphabet.SPACE_BETWEEN_CHARACTERS.value)
        morse_words = list(filter(lambda x: x != MorseAlphabet.EMPTY.value, morse_words))
        result = self._extract_decoded_text_and_morse_translation(morse_words)
        return result.latin_decoded_text

    def _preprocess_audio(self, audio: np.ndarray, sample_rate: Union[int, float]) -> np.ndarray:
        audio = self._handle_stereo_audio(audio)
        if self._configuration.apply_noise_reduction:
            audio = self._reduce_noise(audio, sample_rate)
        return audio

    @classmethod
    def _handle_stereo_audio(cls, audio: np.ndarray) -> np.ndarray:
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        return audio

    def _reduce_noise(self, audio: np.ndarray, sample_rate: int):
        n_audio = len(audio)
        frequencies = np.fft.fftfreq(n_audio, d=1 / sample_rate)
        spectrum = np.abs(fft(audio))
        mf_frequency_index = int(spectrum[:n_audio // 2].argmax())
        mf_frequency = frequencies[:n_audio // 2][mf_frequency_index]
        abs_dev = (mf_frequency * self._configuration.frequencies_deviation_tolerance_perc) / 100
        lowcut = mf_frequency - (abs_dev / 2)
        highcut = mf_frequency + (abs_dev / 2)

        order = 4
        lowcut_freq = lowcut / (sample_rate / 2)
        highcut_freq = highcut / (sample_rate / 2)
        b, a = butter(order, [lowcut_freq, highcut_freq], btype='band')

        return filtfilt(b, a, audio)

    def _convert_raw_signal_to_quantized_fronts(self, data: np.ndarray, sample_rate: Union[int, float]) -> np.ndarray:
        analytic_signal = hilbert(data)
        envelope = np.abs(analytic_signal)

        if self._configuration.amplitude is None:
            threshold_value = max(envelope) / 2
        else:
            threshold_value = self._configuration.amplitude

        if self._configuration.smooth_audio_signal:
            window_length = int(math.ceil((self._configuration.smooth_window_length_perc * sample_rate) / 100))
            envelope = savgol_filter(envelope, window_length, 3, mode='mirror')

        envelop_quantized = np.where(envelope > threshold_value, 1, 0)
        return np.diff(envelop_quantized, n=1, axis=-1)

    def _extract_validated_fronts_index_from_quantized_fronts(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        rising_fronts_list, falling_fronts_list = self._extract_fronts_index_from_quantized_fronts(data)
        return self._validate_fronts(data, rising_fronts_list, falling_fronts_list)

    @classmethod
    def _extract_fronts_index_from_quantized_fronts(cls, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        rising_fronts = np.where(data == 1)
        falling_fronts = np.where(data == -1)

        return rising_fronts[0], falling_fronts[0]

    def _validate_fronts(self, quantized_fronts: np.ndarray, rising_fronts_list: np.ndarray,
                         falling_fronts_list: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        len_r_fronts = len(rising_fronts_list)
        len_f_fronts = len(falling_fronts_list)
        is_sound_clean = (len_r_fronts == len_f_fronts)

        if not is_sound_clean:
            if self._configuration.fail_on_asymmetric_signal_fronts:
                raise MorseDecodingException(
                    f'Asymmetric fronts detected: rising: {len_r_fronts}, falling: {len_f_fronts}')

            if len_f_fronts > len_r_fronts:
                if rising_fronts_list[0] > falling_fronts_list[0] and len_f_fronts == len_r_fronts + 1:
                    # probably it was not recorded a silence at the beginning of file, we can manually insert it
                    rising_fronts_list = np.insert(rising_fronts_list, 0, 0)
                else:
                    raise MorseDecodingException(
                        f'Falling fronts detected are greater than rising ones: rising: {len_r_fronts}, '
                        f'falling: {len_f_fronts}')

            # probably it was not recorded a silence at the end of final high signal, we can manually insert it
            falling_fronts_list = np.append(falling_fronts_list, len(quantized_fronts))

        prev_rising = -1
        prev_falling = -1

        for i, rising_front in enumerate(rising_fronts_list):
            falling_front = falling_fronts_list[i]

            if rising_front > falling_front:
                raise MorseDecodingException(
                    f'{i} cycle: rising front {rising_front} detected ahead of falling front {falling_front}')

            if i > 0:
                if prev_rising > rising_front:
                    raise MorseDecodingException(
                        f'{i} cycle: detected previous rising front {prev_rising} greater '
                        f'than actual rising front: {rising_front}')

                if prev_falling > falling_front:
                    raise MorseDecodingException(
                        f'{i} cycle: detected previous falling front {prev_falling} greater '
                        f'than actual falling front: {falling_front}')

            prev_falling = deepcopy(falling_front)
            prev_rising = deepcopy(rising_front)

        return rising_fronts_list, falling_fronts_list

    @classmethod
    def _extract_intervals_from_fronts(
            cls,
            sample_rate: float,
            rising_fronts_list: np.ndarray,
            falling_fronts_list: np.ndarray
    ) -> List[Interval]:
        intervals: List[Interval] = []

        fronts_len = len(rising_fronts_list)

        for i in range(0, fronts_len, 1):
            rising_front = int(rising_fronts_list[i])
            falling_front = int(falling_fronts_list[i])

            duration = (falling_front - rising_front + 1) / sample_rate
            intervals.append(
                Interval(
                    round(duration, 2),
                    False,
                    rising_front,
                    falling_front
                )
            )
            if (i + 1) < fronts_len:
                next_rising_front = int(rising_fronts_list[i + 1])

                duration = (next_rising_front - falling_front - 1) / sample_rate
                intervals.append(
                    Interval(
                        round(duration, 2),
                        True,
                        falling_front,
                        int(rising_fronts_list[i + 1])
                    )
                )

        return intervals

    def _enrich_time_intervals(self, intervals: List[Interval], time_unit: float):
        d1 = self._morse_utils.get_d1_duration(time_unit)
        d2 = self._morse_utils.get_d2_duration(time_unit)
        d3 = self._morse_utils.get_d3_duration(time_unit)

        abs_tolerance = 0.7 * time_unit
        is_close_d1 = lambda d: isclose(d, d1, abs_tol=abs_tolerance)
        is_close_d2 = lambda d: isclose(d, d2, abs_tol=abs_tolerance)
        is_close_d3 = lambda d: isclose(d, d3, abs_tol=abs_tolerance)

        for interval in intervals:
            if (self._configuration.exact_match_duration and interval.duration == d1) or is_close_d1(interval.duration):
                if interval.is_silence:
                    interval.interval_type = MorseAlphabet.EMPTY
                else:
                    interval.interval_type = MorseAlphabet.DOT
            if (self._configuration.exact_match_duration and interval.duration == d2) or is_close_d2(interval.duration):
                if interval.is_silence:
                    interval.interval_type = MorseAlphabet.SPACE_BETWEEN_CHARACTERS
                else:
                    interval.interval_type = MorseAlphabet.DASH
            if (self._configuration.exact_match_duration and interval.duration == d3) or is_close_d3(interval.duration):
                if self._configuration.exact_match_duration:
                    assert interval.is_silence is True
                interval.interval_type = MorseAlphabet.SPACE_BETWEEN_WORDS

    def _extract_morse_words_from_intervals(self, intervals: List[Interval]) -> List[str]:
        all_durations = [x.duration for x in intervals]
        unique_durations_list = list(set(all_durations))
        unit_interval = self._extract_time_unit(unique_durations_list, all_durations)

        filtered_intervals = self._filter_intervals(intervals, unit_interval)

        self._enrich_time_intervals(filtered_intervals, unit_interval)
        return self._extract_morse_words_from_enriched_intervals(intervals)

    def _filter_intervals(self, intervals: List[Interval], unit_interval: float) -> List[Interval]:
        validated_intervals = []
        allowed_durations: List[float] = self._morse_utils.get_allowed_durations(unit_interval, False)
        abs_tolerance = 0.7 * unit_interval
        valid_interval_flag = False
        for interval in intervals:
            if self._configuration.exact_match_duration:
                if interval in set(allowed_durations):
                    validated_intervals.append(interval)
                elif self._configuration.fail_on_unallowed_duration:
                    raise MorseDecodingException(
                        f'Unallowed duration detected: {interval}, allowed ones: {allowed_durations}')
            else:
                valid_interval_flag = False
                for allowed_duration in allowed_durations:
                    if isclose(interval.duration, allowed_duration, abs_tol=abs_tolerance):
                        validated_intervals.append(interval)
                        valid_interval_flag = True
                        break
            if not valid_interval_flag and self._configuration.fail_on_unallowed_duration:
                raise MorseDecodingException(
                    f'Unallowed duration detected: {interval}, allowed ones: {allowed_durations}')
        return validated_intervals

    @classmethod
    def _extract_morse_words_from_enriched_intervals(cls, intervals: List[Interval]) -> List[str]:
        morse_words = []
        morse_word = ''
        for i, interval in enumerate(intervals):
            if interval.interval_type in {MorseAlphabet.DASH, MorseAlphabet.DOT, MorseAlphabet.EMPTY}:
                morse_word = f'{morse_word}{interval.interval_type.value}'
                if i == len(intervals) - 1:
                    morse_words.append(deepcopy(morse_word))
                    morse_word = ''
            else:
                if len(morse_word) > 0:
                    morse_words.append(deepcopy(morse_word))
                    morse_word = ''
                    if interval.interval_type == MorseAlphabet.SPACE_BETWEEN_WORDS:
                        morse_words.append(MorseAlphabet.SPACE_BETWEEN_WORDS.value)

        return morse_words

    def _extract_decoded_text_and_morse_translation(self, morse_words: List[str]) -> MorseDecodeResult:
        decoded_string = []
        for morse_word in morse_words:
            if morse_word == MorseAlphabet.SPACE_BETWEEN_WORDS.value:
                decoded_string.append(LatinAlphabet.SPACE_BETWEEN_WORDS.value)
            else:
                decoded_char = self._morse_utils.get_morse_to_alphabet_dictionary.get(morse_word)
                if decoded_char is None:
                    text = f'{morse_word} is not translatable to an alphanumeric character'
                    if self._configuration.fail_on_unrecognized_morse_word:
                        raise MorseDecodingException(text)
                    logger.warning(f'{text}, it will be ignored')
                else:
                    decoded_string.append(decoded_char)

        decoded_text = LatinAlphabet.EMPTY.value.join(decoded_string)
        morse_words_formatted = LatinAlphabet.SPACE_BETWEEN_WORDS.value.join(morse_words)

        return MorseDecodeResult(morse_words_formatted.strip(), decoded_text.strip())

    @classmethod
    def _read(cls, path: str) -> Tuple[float, np.ndarray]:
        return read(path)

    def _extract_time_unit(self, unique_durations_list: List[float], all_durations: List[float]) -> float:
        if self._configuration.time_unit is not None:
            return self._configuration.time_unit

        durations_count_map: Dict[float, Dict[Union[str, float], int]] = {}
        max_len_to_consider = min(
            len(unique_durations_list),
            self._configuration.max_low_elements_to_consider_for_time_unit_inference
        )

        possible_time_units: List[float] = sorted(unique_durations_list)[:max_len_to_consider]

        for possible_time_unit in possible_time_units:
            d1 = self._morse_utils.get_d1_duration(possible_time_unit)
            d2 = self._morse_utils.get_d2_duration(possible_time_unit)
            d3 = self._morse_utils.get_d3_duration(possible_time_unit)

            temp = {
                d1: 0,
                d2: 0,
                d3: 0
            }

            for duration in all_durations:
                if d1 == duration:
                    temp[d1] += 1
                elif d2 == duration:
                    temp[d2] += 1
                elif d3 == duration:
                    temp[d3] += 1

            temp['ALL'] = temp[d1] + temp[d2] + temp[d3]
            durations_count_map[possible_time_unit] = temp

        return max(durations_count_map, key=lambda x: durations_count_map[x]['ALL'])
