import random

grades = {
    'I': 0,
    'II': 1,
    'III': 2,
    'IV': 3,
    'V': 4,
    'VI': 5,
    'VII': 6
}

notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

happy_chords = [["Imaj7", "IVmaj7", "V7", "IVmaj7"], ["Imaj7", "IVmaj7", "V7", "VIm"], ["Imaj7", "V7", "VIm", "IVmaj7"], ["Imaj7", "V7", "VIm", "IVmaj7"], [
    "Imaj7", "VIm", "IVmaj7", "V7"], ["IV", "Imaj7", "V7", "VIm7"], ["IV", "V7", "Imaj7", "VIm6"], ["IV", "VIm", "Imaj7", "V7"]]
sad_chords = [["VIm", "IVmaj7", "Imaj7", "V7"], ["VIm", "IVmaj7", "Imaj7", "V9"], ["Imaj7", "VII", "VIm", "V7"], [
    "Imaj7", "VIm", "IIIm", "VII"], ["Imaj7", "VII", "VIm", "IVmaj7"], ["Imaj7", "VIm", "IIIm", "IVmaj7"]]
dance_chords = [["Imaj7", "IVmaj7", "V7", "IVmaj7"], ["Imaj7", "IV6", "V7", "VIm6"], ["Imaj7", "VIm", "IVmaj7", "V7"], [
    "IIm7", "V7", "Imaj7", "Imaj7"], ["IVmaj7", "V7", "Imaj7", "VIm6"], ["V7", "VIm7", "IV7", "V7"], ["VIm", "IVmaj7", "Imaj7", "V7"]]
not_dance_chords = [["I7", "VII", "VIm7", "V7"], ["I6", "VIm7", "III7", "VII"], [
    "Imaj7", "VII", "VIm", "IV7"], ["VIm", "IVmaj7", "Imaj7", "V9"], ["VIm", "IVmaj7", "Imaj7", "V79"], ["IV", "Imaj7", "V7", "VIm7"]]

# TODO have different chord progressions for each mood
MOOD_CHORD_DICT = {
    'excited': happy_chords,
    'delighted': happy_chords,
    'happy': happy_chords,
    'content': happy_chords,
    'relaxed': not_dance_chords,
    'calm': not_dance_chords,
    'tired': sad_chords,
    'bored': sad_chords,
    'depressed': sad_chords,
    'frustrated': sad_chords,
    'angry': sad_chords,
    'tense': sad_chords,
}


def build_scale(key):
    ind = notes.index(key)
    major_scale = [notes[ind], notes[(ind + 2) % 12], notes[(ind + 4) % 12], notes[(
        ind + 5) % 12], notes[(ind + 7) % 12], notes[(ind + 9) % 12], notes[(ind + 11) % 12], notes[ind]]
    return major_scale


def choose_chords(va_value: str, key: str):
    moods = list(MOOD_CHORD_DICT.keys())

    if va_value not in moods:
        va_value = random.choice(moods)
    chords = random.choice(MOOD_CHORD_DICT[va_value])

    if key is None:
        key = random.choice(notes)
    scale = build_scale(key)
    new_chords = []
    for seq in chords:
        removed = seq.replace('7', '').replace('a', '').replace(
            '6', '').replace('9', '').replace('b', '').replace('m', '').replace('j', '').replace('5', '')
        if (removed != seq):
            removed_element = ""
            for lettera in seq:
                if lettera not in removed:
                    removed_element += lettera
        else:
            removed_element = ''

        new_chords.append(scale[grades[removed]]+removed_element)

    return new_chords, key
