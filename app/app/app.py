"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx
from .audio_manager import audio_manager
from .engine import note_to_freq

class State(rx.State):
    """The app state."""
    #These variables automatically sunc between python and js
    frequency: float = 440.0
    sustain:float = 0.99

    def on_load(self):
        print("App started, initializing audio")
        audio_manager.initialize()

    def update_freq(self, value:list[float]):
        self.frequency = value[0]
        audio_manager.set_frequency(self.frequency)

    def update_sustain(self, value: list[float]):
        self.sustain = value[0]
        audio_manager.set_sustain(self.sustain)

    def pluck_string(self):
        audio_manager.pluck()

    def play_chord(self, chord_name: str):
        # ... existing chord logic ...
        # (Define chords as lists of notes)
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
        # Strumming a single note is just a pluck
        audio_manager.strum([freq])

    def play_song(self):
        def _song_thread():
            import time
            from .engine import note_to_freq
            
            # Simple, standard voicings
            chords = {
                "Am_low": ["A2", "E3"],       # The "Pick-Pick" part
                "Am_full": ["A3", "C4", "E4"],# The "Strum" part
                "C_low": ["C3", "E3"],
                "C_full": ["G3", "C4", "E4"],
                "D_low": ["D3", "A3"],
                "D_full": ["D4", "F#4"],
            }
            
            # Sequence: Am -> C -> D -> Am
            loop = ["Am", "C", "D", "Am"]
            
            for chord in loop:
                low = chords[f"{chord}_low"]
                full = chords[f"{chord}_full"]
                
                # 1. The "Pick-Pick" (Slowly pluck the bass notes)
                for note in low:
                    audio_manager.strum([note_to_freq(note)], duration=0.0)
                    time.sleep(0.4)
                
                # 2. The "Strum" (Sweep the rest of the chord)
                audio_manager.strum([note_to_freq(n) for n in full], duration=0.1, direction='down')
                
                time.sleep(2) # Let it ring out...
        
        import threading
        threading.Thread(target=_song_thread, daemon=True).start()


def index() -> rx.Component:
    # Welcome Page (Index)
    return rx.container(
        rx.vstack(
            rx.heading("Physical Modeling Synth", size="8"),

            rx.text("Interactive Guitar", size="2", color="gray"),

            rx.heading("Interactive Keypad (Octaves 2-6)", size="6", margin_top="20px"),
            rx.scroll_area(
                rx.vstack(
                    *[
                        rx.vstack(
                            rx.text(f"Octave {oct}"),
                            rx.hstack(
                                *[rx.button(n, 
                                            on_click=State.play_note(n + str(oct)),
                                            variant="outline",
                                            size="1") 
                                  for n in ["C", "D", "E", "F", "G", "A", "B"]],
                                spacing="1",
                            ),
                            align_items="center",
                            padding_y="5px",
                        ) for oct in range(2, 7) # Octaves 2, 3, 4, 5, 6
                    ],
                    width="100%",
                ),
                style={"height": "300px", "border": "1px solid #444", "padding": "10px", "border_radius": "8px"}
            ),

            rx.divider(margin_y="20px"),
            
            # Legacy Controls (Frequency Slider)
            rx.heading("Physics Controls", size="4"),
            rx.text(f"Decay Factor: {State.sustain}"),
            rx.slider(
                default_value=[0.99],
                min=0.5,
                max=0.999,
                step=0.001,
                on_change=State.update_sustain,
                width="100%"
            ),
            rx.heading("Sequencer", size="6", margin_top="20px"),
            rx.button("Play Song", on_click=State.play_song, color_scheme="purple", width = "100%"),
            rx.heading("Chords", size="6", margin_top="20px"),
            rx.hstack(
                rx.button("E Major", on_click=lambda: State.play_chord("E Major"), color_scheme="green"),
                rx.button("A Major", on_click=lambda: State.play_chord("A Major"), color_scheme="blue"),
                rx.button("G Major", on_click=lambda: State.play_chord("G Major"), color_scheme="orange"),
                rx.button("D Major", on_click=lambda: State.play_chord("D Major"), color_scheme="yellow"),
                rx.button("C Major", on_click=lambda: State.play_chord("C Major"), color_scheme="red"),
                spacing="4",
                wrap="wrap",
                width="100%",
                justify="center"
            ),

            on_mount = State.on_load,
            spacing="5",
            padding="20px",
            max_width="600px",
        )
    )

app = rx.App()
app.add_page(index)
