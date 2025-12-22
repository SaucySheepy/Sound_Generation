import reflex as rx
from .audio_manager import audio_manager
from .engine import note_to_freq

class State(rx.State):
    """The app state."""
    # Physics Parameters
    frequency: float = 440.0
    sustain: float = 0.99
    
    # New Controls
    stiffness: float = -0.7
    resonance: float = 100.0
    
    def on_load(self):
        print("App started, initializing audio")
        audio_manager.initialize()

    # --- Setters ---
    def update_freq(self, value: list[float]):
        self.frequency = value[0]
        audio_manager.set_frequency(self.frequency)

    def update_sustain(self, value: list[float]):
        self.sustain = value[0]
        audio_manager.set_sustain(self.sustain)
        
    def update_stiffness(self, value: list[float]):
        self.stiffness = value[0]
        audio_manager.set_stiffness(self.stiffness)
        print(f"Stiffness updated to {self.stiffness}")

    def play_chord(self, chord_name: str):
        chords = {
            "E Major": ["E2", "B2", "E3", "G#3", "B3", "E4"],
            "A Major": ["A2", "E3", "A3", "C#4", "E4", "A4"],
            "G Major": ["G2", "B2", "D3", "G3", "B3", "G4"],
            "D Major": ["D3", "A3", "D4", "F#4", "A4"], 
            "C Major": ["C3", "E3", "G3", "C4", "E4"]
        }
        if chord_name in chords:
            notes = chords[chord_name]
            freqs = [note_to_freq(n) for n in notes]
            audio_manager.strum(freqs)

    def play_note(self, note_name: str):
        freq = note_to_freq(note_name)
        audio_manager.strum([freq])

    def play_song(self):
        def _song_thread():
            import time
            from .engine import note_to_freq
            
            chords = {
                "Am_low": ["A2", "E3"],
                "Am_full": ["A3", "C4", "E4"],
                "C_low": ["C3", "E3"],
                "C_full": ["G3", "C4", "E4"],
                "D_low": ["D3", "A3"],
                "D_full": ["D4", "F#4"],
            }
            
            loop = ["Am", "C", "D", "Am"]
            
            for chord in loop:
                low = chords[f"{chord}_low"]
                full = chords[f"{chord}_full"]
                
                for note in low:
                    audio_manager.strum([note_to_freq(note)], duration=0.0)
                    time.sleep(0.3)
                
                audio_manager.strum([note_to_freq(n) for n in full], duration=0.1, direction='down')
                time.sleep(1)
        
        import threading
        threading.Thread(target=_song_thread, daemon=True).start()