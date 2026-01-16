
from ..physics.core import note_to_freq

# Standard "Open" Guitar Chord Voicings (6 strings: E A D G B e)
# 'x' means muted/not played
CHORD_SHAPES = {
    # Major Chords
    "C_Major":  ["x", "C3", "E3", "G3", "C4", "E4"],  # x32010
    "G_Major":  ["G2", "B2", "D3", "G3", "B3", "G4"], # 320003
    "D_Major":  ["x", "x", "D3", "A3", "D4", "F#4"],  # xx0232
    "A_Major":  ["x", "A2", "E3", "A3", "C#4", "E4"], # x02220
    "E_Major":  ["E2", "B2", "E3", "G#3", "B3", "E4"],# 022100
    "F_Major":  ["F2", "C3", "F3", "A3", "C4", "F4"], # 133211 (Barre)

    # Minor Chords
    "Am": ["x", "A2", "E3", "A3", "C4", "E4"],      # x02210
    "Em": ["E2", "B2", "E3", "G3", "B3", "E4"],     # 022000
    "Dm": ["x", "x", "D3", "A3", "D4", "F4"],       # xx0231
    "Bm": ["x", "B2", "F#3", "B3", "D4", "F#4"],    # x24432 (Barre)
}

def get_chord_freqs(chord_name):
    """Returns a list of frequencies for a named chord."""
    notes = CHORD_SHAPES.get(chord_name, [])
    freqs = []
    for note in notes:
        if note != "x":
            freqs.append(note_to_freq(note))
    return freqs
