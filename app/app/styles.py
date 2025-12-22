import reflex as rx

colors = {
    "background": "#1A1B26",
    "surface": "#24283B",
    "primary": "#7AA2F7",      # Blue
    "accent": "#E0AF68",       # Gold
    "text": "#C0CAF5",
    "muted": "#565F89", 
    "border": "#414868",
}

# --- Component Styles ---
base_container = {
    "bg": colors["background"],
    "min_height": "100vh",
    "color": colors["text"],
    "font_family": "Inter, sans-serif",
}
sidebar_style = {
    "width": "250px",
    "height": "100vh",
    "bg": colors["surface"],
    "padding": "20px",
    "border_right": f"1px solid {colors['border']}",
    "display": ["none", "none", "block"], # Only show on desktop
}
card_style = {
    "bg": colors["surface"],
    "padding": "20px",
    "border_radius": "12px",
    "border": f"1px solid {colors['border']}",
}
heading_style = {
    "color": colors["primary"],
    "font_weight": "bold",
}
slider_style = {
    "color_scheme": "purple", 
    "padding_y": "10px"
}