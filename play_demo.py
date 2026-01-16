
import time
import threading
import sounddevice as sd
from app.app.instruments.acoustic_guitar import AcousticGuitar
from app.app.music.chords import get_chord_freqs
from app.app.physics.core import note_to_freq
import numpy as np

class GuitarSequencer:
    def __init__(self, guitar_model=None):
        self.guitar = guitar_model if guitar_model else AcousticGuitar()
        self.stop_event = threading.Event()
        
    def play_scale_run(self, notes, duration=0.25):
        """Plays a sequence of single notes (scale)."""
        print(f"   --> SCALE: {notes}")
        for note in notes:
            if self.stop_event.is_set(): return
            freq = note_to_freq(note)
            
            # Alternate picking dynamics
            vel = np.random.uniform(0.9, 1.0)
            
            self.guitar.play(freq, velocity=vel, sustain_time=2.0)
            time.sleep(duration)

    def play_chord(self, chord_name, duration=1.0, strum_speed=0.02, direction='down'):
        """Strums a chord pattern with direction."""
        freqs = get_chord_freqs(chord_name)
        
        if direction == 'up':
            freqs = freqs[::-1] 
            strum_speed *= 0.7 # Upstrokes are usually faster/snappier
            
        # Limit strum speed so we don't exceed duration
        # A strum shouldn't take more than 50% of the beat usually
        safe_strum_time = min(strum_speed * len(freqs), duration * 0.5)
        actual_strum_speed = safe_strum_time / max(1, len(freqs))

        for i, freq in enumerate(freqs):
            if self.stop_event.is_set(): return
            
            # Velocity Humanization
            # Downstrokes: Heavy on bass (first strings). Upstrokes: Light on bass (last strings).
            # We map i (0..5) to velocity. 
            if direction == 'down':
                # Downstroke: i=0 is bass. High vel -> Low vel
                vel = 1.0 - (i * 0.05) 
            else:
                # Upstroke: i=0 is treble (because we reversed freqs). High vel -> Low vel
                vel = 0.9 - (i * 0.05)
                
            # Random jitter
            vel *= np.random.uniform(0.9, 1.1)
            vel = np.clip(vel, 0.4, 1.0) # Ensure minimal volume
            
            self.guitar.play(freq, velocity=vel, sustain_time=4.0)
            time.sleep(actual_strum_speed)
            
        remaining_time = max(0, duration - safe_strum_time)
        time.sleep(remaining_time)

    def run_playlist(self):
        print("Starting Guitar Playlist. Press Ctrl+C to stop.")
        
        # 1. POP PROGRESSION (Strummed)
        pop_prog = ["Am", "F_Major", "C_Major", "G_Major"]
        # Tighter Rhythm Pattern
        pop_rhythm = [
            (1.0, 'down'), (0.5, 'down'), (0.5, 'up'), 
            (1.0, 'down'), (0.5, 'down'), (0.5, 'up')
        ]
        
        # 2. BLUES-ISH (Slower, open chords)
        rock_prog = ["E_Major", "A_Major", "E_Major", "B_Major"]
        rock_rhythm = [(2.0, 'down'), (1.0, 'down'), (1.0, 'up')]
        
        # 3. SOLO RUN (Single Notes - E Minor Pentatonic)
        # E G A B D E
        solo_notes_1 = ["E2", "G2", "A2", "B2", "D3", "E3"]
        solo_notes_2 = ["G3", "A3", "B3", "D4", "E4", "G4"] # High part
        
        beat_duration = 60.0 / 120.0 # 120 BPM base
        
        try:
            while not self.stop_event.is_set():
                print("\n--- TRACK 1: INDIE POP STRUM (x2) ---")
                for _ in range(2):
                    for chord_name in pop_prog:
                        # print(f"[{chord_name}]")
                        for dur, dir in pop_rhythm:
                            if self.stop_event.is_set(): break
                            # MUCH tighter strumming: 15ms per string (0.015) base
                            base_speed = 0.015 if dur < 1.0 else 0.025
                            self.play_chord(chord_name, duration=beat_duration*dur, strum_speed=base_speed, direction=dir)

                print("\n--- TRACK 2: GUITAR SOLO (Scales) ---")
                # Fast run up
                self.play_scale_run(solo_notes_1, duration=beat_duration/2) # 8th notes
                self.play_scale_run(solo_notes_2, duration=beat_duration/2)
                # Hold high note
                self.guitar.play(note_to_freq("E5"), velocity=1.0, sustain_time=4.0)
                time.sleep(beat_duration*4)

                print("\n--- TRACK 3: SLOW ROCK (x2) ---")
                for _ in range(2):
                    for chord_name in rock_prog:
                        print(f"[{chord_name}]")
                        for dur, dir in rock_rhythm:
                            if self.stop_event.is_set(): break
                            # Slower strum for rock
                            self.play_chord(chord_name, duration=beat_duration*dur, strum_speed=0.06, direction=dir)

        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            self.stop_event.set()

def run_standalone_demo():
    print("--- Guitar Physics Engine Concert ---")
    sequencer = GuitarSequencer()
    
    def callback(outdata, frames, time, status):
        block = sequencer.guitar.process_block(frames)
        outdata[:] = block

    # Start Audio Stream
    # Increased blocksize to 2048 to prevent underruns/choppiness
    with sd.OutputStream(channels=2, callback=callback, samplerate=44100, blocksize=2048, latency='high'):
        sequencer.run_playlist()

if __name__ == "__main__":
    run_standalone_demo()
