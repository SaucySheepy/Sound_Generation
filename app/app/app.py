import reflex as rx
from .state import State
from . import styles

def sidebar() -> rx.Component:
    """The side navigation pane."""
    return rx.vstack(
        rx.heading("Studio", style=styles.heading_style, size="6", margin_bottom="20px"),
        
        rx.vstack(
            rx.button("Acoustic Guitar", width="100%", variant="solid", color_scheme="purple"),
            rx.button("Electric Bass", width="100%", variant="ghost", disabled=True),
            rx.button("Piano", width="100%", variant="ghost", disabled=True),
            spacing="2",
            width="100%"
        ),
        
        rx.spacer(),
        rx.text("v0.9.0 (Beta)", color=styles.colors["muted"], size="1"),
        
        style=styles.sidebar_style
    )

def physics_controls() -> rx.Component:
    """The Luthier's Workbench Panel"""
    return rx.vstack(
        rx.heading("Luthier's Workbench", size="4", color=styles.colors["accent"]),
        rx.divider(margin_y="10px"),
        
        rx.text(f"Decay Factor: {State.sustain}", size="1"),
        rx.slider(
            default_value=[0.99],
            min=0.5, max=0.999, step=0.001,
            on_change=State.update_sustain,
            style=styles.slider_style
        ),
        
        rx.text(f"Stiffness: {State.stiffness}", size="1"),
        rx.slider(
            default_value=[-0.7],
            min=-1.0, max=0.0, step=0.01,
            on_change=State.update_stiffness,
            style=styles.slider_style
        ),
        
        style=styles.card_style,
        width="100%"
    )

def index() -> rx.Component:
    return rx.flex(
        sidebar(),
        
        # Main Content area
        rx.container(
            rx.vstack(
                rx.heading("Acoustic Guitar", size="8", style=styles.heading_style),
                rx.text("Physical Modeling Engine", color=styles.colors["muted"]),
                
                rx.separator(margin_y="20px"),
                
                # Layout: Controls on Left, Sequencer on Right
                rx.flex(
                    rx.box(
                        physics_controls(),
                        width=["100%", "100%", "300px"], 
                        margin_right="20px"
                    ),
                    
                    rx.box(
                        rx.heading("Sequencer", size="5", margin_bottom="10px"),
                        rx.button("Play 'Canon in D'", on_click=State.play_song, color_scheme="green", width="100%", size="3"),
                        
                        rx.heading("Chords", size="5", margin_top="20px", margin_bottom="10px"),
                        rx.grid(
                            rx.button("E Maj", on_click=lambda: State.play_chord("E Major"), variant="outline"),
                            rx.button("A Maj", on_click=lambda: State.play_chord("A Major"), variant="outline"),
                            rx.button("G Maj", on_click=lambda: State.play_chord("G Major"), variant="outline"),
                            rx.button("D Maj", on_click=lambda: State.play_chord("D Major"), variant="outline"),
                            rx.button("C Maj", on_click=lambda: State.play_chord("C Major"), variant="outline"),
                            columns="3",
                            spacing="3",
                            width="100%"
                        ),
                        flex="1"
                    ),
                    flex_direction=["column", "column", "row"],
                    width="100%"
                ),
                
                on_mount=State.on_load,
                spacing="5",
                padding="40px",
                max_width="1200px",
            ),
            style=styles.base_container
        ),
        
        width="100%",
        min_height="100vh",
        background_color=styles.colors["background"]
    )

# Create the App
app = rx.App()
app.add_page(index)