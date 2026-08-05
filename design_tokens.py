"""Shared design tokens for Karthik Rajesh Shet's AI & Developer profile aesthetic."""

DESIGN_TOKENS = {
    "surface": "#0D1117",
    "surface_raised": "#161B22",
    "surface_inset": "#21262D",
    "primary": "#2563EB",         # Electric Blue
    "primary_soft": "#3B82F6",
    "accent": "#7C3AED",          # Cyber Anime Purple
    "accent_pink": "#EC4899",     # Sakura Pink
    "accent_cyan": "#06B6D4",     # Cyber Cyan
    "on_surface": "#F0F6FC",
    "on_surface_variant": "#8B949E",
    "on_surface_faint": "#484F58",
    "on_surface_bright": "#FFFFFF",
    "outline": "#30363D",
    "heatmap_0": "#161B22",
    "heatmap_1": "#0E4429",
    "heatmap_2": "#006D32",
    "heatmap_3": "#26A641",
    "heatmap_4": "#39D353",
    "pill_surface": "#161B22",
}

LAYOUT = {
    "card_width": 900,
    "card_radius": 12,
    "content_inset": 28,
    "pill_height": 28,
    "chip_height": 24,
}


def token(name: str) -> str:
    return DESIGN_TOKENS[name]


def token_param(name: str) -> str:
    return token(name).lstrip("#")


def layout(name: str):
    return LAYOUT[name]

