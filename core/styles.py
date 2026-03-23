class Styling:
    """Centralized Design System mapping globally consistent UI constraints for child-friendly layouts."""
    
    # Typography
    FONT_PRIMARY = "'Nunito', 'Comic Sans MS', sans-serif"
    FONT_SECONDARY = "Arial, sans-serif"
    
    # Global Backgrounds & Text
    COLOR_BG_DEFAULT = "#F0F8FF"
    COLOR_TEXT_DARK = "#333333"
    COLOR_ROBOT_TEXT = "#4CAF50"
    
    # Dedicated 5E Module Background Themes (Mapped from native .ui files)
    THEME_ELABORATE_BG = "#E8F5E9"  # Mint Green
    THEME_EXPLAIN_BG = "#E3F2FD"    # Calm Blue
    THEME_EXPLORE_BG = "#FCE4EC"    # Vibrant Pink
    THEME_ENGAGE_BG = "#FFF9C4"     # Warm Yellow
    THEME_TEACHER_BG = "#E3F2FD"    # Soft Sky Blue
    
    # Call-to-Action Highlights
    COLOR_SUCCESS_GREEN = "#4CAF50"
    COLOR_WARNING_ORANGE = "#E65100"
    
    # Borders & Geometry
    BORDER_RADIUS_LARGE = "20px"
    BORDER_RADIUS_SMALL = "10px"
    BORDER_WIDTH_THICK = "4px"

def apply_global_font(app):
    """Dynamically applies the exact child-friendly master typography stack globally across the entire Qt framework kernel."""
    base_css = f"QWidget {{ font-family: {Styling.FONT_PRIMARY}; }}"
    app.setStyleSheet(base_css)
