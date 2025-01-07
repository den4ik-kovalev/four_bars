"""
Backend part
"""

from __future__ import annotations

import copy
import math
import os
import random
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from os import PathLike
from pathlib import Path
from typing import Optional

from music21.chord import Chord
from music21.note import Pitch, Note, Rest, Duration
from music21.stream import Stream

from src.default import DEFAULT_SCALES, DEFAULT_RHYTHMS
from src.utils.yaml_file import YAMLFile
from src.utils.folder import Folder


APP_DIR = Path.home() / ".four_bars"
APP_FOLDER = Folder(APP_DIR, auto_create=True)
MIDI_FOLDER = Folder(APP_DIR / "midi", auto_create=True)
MIDI_FOLDER.clear()
SCALES_YML = YAMLFile(APP_DIR / "scales.yml", auto_create=True)
RHYTHMS_YML = YAMLFile(APP_DIR / "rhythms.yml", auto_create=True)

if not SCALES_YML.read():
    SCALES_YML.write(DEFAULT_SCALES)

if not RHYTHMS_YML.read():
    RHYTHMS_YML.write(DEFAULT_RHYTHMS)

MAJOR_CHORDS = [
    "C", "G", "D", "A", "E", "B", "F#", "C#", "G#", "D#", "A#", "F"
]

MINOR_CHORDS = [
    "Am", "Em", "Bm", "F#m", "C#m", "G#m", "D#m", "A#m", "Fm", "Cm", "Gm", "Dm"
]


class Grid(Enum):
    EIGHTS = 8
    SIXTEENTHS = 16


class Triad(Chord):

    def __init__(self, name: str):
        self._name = name
        self._is_major = not name.endswith("m")
        tonic_name = name if self._is_major else name[:-1]
        tonic = Pitch(tonic_name)
        third = Pitch(tonic_name).transpose(4 if self._is_major else 3)
        fifth = Pitch(tonic_name).transpose(7)
        super(Triad, self).__init__([tonic, third, fifth])

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_major(self) -> bool:
        return self._is_major


class Melody(Stream):

    def __str__(self) -> str:
        return str(list(self))

    def __add__(self, other) -> Melody:
        other = copy.deepcopy(other)
        melody = copy.deepcopy(self)
        melody.append(list(other))
        return melody

    def save_midi(self, path: PathLike):
        self.write("midi", path)

    @classmethod
    def sum(cls, melodies: list[Melody]) -> Melody:
        result = Melody()
        for melody in melodies:
            result += melody
        return result


@dataclass
class MelodyData:
    """
    melody is for service, scheme is for ui
    """

    melody: Optional[Melody] = None
    scheme: list[Optional[Pitch]] = None

    @classmethod
    def empty(cls, grid: Grid):
        return cls(Melody(), [None] * grid.value)


def _get_random_melody(
        pitch_set: list[Pitch],
        note_count: int,
        grid: Grid,
        chord: Optional[Chord] = None,
        chord_tones_threshold: Optional[float] = 1.0
) -> MelodyData:

    cells = [None] * grid.value

    if not pitch_set:
        return MelodyData(Melody(), cells)

    if note_count < 1:
        return MelodyData(Melody(), cells)

    note_count = min([note_count, grid.value])

    grid_indices = list(range(grid.value))
    note_indices = random.sample(grid_indices, k=note_count)
    note_indices.sort()

    if not chord:
        pitches = random.choices(pitch_set, k=note_count)
    else:
        chord_pitch_names = [p.name for p in chord.pitches]
        chord_tones = [p for p in pitch_set if p.name in chord_pitch_names]
        if not chord_tones:
            pitches = random.choices(pitch_set, k=note_count)
        else:
            chord_note_count = math.ceil(note_count * chord_tones_threshold)
            any_note_count = note_count - chord_note_count
            chord_pitches = random.choices(chord_tones, k=chord_note_count)
            any_pitches = random.choices(pitch_set, k=any_note_count)
            pitches = chord_pitches + any_pitches
            random.shuffle(pitches)

    for note_idx, pitch in zip(note_indices, pitches):
        cells[note_idx] = pitch

    cell_duration = Duration(quarterLength=4/grid.value)
    melody_objects = []
    for cell in cells:
        if cell:
            melody_objects.append(Note(pitch=cell, duration=cell_duration))
        else:
            melody_objects.append(Rest(duration=cell_duration))

    return MelodyData(Melody(melody_objects), cells)


@lru_cache(maxsize=None)
def _get_scale_pitches(scale_name: str) -> list[Pitch]:
    scales = SCALES_YML.read()
    if not scales:
        return []
    return [Pitch(p) for p in scales.get(scale_name, [])]


@lru_cache(maxsize=None)
def _get_rhythm_stream(rhythm_name: str, chord: Triad) -> Stream:

    if not chord:
        return Stream([Rest(duration=Duration(quarterLength=4))])

    rhythm = RHYTHMS_YML.read()

    if not rhythm:
        return Stream([Rest(duration=Duration(quarterLength=4))])
    scheme = rhythm.get(rhythm_name)
    if not scheme:
        return Stream([Rest(duration=Duration(quarterLength=4))])

    result = Stream()

    root_pitches = {
        "A": "A2",
        "A#": "A#2",
        "B": "B2",
        "C": "C3",
        "C#": "C3",
        "D": "D3",
        "D#": "D#2",
        "E": "E2",
        "F": "F2",
        "F#": "F#2",
        "G": "G2",
        "G#": "G#2"
    }
    pitch_i = Pitch(root_pitches[chord.name if chord.is_major else chord.name[:-1]])
    pitch_iii = pitch_i.transpose(4 if chord.is_major else 3)
    pitch_v = pitch_i.transpose(7)
    pitch_I = pitch_i.transpose(12)
    pitch_III = pitch_I.transpose(4 if chord.is_major else 3)
    pitch_5 = pitch_i.transpose(-5)

    duration = Duration(quarterLength=0.25)
    for i in range(16):
        chord_notes = []
        if scheme["5"][i] != "-":
            note = Note(pitch_5, duration=duration)
            note.volume.velocity = 48
            chord_notes.append(note)
        if scheme["i"][i] != "-":
            note = Note(pitch_i, duration=duration)
            note.volume.velocity = 48
            chord_notes.append(note)
        if scheme["iii"][i] != "-":
            note = Note(pitch_iii, duration=duration)
            note.volume.velocity = 48
            chord_notes.append(note)
        if scheme["v"][i] != "-":
            note = Note(pitch_v, duration=duration)
            note.volume.velocity = 48
            chord_notes.append(note)
        if scheme["I"][i] != "-":
            note = Note(pitch_I, duration=duration)
            note.volume.velocity = 48
            chord_notes.append(note)
        if scheme["III"][i] != "-":
            note = Note(pitch_III, duration=duration)
            note.volume.velocity = 48
            chord_notes.append(note)

        if chord_notes:
            result.append(Chord(chord_notes))
        else:
            result.append(Rest(duration=duration))

    return result


class Service:

    @dataclass
    class Params:

        @dataclass
        class BarParams:
            chord: Optional[Triad]
            active: bool
            melody_data: MelodyData

        bars: list[BarParams]
        scale_name: str
        note_count: int
        grid: Grid
        chord_tones_threshold: float
        rhythm_name: Optional[str] = None

    @staticmethod
    def process_four_bars(params: Params) -> list[MelodyData]:

        scale_pitches = _get_scale_pitches(params.scale_name)

        melodies_data = []
        rhythms = []
        for bar in params.bars:
            if not bar.active:
                melodies_data.append(bar.melody_data)
            else:
                melody_data = _get_random_melody(
                    pitch_set=scale_pitches,
                    note_count=params.note_count,
                    grid=params.grid,
                    chord=bar.chord,
                    chord_tones_threshold=params.chord_tones_threshold
                )
                melodies_data.append(melody_data)

            rhythms.append(_get_rhythm_stream(params.rhythm_name, bar.chord))

        melody_4 = Melody.sum([md.melody for md in melodies_data])
        rhythm = Melody.sum([Melody(r) for r in rhythms])
        stream = Stream()
        stream.insert(0, melody_4)
        stream.insert(0, rhythm)
        filename = str(len(MIDI_FOLDER.files()) + 1) + ".mid"
        filepath = MIDI_FOLDER.path / filename
        stream.write("midi", filepath)
        os.startfile(filepath)

        return melodies_data

    @staticmethod
    def open_app_folder() -> None:
        os.startfile(APP_DIR)

    @staticmethod
    @lru_cache(maxsize=None)
    def get_scale_names() -> list[str]:
        scales = SCALES_YML.read()
        if not scales:
            return []
        else:
            return list(scales.keys())

    @staticmethod
    @lru_cache(maxsize=None)
    def get_rhythm_names() -> list[str]:
        rhythms = RHYTHMS_YML.read()
        if not rhythms:
            return []
        return list(rhythms.keys())
