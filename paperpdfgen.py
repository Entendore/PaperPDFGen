#!/usr/bin/env python3
"""
Paper PDF Generator v7 — Full-featured PySide6 desktop app for printable paper PDFs.
77 paper types with extensive customization options.
"""

import sys, os, json, math, copy
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox,
    QPushButton, QFileDialog, QScrollArea, QToolBar,
    QCheckBox, QSizePolicy, QMessageBox, QFrame, QFormLayout,
    QColorDialog, QProgressDialog, QDialog, QDialogButtonBox,
    QListWidget, QListWidgetItem, QMenu, QInputDialog,
    QAbstractSpinBox, QToolButton, QStatusBar, QMenuBar
)
from PySide6.QtCore import Qt, QRectF, Signal, QSize, QPoint, QPointF
from PySide6.QtGui import (
    QPainter, QPen, QColor, QBrush, QFont, QAction,
    QKeySequence, QCursor, QPolygonF
)
from fpdf import FPDF

IN_TO_PT = 72.0
MM_TO_PT = 2.83465

def _norm_ppf(p):
    """Rational approximation of the normal distribution inverse CDF (probit)."""
    if p <= 0: return -4.0
    if p >= 1: return 4.0
    if p < 0.5:
        return -_norm_ppf(1.0 - p)
    # Beasley-Springer-Moro algorithm
    t = math.sqrt(-2.0 * math.log(1.0 - p))
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    return t - (c0 + c1*t + c2*t*t) / (1.0 + d1*t + d2*t*t + d3*t*t*t)

APP_NAME = "Paper PDF Generator"
PRESETS_FILE = os.path.join(Path.home(), ".paper_pdf_generator_presets.json")

PAPER_TYPES = [
    "Graph Paper",
    "College Ruled",
    "Wide Ruled",
    "Lined Paper",
    "Dot Grid",
    "Isometric",
    "Cornell Notes",
    "Engineering Paper",
    "Hexagonal Grid",
    "Music Staff",
    "Calligraphy Guide",
    "To-Do List",
    "Kanban Board",
    "Penmanship",
    "Cross Stitch",
    "Piano Keys",
    "Storyboard",
    "Grid Diary",
    "Japanese Genkoyoushi",
    "Meeting Notes",
    "Weekly Planner",
    "Budget Tracker",
    "Reading Log",
    "Seyes French Ruled",
    "Polar Coordinate",
    "Logarithmic Paper",
    "Probability Paper",
    "Seam Allowance",
    "Knitting Grid",
    "Circuit / Schematic",
    "Braille Practice",
    "Musical TAB",
    "Ledger / Accounting",
    "Daily Schedule",
    "Habit Tracker",
    "Recipe Card",
    "Perspective Grid",
    "Mandala Guide",
    "Guitar Chord Diagram",
    "Venn Diagram",
    "Study Notes",
    "Project Planner",
    "Fitness Log",
    "Weight Tracker",
    "Travel Journal",
    "Essay Outline",
    "Grand Staff Paper",
    "Dotted Lined",
    "Weekly Meal Planner",
    "Sleep Tracker",
    "Mood Tracker",
    "Lesson Plan",
    "Expense Tracker",
    "Baseball Scorecard",
    "Atom Diagram",
    "Quadrille Paper",
    "Spiral Grid",
    "Basketball Stat Sheet",
    "Chore Chart",
    "Water Intake Tracker",
    "Phone Call Log",
    "Blood Pressure Log",
    "SWOT Analysis",
    "Doodle Pad",
    "Comic Panel Layout",
    "Gardening Planner",
    "Timeline",
    "Insect Observation Log",
    "Medication Log",
    "Number Bonds",
    "Stargazing Log",
    "Writing Sprint Tracker",
    "Attendance Register",
    "Chess Score Sheet",
    "Wish List",
    "Gratitude Journal",
    "Blank",
]


PAGE_SIZES = {
    "US Letter (8.5 x 11 in)": (8.5 * 72, 11 * 72),
    "A4 (210 x 297 mm)":      (595.28, 841.89),
    "A3 (297 x 420 mm)":      (841.89, 1190.55),
    "A5 (148 x 210 mm)":      (419.53, 595.28),
    "Legal (8.5 x 14 in)":    (8.5 * 72, 14 * 72),
    "Tabloid (11 x 17 in)":   (11 * 72, 17 * 72),
    "B5 (176 x 250 mm)":      (498.90, 708.66),
}

DEFAULT_PARAMS = {
    "Graph Paper": {"grid_size": 0.25, "major_every": 4, "line_style": "solid", "color": "#000080", "line_width": 0.3, "major_width": 0.7, "secondary_color": "#000040", "show_axis": False, "axis_width": 1.5, "show_labels": False, "label_font_size": 7},
    "College Ruled": {"line_spacing": 0.375, "margin_left": 1.5, "line_style": "solid", "color": "#4472C4", "line_width": 0.3, "secondary_color": "#FF0000", "show_top_margin": True, "top_margin": 1.0, "double_line": False, "line_opacity": 1.0, "right_margin": 1.0},
    "Wide Ruled": {"line_spacing": 0.5, "margin_left": 1.25, "line_style": "solid", "color": "#4472C4", "line_width": 0.3, "secondary_color": "#FF0000", "show_top_margin": True, "top_margin": 1.0, "double_line": False, "line_opacity": 1.0, "right_margin": 1.0},
    "Lined Paper": {"line_spacing": 0.5, "margin_left": 1.0, "line_style": "solid", "color": "#666666", "line_width": 0.25, "secondary_color": "#999999", "show_top_margin": True, "top_margin": 1.0, "double_line": False, "line_opacity": 1.0, "right_margin": 1.0},
    "Dot Grid": {"dot_spacing": 0.2, "dot_radius": 0.8, "dot_style": "filled", "major_dots_every": 5, "major_dot_radius": 1.5, "color": "#999999", "dot_opacity": 1.0, "offset_x": 0.0, "offset_y": 0.0},
    "Isometric": {"grid_size": 0.25, "color": "#CC6600", "line_width": 0.3, "show_axis": False, "axis_width": 1.5, "triangle_size": False, "margin": 0.0},
    "Cornell Notes": {"line_spacing": 0.375, "cue_width": 2.5, "summary_height": 2.0, "show_labels": True, "color": "#4472C4", "line_width": 0.3, "secondary_color": "#94A3B8", "notes_line_style": "dashed", "cue_line_style": "solid", "show_date_field": True, "column_split_ratio": 0.3},
    "Engineering Paper": {"grid_size": 0.2, "major_every": 5, "color": "#006633", "line_width": 0.2, "major_width": 0.6, "border": True, "secondary_color": "#00994D", "show_title_block": False, "title_block_width": 2.5, "title_block_height": 1.0, "zone_labels": False},
    "Hexagonal Grid": {"hex_size": 0.25, "orientation": "flat_top", "fill_hexagons": False, "color": "#6600CC", "line_width": 0.3, "secondary_color": "#E8D5F5", "border_hexes": False, "opacity": 1.0},
    "Music Staff": {"staff_spacing": 0.125, "group_spacing": 0.6, "num_staves": 6, "show_barlines": False, "barline_interval": 2.0, "color": "#000000", "line_width": 0.3, "show_clef": False, "show_time_signature": False, "staff_label_font": 8},
    "Calligraphy Guide": {"guide_spacing": 0.5, "ascender": 0.2, "descender": 0.2, "slant_angle": 52, "show_slant": True, "color": "#CC0000", "line_width": 0.25, "secondary_color": "#FF8888", "num_nibs": 1, "nib_width": 0.1, "show_x_height": True},
    "To-Do List": {"line_spacing": 0.5, "margin_left": 0.75, "checkbox_size": 0.25, "show_numbers": False, "priority_col": False, "color": "#333333", "line_width": 0.3, "secondary_color": "#2563EB", "show_date_column": False, "date_col_width": 0.8, "show_priority": False, "category_column": False},
    "Kanban Board": {"num_columns": 3, "column_spacing": 0.25, "cards_per_col": 3, "color": "#333333", "line_width": 0.5, "secondary_color": "#94A3B8", "card_height": 0.7, "show_due_date": False, "show_priority_badge": False},
    "Penmanship": {"line_spacing": 0.5, "midline_offset": 0.0, "descender_depth": 0.0, "color": "#0000CC", "line_width": 0.2, "secondary_color": "#AAAAAA", "show_ascender": True, "ascender_height": 0.0, "line_color_mode": "single"},
    "Cross Stitch": {"grid_size": 0.1, "show_numbers": False, "color": "#AAAAAA", "line_width": 0.2, "major_every": 10, "major_color": "#555555", "major_width": 0.6, "show_symbols": False, "border_width": 0.5, "center_marks": True},
    "Piano Keys": {"num_octaves": 2, "key_height": 0.6, "show_labels": True, "color": "#000000", "line_width": 0.5, "secondary_color": "#FFFFFF", "show_octave_numbers": True, "start_octave": 3, "key_style": "classic"},
    "Storyboard": {"num_panels_w": 2, "num_panels_h": 3, "panel_gap": 0.2, "label_height": 0.3, "show_numbers": True, "color": "#333333", "line_width": 0.5, "secondary_color": "#94A3B8", "show_rule_of_thirds": False, "panel_border_radius": 0.0, "show_aspect_ratio": True},
    "Grid Diary": {"grid_cols": 7, "grid_rows": 5, "header_height": 0.5, "time_col_width": 0.6, "start_day": "Monday", "color": "#333333", "line_width": 0.3, "secondary_color": "#94A3B8", "show_week_numbers": False, "row_labels": "time", "alternate_row_shading": True},
    "Japanese Genkoyoushi": {"cell_size": 0.394, "margin_size": 0.591, "show_title_space": True, "color": "#CC0000", "line_width": 0.2, "secondary_color": "#AAAAAA", "show_field_guide": False, "grid_style": "full", "num_title_rows": 3},
    "Meeting Notes": {"title_area_height": 0.8, "agenda_rows": 5, "notes_line_spacing": 0.375, "action_rows": 5, "show_fields": True, "color": "#333333", "line_width": 0.3, "secondary_color": "#2563EB", "show_timer_section": False, "notes_columns": 1, "show_decision_box": False},
    "Weekly Planner": {"start_hour": 6, "end_hour": 22, "time_col_width": 0.6, "show_weekend": True, "time_interval": 1, "color": "#333333", "line_width": 0.3, "secondary_color": "#2563EB", "show_current_hour_line": False, "time_format": "12h", "column_labels": "short"},
    "Budget Tracker": {"income_rows": 5, "expense_rows": 10, "header_height": 0.5, "color": "#333333", "line_width": 0.3, "secondary_color": "#16A34A", "show_savings_section": False, "savings_rows": 3, "show_total_row": True, "category_col_width": 0.4},
    "Reading Log": {"entry_rows": 15, "header_height": 0.5, "color": "#333333", "line_width": 0.3, "secondary_color": "#94A3B8", "show_genre_column": False, "show_progress_bar": False, "row_height": 0.25},
    "Seyes French Ruled": {"line_spacing": 0.315, "margin_left": 0.5, "num_lines": 8, "color": "#0066CC", "line_width": 0.2, "secondary_color": "#FF6699", "show_top_margin": True, "margin_style": "single", "pink_line_offset": 2.0},
    "Polar Coordinate": {"radius_step": 0.5, "num_radials": 12, "show_labels": True, "start_angle": 0, "label_radius": 0.3, "color": "#336699", "line_width": 0.3, "secondary_color": "#99BBDD"},
    "Logarithmic Paper": {"log_cycles": 3, "grid_size": 0.25, "show_labels": True, "color": "#006633", "line_width": 0.2, "secondary_color": "#66BB66", "margin": 1.0, "label_font_size": 7},
    "Probability Paper": {"grid_size": 0.5, "show_labels": True, "color": "#663399", "line_width": 0.3, "secondary_color": "#BB99DD", "margin": 1.0, "label_font_size": 7},
    "Seam Allowance": {"grid_size": 0.25, "show_quarter_mark": True, "show_five_eighths_mark": True, "margin_width": 1.0, "color": "#CC3333", "line_width": 0.2, "secondary_color": "#FF9999", "margin": 0.5, "label_font_size": 7},
    "Knitting Grid": {"grid_size": 0.25, "show_row_numbers": True, "show_col_numbers": True, "major_every": 10, "color": "#993366", "line_width": 0.2, "secondary_color": "#DDBBCC", "margin": 0.5, "major_line_weight": 2.0, "label_font_size": 6},
    "Circuit / Schematic": {"grid_size": 0.1, "dot_size": 1.0, "major_every": 5, "snap_dots": True, "color": "#003366", "line_width": 0.15, "secondary_color": "#6699CC", "margin": 0.25, "major_line_weight": 2.0},
    "Braille Practice": {"cell_spacing": 0.4, "dot_spacing": 0.08, "cell_size": 0.25, "show_guide_dots": True, "color": "#333333", "line_width": 0.3, "secondary_color": "#AAAAAA", "margin": 1.0, "dot_radius": 1.5},
    "Musical TAB": {"num_staves": 8, "staff_spacing": 0.15, "group_spacing": 0.5, "show_barlines": True, "barline_interval": 2.0, "color": "#000000", "line_width": 0.3, "secondary_color": "#666666"},
    "Ledger / Accounting": {"num_rows": 20, "num_debit_cols": 2, "num_credit_cols": 2, "header_height": 0.5, "show_totals_row": True, "color": "#333333", "line_width": 0.3, "secondary_color": "#16A34A"},
    "Daily Schedule": {"start_hour": 6, "end_hour": 22, "slot_height": 0.6, "time_col_width": 0.7, "show_15min": False, "color": "#333333", "line_width": 0.3, "secondary_color": "#2563EB"},
    "Habit Tracker": {"num_habits": 8, "show_weekday_headers": True, "show_month_header": True, "checkbox_size": 0.2, "color": "#333333", "line_width": 0.3, "secondary_color": "#2563EB", "days_in_month": 31, "label_width": 100, "row_padding": 12},
    "Recipe Card": {"show_prep_time": True, "show_cook_time": True, "show_servings": True, "show_difficulty": True, "ingredients_rows": 12, "instructions_lines": 15, "color": "#333333", "line_width": 0.3, "secondary_color": "#D97706"},
    "Perspective Grid": {"num_points": 1, "grid_size": 0.5, "horizon_position": 50, "show_horizon": True, "show_ground_line": True, "color": '#336699', "line_width": 0.3, "secondary_color": '#99BBDD', "vanishing_point_size": 4.0},
    "Mandala Guide": {"num_rings": 8, "num_radials": 12, "ring_spacing": 0.4, "show_center_dot": True, "center_dot_size": 3.0, "show_concentric_circles": True, "color": '#CC3366', "line_width": 0.25, "secondary_color": '#F0C0D0'},
    "Guitar Chord Diagram": {"diagrams_w": 3, "diagrams_h": 3, "diagram_size": 1.8, "show_fret_numbers": True, "show_string_names": True, "show_open_mute": True, "color": '#333333', "line_width": 0.5, "secondary_color": '#94A3B8', "num_frets": 5},
    "Venn Diagram": {"num_circles": 3, "circle_radius": 1.5, "show_labels": True, "show_shading": False, "color": '#3366CC', "line_width": 0.5, "secondary_color": '#D0E0F0', "overlap_ratio": 0.5, "label_font_size": 9},
    "Study Notes": {"line_spacing": 0.375, "margin_left": 1.0, "section_header_height": 0.5, "show_date_field": True, "show_topic_field": True, "show_summary_section": True, "summary_height": 2.0, "show_key_concepts": True, "concepts_rows": 5, "color": '#4472C4', "line_width": 0.3, "secondary_color": '#94A3B8'},
    "Project Planner": {"num_phases": 4, "tasks_per_phase": 5, "show_timeline": True, "show_deadline_col": True, "show_priority_col": True, "show_status_col": True, "color": '#333333', "line_width": 0.3, "secondary_color": '#2563EB'},
    "Fitness Log": {"num_exercises": 8, "num_sets": 4, "show_weight_col": True, "show_reps_col": True, "show_rest_col": True, "show_notes_col": True, "show_date_field": True, "color": '#333333', "line_width": 0.3, "secondary_color": '#16A34A'},
    "Weight Tracker": {"num_weeks": 12, "show_date_col": True, "show_weight_col": True, "show_change_col": True, "show_goal_line": True, "show_bmi_col": False, "goal_weight": 150.0, "row_height": 0.3, "color": '#333333', "line_width": 0.3, "secondary_color": '#2563EB'},
    "Travel Journal": {"show_date_field": True, "show_location_field": True, "show_weather_section": True, "show_expenses_section": True, "expense_rows": 5, "num_entry_lines": 20, "show_highlights_section": True, "highlights_rows": 5, "color": '#333333', "line_width": 0.3, "secondary_color": '#D97706'},
    "Essay Outline": {"num_body_paragraphs": 3, "show_hook_section": True, "show_thesis_section": True, "evidence_lines_per_para": 3, "show_conclusion_section": True, "show_counter_argument": True, "color": '#4472C4', "line_width": 0.3, "secondary_color": '#94A3B8'},
    "Grand Staff Paper": {"staff_spacing": 0.125, "group_spacing": 0.8, "num_systems": 5, "bracket_style": 'brace', "show_barlines": False, "barline_interval": 2.0, "color": '#000000', "line_width": 0.3, "secondary_color": '#666666'},
    "Dotted Lined": {"line_spacing": 0.5, "dot_spacing": 0.25, "dot_radius": 0.6, "margin_left": 1.0, "color": '#4472C4', "dot_color": '#999999', "line_width": 0.25, "show_margin_line": True, "dot_style": 'filled'},
    "Weekly Meal Planner": {"show_snack_row": True, "meal_col_width": 1.5, "show_calorie_col": True, "show_notes_col": True, "show_week_header": True, "color": '#333333', "line_width": 0.3, "secondary_color": '#16A34A'},
    "Sleep Tracker": {"num_days": 14, "show_nap_col": True, "show_quality_col": True, "show_mood_col": True, "show_notes_col": True, "row_height": 0.35, "color": '#333333', "line_width": 0.3, "secondary_color": '#6366F1'},
    "Mood Tracker": {"num_days": 31, "mood_labels": 'Emoji', "show_day_numbers": True, "show_month_header": True, "grid_size": 0.25, "color": '#333333', "line_width": 0.3, "secondary_color": '#F59E0B'},
    "Lesson Plan": {"num_periods": 6, "show_objectives": True, "show_materials": True, "show_assessment": True, "show_homework": True, "color": '#333333', "line_width": 0.3, "secondary_color": '#2563EB'},
    "Expense Tracker": {"num_rows": 25, "show_category_col": True, "show_payment_col": True, "show_balance_col": True, "header_height": 0.5, "row_height": 0.25, "color": '#333333', "line_width": 0.3, "secondary_color": '#DC2626'},
    "Baseball Scorecard": {"num_innings": 9, "players_per_team": 9, "show_sub_rows": True, "show_totals_row": True, "color": '#333333', "line_width": 0.3, "secondary_color": '#2563EB', "row_height": 20, "stat_columns": "R,H,RBI"},
    "Atom Diagram": {"grid_size": 2.5, "num_shells": 4, "show_electron_dots": True, "show_shell_labels": True, "show_nucleus": True, "nucleus_size": 0.3, "color": '#333333', "line_width": 0.3, "secondary_color": '#2563EB'},
    "Quadrille Paper": {"grid_size": 0.2, "major_every": 5, "dot_mode": False, "color": '#333333', "line_width": 0.2, "major_width": 0.6, "secondary_color": '#AAAAAA', "major_dot_radius": 1.0, "minor_dot_radius": 0.5},
    "Spiral Grid": {"num_spirals": 3, "turns": 4, "grid_size": 0.5, "show_radials": True, "num_radials": 12, "color": '#6B21A8', "line_width": 0.3, "secondary_color": '#C4B5FD'},
    "Basketball Stat Sheet": {"num_players": 12, "num_quarters": 4, "stat_categories": "Points,Rebounds,Assists,Steals,Blocks", "show_totals": True, "show_per_minute": False, "color": '#333333', "line_width": 0.3, "secondary_color": '#EA580C', "row_height": 16, "title_font_size": 16},
    "Chore Chart": {"num_chores": 8, "days_mode": "weekday", "show_points_col": True, "show_parent_initials": False, "color": '#333333', "line_width": 0.3, "secondary_color": '#16A34A', "label_column_width": 120, "checkbox_size": 10, "min_row_height": 18},
    "Water Intake Tracker": {"num_days": 7, "glasses_target": 8, "glass_size_oz": 8, "show_total_row": True, "show_notes_col": True, "color": '#333333', "line_width": 0.3, "secondary_color": '#0EA5E9'},
    "Phone Call Log": {"num_rows": 20, "show_duration_col": True, "show_followup_col": True, "show_outcome_col": True, "row_height": 0.3, "color": '#333333', "line_width": 0.3, "secondary_color": '#2563EB'},
    "Blood Pressure Log": {"num_rows": 30, "row_height": 0.25, "show_pulse_col": True, "show_notes_col": True, "show_date_time": True, "show_header_info": True, "color": '#333333', "line_width": 0.3, "secondary_color": '#DC2626'},
    "SWOT Analysis": {"layout": "quadrant", "show_headers": True, "header_height": 0.4, "show_prompt_lines": True, "lines_per_section": 8, "color": '#333333', "line_width": 0.5, "secondary_color": '#2563EB'},
    "Doodle Pad": {"density": "medium", "shape_types": "circles,squares,triangles", "show_border_frame": True, "corner_radius": 0.0, "color": '#D1D5DB', "line_width": 0.3, "secondary_color": '#E5E7EB', "margin": 0.33, "min_shape_size": 8, "max_shape_size": 38},
    "Comic Panel Layout": {"layout_style": "classic", "num_rows": 3, "show_gutter_labels": False, "gutter_width": 0.15, "panel_border_width": 1.5, "color": '#000000', "line_width": 1.5, "secondary_color": '#94A3B8'},
    "Gardening Planner": {"num_beds": 4, "grid_size": 0.25, "show_plant_list": True, "plant_list_rows": 10, "show_sun_indicator": True, "show_notes_section": True, "color": '#333333', "line_width": 0.3, "secondary_color": '#16A34A'},
    "Timeline": {"orientation": "horizontal", "num_events": 8, "marker_size": 0.15, "show_date_fields": True, "show_year_markers": False, "arrow_style": True, "color": '#2563EB', "line_width": 0.5, "secondary_color": '#93C5FD'},
    "Insect Observation Log": {"num_rows": 10, "row_height": 0.6, "show_habitat_col": True, "show_behavior_col": True, "show_weather_col": True, "show_drawing_area": True, "color": '#333333', "line_width": 0.3, "secondary_color": '#16A34A'},
    "Medication Log": {"num_rows": 20, "row_height": 0.3, "show_time_col": True, "show_dosage_col": True, "show_notes_col": True, "show_header_info": True, "color": '#333333', "line_width": 0.3, "secondary_color": '#7C3AED'},
    "Number Bonds": {"num_problems": 10, "target_range": "1-10", "show_number_bonds": True, "show_addition": True, "show_subtraction": True, "problem_layout": "2x5", "color": '#333333', "line_width": 0.3, "secondary_color": '#F59E0B'},
    "Stargazing Log": {"num_rows": 10, "row_height": 0.5, "show_constellation_col": True, "show_magnitude_col": True, "show_weather_col": True, "show_drawing_area": True, "color": '#333333', "line_width": 0.3, "secondary_color": '#1E3A5F'},
    "Writing Sprint Tracker": {"num_sprints": 15, "target_words": 1667, "show_project_name": True, "show_daily_total": True, "show_cumulative": True, "color": '#333333', "line_width": 0.3, "secondary_color": '#DC2626'},
    "Attendance Register": {"num_students": 25, "num_days": 20, "show_student_id": True, "show_totals_col": True, "show_absence_codes": True, "color": '#333333', "line_width": 0.3, "secondary_color": '#16A34A'},
    "Chess Score Sheet": {"show_player_names": True, "show_date_location": True, "num_rows": 40, "move_number_width": 0.5, "color": '#333333', "line_width": 0.3, "secondary_color": '#78716C', "margin": 0.5, "row_height": 14, "label_font_size": 7, "show_result_area": True},
    "Wish List": {"num_rows": 15, "show_priority_col": True, "show_price_col": True, "show_store_col": True, "show_status_col": True, "show_notes_col": True, "color": '#333333', "line_width": 0.3, "secondary_color": '#EC4899'},
    "Gratitude Journal": {"num_entries": 7, "prompts_per_entry": 3, "show_rating_col": True, "show_date_field": True, "show_mood_check": True, "color": '#333333', "line_width": 0.3, "secondary_color": '#F59E0B'},
    "Blank": {},
}


def hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    return f"#{int(r):02X}{int(g):02X}{int(b):02X}"

def blend_color(c1, c2, factor=0.3):
    r1,g1,b1 = hex_to_rgb(c1); r2,g2,b2 = hex_to_rgb(c2)
    return rgb_to_hex(min(255,max(0,r1+(r2-r1)*factor)),min(255,max(0,g1+(g2-g1)*factor)),min(255,max(0,b1+(b2-b1)*factor)))

def darken_color(c, f=0.3):
    r,g,b = hex_to_rgb(c); return rgb_to_hex(r*(1-f),g*(1-f),b*(1-f))

def lighten_color(c, f=0.3):
    r,g,b = hex_to_rgb(c); return rgb_to_hex(r+(255-r)*f,g+(255-g)*f,b+(255-b)*f)

def apply_opacity(color, opacity, bg="#FFFFFF"):
    if opacity >= 1.0: return color
    return blend_color(bg, color, opacity)

def opacity_qt(color, opacity):
    c = QColor(color)
    c.setAlphaF(max(0.05, opacity))
    return c


# ─────────────────────────────────────────────────────────────
# Presets Manager
# ─────────────────────────────────────────────────────────────
class PresetsManager:
    def __init__(self, path=PRESETS_FILE):
        self.path = path
        self._data = self._load()
    def _load(self):
        try:
            with open(self.path, "r") as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): return {"presets": {}}
    def _save(self):
        with open(self.path, "w") as f: json.dump(self._data, f, indent=2)
    def list_presets(self): return list(self._data["presets"].keys())
    def save_preset(self, name, paper_type, params, page_size_key, orientation):
        self._data["presets"][name] = {"paper_type": paper_type, "params": params, "page_size_key": page_size_key, "orientation": orientation}
        self._save()
    def load_preset(self, name): return self._data["presets"].get(name)
    def delete_preset(self, name):
        self._data["presets"].pop(name, None); self._save()
    def rename_preset(self, old_name, new_name):
        if old_name in self._data["presets"]:
            self._data["presets"][new_name] = self._data["presets"].pop(old_name); self._save()


# ─────────────────────────────────────────────────────────────
# Preview Widget
# ─────────────────────────────────────────────────────────────
class PaperPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._paper_type = "Graph Paper"
        self._page_size_pt = PAGE_SIZES["US Letter (8.5 x 11 in)"]
        self._params = dict(DEFAULT_PARAMS["Graph Paper"])
        self._orientation = "Portrait"
        self._bg_color = "#FFFFFF"
        self._zoom = 1.0
        self._pan = QPoint(0, 0)
        self._drag_start = None
        self._show_page_numbers = False
        self.setMinimumSize(320, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(QCursor(Qt.OpenHandCursor))

    def set_paper_type(self, n): self._paper_type = n; self._params = dict(DEFAULT_PARAMS.get(n, {})); self.update()
    def set_page_size(self, s): self._page_size_pt = s; self.update()
    def set_orientation(self, o): self._orientation = o; self.update()
    def update_param(self, k, v): self._params[k] = v; self.update()
    def set_bg_color(self, c): self._bg_color = c; self.update()
    def set_page_numbers(self, s): self._show_page_numbers = s; self.update()
    def zoom_in(self): self._zoom = min(self._zoom * 1.25, 10.0); self.update()
    def zoom_out(self): self._zoom = max(self._zoom / 1.25, 0.2); self.update()
    def zoom_fit(self): self._zoom = 1.0; self._pan = QPoint(0, 0); self.update()

    def _effective_size(self):
        w, h = self._page_size_pt
        if self._orientation == "Landscape": w, h = h, w
        return w, h

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton: self._drag_start = e.position().toPoint(); self.setCursor(QCursor(Qt.ClosedHandCursor))
    def mouseMoveEvent(self, e):
        if self._drag_start is not None:
            d = e.position().toPoint() - self._drag_start; self._pan += d; self._drag_start = e.position().toPoint(); self.update()
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton: self._drag_start = None; self.setCursor(QCursor(Qt.OpenHandCursor))
    def wheelEvent(self, e):
        (self.zoom_in if e.angleDelta().y() > 0 else self.zoom_out)()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pw, ph = self._effective_size()
        painter.fillRect(self.rect(), QBrush(QColor("#E8ECF0")))
        margin = 24
        base_scale = min((self.width() - 2*margin) / pw, (self.height() - 2*margin) / ph) * 0.92
        scale = base_scale * self._zoom
        ox = (self.width() - pw * scale) / 2 + self._pan.x()
        oy = (self.height() - ph * scale) / 2 + self._pan.y()
        painter.save()
        painter.translate(ox, oy)
        painter.scale(scale, scale)
        painter.setPen(Qt.NoPen); painter.setBrush(QBrush(QColor(0, 0, 0, 30)))
        painter.drawRect(QRectF(4, 4, pw, ph))
        painter.fillRect(QRectF(0, 0, pw, ph), QBrush(QColor(self._bg_color)))
        painter.setPen(QPen(QColor("#BBBBBB"), 1.0)); painter.drawRect(QRectF(0, 0, pw, ph))
        drawer = getattr(self, f"_draw_{self._paper_type.lower().replace(' ', '_')}", None)
        if drawer: drawer(painter, pw, ph)
        if self._show_page_numbers:
            painter.setFont(QFont("Helvetica", 9)); painter.setPen(QPen(QColor("#999999")))
            painter.drawText(QRectF(pw/2-10, ph-40, 20, 16), Qt.AlignCenter, "1")
        painter.restore()
        painter.setPen(QPen(QColor("#64748B"))); painter.setFont(QFont("Helvetica", 9))
        painter.drawText(10, self.height() - 8, f"{self._zoom:.0%}")
        painter.end()

    # ── Helpers ──
    def _line(self, p, x1, y1, x2, y2, color, width):
        p.setPen(QPen(QColor(color), width)); p.drawLine(QRectF(x1, y1, x2, y2))
    def _hline(self, p, y, x1, x2, color, width): self._line(p, x1, y, x2, y, color, width)
    def _vline(self, p, x, y1, y2, color, width): self._line(p, x, y1, x, y2, color, width)
    def _styled_hline(self, p, y, x1, x2, color, width, style="solid"):
        pen = QPen(QColor(color), width)
        if style == "dashed": pen.setStyle(Qt.DashLine)
        elif style == "dotted": pen.setStyle(Qt.DotLine)
        elif style == "dashdot": pen.setStyle(Qt.DashDotLine)
        p.setPen(pen); p.drawLine(QRectF(x1, y, x2, y))
    def _oc(self, color, op=1.0):
        if op >= 1.0: return color
        return apply_opacity(color, op, self._bg_color)

    # ── Graph Paper (with axis + labels) ──
    def _draw_graph_paper(self, p, w, h):
        gs = self._params["grid_size"] * IN_TO_PT
        major = int(self._params["major_every"])
        c = self._oc(self._params["color"])
        sc = self._oc(self._params.get("secondary_color", darken_color(self._params["color"])))
        lw = self._params["line_width"]; mw = self._params["major_width"]
        ls = self._params.get("line_style", "solid")
        x = gs
        while x < w:
            pen = QPen(QColor(sc), lw)
            if ls == "dashed": pen.setStyle(Qt.DashLine)
            elif ls == "dotted": pen.setStyle(Qt.DotLine)
            elif ls == "dashdot": pen.setStyle(Qt.DashDotLine)
            p.setPen(pen); p.drawLine(QRectF(x, 0, x, h)); x += gs
        y = gs
        while y < h: self._styled_hline(p, y, 0, w, sc, lw, ls); y += gs
        x = gs * major
        while x < w: self._vline(p, x, 0, h, c, mw); x += gs * major
        y = gs * major
        while y < h: self._hline(p, y, 0, w, c, mw); y += gs * major
        if self._params.get("show_axis"):
            aw = self._params.get("axis_width", 1.5)
            cx, cy = w / 2, h / 2
            self._vline(p, cx, 0, h, c, aw)
            self._hline(p, cy, 0, w, c, aw)
        if self._params.get("show_labels"):
            fs = int(self._params.get("label_font_size", 7))
            p.setFont(QFont("Helvetica", fs)); p.setPen(QPen(QColor(c)))
            x = gs * major
            idx = int(major)
            while x < w:
                p.drawText(QRectF(x - 8, h/2 + 2, 16, 12), Qt.AlignCenter, str(idx))
                x += gs * major; idx += int(major)
            y = gs * major
            idx = int(major)
            while y < h:
                p.drawText(QRectF(w/2 + 2, y - 8, 20, 12), Qt.AlignLeft, str(idx))
                y += gs * major; idx += int(major)

    # ── Ruled papers ──
    def _draw_college_ruled(self, p, w, h): self._draw_ruled(p, w, h)
    def _draw_wide_ruled(self, p, w, h): self._draw_ruled(p, w, h)
    def _draw_lined_paper(self, p, w, h): self._draw_ruled(p, w, h)

    def _draw_ruled(self, p, w, h):
        ls = self._params["line_spacing"] * IN_TO_PT
        ml = self._params["margin_left"] * IN_TO_PT
        c = self._params["color"]
        sc = self._params.get("secondary_color", "#FF0000")
        lw = self._params["line_width"]
        line_st = self._params.get("line_style", "solid")
        op = self._params.get("line_opacity", 1.0)
        oc = self._oc(c, op)
        top_m = self._params.get("top_margin", 1.0) * IN_TO_PT if self._params.get("show_top_margin") else 72
        rm = self._params.get("right_margin", 1.0) * IN_TO_PT
        y = top_m
        while y < h - 72:
            self._styled_hline(p, y, ml, w - rm, oc, lw, line_st)
            if self._params.get("double_line"):
                self._styled_hline(p, y + lw * 2, ml, w - 72, oc, lw * 0.5, line_st)
                y += ls
            else:
                y += ls
        self._vline(p, ml, 0, h, sc, lw)
        if self._params.get("show_top_margin"):
            self._hline(p, top_m, 0, w, sc, lw * 0.5)

    # ── Dot Grid ──
    def _draw_dot_grid(self, p, w, h):
        sp = self._params["dot_spacing"] * IN_TO_PT
        r = self._params["dot_radius"]
        dot_style = self._params.get("dot_style", "filled")
        major_every = int(self._params.get("major_dots_every", 5))
        major_r = self._params.get("major_dot_radius", r * 1.8)
        color = self._oc(self._params["color"], self._params.get("dot_opacity", 1.0))
        off_x = self._params.get("offset_x", 0.0) * IN_TO_PT
        off_y = self._params.get("offset_y", 0.0) * IN_TO_PT
        p.setPen(Qt.NoPen)
        xi = off_x
        col_idx = 0
        while xi < w:
            yi = off_y
            row_idx = 0
            while yi < h:
                is_major = (row_idx % major_every == 0 and col_idx % major_every == 0)
                cr = major_r if is_major else r
                if dot_style == "filled":
                    p.setBrush(QBrush(QColor(color)))
                    p.drawEllipse(QRectF(xi - cr, yi - cr, 2*cr, 2*cr))
                elif dot_style == "ring":
                    p.setBrush(Qt.NoBrush); p.setPen(QPen(QColor(color), 0.5))
                    p.drawEllipse(QRectF(xi - cr, yi - cr, 2*cr, 2*cr)); p.setPen(Qt.NoPen)
                elif dot_style == "cross":
                    p.setPen(QPen(QColor(color), 0.5))
                    p.drawLine(QRectF(xi-cr, yi, xi+cr, yi))
                    p.drawLine(QRectF(xi, yi-cr, xi, yi+cr)); p.setPen(Qt.NoPen)
                yi += sp; row_idx += 1
            xi += sp; col_idx += 1

    # ── Isometric ──
    def _draw_isometric(self, p, w, h):
        gs = self._params["grid_size"] * IN_TO_PT
        mg = self._params.get("margin", 0.0) * IN_TO_PT
        c = self._params["color"]; lw = self._params["line_width"]
        dy = gs * math.sin(math.radians(60)); dx = gs * math.cos(math.radians(60))
        y = 0
        while y < h: self._hline(p, y, 0, w, c, lw); y += gs
        for sx_i in range(0, int(w + h) + 1, max(int(gs), 1)):
            sx, sy = float(sx_i), 0.0
            while sy <= h and sx >= -w:
                if 0 <= sx <= w:
                    ex, ey = sx - dx, sy + dy
                    if ey > h: ratio = (h - sy) / dy if dy else 0; ex, ey = sx - dx * ratio, h
                    self._line(p, sx, sy, ex, ey, c, lw)
                sx -= dx; sy += dy
        for sx_i in range(0, int(w + h) + 1, max(int(gs), 1)):
            sx, sy = float(sx_i), 0.0
            while sy <= h and sx <= w + h:
                if 0 <= sx <= w:
                    ex, ey = sx + dx, sy + dy
                    if ey > h: ratio = (h - sy) / dy if dy else 0; ex, ey = sx + dx * ratio, h
                    self._line(p, sx, sy, ex, ey, c, lw)
                sx += dx; sy += dy
        if self._params.get("show_axis"):
            aw = self._params.get("axis_width", 1.5)
            cx, cy = w / 2, h / 2
            self._vline(p, cx, 0, h, c, aw)
            ex1, ey1 = cx - dx * 40, cy + dy * 40
            ex2, ey2 = cx + dx * 40, cy + dy * 40
            self._line(p, cx, cy, ex1, ey1, c, aw)
            self._line(p, cx, cy, ex2, ey2, c, aw)

    # ── Cornell Notes ──
    def _draw_cornell_notes(self, p, w, h):
        ls = self._params["line_spacing"] * IN_TO_PT
        ratio = self._params.get("column_split_ratio", 0.3)
        cw = (w - 2 * 72) * ratio
        sh = self._params["summary_height"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#94A3B8")
        lw = self._params["line_width"]; m = 72; bottom = h - sh - 36
        nls = self._params.get("notes_line_style", "dashed")
        y = m
        while y < bottom: self._styled_hline(p, y, m, w - m, sc, lw * 0.6, nls); y += ls
        cls = self._params.get("cue_line_style", "solid")
        if cls == "dashed":
            pen = QPen(QColor(c), lw * 2); pen.setStyle(Qt.DashLine)
            p.setPen(pen); p.drawLine(QRectF(m + cw, m, m + cw, bottom))
        else:
            self._vline(p, m + cw, m, bottom, c, lw * 2)
        self._hline(p, bottom, m, w - m, c, lw * 2)
        if self._params.get("show_labels", True):
            p.setFont(QFont("Arial", 8)); p.setPen(QPen(QColor("#888888")))
            p.drawText(QRectF(m+2, m+2, cw-4, 16), Qt.AlignLeft, "Cue Column")
            p.drawText(QRectF(m+cw+2, m+2, 80, 16), Qt.AlignLeft, "Notes")
            p.drawText(QRectF(m+2, bottom-14, 100, 16), Qt.AlignLeft, "Summary")
        if self._params.get("show_date_field", True):
            p.setPen(QPen(QColor("#AAAAAA"))); p.setFont(QFont("Helvetica", 7))
            p.drawText(QRectF(w - 180, m + 2, 100, 14), Qt.AlignRight, "Date: ________")

    # ── Engineering Paper ──
    def _draw_engineering_paper(self, p, w, h):
        gs = self._params["grid_size"] * IN_TO_PT
        major = int(self._params["major_every"])
        c = self._params["color"]; sc = self._params.get("secondary_color", lighten_color(c))
        lw = self._params["line_width"]; mlw = self._params["major_width"]; m = 36
        if self._params.get("border"):
            p.setPen(QPen(QColor(c), 1.5)); p.drawRect(QRectF(m, m, w-2*m, h-2*m))
        x = m
        while x <= w - m: self._vline(p, x, m, h-m, sc, lw); x += gs
        y = m
        while y <= h - m: self._hline(p, y, m, w-m, sc, lw); y += gs
        x = m + gs * major
        while x < w - m: self._vline(p, x, m, h-m, c, mlw); x += gs * major
        y = m + gs * major
        while y < h - m: self._hline(p, y, m, w-m, c, mlw); y += gs * major
        if self._params.get("zone_labels"):
            p.setFont(QFont("Helvetica", 6)); p.setPen(QPen(QColor(c)))
            col_labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            xi = 0
            while xi < 26:
                cx = m + gs * major * xi + gs * major / 2
                if cx > w - m: break
                p.drawText(QRectF(cx - 4, m + 2, 8, 10), Qt.AlignCenter, col_labels[xi])
                p.drawText(QRectF(cx - 4, h - m - 10, 8, 10), Qt.AlignCenter, col_labels[xi])
                xi += 1
            yi = 0
            while yi < 50:
                cy = m + gs * major * yi + gs * major / 2
                if cy > h - m: break
                p.drawText(QRectF(m + 2, cy - 5, 16, 10), Qt.AlignLeft, str(yi + 1))
                yi += 1
        if self._params.get("show_title_block"):
            tbw = self._params.get("title_block_width", 2.5) * IN_TO_PT
            tbh = self._params.get("title_block_height", 1.0) * IN_TO_PT
            p.setPen(QPen(QColor(c), 1.5))
            p.drawRect(QRectF(w - m - tbw, h - m - tbh, tbw, tbh))
            p.drawLine(QRectF(w - m - tbw, h - m - tbh * 0.5, w - m, h - m - tbh * 0.5))

    # ── Hexagonal Grid ──
    def _draw_hexagonal_grid(self, p, w, h):
        size = self._params["hex_size"] * IN_TO_PT
        c = self._params["color"]; lw = self._params["line_width"]
        orient = self._params.get("orientation", "flat_top")
        fill = self._params.get("fill_hexagons", False)
        fill_c = self._params.get("secondary_color", "#E8D5F5")
        op = self._params.get("opacity", 1.0)
        oc = self._oc(c, op)
        ofc = self._oc(fill_c, op)
        if orient == "pointy_top":
            hex_h = 2 * size; vert = hex_h * 0.75; horiz = size * math.sqrt(3)
        else:
            hex_h = size * math.sqrt(3); vert = hex_h * 0.75; horiz = 2 * size
        row = 0; y = 0
        while y < h + hex_h:
            offset = (horiz / 2) if row % 2 else 0; x = offset
            while x < w + horiz:
                pts = []
                for i in range(6):
                    angle = math.radians(60 * i - 30) if orient == "flat_top" else math.radians(60 * i)
                    pts.append((x + size * math.cos(angle), y + size * math.sin(angle)))
                if fill:
                    poly = [QPointF(px, py) for px, py in pts]
                    p.setPen(QPen(QColor(oc), lw)); p.setBrush(QBrush(QColor(ofc)))
                    p.drawPolygon(QPolygonF(poly)); p.setBrush(Qt.NoBrush)
                else:
                    for i in range(6):
                        x1, y1 = pts[i]; x2, y2 = pts[(i+1) % 6]
                        self._line(p, x1, y1, x2, y2, oc, lw)
                x += horiz
            y += vert; row += 1

    # ── Music Staff ──
    def _draw_music_staff(self, p, w, h):
        ss = self._params["staff_spacing"] * IN_TO_PT
        gs = self._params["group_spacing"] * IN_TO_PT
        ns = int(self._params["num_staves"])
        c = self._params["color"]; lw = self._params["line_width"]
        show_bar = self._params.get("show_barlines", False)
        bar_int = self._params.get("barline_interval", 2.0) * IN_TO_PT
        show_clef = self._params.get("show_clef", False)
        show_ts = self._params.get("show_time_signature", False)
        lfont = int(self._params.get("staff_label_font", 8))
        group_h = 4 * ss; total = ns * (group_h + gs) - gs
        start_y = (h - total) / 2
        for i in range(ns):
            base = start_y + i * (group_h + gs)
            for j in range(5): self._hline(p, base + j * ss, 54, w - 54, c, lw)
            if show_clef:
                p.setFont(QFont("Helvetica", lfont + 8)); p.setPen(QPen(QColor(c)))
                p.drawText(QRectF(58, base - 4, 20, group_h + 8), Qt.AlignLeft, "K")
            if show_ts:
                p.setFont(QFont("Helvetica", lfont + 4, QFont.Bold)); p.setPen(QPen(QColor(c)))
                tx = 78 if show_clef else 62
                p.drawText(QRectF(tx, base, 14, group_h / 2), Qt.AlignCenter, "4")
                p.drawText(QRectF(tx, base + group_h / 2, 14, group_h / 2), Qt.AlignCenter, "4")
            if show_bar and bar_int > 0:
                bx = 54 + bar_int
                while bx < w - 54: self._vline(p, bx, base, base + 4 * ss, c, lw); bx += bar_int

    # ── Calligraphy Guide ──
    def _draw_calligraphy_guide(self, p, w, h):
        sp = self._params["guide_spacing"] * IN_TO_PT
        desc = self._params["descender"] * IN_TO_PT
        asc = self._params.get("ascender", 0.2) * IN_TO_PT
        angle = self._params["slant_angle"]
        show_slant = self._params.get("show_slant", True)
        c = self._params["color"]; sc = self._params.get("secondary_color", lighten_color(c, 0.5))
        lw = self._params["line_width"]; mx = 72
        num_nibs = int(self._params.get("num_nibs", 1))
        nib_w = self._params.get("nib_width", 0.1) * IN_TO_PT
        show_xh = self._params.get("show_x_height", True)
        y = 72
        while y < h - 72 - desc:
            self._hline(p, y, mx, w - mx, c, lw * 1.5)
            if show_xh:
                self._hline(p, y - asc, mx, w - mx, sc, lw * 0.7)
            self._hline(p, y - sp, mx, w - mx, sc, lw)
            self._hline(p, y + desc, mx, w - mx, sc, lw)
            if show_slant:
                rad = math.radians(angle); tan_a = math.tan(rad)
                step = sp / tan_a if tan_a != 0 else sp
                x = mx
                while x < w - mx:
                    self._line(p, x, y - sp, x + step, y, lighten_color(c, 0.6), lw * 0.4)
                    x += max(step, 1)
            if num_nibs > 1:
                for n in range(1, num_nibs):
                    nw = nib_w * n
                    pen = QPen(QColor(lighten_color(c, 0.5 + 0.1*n)), lw * 0.3)
                    pen.setStyle(Qt.DashDotLine); p.setPen(pen)
                    p.drawLine(QRectF(mx, y - nw, w - mx, y - nw))
                    p.drawLine(QRectF(mx, y + nw, w - mx, y + nw))
            y += sp + desc

    # ── To-Do List ──
    def _draw_to_do_list(self, p, w, h):
        ls = self._params["line_spacing"] * IN_TO_PT
        ml = self._params["margin_left"] * IN_TO_PT
        cbs = self._params["checkbox_size"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#2563EB")
        lw = self._params["line_width"]; m = 72
        show_date = self._params.get("show_date_column", False)
        show_pri = self._params.get("show_priority", False)
        date_w = self._params.get("date_col_width", 0.8) * IN_TO_PT if show_date else 0
        pri_w = 24 if show_pri else 0
        x_start = ml + cbs + 8 + date_w + pri_w
        y = m + ls
        num = 1
        while y < h - m:
            self._hline(p, y, x_start, w - m, c, lw)
            p.setPen(QPen(QColor(sc), lw * 0.8)); p.setBrush(Qt.NoBrush)
            p.drawRect(QRectF(ml + 2, y - ls * 0.65, cbs, cbs))
            if show_date:
                pen = QPen(QColor("#AAAAAA"), lw * 0.3); pen.setStyle(Qt.DashLine); p.setPen(pen)
                self._vline(p, ml + cbs + 8 + date_w, y - ls * 0.65, y, "#AAAAAA", lw * 0.3)
            if show_pri:
                p.setPen(QPen(QColor("#AAAAAA"), lw * 0.3))
                p.drawText(QRectF(ml + cbs + 8 + date_w + 2, y - ls * 0.55, 20, 14), Qt.AlignCenter, "A")
            if self._params.get("show_numbers"):
                p.setPen(QPen(QColor("#BBBBBB"))); p.setFont(QFont("Helvetica", 7))
                p.drawText(QRectF(ml + cbs + 12, y - ls * 0.55, 16, 14), Qt.AlignLeft, str(num))
            y += ls; num += 1

    # ── Kanban Board ──
    def _draw_kanban_board(self, p, w, h):
        nc = int(self._params["num_columns"])
        gap = self._params["column_spacing"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#94A3B8")
        lw = self._params["line_width"]; m = 36; header_h = 36
        card_h = self._params.get("card_height", 0.7) * IN_TO_PT
        show_due = self._params.get("show_due_date", False)
        show_pri = self._params.get("show_priority_badge", False)
        col_w = (w - 2 * m - (nc - 1) * gap) / nc
        col_labels = ["To Do", "In Progress", "Done", "Review", "Backlog"]
        x = m
        for i in range(nc):
            p.setPen(QPen(QColor(c), lw)); p.setBrush(QBrush(QColor("#F8FAFC")))
            p.drawRect(QRectF(x, m, col_w, h - 2 * m))
            p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(sc)))
            p.drawRect(QRectF(x, m, col_w, header_h))
            p.setPen(QPen(QColor("#FFFFFF"))); p.setFont(QFont("Helvetica", 9, QFont.Bold))
            label = col_labels[i] if i < len(col_labels) else f"Col {i+1}"
            p.drawText(QRectF(x + 6, m + 8, col_w - 12, 20), Qt.AlignLeft, label)
            card_y = m + header_h + 16
            max_cards = int(self._params.get("cards_per_col", 99))
            for _ in range(max_cards):
                if card_y + card_h > h - m - 10: break
                p.setPen(QPen(QColor(lighten_color(sc, 0.7)), lw * 0.3))
                p.setBrush(QBrush(QColor("#FFFFFF")))
                p.drawRect(QRectF(x + 6, card_y, col_w - 12, card_h))
                if show_due:
                    p.setPen(QPen(QColor("#CCCCCC"), lw * 0.2))
                    self._hline(p, card_y + card_h - 14, x + 6, x + col_w - 6, "#CCCCCC", lw * 0.2)
                if show_pri:
                    p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor("#F59E0B")))
                    p.drawEllipse(QRectF(x + col_w - 22, card_y + 4, 12, 12))
                    p.setBrush(Qt.NoBrush)
                card_y += card_h + 20
            x += col_w + gap

    # ── Penmanship ──
    def _draw_penmanship(self, p, w, h):
        ls = self._params["line_spacing"] * IN_TO_PT
        mid = self._params["midline_offset"] * IN_TO_PT
        desc_d = self._params["descender_depth"] * IN_TO_PT
        asc_h = self._params.get("ascender_height", 0.0) * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#AAAAAA")
        lw = self._params["line_width"]; m = 72
        show_asc = self._params.get("show_ascender", True)
        color_mode = self._params.get("line_color_mode", "single")
        if mid == 0: mid = ls * 0.4
        if desc_d == 0: desc_d = ls * 0.3
        if asc_h == 0 and show_asc: asc_h = ls * 0.3
        y = m + ls
        while y < h - m:
            self._hline(p, y, m, w - m, c, lw)
            mc = sc if color_mode == "dual" else c
            pen = QPen(QColor(mc), lw * 0.7); pen.setStyle(Qt.DashLine); p.setPen(pen)
            p.drawLine(QRectF(m, y - mid, w - m, y - mid))
            pen.setStyle(Qt.DotLine); p.setPen(pen)
            p.drawLine(QRectF(m, y + desc_d, w - m, y + desc_d))
            if show_asc and asc_h > 0:
                pen.setStyle(Qt.DashLine); p.setPen(pen)
                p.drawLine(QRectF(m, y - mid - asc_h, w - m, y - mid - asc_h))
            p.setPen(QPen(QColor(c), lw))
            y += ls + desc_d

    # ── Cross Stitch ──
    def _draw_cross_stitch(self, p, w, h):
        gs = self._params["grid_size"] * IN_TO_PT
        major = int(self._params.get("major_every", 10))
        c = self._params["color"]; mc = self._params.get("major_color", darken_color(c))
        lw = self._params["line_width"]; mw = self._params.get("major_width", lw * 2.5)
        bm = self._params.get("border_width", 0.5) * IN_TO_PT
        m = bm
        x = m
        while x <= w - m: self._vline(p, x, m, h - m, c, lw); x += gs
        y = m
        while y <= h - m: self._hline(p, y, m, w - m, c, lw); y += gs
        x = m
        while x <= w - m: self._vline(p, x, m, h - m, mc, mw); x += gs * major
        y = m
        while y <= h - m: self._hline(p, y, m, w - m, mc, mw); y += gs * major
        if self._params.get("center_marks"):
            cx, cy = w / 2, h / 2
            self._vline(p, cx, cy - 8, cy + 8, c, lw * 2)
            self._hline(p, cy, cx - 8, cx + 8, c, lw * 2)
        if self._params.get("show_symbols"):
            p.setFont(QFont("Helvetica", 5)); p.setPen(QPen(QColor(c)))
            x = m
            col = 0
            while x <= w - m:
                if col % major == 0 and col > 0:
                    y2 = m
                    while y2 <= h - m:
                        p.drawText(QRectF(x - 3, y2 - 3, 6, 6), Qt.AlignCenter, "+")
                        y2 += gs * major
                x += gs; col += 1

    # ── Piano Keys ──
    def _draw_piano_keys(self, p, w, h):
        no = int(self._params["num_octaves"])
        kh = self._params["key_height"] * IN_TO_PT
        show_labels = self._params.get("show_labels", True)
        show_oct = self._params.get("show_octave_numbers", True)
        start_oct = int(self._params.get("start_octave", 3))
        c = self._params["color"]; sc = self._params.get("secondary_color", "#FFFFFF")
        lw = self._params["line_width"]; m = 54
        key_style = self._params.get("key_style", "classic")
        white_notes = ["C", "D", "E", "F", "G", "A", "B"]
        black_pattern = [True, True, False, True, True, True, False]
        total_white = 7 * no
        key_w = (w - 2 * m) / total_white
        x = m
        for octave in range(no):
            for i, note in enumerate(white_notes):
                p.setPen(QPen(QColor(c), lw)); p.setBrush(QBrush(QColor(sc)))
                p.drawRect(QRectF(x, m, key_w, kh))
                if black_pattern[i]:
                    p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(c)))
                    p.drawRect(QRectF(x + key_w * 0.65, m, key_w * 0.7, kh * 0.6))
                if show_labels and key_style != "blank":
                    p.setPen(QPen(QColor(c))); p.setFont(QFont("Helvetica", 7))
                    oct_num = start_oct + octave
                    p.drawText(QRectF(x+2, m+kh-16, key_w-4, 14), Qt.AlignCenter, f"{note}{oct_num}")
                x += key_w
            if show_oct and key_style != "blank":
                p.setPen(QPen(QColor("#999999"))); p.setFont(QFont("Helvetica", 8, QFont.Bold))
                p.drawText(QRectF(x - 7 * key_w / 2 - 10, m + kh + 4, 20, 14), Qt.AlignCenter, str(start_oct + octave))

    # ── Storyboard ──
    def _draw_storyboard(self, p, w, h):
        pw_c = int(self._params["num_panels_w"]); ph_c = int(self._params["num_panels_h"])
        gap = self._params["panel_gap"] * IN_TO_PT; label_h = self._params["label_height"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#94A3B8")
        lw = self._params["line_width"]; m = 36
        show_ro3 = self._params.get("show_rule_of_thirds", False)
        show_ar = self._params.get("show_aspect_ratio", True)
        avail_w = w - 2*m; avail_h = h - 2*m
        panel_w = (avail_w - (pw_c-1)*gap) / pw_c; panel_h = (avail_h - (ph_c-1)*gap) / ph_c
        x = m; y = m; panel_num = 1
        for row in range(ph_c):
            for col in range(pw_c):
                draw_h = panel_h - label_h
                br = self._params.get("panel_border_radius", 0.0) * IN_TO_PT
                p.setPen(QPen(QColor(c), lw)); p.setBrush(QBrush(QColor("#FAFAFA")))
                if br > 0:
                    p.drawRoundedRect(QRectF(x, y, panel_w, draw_h), br, br)
                else:
                    p.drawRect(QRectF(x, y, panel_w, draw_h))
                if show_ro3:
                    p.setPen(QPen(QColor("#DDDDDD"), lw * 0.3))
                    for t in [1/3, 2/3]:
                        self._vline(p, x + panel_w * t, y, y + draw_h, "#DDDDDD", lw * 0.3)
                        self._hline(p, y + draw_h * t, x, x + panel_w, "#DDDDDD", lw * 0.3)
                p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(sc)))
                p.drawRect(QRectF(x, y + draw_h, panel_w, label_h))
                p.setPen(QPen(QColor("#FFFFFF"))); p.setFont(QFont("Helvetica", 7))
                lbl = f"Panel {panel_num}"
                if show_ar: lbl += f"  ({pw_c}:{ph_c})"
                p.drawText(QRectF(x+4, y+draw_h+2, panel_w-8, label_h-4), Qt.AlignLeft|Qt.AlignVCenter, lbl)
                panel_num += 1; x += panel_w + gap
            x = m; y += panel_h + gap

    # ── Grid Diary ──
    def _draw_grid_diary(self, p, w, h):
        cols = int(self._params["grid_cols"]); rows = int(self._params["grid_rows"])
        header_h = self._params["header_height"] * IN_TO_PT
        tcw = self._params["time_col_width"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#94A3B8")
        lw = self._params["line_width"]; m = 36
        alt_shade = self._params.get("alternate_row_shading", True)
        avail_w = w - 2*m - tcw; avail_h = h - 2*m - header_h
        cell_w = avail_w / cols; cell_h = avail_h / rows
        p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(sc)))
        p.drawRect(QRectF(m, m, w - 2*m, header_h))
        p.setPen(QPen(QColor("#FFFFFF"))); p.setFont(QFont("Helvetica", 8, QFont.Bold))
        all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        all_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        start = self._params.get("start_day", "Monday")
        start_idx = all_days.index(start) if start in all_days else 0
        rotated = all_short[start_idx:] + all_short[:start_idx]
        day_names = (rotated * 3)[:max(cols, 7)]
        x = m + tcw
        for i in range(cols):
            label = day_names[i] if i < len(day_names) else f"D{i+1}"
            p.drawText(QRectF(x+2, m+4, cell_w-4, header_h-8), Qt.AlignCenter, label); x += cell_w
        p.drawText(QRectF(m+2, m+4, tcw-4, header_h-8), Qt.AlignCenter, "Time")
        for r in range(rows + 1):
            y = m + header_h + r * cell_h
            self._hline(p, y, m, w - m, c, lw * 1.5 if r == 0 else lw)
        for col in range(cols + 1):
            x = m + tcw + col * cell_w
            self._vline(p, x, m + header_h, h - m, c, lw * 0.5)
        self._vline(p, m + tcw, m, h - m, c, lw * 1.5)
        if alt_shade:
            for r in range(rows):
                if r % 2 == 0:
                    y = m + header_h + r * cell_h
                    p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(248, 250, 252, 80)))
                    p.drawRect(QRectF(m, y, w - 2*m, cell_h))

    # ── Japanese Genkoyoushi ──
    def _draw_japanese_genkoyoushi(self, p, w, h):
        cs = self._params["cell_size"] * IN_TO_PT
        ms = self._params["margin_size"] * IN_TO_PT
        show_title = self._params.get("show_title_space", True)
        num_title = int(self._params.get("num_title_rows", 3))
        c = self._params["color"]; sc = self._params.get("secondary_color", "#AAAAAA")
        lw = self._params["line_width"]; m = 36
        grid_style = self._params.get("grid_style", "full")
        start_y = m + (num_title * cs if show_title else 0)
        p.setPen(QPen(QColor(c), lw * 2)); p.drawLine(QRectF(m + ms, m, m + ms, h - m))
        if grid_style != "none":
            cx = w / 2
            pen_c = QPen(QColor(sc), lw * 0.7); pen_c.setStyle(Qt.DashLine); p.setPen(pen_c)
            p.drawLine(QRectF(cx, start_y, cx, h - m))
            if grid_style == "full":
                y = start_y
                while y <= h - m:
                    is_first = (y == start_y)
                    self._hline(p, y, m, w - m, c if is_first else sc, lw if is_first else lw * 0.5)
                    y += cs
                x = m
                while x <= w - m:
                    is_first = (x == m)
                    self._vline(p, x, start_y, h - m, c if is_first else sc, lw if is_first else lw * 0.5)
                    x += cs
        if show_title:
            p.setPen(QPen(QColor("#BBBBBB"))); p.setFont(QFont("Helvetica", 8))
            p.drawText(QRectF(m + 4, m + cs * 0.7, ms - 8, 16), Qt.AlignLeft, "Title")
        if self._params.get("show_field_guide"):
            gx, gy = m + ms + cs / 2, start_y + cs / 2
            d = cs * 0.3
            p.setPen(QPen(QColor(sc), lw * 0.5))
            self._line(p, gx - d, gy - d, gx + d, gy + d, sc, lw * 0.5)
            self._line(p, gx + d, gy - d, gx - d, gy + d, sc, lw * 0.5)

    # ── Meeting Notes ──
    def _draw_meeting_notes(self, p, w, h):
        ta_h = self._params["title_area_height"] * IN_TO_PT
        agenda_rows = int(self._params["agenda_rows"])
        nls = self._params["notes_line_spacing"] * IN_TO_PT
        action_rows = int(self._params["action_rows"])
        show_fields = self._params.get("show_fields", True)
        show_decision = self._params.get("show_decision_box", False)
        notes_cols = int(self._params.get("notes_columns", 1))
        show_timer = self._params.get("show_timer_section", False)
        c = self._params["color"]; sc = self._params.get("secondary_color", "#2563EB")
        lw = self._params["line_width"]; m = 36; y = m
        if show_timer:
            p.setPen(QPen(QColor(sc), lw)); p.setFont(QFont("Helvetica", 8))
            p.drawText(QRectF(w - m - 120, y + 4, 110, 14), Qt.AlignRight, "Start Time: ________")
            p.drawText(QRectF(w - m - 120, y + 20, 110, 14), Qt.AlignRight, "End Time:   ________")
        self._hline(p, y + ta_h, m, w - m, c, lw * 2)
        p.setPen(QPen(QColor(c), lw * 1.5)); p.drawRect(QRectF(m, y, w - 2*m, ta_h))
        if show_fields:
            p.setPen(QPen(QColor("#AAAAAA"))); p.setFont(QFont("Helvetica", 8))
            p.drawText(QRectF(m+4, y+4, 80, 14), Qt.AlignLeft, "Date:")
            p.drawText(QRectF(m+4, y+20, 80, 14), Qt.AlignLeft, "Time:")
            p.drawText(QRectF(m+w/4, y+4, 80, 14), Qt.AlignLeft, "Location:")
            p.drawText(QRectF(m+w/4, y+20, 80, 14), Qt.AlignLeft, "Attendees:")
        y += ta_h + 8
        p.setPen(QPen(QColor(sc))); p.setFont(QFont("Helvetica", 10, QFont.Bold))
        p.drawText(QRectF(m, y, w - 2*m, 18), Qt.AlignLeft, "Agenda"); y += 18
        for i in range(agenda_rows):
            self._hline(p, y, m, w - m, c, lw * 0.5); y += 18
        y += 8
        p.setPen(QPen(QColor(sc))); p.setFont(QFont("Helvetica", 10, QFont.Bold))
        p.drawText(QRectF(m, y, w - 2*m, 18), Qt.AlignLeft, "Notes"); y += 18
        notes_bottom = h - m - action_rows * 22 - 40
        if show_decision: notes_bottom -= 80
        while y < notes_bottom:
            self._hline(p, y, m, w - m, c, lw * 0.3); y += nls
        if show_decision:
            y += 8
            p.setPen(QPen(QColor(sc))); p.setFont(QFont("Helvetica", 10, QFont.Bold))
            p.drawText(QRectF(m, y, w - 2*m, 18), Qt.AlignLeft, "Decisions / Outcomes"); y += 18
            for i in range(3):
                if y + 16 > h - m - action_rows * 22 - 20: break
                self._hline(p, y + 14, m + 18, w - m, c, lw * 0.3)
                p.setPen(QPen(QColor(sc), lw * 0.7)); p.setBrush(Qt.NoBrush)
                p.drawRect(QRectF(m + 2, y + 1, 12, 12)); y += 18
        y += 8
        p.setPen(QPen(QColor(sc))); p.setFont(QFont("Helvetica", 10, QFont.Bold))
        p.drawText(QRectF(m, y, w - 2*m, 18), Qt.AlignLeft, "Action Items"); y += 18
        for i in range(action_rows):
            if y + 18 > h - m: break
            self._hline(p, y + 14, m + 18, w - m, c, lw * 0.3)
            p.setPen(QPen(QColor(sc), lw * 0.7)); p.setBrush(Qt.NoBrush)
            p.drawRect(QRectF(m + 2, y + 1, 12, 12)); y += 22

    # ── Weekly Planner ──
    def _draw_weekly_planner(self, p, w, h):
        sh = int(self._params["start_hour"]); eh = int(self._params["end_hour"])
        tcw = self._params["time_col_width"] * IN_TO_PT
        show_we = self._params.get("show_weekend", True)
        interval = int(self._params.get("time_interval", 1))
        tf = self._params.get("time_format", "12h")
        cl = self._params.get("column_labels", "short")
        c = self._params["color"]; sc = self._params.get("secondary_color", "#2563EB")
        lw = self._params["line_width"]; m = 36
        num_days = 7 if show_we else 5
        day_names_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_names_full = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_names = day_names_full if cl == "full" else day_names_short
        if not show_we: day_names = day_names[:5]
        hours = list(range(sh, eh + 1)); header_h = 24
        row_h = (h - 2*m - header_h) / len(hours) if hours else 1
        col_w = (w - 2*m - tcw) / num_days
        p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(sc)))
        p.drawRect(QRectF(m, m, w - 2*m, header_h))
        p.setPen(QPen(QColor("#FFFFFF"))); p.setFont(QFont("Helvetica", 8, QFont.Bold))
        x = m + tcw
        for i, dn in enumerate(day_names):
            p.drawText(QRectF(x+2, m+4, col_w-4, header_h-8), Qt.AlignCenter, dn); x += col_w
        p.drawText(QRectF(m+2, m+4, tcw-4, header_h-8), Qt.AlignCenter, "Time")
        for idx, hr in enumerate(hours):
            y = m + header_h + idx * row_h
            self._hline(p, y, m, w - m, c, lw * 1.2 if hr % interval == 0 else lw * 0.3)
            if hr % interval == 0:
                p.setPen(QPen(QColor("#999999"))); p.setFont(QFont("Helvetica", 7))
                if tf == "24h":
                    hr_str = f"{hr:02d}:00"
                else:
                    hr_str = f"{hr % 12 or 12}:00 {'AM' if hr < 12 else 'PM'}"
                p.drawText(QRectF(m+2, y+2, tcw-4, 14), Qt.AlignCenter, hr_str)
        for col in range(num_days + 1):
            x = m + tcw + col * col_w
            self._vline(p, x, m + header_h, h - m, c, lw * 0.5)
        self._vline(p, m + tcw, m, h - m, c, lw * 1.5)
        if self._params.get("show_current_hour_line"):
            noon_y = m + header_h + (12 - sh) * row_h
            if m + header_h < noon_y < h - m:
                self._hline(p, noon_y, m, w - m, sc, lw * 2)

    # ── Budget Tracker ──
    def _draw_budget_tracker(self, p, w, h):
        inc_rows = int(self._params["income_rows"])
        exp_rows = int(self._params["expense_rows"])
        hdr_h = self._params["header_height"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#16A34A")
        lw = self._params["line_width"]; m = 36
        cat_w = self._params.get("category_col_width", 0.4)
        remaining = 1.0 - cat_w
        col_widths = [cat_w, remaining * 0.416, remaining * 0.333, remaining * 0.251]
        cols = ["Category", "Budgeted", "Actual", "Difference"]
        y = m
        p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(sc)))
        p.drawRect(QRectF(m, y, w - 2*m, hdr_h))
        p.setPen(QPen(QColor("#FFFFFF"))); p.setFont(QFont("Helvetica", 9, QFont.Bold))
        p.drawText(QRectF(m+4, y+4, w-2*m-8, hdr_h-8), Qt.AlignLeft, "INCOME"); y += hdr_h
        x = m
        for cw_frac, col_name in zip(col_widths, cols):
            cw_pt = (w - 2*m) * cw_frac
            p.setPen(QPen(QColor(c), lw)); p.setFont(QFont("Helvetica", 7, QFont.Bold))
            p.drawText(QRectF(x+2, y+2, cw_pt-4, 14), Qt.AlignLeft, col_name); x += cw_pt
        y += 16
        for r in range(inc_rows):
            x = m
            for cw_frac in col_widths:
                cw_pt = (w - 2*m) * cw_frac
                self._hline(p, y+14, x, x+cw_pt, c, lw * 0.3)
                self._vline(p, x, y, y+14, c, lw * 0.3); x += cw_pt
            y += 18
        if self._params.get("show_savings_section"):
            y += 10; sav_rows = int(self._params.get("savings_rows", 3))
            p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor("#2563EB")))
            p.drawRect(QRectF(m, y, w - 2*m, hdr_h))
            p.setPen(QPen(QColor("#FFFFFF"))); p.setFont(QFont("Helvetica", 9, QFont.Bold))
            p.drawText(QRectF(m+4, y+4, w-2*m-8, hdr_h-8), Qt.AlignLeft, "SAVINGS"); y += hdr_h
            x = m
            for cw_frac, col_name in zip(col_widths, cols):
                cw_pt = (w - 2*m) * cw_frac
                p.setPen(QPen(QColor(c), lw)); p.setFont(QFont("Helvetica", 7, QFont.Bold))
                p.drawText(QRectF(x+2, y+2, cw_pt-4, 14), Qt.AlignLeft, col_name); x += cw_pt
            y += 16
            for r in range(sav_rows):
                x = m
                for cw_frac in col_widths:
                    cw_pt = (w - 2*m) * cw_frac
                    self._hline(p, y+14, x, x+cw_pt, c, lw * 0.3)
                    self._vline(p, x, y, y+14, c, lw * 0.3); x += cw_pt
                y += 18
        y += 10
        p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor("#DC2626")))
        p.drawRect(QRectF(m, y, w - 2*m, hdr_h))
        p.setPen(QPen(QColor("#FFFFFF"))); p.setFont(QFont("Helvetica", 9, QFont.Bold))
        p.drawText(QRectF(m+4, y+4, w-2*m-8, hdr_h-8), Qt.AlignLeft, "EXPENSES"); y += hdr_h
        x = m
        for cw_frac, col_name in zip(col_widths, cols):
            cw_pt = (w - 2*m) * cw_frac
            p.setPen(QPen(QColor(c), lw)); p.setFont(QFont("Helvetica", 7, QFont.Bold))
            p.drawText(QRectF(x+2, y+2, cw_pt-4, 14), Qt.AlignLeft, col_name); x += cw_pt
        y += 16
        for r in range(exp_rows):
            x = m
            for cw_frac in col_widths:
                cw_pt = (w - 2*m) * cw_frac
                self._hline(p, y+14, x, x+cw_pt, c, lw * 0.3)
                self._vline(p, x, y, y+14, c, lw * 0.3); x += cw_pt
            y += 18
        if self._params.get("show_total_row"):
            self._hline(p, y, m, w - m, c, lw * 1.5)
            p.setPen(QPen(QColor(c), lw)); p.setFont(QFont("Helvetica", 8, QFont.Bold))
            p.drawText(QRectF(m+2, y+2, 80, 14), Qt.AlignLeft, "TOTAL")

    # ── Reading Log ──
    def _draw_reading_log(self, p, w, h):
        rows = int(self._params["entry_rows"]); hdr_h = self._params["header_height"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#94A3B8")
        lw = self._params["line_width"]; m = 36
        rh = self._params.get("row_height", 0.25) * IN_TO_PT
        show_genre = self._params.get("show_genre_column", False)
        show_prog = self._params.get("show_progress_bar", False)
        if show_genre:
            col_fracs = [0.03, 0.18, 0.14, 0.10, 0.10, 0.08, 0.08, 0.10, 0.19]
            col_names = ["#", "Title", "Author", "Started", "Finished", "Rating", "Genre", "Progress", "Notes"]
        elif show_prog:
            col_fracs = [0.04, 0.20, 0.16, 0.11, 0.11, 0.08, 0.08, 0.22]
            col_names = ["#", "Title", "Author", "Started", "Finished", "Rating", "Progress", "Notes"]
        else:
            col_fracs = [0.04, 0.22, 0.18, 0.12, 0.12, 0.10, 0.22]
            col_names = ["#", "Title", "Author", "Started", "Finished", "Rating", "Notes"]
        y = m
        p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(sc)))
        p.drawRect(QRectF(m, y, w - 2*m, hdr_h))
        p.setPen(QPen(QColor("#FFFFFF"))); p.setFont(QFont("Helvetica", 8, QFont.Bold))
        p.drawText(QRectF(m+4, y+4, w-2*m-8, hdr_h-8), Qt.AlignLeft, "Reading Log"); y += hdr_h
        x = m
        for frac, name in zip(col_fracs, col_names):
            cw_pt = (w - 2*m) * frac
            p.setPen(QPen(QColor(c), lw)); p.setFont(QFont("Helvetica", 7, QFont.Bold))
            p.drawText(QRectF(x+2, y+2, cw_pt-4, 14), Qt.AlignLeft, name); x += cw_pt
        y += 16
        for r in range(rows):
            if y + rh > h - m: break
            x = m
            for frac in col_fracs:
                cw_pt = (w - 2*m) * frac
                self._vline(p, x, y, y + rh, c, lw * 0.3); x += cw_pt
            self._vline(p, x, y, y + rh, c, lw * 0.3)
            self._hline(p, y + rh, m, w - m, c, lw * 0.3)
            if r % 2 == 0:
                p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(248, 250, 252, 80)))
                p.drawRect(QRectF(m, y, w - 2*m, rh))
            y += rh

    # ── Seyes French Ruled ──
    def _draw_seyes_french_ruled(self, p, w, h):
        ls = self._params["line_spacing"] * IN_TO_PT
        ml = self._params["margin_left"] * IN_TO_PT
        num_l = int(self._params.get("num_lines", 8))
        c = self._params["color"]; sc = self._params.get("secondary_color", "#FF6699")
        lw = self._params["line_width"]; m = 36
        pink_off = self._params.get("pink_line_offset", 2.0) * MM_TO_PT
        ms = self._params.get("margin_style", "single")
        y = m
        row_in_group = 0
        while y < h - m:
            if row_in_group % num_l == 0:
                self._hline(p, y, ml, w - m, c, lw * 2.5)
                self._hline(p, y + pink_off, ml, w - m, sc, lw * 1.0)
            elif row_in_group % (num_l // 2) == 0:
                self._hline(p, y, ml, w - m, c, lw * 1.2)
            else:
                pen = QPen(QColor(c), lw * 0.5); pen.setStyle(Qt.DashLine); p.setPen(pen)
                p.drawLine(QRectF(ml, y, w - m, y))
            y += ls; row_in_group += 1
            if row_in_group >= num_l: row_in_group = 0
        if ms == "double":
            self._vline(p, ml, m, h - m, sc, lw * 1.5)
            self._vline(p, ml + 4, m, h - m, sc, lw * 0.7)
        else:
            self._vline(p, ml, m, h - m, sc, lw * 1.5)
        if self._params.get("show_top_margin"):
            self._hline(p, m, 0, w, c, lw * 1.0)

    # ── NEW: Polar Coordinate ──
    def _draw_polar_coordinate(self, p, w, h):
        rs = self._params["radius_step"] * IN_TO_PT
        nr = int(self._params["num_radials"])
        show_lbl = self._params.get("show_labels", True)
        lr = self._params.get("label_radius", 0.3) * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#99BBDD")
        lw = self._params["line_width"]
        cx, cy = w / 2, h / 2
        max_r = math.sqrt(cx * cx + cy * cy)
        r = rs
        while r < max_r:
            p.setPen(QPen(QColor(sc), lw))
            p.drawEllipse(QRectF(cx - r, cy - r, 2 * r, 2 * r))
            if show_lbl:
                p.setPen(QPen(QColor(c))); p.setFont(QFont("Helvetica", 6))
                val = r / IN_TO_PT
                p.drawText(QRectF(cx + lr - 10, cy - r - 6, 20, 10), Qt.AlignCenter, f"{val:.1f}")
            r += rs
        start_ang = self._params.get("start_angle", 0)
        for i in range(nr):
            angle = math.radians(start_ang + 360 / nr * i)
            ex = cx + max_r * math.cos(angle)
            ey = cy - max_r * math.sin(angle)
            p.setPen(QPen(QColor(sc), lw * 0.7))
            p.drawLine(QRectF(cx, cy, ex, ey))
            if show_lbl:
                p.setPen(QPen(QColor(c))); p.setFont(QFont("Helvetica", 6))
                lx = cx + (lr + 10) * math.cos(angle)
                ly = cy - (lr + 10) * math.sin(angle)
                deg = int(start_ang + 360 / nr * i) % 360
                p.drawText(QRectF(lx - 10, ly - 6, 20, 12), Qt.AlignCenter, f"{deg}\u00b0")

    # ── NEW: Logarithmic Paper ──
    def _draw_logarithmic_paper(self, p, w, h):
        cycles = int(self._params["log_cycles"])
        gs = self._params["grid_size"] * IN_TO_PT
        show_lbl = self._params.get("show_labels", True)
        c = self._params["color"]; sc = self._params.get("secondary_color", "#66BB66")
        lw = self._params["line_width"]; m = self._params.get("margin", 1.0) * IN_TO_PT
        lfs = int(self._params.get("label_font_size", 7))
        log_w = w - 2 * m
        # Vertical lines: logarithmic spacing
        for cyc in range(cycles):
            base_x = m + (log_w / cycles) * cyc
            for sub in range(1, 10):
                x = base_x + (log_w / cycles) * math.log10(sub + 1)
                self._vline(p, x, m, h - m, sc, lw * 0.5)
            # Major line at decade
            major_x = m + (log_w / cycles) * (cyc + 1)
            self._vline(p, major_x, m, h - m, c, lw)
            if show_lbl:
                p.setPen(QPen(QColor(c))); p.setFont(QFont("Helvetica", lfs))
                p.drawText(QRectF(major_x - 8, h - m + 4, 16, 12), Qt.AlignCenter, f"10^{cyc+1}")
        self._vline(p, m, m, h - m, c, lw)
        # Horizontal lines: linear
        y = m
        while y <= h - m: self._hline(p, y, m, w - m, sc, lw * 0.5); y += gs
        # Axis labels
        if show_lbl:
            p.setPen(QPen(QColor(c))); p.setFont(QFont("Helvetica", lfs))
            for cyc in range(cycles + 1):
                x = m + (log_w / cycles) * cyc
                val = 10 ** cyc
                p.drawText(QRectF(x - 8, h - m + 4, 16, 12), Qt.AlignCenter, str(val))

    # ── NEW: Probability Paper ──
    def _draw_probability_paper(self, p, w, h):
        gs = self._params["grid_size"] * IN_TO_PT
        show_lbl = self._params.get("show_labels", True)
        c = self._params["color"]; sc = self._params.get("secondary_color", "#BB99DD")
        lw = self._params["line_width"]; m = self._params.get("margin", 1.0) * IN_TO_PT
        lfs = int(self._params.get("label_font_size", 7))
        # Regular grid
        x = m
        while x <= w - m: self._vline(p, x, m, h - m, sc, lw * 0.5); x += gs
        y = m
        while y <= h - m: self._hline(p, y, m, w - m, sc, lw * 0.5); y += gs
        # Probability axis labels (0.1% to 99.9%)
        if show_lbl:
            p.setPen(QPen(QColor(c))); p.setFont(QFont("Helvetica", lfs))
            probs = [0.1, 0.5, 1, 2, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 98, 99, 99.5, 99.9]
            usable_h = h - 2 * m
            for prob in probs:
                # Normal distribution inverse approximation (rational)
                p_val = prob / 100.0
                if p_val < 0.5:
                    z = -_norm_ppf(p_val)
                else:
                    z = _norm_ppf(1.0 - p_val)
                y_pos = m + usable_h * (1 - (z + 3.5) / 7.0)
                if m < y_pos < h - m:
                    self._hline(p, y_pos, m, w - m, c, lw)
                    p.drawText(QRectF(m - 36, y_pos - 6, 32, 12), Qt.AlignRight, f"{prob}%")

    # ── NEW: Seam Allowance ──
    def _draw_seam_allowance(self, p, w, h):
        gs = self._params["grid_size"] * IN_TO_PT
        mw = self._params["margin_width"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#FF9999")
        lw = self._params["line_width"]; m = self._params.get("margin", 0.5) * IN_TO_PT
        lfs = int(self._params.get("label_font_size", 7))
        # Regular grid
        x = m
        while x <= w - m: self._vline(p, x, m, h - m, sc, lw * 0.3); x += gs
        y = m
        while y <= h - m: self._hline(p, y, m, w - m, sc, lw * 0.3); y += gs
        # Quarter inch mark (0.25")
        qm = 0.25 * IN_TO_PT
        if self._params.get("show_quarter_mark"):
            pen = QPen(QColor(c), lw); pen.setStyle(Qt.DashLine); p.setPen(pen)
            p.drawLine(QRectF(m + qm, m, m + qm, h - m))
            p.drawLine(QRectF(w - m - qm, m, w - m - qm, h - m))
            p.drawLine(QRectF(m, m + qm, w - m, m + qm))
            p.drawLine(QRectF(m, h - m - qm, w - m, h - m - qm))
        # Five-eighths mark (0.625")
        fe = 0.625 * IN_TO_PT
        if self._params.get("show_five_eighths_mark"):
            pen = QPen(QColor(c), lw * 1.5); pen.setStyle(Qt.DashLine); p.setPen(pen)
            p.drawLine(QRectF(m + fe, m, m + fe, h - m))
            p.drawLine(QRectF(w - m - fe, m, w - m - fe, h - m))
            p.drawLine(QRectF(m, m + fe, w - m, m + fe))
            p.drawLine(QRectF(m, h - m - fe, w - m, h - m - fe))
        # Margin border
        self._vline(p, m + mw, m, h - m, c, lw)
        self._vline(p, w - m - mw, m, h - m, c, lw)
        self._hline(p, m + mw, m + mw, w - m - mw, c, lw)
        self._hline(p, h - m - mw, m + mw, w - m - mw, c, lw)
        # Labels
        p.setPen(QPen(QColor(c))); p.setFont(QFont("Helvetica", lfs))
        p.drawText(QRectF(m + mw + 2, m + 2, 60, 12), Qt.AlignLeft, "Seam: 5/8\"")
        if self._params.get("show_quarter_mark"):
            p.drawText(QRectF(m + 2, m + qm + 2, 40, 12), Qt.AlignLeft, "1/4\"")

    # ── NEW: Knitting Grid ──
    def _draw_knitting_grid(self, p, w, h):
        gs = self._params["grid_size"] * IN_TO_PT
        major = int(self._params.get("major_every", 10))
        show_rn = self._params.get("show_row_numbers", True)
        show_cn = self._params.get("show_col_numbers", True)
        c = self._params["color"]; sc = self._params.get("secondary_color", "#DDBBCC")
        mlw = self._params.get("major_line_weight", 2.0)
        lw = self._params["line_width"]; m = self._params.get("margin", 0.5) * IN_TO_PT
        lfs = int(self._params.get("label_font_size", 6))
        x = m
        while x <= w - m: self._vline(p, x, m, h - m, sc, lw); x += gs
        y = m
        while y <= h - m: self._hline(p, y, m, w - m, sc, lw); y += gs
        x = m
        while x <= w - m: self._vline(p, x, m, h - m, c, lw * mlw); x += gs * major
        y = m
        while y <= h - m: self._hline(p, y, m, w - m, c, lw * mlw); y += gs * major
        p.setFont(QFont("Helvetica", lfs)); p.setPen(QPen(QColor(c)))
        if show_cn:
            col = 0; x = m
            while x <= w - m:
                if col % major == 0 and col > 0:
                    p.drawText(QRectF(x + 1, h - m + 2, gs * major - 2, 10), Qt.AlignCenter, str(col))
                x += gs; col += 1
        if show_rn:
            row = 0; y = m
            while y <= h - m:
                if row % major == 0 and row > 0:
                    p.drawText(QRectF(m - 30, y + 1, 26, gs - 2), Qt.AlignRight, str(row))
                y += gs; row += 1

    # ── NEW: Circuit / Schematic ──
    def _draw_circuit___schematic(self, p, w, h):
        gs = self._params["grid_size"] * IN_TO_PT
        ds = self._params.get("dot_size", 1.0)
        major = int(self._params.get("major_every", 5))
        snap = self._params.get("snap_dots", True)
        c = self._params["color"]; sc = self._params.get("secondary_color", "#6699CC")
        mlw = self._params.get("major_line_weight", 2.0)
        lw = self._params["line_width"]; m = self._params.get("margin", 0.25) * IN_TO_PT
        # Fine grid
        x = m
        while x <= w - m: self._vline(p, x, m, h - m, sc, lw); x += gs
        y = m
        while y <= h - m: self._hline(p, y, m, w - m, sc, lw); y += gs
        # Major grid
        x = m
        while x <= w - m: self._vline(p, x, m, h - m, c, lw * mlw); x += gs * major
        y = m
        while y <= h - m: self._hline(p, y, m, w - m, c, lw * mlw); y += gs * major
        # Snap dots at intersections
        if snap:
            p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(c)))
            x = m
            while x <= w - m:
                y = m
                while y <= h - m:
                    p.drawEllipse(QRectF(x - ds/2, y - ds/2, ds, ds))
                    y += gs * major
                x += gs * major

    # ── NEW: Braille Practice ──
    def _draw_braille_practice(self, p, w, h):
        cs = self._params["cell_spacing"] * IN_TO_PT
        ds = self._params["dot_spacing"] * IN_TO_PT
        cell_sz = self._params["cell_size"] * IN_TO_PT
        show_guide = self._params.get("show_guide_dots", True)
        c = self._params["color"]; sc = self._params.get("secondary_color", "#AAAAAA")
        lw = self._params["line_width"]; m = self._params.get("margin", 1.0) * IN_TO_PT
        # Braille cell is 2 columns x 3 rows of dots
        dot_r = self._params.get("dot_radius", 1.5)
        y = m
        while y < h - m - cell_sz:
            x = m
            while x < w - m - cell_sz:
                # Cell border
                p.setPen(QPen(QColor(sc), lw * 0.3)); p.setBrush(Qt.NoBrush)
                p.drawRect(QRectF(x, y, cell_sz, cell_sz))
                # Draw guide dots (all 6 positions)
                if show_guide:
                    p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(sc)))
                    for col in range(2):
                        for row in range(3):
                            dx = x + cell_sz * 0.35 + col * ds
                            dy = y + cell_sz * 0.2 + row * ds
                            p.drawEllipse(QRectF(dx - dot_r, dy - dot_r, 2*dot_r, 2*dot_r))
                x += cs
            y += cs

    # ── NEW: Musical TAB ──
    def _draw_musical_tab(self, p, w, h):
        ns = int(self._params["num_staves"])
        ss = self._params["staff_spacing"] * IN_TO_PT
        gs = self._params["group_spacing"] * IN_TO_PT
        show_bar = self._params.get("show_barlines", True)
        bar_int = self._params.get("barline_interval", 2.0) * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#666666")
        lw = self._params["line_width"]
        staff_h = 5 * ss
        total = ns * (staff_h + gs) - gs
        start_y = (h - total) / 2
        for i in range(ns):
            base = start_y + i * (staff_h + gs)
            for j in range(6): self._hline(p, base + j * ss, 54, w - 54, c, lw)
            # TAB label
            p.setFont(QFont("Helvetica", 10, QFont.Bold)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(10, base, 40, staff_h), Qt.AlignCenter, "TAB")
            if show_bar and bar_int > 0:
                bx = 54 + bar_int
                while bx < w - 54: self._vline(p, bx, base, base + 5 * ss, c, lw); bx += bar_int

    # ── NEW: Ledger / Accounting ──
    def _draw_ledger___accounting(self, p, w, h):
        num_rows = int(self._params["num_rows"])
        ndc = int(self._params["num_debit_cols"])
        ncc = int(self._params["num_credit_cols"])
        hdr_h = self._params["header_height"] * IN_TO_PT
        show_total = self._params.get("show_totals_row", True)
        c = self._params["color"]; sc = self._params.get("secondary_color", "#16A34A")
        lw = self._params["line_width"]; m = 36
        # Column layout: Account | Debit cols | Credit cols
        total_data_cols = ndc + ncc
        acct_w = (w - 2 * m) * 0.25
        data_w = (w - 2 * m - acct_w) / total_data_cols
        y = m
        # Header
        p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(sc)))
        p.drawRect(QRectF(m, y, w - 2*m, hdr_h))
        p.setPen(QPen(QColor("#FFFFFF"))); p.setFont(QFont("Helvetica", 9, QFont.Bold))
        p.drawText(QRectF(m+4, y+4, acct_w-8, hdr_h-8), Qt.AlignLeft, "Account")
        for i in range(ndc):
            x = m + acct_w + i * data_w
            p.drawText(QRectF(x+2, y+4, data_w-4, hdr_h-8), Qt.AlignCenter, f"Debit {i+1}" if ndc > 1 else "Debit")
        for i in range(ncc):
            x = m + acct_w + ndc * data_w + i * data_w
            p.drawText(QRectF(x+2, y+4, data_w-4, hdr_h-8), Qt.AlignCenter, f"Credit {i+1}" if ncc > 1 else "Credit")
        y += hdr_h
        # Rows
        row_h = (h - m - y) / (num_rows + (1 if show_total else 0))
        for r in range(num_rows):
            self._hline(p, y + row_h, m, w - m, c, lw * 0.5)
            x = m + acct_w
            for i in range(total_data_cols + 1):
                self._vline(p, x, y, y + row_h, c, lw * 0.3)
                x += data_w
            if r % 2 == 0:
                p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(248, 250, 252, 60)))
                p.drawRect(QRectF(m, y, w - 2*m, row_h))
            y += row_h
        if show_total:
            self._hline(p, y, m, w - m, c, lw * 1.5)
            p.setPen(QPen(QColor(c))); p.setFont(QFont("Helvetica", 8, QFont.Bold))
            p.drawText(QRectF(m+4, y+2, acct_w-8, row_h-4), Qt.AlignLeft, "TOTAL")

    # ── NEW: Daily Schedule ──
    def _draw_daily_schedule(self, p, w, h):
        sh = int(self._params["start_hour"]); eh = int(self._params["end_hour"])
        slot_h = self._params["slot_height"] * IN_TO_PT
        tcw = self._params["time_col_width"] * IN_TO_PT
        show_15 = self._params.get("show_15min", False)
        c = self._params["color"]; sc = self._params.get("secondary_color", "#2563EB")
        lw = self._params["line_width"]; m = 36
        hours = list(range(sh, eh + 1))
        header_h = 28
        # Title
        p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(sc)))
        p.drawRect(QRectF(m, m, w - 2*m, header_h))
        p.setPen(QPen(QColor("#FFFFFF"))); p.setFont(QFont("Helvetica", 12, QFont.Bold))
        p.drawText(QRectF(m+8, m+4, w-2*m-16, header_h-8), Qt.AlignLeft, "Daily Schedule")
        y = m + header_h
        for hr in hours:
            self._hline(p, y, m, w - m, c, lw)
            p.setPen(QPen(QColor("#666666"))); p.setFont(QFont("Helvetica", 9))
            ampm = "AM" if hr < 12 else "PM"
            hr12 = hr % 12 or 12
            p.drawText(QRectF(m+4, y+4, tcw-8, slot_h-8), Qt.AlignLeft, f"{hr12}:00 {ampm}")
            if show_15:
                for q in range(1, 4):
                    qy = y + slot_h * q / 4
                    pen = QPen(QColor(sc), lw * 0.2); pen.setStyle(Qt.DotLine); p.setPen(pen)
                    p.drawLine(QRectF(m+tcw, qy, w-m, qy))
            y += slot_h
        self._vline(p, m + tcw, m + header_h, h - m, c, lw * 1.0)

    # ── NEW: Habit Tracker ──
    def _draw_habit_tracker(self, p, w, h):
        nh = int(self._params["num_habits"])
        show_wd = self._params.get("show_weekday_headers", True)
        show_mh = self._params.get("show_month_header", True)
        cbs = self._params["checkbox_size"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#2563EB")
        lw = self._params["line_width"]; m = 36
        days_in_month = int(self._params.get("days_in_month", 31))
        header_h = 32 if show_mh else 0
        wd_h = 20 if show_wd else 0
        habit_label_w = self._params.get("label_width", 100)
        row_pad = self._params.get("row_padding", 12)
        day_col_w = (w - 2*m - habit_label_w) / days_in_month
        y = m
        if show_mh:
            p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(sc)))
            p.drawRect(QRectF(m, y, w - 2*m, header_h))
            p.setPen(QPen(QColor("#FFFFFF"))); p.setFont(QFont("Helvetica", 11, QFont.Bold))
            p.drawText(QRectF(m+8, y+4, w-2*m-16, header_h-8), Qt.AlignLeft, "Habit Tracker")
            y += header_h
        if show_wd:
            p.setPen(QPen(QColor(c), lw * 0.5))
            day_names = ["M", "T", "W", "T", "F", "S", "S"]
            for d in range(days_in_month):
                x = m + habit_label_w + d * day_col_w
                dn = day_names[d % 7]
                p.setFont(QFont("Helvetica", 6))
                p.drawText(QRectF(x, y, day_col_w, wd_h), Qt.AlignCenter, dn)
                self._vline(p, x + day_col_w, y, y + wd_h, c, lw * 0.3)
            y += wd_h
        # Habit rows
        for i in range(nh):
            row_y = y + i * (cbs + row_pad)
            if row_y + cbs + row_pad > h - m: break
            # Habit label area
            p.setPen(QPen(QColor(c), lw * 0.3))
            self._hline(p, row_y + cbs + row_pad, m, w - m, c, lw * 0.3)
            # Day checkboxes
            for d in range(days_in_month):
                cx = m + habit_label_w + d * day_col_w + day_col_w / 2
                cy = row_y + cbs / 2
                p.setPen(QPen(QColor(sc), lw * 0.5)); p.setBrush(Qt.NoBrush)
                p.drawRect(QRectF(cx - cbs/2, cy - cbs/2, cbs, cbs))
                p.setPen(QPen(QColor("#AAAAAA"))); p.setFont(QFont("Helvetica", 6))
                p.drawText(QRectF(cx - 4, cy - 4, 8, 8), Qt.AlignCenter, str(d + 1))

    # ── NEW: Recipe Card ──
    def _draw_recipe_card(self, p, w, h):
        c = self._params["color"]; sc = self._params.get("secondary_color", "#D97706")
        lw = self._params["line_width"]; m = 54
        show_prep = self._params.get("show_prep_time", True)
        show_cook = self._params.get("show_cook_time", True)
        show_serv = self._params.get("show_servings", True)
        show_diff = self._params.get("show_difficulty", True)
        ing_rows = int(self._params.get("ingredients_rows", 12))
        inst_lines = int(self._params.get("instructions_lines", 15))
        y = m
        # Title
        p.setPen(QPen(QColor(sc), lw * 1.5))
        p.drawRect(QRectF(m, y, w - 2*m, 28))
        p.setPen(QPen(QColor("#AAAAAA"))); p.setFont(QFont("Helvetica", 8))
        p.drawText(QRectF(m+4, y+6, w-2*m-8, 16), Qt.AlignLeft, "Recipe Title: ________________________")
        y += 36
        # Info fields
        fields = []
        if show_prep: fields.append(("Prep Time:", 0.2))
        if show_cook: fields.append(("Cook Time:", 0.2))
        if show_serv: fields.append(("Servings:", 0.15))
        if show_diff: fields.append(("Difficulty:", 0.15))
        if fields:
            x = m
            for label, frac in fields:
                fw = (w - 2*m) * frac
                p.setPen(QPen(QColor(c), lw)); p.setFont(QFont("Helvetica", 8))
                p.drawText(QRectF(x, y, 60, 16), Qt.AlignLeft, label)
                self._hline(p, y + 16, x + 60, x + fw, c, lw * 0.3)
                x += fw
            y += 24
        # Ingredients
        p.setPen(QPen(QColor(sc))); p.setFont(QFont("Helvetica", 11, QFont.Bold))
        p.drawText(QRectF(m, y, w-2*m, 18), Qt.AlignLeft, "Ingredients"); y += 20
        for i in range(ing_rows):
            if y + 16 > h - m - inst_lines * 16 - 40: break
            p.setPen(QPen(QColor(c), lw * 0.3))
            p.drawRect(QRectF(m + 2, y, 10, 10))
            self._hline(p, y + 5, m + 16, w - m, c, lw * 0.3)
            y += 16
        y += 10
        # Instructions
        p.setPen(QPen(QColor(sc))); p.setFont(QFont("Helvetica", 11, QFont.Bold))
        p.drawText(QRectF(m, y, w-2*m, 18), Qt.AlignLeft, "Instructions"); y += 20
        for i in range(inst_lines):
            if y + 16 > h - m: break
            p.setPen(QPen(QColor(c), lw * 0.3))
            p.drawText(QRectF(m + 4, y, 16, 12), Qt.AlignLeft, f"{i+1}.")
            self._hline(p, y + 8, m + 24, w - m, c, lw * 0.3)
            y += 16


    # ── Perspective Grid ──
    def _draw_perspective_grid(self, p, w, h):
        npts = int(self._params["num_points"])
        gs = self._params["grid_size"] * IN_TO_PT
        horizon_pct = self._params["horizon_position"] / 100.0
        c = self._params["color"]; sc = self._params.get("secondary_color", "#99BBDD")
        lw = self._params["line_width"]
        vp_size = self._params.get("vanishing_point_size", 4.0)
        horizon_y = h * horizon_pct
        # Horizon line
        if self._params.get("show_horizon", True):
            self._hline(p, horizon_y, 0, w, sc, lw * 1.5)
        # Ground line
        if self._params.get("show_ground_line", True):
            ground_y = horizon_y + (h - horizon_y) * 0.15
            self._hline(p, ground_y, 0, w, sc, lw * 0.5)
        if npts == 1:
            # 1-point perspective
            vx, vy = w / 2, horizon_y
            # Radial lines from vanishing point
            x = 0
            while x <= w:
                self._line(p, vx, vy, x, 0, c, lw * 0.5)
                self._line(p, vx, vy, x, h, c, lw * 0.5)
                x += gs * 2
            # Horizontal guide lines (closer together near horizon)
            num_h = int((h - horizon_y) / gs)
            for i in range(1, num_h + 1):
                y = horizon_y + (h - horizon_y) * (i / num_h) ** 1.5
                if y < h:
                    self._hline(p, y, 0, w, sc, lw * 0.3)
            num_h2 = int(horizon_y / gs)
            for i in range(1, num_h2 + 1):
                y = horizon_y - (horizon_y) * (i / num_h2) ** 1.5
                if y > 0:
                    self._hline(p, y, 0, w, sc, lw * 0.3)
            # Vanishing point dot
            p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(c)))
            p.drawEllipse(QRectF(vx - vp_size, vy - vp_size, 2 * vp_size, 2 * vp_size))
        elif npts == 2:
            # 2-point perspective
            vx1, vy1 = 0, horizon_y
            vx2, vy2 = w, horizon_y
            for vi, (vx, vy) in enumerate([(vx1, vy1), (vx2, vy2)]):
                x = 0
                while x <= w:
                    if vi == 0:
                        self._line(p, vx, vy, x, h, c, lw * 0.5)
                    else:
                        self._line(p, vx, vy, x, h, c, lw * 0.5)
                    x += gs * 2
            # Vertical lines
            x = gs * 2
            while x < w:
                self._vline(p, x, horizon_y, h, sc, lw * 0.3)
                x += gs * 2
            # Horizontal guide lines below horizon
            num_h = int((h - horizon_y) / gs)
            for i in range(1, num_h + 1):
                y = horizon_y + (h - horizon_y) * (i / num_h) ** 1.5
                if y < h:
                    self._hline(p, y, 0, w, sc, lw * 0.3)
            # Vanishing points
            p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(c)))
            p.drawEllipse(QRectF(vx1 - vp_size, vy1 - vp_size, 2 * vp_size, 2 * vp_size))
            p.drawEllipse(QRectF(vx2 - vp_size, vy2 - vp_size, 2 * vp_size, 2 * vp_size))

    # ── Mandala Guide ──
    def _draw_mandala_guide(self, p, w, h):
        nradials = int(self._params["num_radials"])
        nrings = int(self._params["num_rings"])
        rs = self._params["ring_spacing"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#F0C0D0")
        lw = self._params["line_width"]
        cx, cy = w / 2, h / 2
        max_r = min(w, h) / 2 - 20
        # Concentric circles
        if self._params.get("show_concentric_circles", True):
            p.setPen(QPen(QColor(sc), lw * 0.5))
            p.setBrush(Qt.NoBrush)
            for i in range(1, nrings + 1):
                r = rs * i
                if r > max_r: break
                p.drawEllipse(QRectF(cx - r, cy - r, 2 * r, 2 * r))
        # Radial lines
        p.setPen(QPen(QColor(c), lw))
        for i in range(nradials):
            angle = 2 * math.pi * i / nradials
            ex = cx + max_r * math.cos(angle)
            ey = cy + max_r * math.sin(angle)
            p.drawLine(QRectF(cx, cy, ex, ey))
            # Extend radials between rings as lighter lines
            p.setPen(QPen(QColor(sc), lw * 0.3))
            for j in range(1, nrings):
                r1 = rs * j
                r2 = rs * (j + 1)
                if r2 > max_r: break
                sx = cx + r1 * math.cos(angle)
                sy = cy + r1 * math.sin(angle)
                ex2 = cx + r2 * math.cos(angle)
                ey2 = cy + r2 * math.sin(angle)
                p.drawLine(QRectF(sx, sy, ex2, ey2))
            p.setPen(QPen(QColor(c), lw))
        # Center dot
        if self._params.get("show_center_dot", True):
            cds = self._params.get("center_dot_size", 3.0)
            p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(c)))
            p.drawEllipse(QRectF(cx - cds, cy - cds, 2 * cds, 2 * cds))

    # ── Guitar Chord Diagram ──
    def _draw_guitar_chord_diagram(self, p, w, h):
        dw = int(self._params["diagrams_w"])
        dh = int(self._params["diagrams_h"])
        ds = self._params["diagram_size"] * IN_TO_PT
        nfrets = int(self._params.get("num_frets", 5))
        c = self._params["color"]; sc = self._params.get("secondary_color", "#94A3B8")
        lw = self._params["line_width"]
        m = 36
        # Calculate layout
        total_w_needed = dw * ds + (dw - 1) * m
        total_h_needed = dh * (ds + 36) + (dh - 1) * m
        start_x = (w - total_w_needed) / 2
        start_y = (h - total_h_needed) / 2
        if start_x < m: start_x = m
        if start_y < m: start_y = m
        for row in range(dh):
            for col in range(dw):
                x = start_x + col * (ds + m)
                y = start_y + row * (ds + 36)
                # Fret spacing
                fret_h = ds / nfrets
                # Nut (thick top line)
                p.setPen(QPen(QColor(c), lw * 2))
                p.drawLine(QRectF(x, y, x + ds, y))
                # Frets
                p.setPen(QPen(QColor(c), lw))
                for f in range(1, nfrets + 1):
                    fy = y + f * fret_h
                    p.drawLine(QRectF(x, fy, x + ds, fy))
                # Strings (6)
                string_spacing = ds / 5
                for s in range(6):
                    sx = x + s * string_spacing
                    p.drawLine(QRectF(sx, y, sx, y + ds))
                # String names
                if self._params.get("show_string_names", True):
                    names = ["E", "A", "D", "G", "B", "e"]
                    p.setFont(QFont("Helvetica", 7)); p.setPen(QPen(QColor(sc)))
                    for s in range(6):
                        sx = x + s * string_spacing
                        p.drawText(QRectF(sx - 6, y - 14, 12, 12), Qt.AlignCenter, names[s])
                # Fret numbers
                if self._params.get("show_fret_numbers", True):
                    p.setFont(QFont("Helvetica", 7)); p.setPen(QPen(QColor(sc)))
                    for f in range(1, nfrets + 1):
                        fy = y + (f - 0.5) * fret_h
                        p.drawText(QRectF(x - 18, fy - 6, 14, 12), Qt.AlignRight, str(f))
                # Open/mute circles above nut
                if self._params.get("show_open_mute", True):
                    p.setPen(Qt.NoPen)
                    for s in range(6):
                        sx = x + s * string_spacing
                        # Open circle (O)
                        p.setBrush(Qt.NoBrush); p.setPen(QPen(QColor(sc), 0.5))
                        p.drawEllipse(QRectF(sx - 4, y - 24, 8, 8))
                    p.setPen(Qt.NoPen)

    # ── Venn Diagram ──
    def _draw_venn_diagram(self, p, w, h):
        nc = int(self._params["num_circles"])
        cr = self._params["circle_radius"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#D0E0F0")
        lw = self._params["line_width"]
        cx, cy = w / 2, h / 2
        # Adjust radius to fit
        max_r = min(w, h) / 3.5
        if cr > max_r: cr = max_r
        # Calculate circle positions
        positions = []
        overlap = self._params.get("overlap_ratio", 0.5)
        if nc == 2:
            offset = cr * overlap
            positions = [(cx - offset, cy), (cx + offset, cy)]
        elif nc == 3:
            offset = cr * overlap
            for i in range(3):
                angle = math.pi / 2 + 2 * math.pi * i / 3
                positions.append((cx + offset * math.cos(angle), cy - offset * math.sin(angle)))
        elif nc >= 4:
            offset = cr * overlap
            positions = [
                (cx - offset, cy - offset * 0.7),
                (cx + offset, cy - offset * 0.7),
                (cx - offset, cy + offset * 0.7),
                (cx + offset, cy + offset * 0.7),
            ]
        # Shading
        if self._params.get("show_shading", False):
            p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(sc)))
            for (px, py) in positions:
                p.drawEllipse(QRectF(px - cr, py - cr, 2 * cr, 2 * cr))
        # Circles
        p.setBrush(Qt.NoBrush); p.setPen(QPen(QColor(c), lw))
        for (px, py) in positions:
            p.drawEllipse(QRectF(px - cr, py - cr, 2 * cr, 2 * cr))
        # Labels
        if self._params.get("show_labels", True):
            lfs = int(self._params.get("label_font_size", 9))
            p.setFont(QFont("Helvetica", lfs)); p.setPen(QPen(QColor(c)))
            labels_2 = ["A", "B"]
            labels_3 = ["A", "B", "C"]
            labels_4 = ["A", "B", "C", "D"]
            labels = {2: labels_2, 3: labels_3, 4: labels_4}.get(nc, [chr(65+i) for i in range(nc)])
            for i, (px, py) in enumerate(positions):
                # Place label outside the overlapping area
                if nc == 2:
                    lx = px + (-cr * 0.7 if i == 0 else cr * 0.5)
                elif nc == 3:
                    angle = math.pi / 2 + 2 * math.pi * i / 3
                    lx = px + cr * 0.55 * math.cos(angle)
                else:
                    lx = px + (cr * 0.6 if i % 2 == 0 else -cr * 0.6)
                ly = py - cr - 10
                p.drawText(QRectF(lx - 8, ly, 16, 14), Qt.AlignCenter, labels[i] if i < len(labels) else "")

    # ── Study Notes ──
    def _draw_study_notes(self, p, w, h):
        ls = self._params["line_spacing"] * IN_TO_PT
        ml = self._params["margin_left"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#94A3B8")
        lw = self._params["line_width"]
        sh = self._params.get("summary_height", 2.0) * IN_TO_PT
        hdr = self._params.get("section_header_height", 0.5) * IN_TO_PT
        m = 54  # smaller margin
        y = m
        # Date and Topic fields
        if self._params.get("show_date_field", True):
            p.setFont(QFont("Helvetica", 9, QFont.Bold)); p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m, y, 80, 14), Qt.AlignLeft, "Date:")
            p.setPen(QPen(QColor(c), lw * 0.5))
            self._hline(p, y + 12, m + 45, m + 220, c, lw * 0.5)
            y += 22
        if self._params.get("show_topic_field", True):
            p.setFont(QFont("Helvetica", 9, QFont.Bold)); p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m, y, 80, 14), Qt.AlignLeft, "Topic:")
            p.setPen(QPen(QColor(c), lw * 0.5))
            self._hline(p, y + 12, m + 50, w - m, c, lw * 0.5)
            y += 24
        # Key Concepts section
        if self._params.get("show_key_concepts", True):
            p.setFont(QFont("Helvetica", 10, QFont.Bold)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(m, y, w - 2*m, 16), Qt.AlignLeft, "Key Concepts"); y += 18
            concepts = int(self._params.get("concepts_rows", 5))
            for i in range(concepts):
                if y > h - sh - 20: break
                p.setPen(QPen(QColor(c), lw * 0.3))
                self._hline(p, y + 12, m + 8, w - m, c, lw * 0.3)
                y += ls * 0.8
            y += 8
        # Section divider
        self._hline(p, y, m, w - m, sc, lw * 0.5); y += 8
        # Notes lines
        bottom = h - sh - 10
        while y < bottom:
            self._hline(p, y, ml, w - m, c, lw * 0.5)
            y += ls
        # Summary section
        if self._params.get("show_summary_section", True):
            self._hline(p, h - sh, m, w - m, c, lw * 1.5)
            p.setFont(QFont("Helvetica", 10, QFont.Bold)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(m + 4, h - sh + 4, w - 2*m, 16), Qt.AlignLeft, "Summary")
            sy = h - sh + 22
            while sy < h - 10:
                self._hline(p, sy, m, w - m, sc, lw * 0.3)
                sy += ls * 0.8

    # ── Project Planner ──
    def _draw_project_planner(self, p, w, h):
        nph = int(self._params["num_phases"])
        tpp = int(self._params["tasks_per_phase"])
        c = self._params["color"]; sc = self._params.get("secondary_color", "#2563EB")
        lw = self._params["line_width"]
        m = 36
        hdr_h = 50
        y = m
        # Title
        p.setFont(QFont("Helvetica", 14, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2*m, 22), Qt.AlignLeft, "Project Planner")
        p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(sc)))
        self._hline(p, y + 24, m, w - m, c, lw * 0.5)
        y += 32
        # Column headers
        cols = ["Phase / Task"]
        if self._params.get("show_priority_col", True): cols.append("Priority")
        if self._params.get("show_status_col", True): cols.append("Status")
        if self._params.get("show_deadline_col", True): cols.append("Deadline")
        cols.append("Notes")
        num_cols = len(cols)
        col_w = (w - 2 * m) / num_cols
        x = m
        p.setFont(QFont("Helvetica", 9, QFont.Bold)); p.setPen(QPen(QColor(c)))
        for ci, col_name in enumerate(cols):
            p.drawText(QRectF(x + 4, y, col_w - 8, 16), Qt.AlignLeft, col_name)
            x += col_w
        self._hline(p, y + 18, m, w - m, c, lw); y += 20
        # Phase rows
        row_h = 18
        for phase in range(nph):
            if y + row_h > h - m: break
            # Phase header
            p.setPen(QPen(QColor(sc), lw * 0.3))
            p.setFont(QFont("Helvetica", 9, QFont.Bold))
            p.drawText(QRectF(m + 4, y, col_w - 8, row_h), Qt.AlignLeft, f"Phase {phase + 1}")
            # Shading
            p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(sc)))
            p.setOpacity(0.05)
            p.drawRect(QRectF(m, y, w - 2*m, row_h))
            p.setOpacity(1.0)
            p.setPen(Qt.NoPen)
            y += row_h
            # Task rows
            for task in range(tpp):
                if y + row_h > h - m: break
                self._hline(p, y + row_h, m, w - m, c, lw * 0.3)
                # Vertical column lines
                x = m + col_w
                for ci in range(1, num_cols):
                    self._vline(p, x, y, y + row_h, c, lw * 0.2)
                    x += col_w
                y += row_h
            # Phase separator
            self._hline(p, y, m, w - m, c, lw * 0.8)
            y += 4
        # Timeline section
        if self._params.get("show_timeline", True) and y + 60 < h - m:
            y += 8
            p.setFont(QFont("Helvetica", 10, QFont.Bold)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(m, y, w - 2*m, 18), Qt.AlignLeft, "Timeline")
            y += 22
            self._hline(p, y, m, w - m, sc, lw)
            y += 4
            # Timeline arrow
            p.setPen(QPen(QColor(sc), lw))
            p.drawLine(QRectF(m, y + 10, w - m, y + 10))
            p.drawLine(QRectF(w - m - 12, y + 4, w - m, y + 10))
            p.drawLine(QRectF(w - m - 12, y + 16, w - m, y + 10))
            # Milestone markers
            for i in range(nph):
                mx = m + (w - 2 * m) * (i + 1) / (nph + 1)
                p.setBrush(QBrush(QColor(sc))); p.setPen(Qt.NoPen)
                p.drawEllipse(QRectF(mx - 4, y + 6, 8, 8))

    # ── Fitness Log ──
    def _draw_fitness_log(self, p, w, h):
        nex = int(self._params["num_exercises"])
        nsets = int(self._params["num_sets"])
        c = self._params["color"]; sc = self._params.get("secondary_color", "#16A34A")
        lw = self._params["line_width"]
        m = 36
        y = m
        # Title
        p.setFont(QFont("Helvetica", 13, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2*m, 20), Qt.AlignLeft, "Fitness Log")
        y += 26
        # Date field
        if self._params.get("show_date_field", True):
            p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m, y, 40, 14), Qt.AlignLeft, "Date:")
            self._hline(p, y + 12, m + 40, m + 200, c, lw * 0.5)
            y += 22
        # Build columns
        cols = ["Exercise"]
        for s in range(1, nsets + 1):
            cols.append(f"Set {s}")
        if self._params.get("show_weight_col", True): cols.append("Wt")
        if self._params.get("show_reps_col", True): cols.append("Reps")
        if self._params.get("show_rest_col", True): cols.append("Rest")
        if self._params.get("show_notes_col", True): cols.append("Notes")
        num_cols = len(cols)
        col_w = (w - 2 * m) / num_cols
        # Header row
        hdr_h = 18
        row_h = self._params.get("row_height", 20)
        p.setFont(QFont("Helvetica", 8, QFont.Bold)); p.setPen(QPen(QColor(c)))
        x = m
        for col_name in cols:
            p.drawText(QRectF(x + 2, y, col_w - 4, hdr_h), Qt.AlignCenter, col_name)
            x += col_w
        self._hline(p, y + hdr_h, m, w - m, c, lw); y += hdr_h
        # Exercise rows
        row_h = 20
        for ex in range(nex):
            if y + row_h > h - m: break
            # Alternate shading
            if ex % 2 == 0:
                p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(sc)))
                p.setOpacity(0.04)
                p.drawRect(QRectF(m, y, w - 2*m, row_h))
                p.setOpacity(1.0); p.setPen(Qt.NoPen)
            # Exercise number label
            p.setFont(QFont("Helvetica", 8)); p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m + 4, y, col_w - 8, row_h), Qt.AlignLeft, f"{ex + 1}.")
            # Cell borders
            self._hline(p, y + row_h, m, w - m, c, lw * 0.3)
            x = m + col_w
            for ci in range(1, num_cols):
                self._vline(p, x, y, y + row_h, c, lw * 0.2)
                x += col_w
            y += row_h

    # ── Weight Tracker ──
    def _draw_weight_tracker(self, p, w, h):
        nw = int(self._params["num_weeks"])
        rh = self._params["row_height"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#2563EB")
        lw = self._params["line_width"]
        m = 36
        y = m
        # Title
        p.setFont(QFont("Helvetica", 13, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2*m, 20), Qt.AlignLeft, "Weight Tracker")
        y += 28
        # Build columns
        cols = ["Week"]
        if self._params.get("show_date_col", True): cols.append("Date")
        if self._params.get("show_weight_col", True): cols.append("Weight")
        if self._params.get("show_change_col", True): cols.append("Change")
        if self._params.get("show_bmi_col", False): cols.append("BMI")
        cols.append("Notes")
        num_cols = len(cols)
        col_w = (w - 2 * m) / num_cols
        # Header
        hdr_h = 18
        row_h = self._params.get("row_height", 20)
        p.setFont(QFont("Helvetica", 9, QFont.Bold)); p.setPen(QPen(QColor(c)))
        x = m
        for col_name in cols:
            p.drawText(QRectF(x + 2, y, col_w - 4, hdr_h), Qt.AlignCenter, col_name)
            x += col_w
        self._hline(p, y + hdr_h, m, w - m, c, lw); y += hdr_h
        # Data rows
        for week in range(1, nw + 1):
            if y + rh > h - m: break
            # Week number
            p.setFont(QFont("Helvetica", 8)); p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m + 4, y, col_w - 8, rh), Qt.AlignLeft, f"{week}")
            # Row border
            self._hline(p, y + rh, m, w - m, c, lw * 0.3)
            # Column lines
            x = m + col_w
            for ci in range(1, num_cols):
                self._vline(p, x, y, y + rh, c, lw * 0.2)
                x += col_w
            y += rh
        # Goal line
        if self._params.get("show_goal_line", True):
            goal = self._params.get("goal_weight", 150.0)
            y_goal = y + 10
            if y_goal < h - 20:
                p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(c)))
                p.drawText(QRectF(m, y_goal, w - 2*m, 16), Qt.AlignLeft, f"Goal: {goal} lbs")

    # ── Travel Journal ──
    def _draw_travel_journal(self, p, w, h):
        c = self._params["color"]; sc = self._params.get("secondary_color", "#D97706")
        lw = self._params["line_width"]
        m = 40
        y = m
        # Title area
        p.setFont(QFont("Helvetica", 16, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2*m, 24), Qt.AlignLeft, "Travel Journal")
        y += 30
        # Date and Location
        if self._params.get("show_date_field", True):
            p.setFont(QFont("Helvetica", 9, QFont.Bold)); p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m, y, 60, 14), Qt.AlignLeft, "Date:")
            self._hline(p, y + 12, m + 45, m + 230, c, lw * 0.5)
        if self._params.get("show_location_field", True):
            p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m + 250, y, 70, 14), Qt.AlignLeft, "Location:")
            self._hline(p, y + 12, m + 320, w - m, c, lw * 0.5)
        y += 24
        self._hline(p, y, m, w - m, sc, lw * 0.5); y += 8
        # Journal lines
        entry_lines = int(self._params.get("num_entry_lines", 20))
        ls = self._params.get("line_spacing", 0.375) * IN_TO_PT if "line_spacing" in self._params else 0.375 * IN_TO_PT
        # Calculate bottom area needs
        bottom_needed = 0
        if self._params.get("show_weather_section", True): bottom_needed += 50
        if self._params.get("show_highlights_section", True):
            bottom_needed += 24 + int(self._params.get("highlights_rows", 5)) * 16
        if self._params.get("show_expenses_section", True):
            bottom_needed += 24 + int(self._params.get("expense_rows", 5)) * 16
        max_y = h - m - bottom_needed
        while y < max_y and entry_lines > 0:
            self._hline(p, y, m, w - m, c, lw * 0.3)
            y += ls
            entry_lines -= 1
        y += 6
        # Weather section
        if self._params.get("show_weather_section", True) and y + 40 < h - m:
            p.setFont(QFont("Helvetica", 9, QFont.Bold)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(m, y, w - 2*m, 16), Qt.AlignLeft, "Weather")
            y += 16
            p.setFont(QFont("Helvetica", 8)); p.setPen(QPen(QColor(sc)))
            for label, xo in [("Temp:", 0), ("Condition:", 150), ("High/Low:", 320)]:
                p.drawText(QRectF(m + xo, y, 80, 14), Qt.AlignLeft, label)
                self._hline(p, y + 12, m + xo + 55, m + xo + 130, c, lw * 0.3)
            y += 22
        # Highlights section
        if self._params.get("show_highlights_section", True) and y + 30 < h - m:
            p.setFont(QFont("Helvetica", 9, QFont.Bold)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(m, y, w - 2*m, 16), Qt.AlignLeft, "Highlights")
            y += 18
            h_rows = int(self._params.get("highlights_rows", 5))
            for i in range(h_rows):
                if y + 14 > h - m: break
                self._hline(p, y + 12, m + 8, w - m, c, lw * 0.3)
                y += 16
            y += 4
        # Expenses section
        if self._params.get("show_expenses_section", True) and y + 30 < h - m:
            self._hline(p, y, m, w - m, sc, lw * 0.5); y += 6
            p.setFont(QFont("Helvetica", 9, QFont.Bold)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(m, y, 100, 16), Qt.AlignLeft, "Expenses")
            # Expense header
            y += 16
            p.setFont(QFont("Helvetica", 7, QFont.Bold)); p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m, y, 120, 12), Qt.AlignLeft, "Item")
            p.drawText(QRectF(m + 140, y, 60, 12), Qt.AlignLeft, "Amount")
            y += 14
            e_rows = int(self._params.get("expense_rows", 5))
            for i in range(e_rows):
                if y + 14 > h - m: break
                self._hline(p, y + 12, m, m + 130, c, lw * 0.3)
                self._hline(p, y + 12, m + 135, m + 200, c, lw * 0.3)
                y += 16

    # ── Essay Outline ──
    def _draw_essay_outline(self, p, w, h):
        nbp = int(self._params["num_body_paragraphs"])
        c = self._params["color"]; sc = self._params.get("secondary_color", "#94A3B8")
        lw = self._params["line_width"]
        m = 50
        y = m
        # Title area
        p.setFont(QFont("Helvetica", 13, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2*m, 20), Qt.AlignLeft, "Essay Outline")
        y += 28
        # Essay title field
        p.setFont(QFont("Helvetica", 10)); p.setPen(QPen(QColor(sc)))
        p.drawText(QRectF(m, y, 120, 14), Qt.AlignLeft, "Essay Title:")
        self._hline(p, y + 14, m, w - m, c, lw * 0.5)
        y += 24
        # Hook section
        if self._params.get("show_hook_section", True):
            p.setFont(QFont("Helvetica", 10, QFont.Bold)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(m, y, w - 2*m, 16), Qt.AlignLeft, "I. Introduction")
            y += 20
            p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m + 16, y, w - 2*m - 16, 14), Qt.AlignLeft, "Hook / Attention Grabber:")
            y += 14
            self._hline(p, y, m + 16, w - m, c, lw * 0.3)
            y += 18
        # Thesis section
        if self._params.get("show_thesis_section", True):
            p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m + 16, y, w - 2*m - 16, 14), Qt.AlignLeft, "Thesis Statement:")
            y += 14
            self._hline(p, y, m + 16, w - m, c, lw * 0.5)
            y += 12
            self._hline(p, y, m + 16, w - m, c, lw * 0.3)
            y += 20
        # Body paragraphs
        evidence = int(self._params.get("evidence_lines_per_para", 3))
        avail = h - m - y
        if self._params.get("show_conclusion_section", True):
            avail -= 80
        if self._params.get("show_counter_argument", True):
            avail -= 60
        para_h = min(avail / (nbp + 0.5), 160)
        for i in range(nbp):
            if y + para_h > h - m - 40: break
            roman = ["II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
            label = roman[i] if i < len(roman) else f"{i + 2}"
            p.setFont(QFont("Helvetica", 10, QFont.Bold)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(m, y, w - 2*m, 16), Qt.AlignLeft, f"{label}. Body Paragraph {i + 1}")
            y += 18
            p.setFont(QFont("Helvetica", 8)); p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m + 16, y, 120, 12), Qt.AlignLeft, "Topic Sentence:")
            y += 12
            self._hline(p, y, m + 16, w - m, c, lw * 0.3)
            y += 14
            for e in range(evidence):
                if y + 12 > h - m - 40: break
                p.setPen(QPen(QColor(sc)))
                p.drawText(QRectF(m + 24, y, 120, 12), Qt.AlignLeft, f"Evidence {e + 1}:")
                y += 12
                self._hline(p, y, m + 24, w - m, c, lw * 0.3)
                y += 14
            p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m + 24, y, 120, 12), Qt.AlignLeft, "Analysis:")
            y += 12
            self._hline(p, y, m + 24, w - m, c, lw * 0.3)
            y += 18
        # Counter argument
        if self._params.get("show_counter_argument", True) and y + 50 < h - m:
            next_roman = ["III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
            ri = nbp
            label = next_roman[ri] if ri < len(next_roman) else f"{ri + 2}"
            p.setFont(QFont("Helvetica", 10, QFont.Bold)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(m, y, w - 2*m, 16), Qt.AlignLeft, f"{label}. Counter Argument")
            y += 18
            p.setFont(QFont("Helvetica", 8)); p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m + 16, y, 120, 12), Qt.AlignLeft, "Opposing View:")
            y += 12
            self._hline(p, y, m + 16, w - m, c, lw * 0.3)
            y += 14
            p.drawText(QRectF(m + 16, y, 120, 12), Qt.AlignLeft, "Rebuttal:")
            y += 12
            self._hline(p, y, m + 16, w - m, c, lw * 0.3)
            y += 20
        # Conclusion
        if self._params.get("show_conclusion_section", True) and y + 50 < h - m:
            last_roman = ["IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
            ri = nbp + (1 if self._params.get("show_counter_argument", True) else 0)
            label = last_roman[ri] if ri < len(last_roman) else f"{ri + 2}"
            p.setFont(QFont("Helvetica", 10, QFont.Bold)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(m, y, w - 2*m, 16), Qt.AlignLeft, f"{label}. Conclusion")
            y += 18
            p.setFont(QFont("Helvetica", 8)); p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m + 16, y, 120, 12), Qt.AlignLeft, "Restate Thesis:")
            y += 12
            self._hline(p, y, m + 16, w - m, c, lw * 0.3)
            y += 14
            p.drawText(QRectF(m + 16, y, 120, 12), Qt.AlignLeft, "Summary of Points:")
            y += 12
            self._hline(p, y, m + 16, w - m, c, lw * 0.3)
            y += 14
            p.drawText(QRectF(m + 16, y, 120, 12), Qt.AlignLeft, "Final Thought:")
            y += 12
            self._hline(p, y, m + 16, w - m, c, lw * 0.3)


    # ── Grand Staff Paper ──
    def _draw_grand_staff_paper(self, p, w, h):
        ss = self._params["staff_spacing"] * IN_TO_PT
        gs = self._params["group_spacing"] * IN_TO_PT
        nsys = int(self._params["num_systems"])
        c = self._params["color"]; sc = self._params.get("secondary_color", "#666666")
        lw = self._params["line_width"]
        m = 54
        system_h = 10 * ss + gs  # 5 lines treble + 5 lines bass + gap
        total_h = nsys * system_h
        start_y = max((h - total_h) / 2, m)
        for s in range(nsys):
            y = start_y + s * system_h
            if y + 10 * ss > h - 20: break
            # Treble clef staff (top 5 lines)
            for i in range(5):
                self._hline(p, y + i * ss, m, w - m, c, lw)
            # Bass clef staff (bottom 5 lines)
            bass_y = y + 6 * ss
            for i in range(5):
                self._hline(p, bass_y + i * ss, m, w - m, c, lw)
            # Brace / bracket
            bstyle = self._params.get("bracket_style", "brace")
            if bstyle == "brace":
                p.setPen(QPen(QColor(c), lw * 2))
                p.drawLine(QRectF(m - 6, y, m - 6, bass_y + 4 * ss))
            elif bstyle == "bracket":
                p.setPen(QPen(QColor(c), lw * 1.5))
                p.drawLine(QRectF(m - 4, y, m - 4, y + 6))
                p.drawLine(QRectF(m - 4, bass_y, m - 4, bass_y + 4 * ss))
                self._hline(p, y, m - 8, m, c, lw * 1.5)
                self._hline(p, bass_y, m - 8, m, c, lw * 1.5)
            # Barlines
            if self._params.get("show_barlines", False):
                bi = self._params.get("barline_interval", 2.0) * IN_TO_PT
                bx = m + bi
                while bx < w - m:
                    self._vline(p, bx, y, bass_y + 4 * ss, c, lw * 0.5)
                    bx += bi

    # ── Dotted Lined ──
    def _draw_dotted_lined(self, p, w, h):
        ls = self._params["line_spacing"] * IN_TO_PT
        ds = self._params["dot_spacing"] * IN_TO_PT
        dr = self._params["dot_radius"]
        ml = self._params["margin_left"] * IN_TO_PT
        c = self._params["color"]
        dc = self._params.get("dot_color", "#999999")
        lw = self._params["line_width"]
        m = 54
        dot_style = self._params.get("dot_style", "filled")
        # Draw horizontal ruled lines
        y = m
        while y < h - m:
            self._hline(p, y, ml, w - m, c, lw * 0.5)
            # Draw dots along each line
            xi = ml
            while xi < w - m:
                p.setPen(Qt.NoPen)
                if dot_style == "filled":
                    p.setBrush(QBrush(QColor(dc)))
                    p.drawEllipse(QRectF(xi - dr, y - dr, 2 * dr, 2 * dr))
                elif dot_style == "ring":
                    p.setBrush(Qt.NoBrush); p.setPen(QPen(QColor(dc), 0.4))
                    p.drawEllipse(QRectF(xi - dr, y - dr, 2 * dr, 2 * dr))
                xi += ds
            y += ls
        # Margin line
        if self._params.get("show_margin_line", True):
            self._vline(p, ml, 0, h, c, lw)

    # ── Weekly Meal Planner ──
    def _draw_weekly_meal_planner(self, p, w, h):
        c = self._params["color"]; sc = self._params.get("secondary_color", "#16A34A")
        lw = self._params["line_width"]; m = 36
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        meals = ["Breakfast", "Lunch", "Dinner"]
        if self._params.get("show_snack_row", True):
            meals.append("Snacks")
        y = m
        # Title
        if self._params.get("show_week_header", True):
            p.setFont(QFont("Helvetica", 14, QFont.Bold)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(m, y, w - 2*m, 22), Qt.AlignLeft, "Weekly Meal Planner")
            y += 30
        # Day header row
        num_cols = len(days) + 1  # +1 for meal labels
        col_w = (w - 2*m) / num_cols
        hdr_h = 22
        p.setFont(QFont("Helvetica", 8, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, col_w - 4, hdr_h), Qt.AlignCenter, "")
        for di, day in enumerate(days):
            p.drawText(QRectF(m + (di + 1) * col_w, y, col_w - 4, hdr_h), Qt.AlignCenter, day)
        self._hline(p, y + hdr_h, m, w - m, c, lw); y += hdr_h
        # Vertical column lines
        for ci in range(num_cols + 1):
            x = m + ci * col_w
            self._vline(p, x, y, h - m, c, lw * 0.3)
        # Meal rows
        avail_h = h - m - y
        row_h = avail_h / len(meals)
        for mi, meal in enumerate(meals):
            ry = y + mi * row_h
            # Meal label
            p.setFont(QFont("Helvetica", 9, QFont.Bold)); p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m + 2, ry + row_h / 2 - 6, col_w - 4, 14), Qt.AlignCenter, meal)
            # Row separator
            self._hline(p, ry + row_h, m, w - m, c, lw * 0.5)
            # Sub-columns if calorie/notes enabled
            sub_y = ry + 8
            p.setFont(QFont("Helvetica", 7)); p.setPen(QPen(QColor(sc)))
            if self._params.get("show_calorie_col", True):
                for di in range(len(days)):
                    cx = m + (di + 1) * col_w
                    p.drawText(QRectF(cx + 2, sub_y, col_w - 4, 10), Qt.AlignLeft, "Cal:")
            if self._params.get("show_notes_col", True):
                for di in range(len(days)):
                    cx = m + (di + 1) * col_w
                    p.drawText(QRectF(cx + 2, sub_y + 12, col_w - 4, 10), Qt.AlignLeft, "Notes:")

    # ── Sleep Tracker ──
    def _draw_sleep_tracker(self, p, w, h):
        nd = int(self._params["num_days"])
        rh = self._params["row_height"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#6366F1")
        lw = self._params["line_width"]; m = 36
        y = m
        # Title
        p.setFont(QFont("Helvetica", 14, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2*m, 22), Qt.AlignLeft, "Sleep Tracker")
        y += 30
        # Build columns
        cols = ["Day"]
        if self._params.get("show_nap_col", True): cols.append("Nap")
        cols.extend(["Bedtime", "Wake", "Hours"])
        if self._params.get("show_quality_col", True): cols.append("Quality")
        if self._params.get("show_mood_col", True): cols.append("Mood")
        if self._params.get("show_notes_col", True): cols.append("Notes")
        num_cols = len(cols); col_w = (w - 2*m) / num_cols
        # Header
        hdr_h = 18
        row_h = self._params.get("row_height", 20)
        p.setFont(QFont("Helvetica", 8, QFont.Bold)); p.setPen(QPen(QColor(c)))
        for ci, cn in enumerate(cols):
            p.drawText(QRectF(m + ci * col_w + 2, y, col_w - 4, hdr_h), Qt.AlignCenter, cn)
        self._hline(p, y + hdr_h, m, w - m, c, lw); y += hdr_h
        # Data rows
        for d in range(1, nd + 1):
            if y + rh > h - m: break
            if d % 2 == 0:
                p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(sc))); p.setOpacity(0.04)
                p.drawRect(QRectF(m, y, w - 2*m, rh)); p.setOpacity(1.0); p.setPen(Qt.NoPen)
            p.setFont(QFont("Helvetica", 8)); p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m + 4, y + rh/2 - 5, col_w - 8, 12), Qt.AlignLeft, f"{d}")
            self._hline(p, y + rh, m, w - m, c, lw * 0.3)
            x = m + col_w
            for ci in range(1, num_cols):
                self._vline(p, x, y, y + rh, c, lw * 0.2); x += col_w
            y += rh

    # ── Mood Tracker ──
    def _draw_mood_tracker(self, p, w, h):
        nd = int(self._params["num_days"])
        gs = self._params["grid_size"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#F59E0B")
        lw = self._params["line_width"]; m = 50
        y = m
        # Title
        p.setFont(QFont("Helvetica", 14, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2*m, 22), Qt.AlignLeft, "Mood Tracker")
        y += 28
        # Month header
        if self._params.get("show_month_header", True):
            p.setFont(QFont("Helvetica", 10)); p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m, y, w - 2*m, 16), Qt.AlignLeft, "Month: _______________")
            y += 22; self._hline(p, y, m, w - m, c, lw * 0.5); y += 8
        # Mood labels
        mood_labels_opt = self._params.get("mood_labels", "Emoji")
        moods = ["Great", "Good", "Okay", "Bad", "Awful"] if mood_labels_opt == "Text" else ["1", "2", "3", "4", "5"]
        mood_colors = ["#22C55E", "#84CC16", "#F59E0B", "#F97316", "#EF4444"]
        # Grid layout: 7 columns (days of week) x rows
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        num_cols = 7
        col_w = (w - 2 * m) / num_cols
        row_h = gs * 2.5
        # Day name headers
        p.setFont(QFont("Helvetica", 8, QFont.Bold)); p.setPen(QPen(QColor(c)))
        for di, dn in enumerate(day_names):
            p.drawText(QRectF(m + di * col_w, y, col_w, 14), Qt.AlignCenter, dn)
        y += 16
        # Day cells
        day = 1
        while day <= nd and y + row_h < h - m:
            for di in range(num_cols):
                if day > nd: break
                cx = m + di * col_w + col_w / 2
                cy = y + row_h / 2
                # Day number
                if self._params.get("show_day_numbers", True):
                    p.setFont(QFont("Helvetica", 8)); p.setPen(QPen(QColor(sc)))
                    p.drawText(QRectF(m + di * col_w, y, col_w, 12), Qt.AlignCenter, str(day))
                # Cell border
                p.setPen(QPen(QColor(c), lw * 0.3)); p.setBrush(Qt.NoBrush)
                p.drawRect(QRectF(m + di * col_w + 2, y + 14, col_w - 4, row_h - 16))
                # Mood circles
                circle_r = min(col_w, row_h) / (len(moods) + 1) * 0.35
                mx_start = m + di * col_w + 6
                for mi, (mood, mc) in enumerate(zip(moods, mood_colors)):
                    mx = mx_start + mi * (col_w - 12) / max(len(moods) - 1, 1) if len(moods) > 1 else m + di * col_w + col_w / 2
                    p.setPen(QPen(QColor(mc), lw * 0.4)); p.setBrush(Qt.NoBrush)
                    my = cy + 4
                    p.drawEllipse(QRectF(mx - circle_r, my - circle_r, 2 * circle_r, 2 * circle_r))
                    p.setFont(QFont("Helvetica", 5)); p.setPen(QPen(QColor(mc)))
                    p.drawText(QRectF(mx - circle_r, my - 3, 2 * circle_r, 7), Qt.AlignCenter, mood)
                day += 1
            y += row_h

    # ── Lesson Plan ──
    def _draw_lesson_plan(self, p, w, h):
        nper = int(self._params["num_periods"])
        c = self._params["color"]; sc = self._params.get("secondary_color", "#2563EB")
        lw = self._params["line_width"]; m = 36
        y = m
        # Title and info fields
        p.setFont(QFont("Helvetica", 14, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2*m, 22), Qt.AlignLeft, "Lesson Plan")
        y += 26
        p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(sc)))
        p.drawText(QRectF(m, y, 50, 14), Qt.AlignLeft, "Date:")
        self._hline(p, y + 12, m + 40, m + 220, c, lw * 0.5)
        p.drawText(QRectF(m + 250, y, 50, 14), Qt.AlignLeft, "Subject:")
        self._hline(p, y + 12, m + 300, w - m, c, lw * 0.5)
        y += 24; self._hline(p, y, m, w - m, c, lw); y += 6
        # Sections per period
        sections = ["Topic / Objective"]
        if self._params.get("show_objectives", True): sections.append("Objectives")
        if self._params.get("show_materials", True): sections.append("Materials")
        sections.append("Activities / Notes")
        if self._params.get("show_assessment", True): sections.append("Assessment")
        if self._params.get("show_homework", True): sections.append("Homework")
        # Period rows
        avail_h = h - m - y - 10
        per_h = avail_h / nper
        for per in range(1, nper + 1):
            if y + per_h > h - m: break
            # Period header
            p.setFont(QFont("Helvetica", 9, QFont.Bold)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(m, y, 100, 16), Qt.AlignLeft, f"Period {per}")
            self._hline(p, y + 16, m, w - m, c, lw * 0.5)
            y += 18
            # Section labels
            sec_h = (per_h - 18) / len(sections)
            for si, sec_name in enumerate(sections):
                sy = y + si * sec_h
                p.setFont(QFont("Helvetica", 7)); p.setPen(QPen(QColor(sc)))
                p.drawText(QRectF(m + 4, sy + 2, 100, 12), Qt.AlignLeft, sec_name)
                self._hline(p, sy + sec_h, m, w - m, c, lw * 0.2)
            y += per_h - 18

    # ── Expense Tracker ──
    def _draw_expense_tracker(self, p, w, h):
        nr = int(self._params["num_rows"])
        rh = self._params["row_height"] * IN_TO_PT
        hdr_h = self._params.get("header_height", 0.5) * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#DC2626")
        lw = self._params["line_width"]; m = 36
        y = m
        # Title
        p.setFont(QFont("Helvetica", 14, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2*m, 22), Qt.AlignLeft, "Expense Tracker")
        y += 28
        # Date field
        p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(sc)))
        p.drawText(QRectF(m, y, 50, 14), Qt.AlignLeft, "Month:")
        self._hline(p, y + 12, m + 45, m + 250, c, lw * 0.5)
        y += 22
        # Column headers
        cols = ["Date", "Description"]
        if self._params.get("show_category_col", True): cols.append("Category")
        cols.append("Amount")
        if self._params.get("show_payment_col", True): cols.append("Payment")
        cols.append("Notes")
        num_cols = len(cols); col_w = (w - 2 * m) / num_cols
        p.setFont(QFont("Helvetica", 8, QFont.Bold)); p.setPen(QPen(QColor(c)))
        for ci, cn in enumerate(cols):
            p.drawText(QRectF(m + ci * col_w + 2, y, col_w - 4, hdr_h), Qt.AlignCenter, cn)
        self._hline(p, y + hdr_h, m, w - m, c, lw); y += hdr_h
        # Data rows
        for r in range(nr):
            if y + rh > h - m: break
            if r % 2 == 0:
                p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(sc))); p.setOpacity(0.04)
                p.drawRect(QRectF(m, y, w - 2*m, rh)); p.setOpacity(1.0); p.setPen(Qt.NoPen)
            self._hline(p, y + rh, m, w - m, c, lw * 0.3)
            x = m + col_w
            for ci in range(1, num_cols):
                self._vline(p, x, y, y + rh, c, lw * 0.2); x += col_w
            y += rh
        # Totals area
        if y + 30 < h - m:
            y += 4; self._hline(p, y, m, w - m, c, lw); y += 4
            p.setFont(QFont("Helvetica", 9, QFont.Bold)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(m, y, col_w * 3, 16), Qt.AlignRight, "Total:")
            self._hline(p, y + 16, m + col_w * 3, m + col_w * 4, c, lw * 0.5)
            if self._params.get("show_balance_col", True):
                p.drawText(QRectF(m + col_w * 4, y, col_w * 2, 16), Qt.AlignRight, "Balance:")
                self._hline(p, y + 16, m + col_w * 5, m + col_w * 6, c, lw * 0.5)

    # ── Baseball Scorecard ──
    def _draw_baseball_scorecard(self, p, w, h):
        nin = int(self._params["num_innings"])
        npt = int(self._params["players_per_team"])
        c = self._params["color"]; sc = self._params.get("secondary_color", "#2563EB")
        lw = self._params["line_width"]; m = 30
        y = m
        # Title
        p.setFont(QFont("Helvetica", 13, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2*m, 20), Qt.AlignLeft, "Baseball Scorecard")
        y += 24
        # Team info
        p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(sc)))
        p.drawText(QRectF(m, y, 40, 14), Qt.AlignLeft, "Team:")
        self._hline(p, y + 12, m + 40, m + 200, c, lw * 0.5)
        p.drawText(QRectF(w/2, y, 50, 14), Qt.AlignLeft, "Opp:")
        self._hline(p, y + 12, w/2 + 35, w - m, c, lw * 0.5)
        y += 22
        # Date/Weather
        p.drawText(QRectF(m, y, 40, 14), Qt.AlignLeft, "Date:")
        self._hline(p, y + 12, m + 40, m + 200, c, lw * 0.5)
        p.drawText(QRectF(w/2, y, 50, 14), Qt.AlignLeft, "Weather:")
        self._hline(p, y + 12, w/2 + 55, w - m, c, lw * 0.5)
        y += 22
        # Header row: Player # | Name | Innings 1-9 | R | H | RBI
        num_inning_cols = nin
        stat_cols = self._params.get("stat_columns", "R,H,RBI").split(",")
        total_cols = 2 + num_inning_cols + len(stat_cols)  # #, Name, innings, stats
        col_w = (w - 2*m) / total_cols
        hdr_h = 18
        row_h = self._params.get("row_height", 20)
        p.setFont(QFont("Helvetica", 7, QFont.Bold)); p.setPen(QPen(QColor(c)))
        headers = ["#", "Player"] + [str(i) for i in range(1, nin + 1)] + stat_cols
        for ci, hdr in enumerate(headers):
            p.drawText(QRectF(m + ci * col_w, y, col_w, hdr_h), Qt.AlignCenter, hdr)
        self._hline(p, y + hdr_h, m, w - m, c, lw); y += hdr_h
        # Player rows
        for pl in range(npt):
            if y + row_h > h - m: break
            # Player number
            p.setFont(QFont("Helvetica", 8)); p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m + 4, y + 3, col_w - 8, 14), Qt.AlignCenter, str(pl + 1))
            # Cell borders
            self._hline(p, y + row_h, m, w - m, c, lw * 0.3)
            x = m + col_w
            for ci in range(1, total_cols):
                self._vline(p, x, y, y + row_h, c, lw * 0.2); x += col_w
            # Sub-rows for subs
            if self._params.get("show_sub_rows", True):
                sub_y = y + row_h
                self._hline(p, sub_y + 12, m, w - m, c, lw * 0.15)
                x = m + col_w
                for ci in range(1, total_cols):
                    self._vline(p, x, sub_y, sub_y + 12, c, lw * 0.1); x += col_w
                row_h_total = row_h + 12
            else:
                row_h_total = row_h
            y += row_h_total
        # Totals row
        if self._params.get("show_totals_row", True) and y + 20 < h - m:
            self._hline(p, y, m, w - m, c, lw); y += 2
            p.setFont(QFont("Helvetica", 8, QFont.Bold)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(m + 4, y, col_w * 2, 16), Qt.AlignCenter, "TOTALS")
            y += 20

    # ── Atom Diagram ──
    def _draw_atom_diagram(self, p, w, h):
        gs = self._params["grid_size"] * IN_TO_PT
        nsh = int(self._params["num_shells"])
        c = self._params["color"]; sc = self._params.get("secondary_color", "#2563EB")
        lw = self._params["line_width"]
        ns = self._params.get("nucleus_size", 0.3) * IN_TO_PT
        # Grid of atom templates
        m = 50
        max_shell_r = gs / 2 - 10
        # Calculate how many atoms fit
        atoms_w = max(1, int((w - 2*m) / gs))
        atoms_h = max(1, int((h - 2*m) / gs))
        # Center the grid
        total_w = atoms_w * gs
        total_h = atoms_h * gs
        sx = (w - total_w) / 2
        sy = (h - total_h) / 2
        for row in range(atoms_h):
            for col in range(atoms_w):
                cx = sx + col * gs + gs / 2
                cy = sy + row * gs + gs / 2
                # Cell border
                p.setPen(QPen(QColor(c), lw * 0.3)); p.setBrush(Qt.NoBrush)
                p.drawRect(QRectF(sx + col * gs, sy + row * gs, gs, gs))
                # Electron shells
                shell_r = max_shell_r / nsh
                p.setPen(QPen(QColor(sc), lw * 0.5)); p.setBrush(Qt.NoBrush)
                for s in range(1, nsh + 1):
                    r = shell_r * s
                    p.drawEllipse(QRectF(cx - r, cy - r, 2*r, 2*r))
                # Nucleus
                if self._params.get("show_nucleus", True):
                    p.setPen(QPen(QColor(c), lw)); p.setBrush(QBrush(QColor(c)))
                    p.drawEllipse(QRectF(cx - ns/2, cy - ns/2, ns, ns))
                    # Plus sign on nucleus
                    p.setPen(QPen(QColor("#FFFFFF"), lw * 0.5))
                    p.drawLine(QRectF(cx - ns/4, cy, cx + ns/4, cy))
                    p.drawLine(QRectF(cx, cy - ns/4, cx, cy + ns/4))
                # Shell labels
                if self._params.get("show_shell_labels", True):
                    p.setFont(QFont("Helvetica", 6)); p.setPen(QPen(QColor(c)))
                    shell_names = ["K", "L", "M", "N", "O", "P", "Q"]
                    for s in range(min(nsh, len(shell_names))):
                        r = shell_r * (s + 1)
                        p.drawText(QRectF(cx + r - 10, cy - 10, 10, 10), Qt.AlignRight, shell_names[s])

    # ── Quadrille Paper ──
    def _draw_quadrille_paper(self, p, w, h):
        gs = self._params["grid_size"] * IN_TO_PT
        major = int(self._params["major_every"])
        c = self._params["color"]; sc = self._params.get("secondary_color", "#AAAAAA")
        lw = self._params["line_width"]; mw = self._params["major_width"]
        dot_mode = self._params.get("dot_mode", False)
        if dot_mode:
            # Draw dots at major intersections only
            p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(c)))
            x = gs * major
            while x < w:
                y = gs * major
                while y < h:
                    mdr = self._params.get("major_dot_radius", 1.0)
                    p.drawEllipse(QRectF(x - mdr/2, y - mdr/2, mdr, mdr))
                    y += gs * major
                x += gs * major
            # Light dots at minor intersections
            mdr2 = self._params.get("minor_dot_radius", 0.5)
            p.setBrush(QBrush(QColor(sc)))
            x = gs
            while x < w:
                y = gs
                while y < h:
                    is_major = (int(x/gs) % major == 0 and int(y/gs) % major == 0)
                    if not is_major:
                        p.drawEllipse(QRectF(x - mdr2/2, y - mdr2/2, mdr2, mdr2))
                    y += gs
                x += gs
        else:
            # Traditional quadrille: light grid, heavier every 5
            p.setPen(QPen(QColor(sc), lw))
            x = gs
            while x < w:
                self._vline(p, x, 0, h, sc, lw)
                x += gs
            y = gs
            while y < h:
                self._hline(p, y, 0, w, sc, lw)
                y += gs
            # Major grid
            x = gs * major
            while x < w:
                self._vline(p, x, 0, h, c, mw)
                x += gs * major
            y = gs * major
            while y < h:
                self._hline(p, y, 0, w, c, mw)
                y += gs * major

    # ── Spiral Grid ──
    def _draw_spiral_grid(self, p, w, h):
        ns = int(self._params["num_spirals"])
        turns = int(self._params["turns"])
        gs = self._params["grid_size"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#C4B5FD")
        lw = self._params["line_width"]
        show_rad = self._params.get("show_radials", True)
        nrad = int(self._params.get("num_radials", 12))
        cx, cy = w / 2, h / 2
        max_r = min(w, h) / 2 - 20
        # Concentric circles as grid
        p.setPen(QPen(QColor(sc), lw * 0.5)); p.setBrush(Qt.NoBrush)
        r = gs
        while r < max_r:
            p.drawEllipse(QRectF(cx - r, cy - r, 2 * r, 2 * r))
            r += gs
        # Radials
        if show_rad:
            p.setPen(QPen(QColor(sc), lw * 0.3))
            for i in range(nrad):
                a = 2 * math.pi * i / nrad
                ex = cx + max_r * math.cos(a)
                ey = cy + max_r * math.sin(a)
                p.drawLine(QRectF(cx, cy, ex, ey))
        # Archimedean spirals
        p.setPen(QPen(QColor(c), lw))
        for s in range(ns):
            offset = 2 * math.pi * s / ns
            pts = []
            steps = turns * 120
            for i in range(steps + 1):
                t = i / 120.0
                a = offset + t * 2 * math.pi
                r = t * gs * 0.8
                if r > max_r: break
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
            if len(pts) >= 2:
                for i in range(len(pts) - 1):
                    p.drawLine(QRectF(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1]))

    # ── Basketball Stat Sheet ──
    def _draw_basketball_stat_sheet(self, p, w, h):
        nplayers = int(self._params["num_players"])
        nq = int(self._params["num_quarters"])
        stats = self._params.get("stat_categories", "Points,Rebounds,Assists,Steals,Blocks").split(",")
        c = self._params["color"]; sc = self._params.get("secondary_color", "#EA580C")
        lw = self._params["line_width"]; m = 30
        y = m
        tfs = int(self._params.get("title_font_size", 16))
        p.setFont(QFont("Helvetica", tfs, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2 * m, 22), Qt.AlignLeft, "Basketball Stat Sheet")
        y += 28
        p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(sc)))
        p.drawText(QRectF(m, y, 200, 14), Qt.AlignLeft, "Date:")
        p.drawText(QRectF(m + 250, y, 200, 14), Qt.AlignLeft, "Opponent:")
        p.drawText(QRectF(m + 500, y, 200, 14), Qt.AlignLeft, "Location:")
        y += 22
        # Build columns: Player#, Name, Q1..Qn for each stat, Totals
        cols = ["#", "Player"]
        for q in range(1, nq + 1):
            for st in stats:
                cols.append(f"Q{q} {st.strip()[:3]}")
        cols.append("TOT")
        ncols = len(cols)
        # Header
        col_w = (w - 2 * m) / ncols
        p.setFont(QFont("Helvetica", 6, QFont.Bold)); p.setPen(QPen(QColor(c)))
        for ci, cn in enumerate(cols):
            p.drawText(QRectF(m + ci * col_w, y, col_w, 12), Qt.AlignCenter, cn)
        y += 14; p.setPen(QPen(QColor(c), lw)); p.drawLine(QRectF(m, y, w - m, y)); y += 2
        # Rows
        p.setFont(QFont("Helvetica", 7)); p.setPen(QPen(QColor(c)))
        for r in range(nplayers):
            rh = self._params.get("row_height", 16)
            if y + rh > h - m: break
            # Row line
            p.setPen(QPen(QColor(c), lw * 0.3)); p.drawLine(QRectF(m, y + rh, w - m, y + rh))
            # Vertical lines
            p.setPen(QPen(QColor(c), lw * 0.3))
            for ci in range(1, ncols):
                x = m + ci * col_w
                p.drawLine(QRectF(x, y, x, y + rh))
            # Player number hint
            p.setPen(QPen(QColor(sc), lw * 0.3))
            p.drawText(QRectF(m + 2, y + 2, col_w - 4, 12), Qt.AlignCenter, str(r + 1))
            y += rh
        # Totals row
        if self._params.get("show_totals", True) and y + 18 < h - m:
            p.setPen(QPen(QColor(c), lw)); p.drawLine(QRectF(m, y, w - m, y)); y += 2
            p.setFont(QFont("Helvetica", 7, QFont.Bold)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(m, y, col_w * 2, 14), Qt.AlignCenter, "TEAM TOTALS")

    # ── Chore Chart ──
    def _draw_chore_chart(self, p, w, h):
        nchores = int(self._params["num_chores"])
        dm = self._params.get("days_mode", "weekday")
        c = self._params["color"]; sc = self._params.get("secondary_color", "#16A34A")
        lw = self._params["line_width"]; m = 36
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] if dm == "weekday" else ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"]
        show_pts = self._params.get("show_points_col", True)
        show_pi = self._params.get("show_parent_initials", False)
        num_data_cols = len(days) + (1 if show_pts else 0) + (1 if show_pi else 0)
        clw = self._params.get("label_column_width", 120)
        cbs = self._params.get("checkbox_size", 10)
        mrh = self._params.get("min_row_height", 18)
        col_w = (w - 2 * m - clw) / num_data_cols
        y = m
        p.setFont(QFont("Helvetica", 16, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2 * m, 22), Qt.AlignLeft, "Weekly Chore Chart")
        y += 28
        p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(sc)))
        p.drawText(QRectF(m, y, 200, 14), Qt.AlignLeft, "Week of:")
        p.drawLine(QRectF(m + 55, y + 12, m + 200, y + 12))
        y += 24
        # Header row
        p.setFont(QFont("Helvetica", 8, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, clw, 16), Qt.AlignCenter, "Chore")
        ci = 0
        for d in days:
            p.drawText(QRectF(m + clw + ci * col_w, y, col_w, 16), Qt.AlignCenter, d)
            ci += 1
        if show_pts:
            p.drawText(QRectF(m + clw + ci * col_w, y, col_w, 16), Qt.AlignCenter, "Pts")
            ci += 1
        if show_pi:
            p.drawText(QRectF(m + clw + ci * col_w, y, col_w, 16), Qt.AlignCenter, "Initials")
            ci += 1
        y += 16; p.setPen(QPen(QColor(c), lw)); p.drawLine(QRectF(m, y, w - m, y)); y += 2
        # Chore rows
        p.setFont(QFont("Helvetica", 8)); p.setPen(QPen(QColor(sc), lw * 0.3))
        row_h = max(mrh, (h - y - m) / max(nchores, 1))
        for r in range(nchores):
            if y + row_h > h - m: break
            p.setPen(QPen(QColor(c), lw * 0.3)); p.drawLine(QRectF(m, y + row_h, w - m, y + row_h))
            # Vertical lines
            p.drawLine(QRectF(m + clw, y, m + clw, y + row_h))
            for ci2 in range(1, num_data_cols):
                x = m + clw + ci2 * col_w
                p.drawLine(QRectF(x, y, x, y + row_h))
            # Checkbox in each cell
            cx_base = m + clw + col_w / 2
            for ci2 in range(min(num_data_cols, len(days))):
                cx = cx_base + ci2 * col_w
                cy_cell = y + row_h / 2
                p.setPen(QPen(QColor(sc), lw * 0.5)); p.setBrush(Qt.NoBrush)
                p.drawRect(QRectF(cx - cbs/2, cy_cell - cbs/2, cbs, cbs))
            y += row_h

    # ── Water Intake Tracker ──
    def _draw_water_intake_tracker(self, p, w, h):
        nd = int(self._params["num_days"])
        tgt = int(self._params["glasses_target"])
        c = self._params["color"]; sc = self._params.get("secondary_color", "#0EA5E9")
        lw = self._params["line_width"]; m = 36
        show_notes = self._params.get("show_notes_col", True)
        y = m
        p.setFont(QFont("Helvetica", 16, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2 * m, 22), Qt.AlignLeft, "Water Intake Tracker")
        y += 24
        p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(sc)))
        p.drawText(QRectF(m, y, 300, 14), Qt.AlignLeft, f"Goal: {tgt} glasses/day ({self._params.get('glass_size_oz', 8)} oz each)")
        y += 20
        # Columns: Day, checkboxes for glasses, Total, Notes
        checkbox_area = tgt * 18
        notes_w = 120 if show_notes else 0
        total_w = 80
        day_w = 80
        avail = w - 2 * m - day_w - total_w - notes_w - 20
        cb_size = min(18, avail / max(tgt, 1))
        row_h = max(24, cb_size + 8)
        # Header
        p.setFont(QFont("Helvetica", 8, QFont.Bold)); p.setPen(QPen(QColor(c)))
        x = m
        p.drawText(QRectF(x, y, day_w, 14), Qt.AlignCenter, "Day"); x += day_w
        for g in range(1, tgt + 1):
            p.drawText(QRectF(x, y, cb_size, 14), Qt.AlignCenter, str(g))
            x += cb_size
        p.drawText(QRectF(x, y, total_w, 14), Qt.AlignCenter, "Total")
        x += total_w
        if show_notes:
            p.drawText(QRectF(x, y, notes_w, 14), Qt.AlignCenter, "Notes")
        y += 16; p.setPen(QPen(QColor(c), lw)); p.drawLine(QRectF(m, y, w - m, y)); y += 2
        # Day rows
        p.setFont(QFont("Helvetica", 8)); p.setPen(QPen(QColor(c), lw * 0.3))
        for r in range(nd):
            if y + row_h > h - m: break
            p.drawLine(QRectF(m, y + row_h, w - m, y + row_h))
            x = m
            p.drawText(QRectF(x, y + 2, day_w, row_h - 4), Qt.AlignCenter, f"Day {r+1}"); x += day_w
            for g in range(tgt):
                cx = x + cb_size / 2
                cy = y + row_h / 2
                p.setPen(QPen(QColor(sc), lw * 0.4)); p.setBrush(Qt.NoBrush)
                # Water drop shape: small circle
                p.drawEllipse(QRectF(cx - 5, cy - 5, 10, 10))
                x += cb_size
            # Vertical dividers
            p.setPen(QPen(QColor(c), lw * 0.3))
            x_line = m + day_w
            p.drawLine(QRectF(x_line, y, x_line, y + row_h))
            if show_notes:
                x_note = m + day_w + tgt * cb_size + total_w
                p.drawLine(QRectF(x_note, y, x_note, y + row_h))
            y += row_h
        # Total row
        if self._params.get("show_total_row", True) and y + 20 < h - m:
            p.setPen(QPen(QColor(c), lw)); p.drawLine(QRectF(m, y, w - m, y)); y += 3
            p.setFont(QFont("Helvetica", 8, QFont.Bold)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(m, y, day_w + tgt * cb_size, 14), Qt.AlignRight, "Weekly Total:")

    # ── Phone Call Log ──
    def _draw_phone_call_log(self, p, w, h):
        nr = int(self._params["num_rows"])
        rh = self._params["row_height"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#2563EB")
        lw = self._params["line_width"]; m = 36; y = m
        p.setFont(QFont("Helvetica", 16, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2 * m, 22), Qt.AlignLeft, "Phone Call Log")
        y += 26
        p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(sc)))
        p.drawText(QRectF(m, y, 120, 14), Qt.AlignLeft, "Month/Year:")
        p.drawLine(QRectF(m + 80, y + 12, m + 200, y + 12))
        y += 22
        cols = ["Date/Time", "Contact", "Phone #", "Type"]
        if self._params.get("show_duration_col", True): cols.append("Duration")
        if self._params.get("show_outcome_col", True): cols.append("Outcome")
        if self._params.get("show_followup_col", True): cols.append("Follow-Up")
        ncols = len(cols); col_w = (w - 2 * m) / ncols
        # Header
        p.setFont(QFont("Helvetica", 7, QFont.Bold)); p.setPen(QPen(QColor(c)))
        for ci, cn in enumerate(cols):
            p.drawText(QRectF(m + ci * col_w, y, col_w, 12), Qt.AlignCenter, cn)
        y += 14; p.setPen(QPen(QColor(c), lw)); p.drawLine(QRectF(m, y, w - m, y)); y += 2
        # Rows
        for r in range(nr):
            if y + rh > h - m: break
            p.setPen(QPen(QColor(c), lw * 0.3)); p.drawLine(QRectF(m, y + rh, w - m, y + rh))
            for ci in range(1, ncols):
                x = m + ci * col_w
                p.drawLine(QRectF(x, y, x, y + rh))
            y += rh

    # ── Blood Pressure Log ──
    def _draw_blood_pressure_log(self, p, w, h):
        nr = int(self._params["num_rows"])
        rh = self._params["row_height"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#DC2626")
        lw = self._params["line_width"]; m = 36; y = m
        p.setFont(QFont("Helvetica", 16, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2 * m, 22), Qt.AlignLeft, "Blood Pressure Log")
        y += 26
        if self._params.get("show_header_info", True):
            p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m, y, 200, 14), Qt.AlignLeft, "Name:")
            p.drawLine(QRectF(m + 40, y + 12, m + 200, y + 12))
            p.drawText(QRectF(m + 250, y, 200, 14), Qt.AlignLeft, "Doctor:")
            p.drawLine(QRectF(m + 290, y + 12, m + 440, y + 12))
            y += 22
        cols = ["Date"]
        if self._params.get("show_date_time", True): cols[0] = "Date/Time"
        cols += ["Systolic", "Diastolic"]
        if self._params.get("show_pulse_col", True): cols.append("Pulse")
        cols.append("Notes")
        ncols = len(cols); col_w = (w - 2 * m) / ncols
        # Header
        p.setFont(QFont("Helvetica", 7, QFont.Bold)); p.setPen(QPen(QColor(c)))
        for ci, cn in enumerate(cols):
            p.drawText(QRectF(m + ci * col_w, y, col_w, 12), Qt.AlignCenter, cn)
        y += 14; p.setPen(QPen(QColor(c), lw)); p.drawLine(QRectF(m, y, w - m, y)); y += 2
        # Rows
        for r in range(nr):
            if y + rh > h - m: break
            p.setPen(QPen(QColor(c), lw * 0.3)); p.drawLine(QRectF(m, y + rh, w - m, y + rh))
            for ci in range(1, ncols):
                x = m + ci * col_w
                p.drawLine(QRectF(x, y, x, y + rh))
            # Highlight BP zone background for first few rows
            if r < 3:
                p.setPen(Qt.NoPen)
                p.setBrush(QBrush(QColor(sc)))
                p.setOpacity(0.04)
                p.drawRect(QRectF(m, y, w - 2 * m, rh))
                p.setOpacity(1.0)
            y += rh
        # BP zones legend
        if y + 60 < h - m:
            y += 8
            p.setFont(QFont("Helvetica", 7)); p.setPen(QPen(QColor(c)))
            zones = [("Normal: <120/<80", "#16A34A"), ("Elevated: 120-129/<80", "#F59E0B"),
                     ("High S1: 130-139/80-89", "#EA580C"), ("High S2: >=140/>=90", "#DC2626")]
            for zi, (zt, zc) in enumerate(zones):
                p.setBrush(QBrush(QColor(zc)))
                p.setPen(Qt.NoPen)
                p.drawRect(QRectF(m + zi * 130, y, 8, 8))
                p.setPen(QPen(QColor(c))); p.setFont(QFont("Helvetica", 6))
                p.drawText(QRectF(m + zi * 130 + 12, y, 120, 10), Qt.AlignLeft, zt)

    # ── SWOT Analysis ──
    def _draw_swot_analysis(self, p, w, h):
        c = self._params["color"]; sc = self._params.get("secondary_color", "#2563EB")
        lw = self._params["line_width"]; m = 36
        hdr_h = self._params.get("header_height", 0.4) * IN_TO_PT
        nlines = int(self._params.get("lines_per_section", 8))
        y = m
        p.setFont(QFont("Helvetica", 16, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2 * m, 22), Qt.AlignLeft, "SWOT Analysis")
        y += 26
        p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(sc)))
        p.drawText(QRectF(m, y, 200, 14), Qt.AlignLeft, "Topic / Project:")
        p.drawLine(QRectF(m + 100, y + 12, w - m - 20, y + 12))
        y += 24
        # 2x2 quadrant
        qw = (w - 2 * m) / 2
        qh = (h - y - m) / 2
        labels = ["S — Strengths", "W — Weaknesses", "O — Opportunities", "T — Threats"]
        label_colors = [sc, "#DC2626", "#16A34A", "#F59E0B"]
        positions = [(m, y), (m + qw, y), (m, y + qh), (m + qw, y + qh)]
        line_sp = (qh - hdr_h - 10) / max(nlines, 1)
        for qi, ((qx, qy), label, lc) in enumerate(zip(positions, labels, label_colors)):
            # Box border
            p.setPen(QPen(QColor(c), lw)); p.setBrush(Qt.NoBrush)
            p.drawRect(QRectF(qx, qy, qw, qh))
            # Header
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor(lc)))
            p.setOpacity(0.1)
            p.drawRect(QRectF(qx, qy, qw, hdr_h))
            p.setOpacity(1.0)
            if self._params.get("show_headers", True):
                p.setFont(QFont("Helvetica", 10, QFont.Bold)); p.setPen(QPen(QColor(lc)))
                p.drawText(QRectF(qx + 8, qy + 4, qw - 16, hdr_h - 4), Qt.AlignVCenter | Qt.AlignLeft, label)
            # Lines
            if self._params.get("show_prompt_lines", True):
                p.setPen(QPen(QColor(c), lw * 0.3))
                ly = qy + hdr_h + line_sp
                for li in range(nlines):
                    if ly + line_sp > qy + qh - 4: break
                    p.drawLine(QRectF(qx + 8, ly, qx + qw - 8, ly))
                    ly += line_sp

    # ── Doodle Pad ──
    def _draw_doodle_pad(self, p, w, h):
        c = self._params["color"]; sc = self._params.get("secondary_color", "#E5E7EB")
        lw = self._params["line_width"]
        density_map = {"light": 0.3, "medium": 0.6, "heavy": 1.0}
        density = density_map.get(self._params.get("density", "medium"), 0.6)
        shapes = self._params.get("shape_types", "circles,squares,triangles").split(",")
        m = self._params.get("margin", 0.33) * IN_TO_PT
        min_sz = self._params.get("min_shape_size", 8)
        max_sz = self._params.get("max_shape_size", 38)
        if self._params.get("show_border_frame", True):
            p.setPen(QPen(QColor(c), lw)); p.setBrush(Qt.NoBrush)
            p.drawRect(QRectF(m, m, w - 2*m, h - 2*m))
        # Simple deterministic pseudo-random
        seed = 42
        def rng():
            nonlocal seed
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            return seed / 0x7FFFFFFF
        p.setPen(QPen(QColor(c), lw * 0.5)); p.setBrush(Qt.NoBrush)
        num_shapes = int(density * 60)
        inner_w = w - 2*m - 20; inner_h = h - 2*m - 20
        for i in range(num_shapes):
            sx = m + 10 + rng() * inner_w
            sy = m + 10 + rng() * inner_h
            size = min_sz + rng() * (max_sz - min_sz)
            shape = shapes[i % len(shapes)].strip()
            if shape == "circles":
                p.drawEllipse(QRectF(sx - size/2, sy - size/2, size, size))
            elif shape == "squares":
                p.drawRect(QRectF(sx - size/2, sy - size/2, size, size))
            elif shape == "triangles":
                pts = QPolygonF([QPointF(sx, sy - size/2), QPointF(sx - size/2, sy + size/2), QPointF(sx + size/2, sy + size/2)])
                p.drawPolygon(pts)

    # ── Comic Panel Layout ──
    def _draw_comic_panel_layout(self, p, w, h):
        style = self._params.get("layout_style", "classic")
        nrows = int(self._params.get("num_rows", 3))
        gw = self._params.get("gutter_width", 0.15) * IN_TO_PT
        pbw = self._params.get("panel_border_width", 1.5)
        c = self._params["color"]; sc = self._params.get("secondary_color", "#94A3B8")
        lw = self._params["line_width"]; m = 24
        show_labels = self._params.get("show_gutter_labels", False)
        # Classic: 2-2-1 pattern per row group; Grid: equal panels; Varied: mixed
        if style == "classic":
            row_configs = []
            for r in range(nrows):
                if r % 3 == 2 and r > 0:
                    row_configs.append([(m, 1.0)])  # Full-width panel
                else:
                    row_configs.append([(m, 0.5), (m, 0.5)])
        elif style == "grid":
            row_configs = [[(m, 0.5), (m, 0.5)] for _ in range(nrows)]
        else:  # varied
            row_configs = []
            patterns = [[(m, 0.6), (m, 0.4)], [(m, 0.33), (m, 0.34), (m, 0.33)],
                        [(m, 1.0)], [(m, 0.4), (m, 0.6)]]
            for r in range(nrows):
                row_configs.append(patterns[r % len(patterns)])
        avail_w = w - 2 * m
        avail_h = h - 2 * m
        row_h = avail_h / max(len(row_configs), 1)
        y = m
        p.setPen(QPen(QColor(c), lw)); p.setBrush(Qt.NoBrush)
        for ri, row in enumerate(row_configs):
            x = m
            npanels = len(row)
            for pi, (mx, ratio) in enumerate(row):
                pw = (avail_w - gw * (npanels - 1)) * ratio
                ph = row_h - gw
                p.setPen(QPen(QColor(c), lw)); p.drawRect(QRectF(x, y, pw, ph))
                # Panel number
                if show_labels:
                    p.setFont(QFont("Helvetica", 7)); p.setPen(QPen(QColor(sc)))
                    p.drawText(QRectF(x + 3, y + 2, 20, 10), Qt.AlignLeft, f"P{ri*npanels+pi+1}")
                x += pw + gw
            y += row_h

    # ── Gardening Planner ──
    def _draw_gardening_planner(self, p, w, h):
        nbeds = int(self._params["num_beds"])
        gs = self._params["grid_size"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#16A34A")
        lw = self._params["line_width"]; m = 30
        y = m
        p.setFont(QFont("Helvetica", 16, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2 * m, 22), Qt.AlignLeft, "Gardening Planner")
        y += 24
        p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(sc)))
        p.drawText(QRectF(m, y, 200, 14), Qt.AlignLeft, "Season:")
        p.drawLine(QRectF(m + 50, y + 12, m + 180, y + 12))
        p.drawText(QRectF(m + 220, y, 200, 14), Qt.AlignLeft, "Year:")
        p.drawLine(QRectF(m + 260, y + 12, m + 380, y + 12))
        y += 22
        # Garden beds as grid boxes
        beds_per_row = min(nbeds, 2)
        num_bed_rows = math.ceil(nbeds / beds_per_row)
        bed_w = (w - 2 * m - 20) / beds_per_row
        bed_h = min(bed_w * 0.75, (h - y - m - (100 if self._params.get("show_plant_list", True) else 0) - (80 if self._params.get("show_notes_section", True) else 0)) / max(num_bed_rows, 1))
        bed_h = max(bed_h, 80)
        for bi in range(nbeds):
            br = bi // beds_per_row; bc = bi % beds_per_row
            bx = m + bc * (bed_w + 20)
            by = y + br * (bed_h + 16)
            if by + bed_h > h - m - 60: break
            # Bed border
            p.setPen(QPen(QColor(c), lw)); p.setBrush(Qt.NoBrush)
            p.drawRect(QRectF(bx, by, bed_w, bed_h))
            # Label
            p.setFont(QFont("Helvetica", 8, QFont.Bold)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(bx + 4, by + 2, bed_w - 8, 12), Qt.AlignLeft, f"Bed {bi+1}")
            # Grid inside bed
            p.setPen(QPen(QColor(sc), lw * 0.3))
            gx = bx + gs
            while gx < bx + bed_w:
                p.drawLine(QRectF(gx, by, gx, by + bed_h))
                gx += gs
            gy = by + gs
            while gy < by + bed_h:
                p.drawLine(QRectF(bx, gy, bx + bed_w, gy))
                gy += gs
            # Sun indicator
            if self._params.get("show_sun_indicator", True):
                p.setPen(QPen(QColor("#F59E0B"), lw))
                sun_x = bx + bed_w - 16; sun_y = by + 16
                p.setBrush(QBrush(QColor("#F59E0B")))
                p.drawEllipse(QRectF(sun_x - 4, sun_y - 4, 8, 8))
                p.setBrush(Qt.NoBrush)
                for a in range(0, 360, 45):
                    rad = math.radians(a)
                    p.drawLine(QRectF(sun_x + 6 * math.cos(rad), sun_y + 6 * math.sin(rad),
                                      sun_x + 10 * math.cos(rad), sun_y + 10 * math.sin(rad)))
        y_next = y + num_bed_rows * (bed_h + 16) + 10
        # Plant list
        if self._params.get("show_plant_list", True) and y_next + 100 < h - m:
            p.setFont(QFont("Helvetica", 10, QFont.Bold)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(m, y_next, w - 2 * m, 16), Qt.AlignLeft, "Plant List")
            y_next += 16
            plrows = int(self._params.get("plant_list_rows", 10))
            plrh = 14
            cols_pl = ["Plant", "Variety", "Qty", "Plant Date", "Harvest"]
            col_w_pl = (w - 2 * m) / len(cols_pl)
            p.setFont(QFont("Helvetica", 7, QFont.Bold)); p.setPen(QPen(QColor(c)))
            for ci, cn in enumerate(cols_pl):
                p.drawText(QRectF(m + ci * col_w_pl, y_next, col_w_pl, 12), Qt.AlignCenter, cn)
            y_next += 14; p.setPen(QPen(QColor(c), lw * 0.5)); p.drawLine(QRectF(m, y_next, w - m, y_next)); y_next += 2
            for r in range(plrows):
                if y_next + plrh > h - m: break
                p.setPen(QPen(QColor(c), lw * 0.2)); p.drawLine(QRectF(m, y_next + plrh, w - m, y_next + plrh))
                for ci in range(1, len(cols_pl)):
                    x = m + ci * col_w_pl
                    p.drawLine(QRectF(x, y_next, x, y_next + plrh))
                y_next += plrh

    # ── Timeline ──
    def _draw_timeline(self, p, w, h):
        orient = self._params.get("orientation", "horizontal")
        ne = int(self._params["num_events"])
        ms = self._params["marker_size"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#93C5FD")
        lw = self._params["line_width"]; m = 36
        show_dates = self._params.get("show_date_fields", True)
        show_years = self._params.get("show_year_markers", False)
        arrow = self._params.get("arrow_style", True)
        p.setFont(QFont("Helvetica", 14, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, m, w - 2 * m, 20), Qt.AlignCenter, "Timeline")
        if orient == "horizontal":
            y_line = h / 2
            x_start = m + 40; x_end = w - m - 20
            p.setPen(QPen(QColor(c), lw))
            p.drawLine(QRectF(x_start, y_line, x_end, y_line))
            if arrow:
                p.drawLine(QRectF(x_end - 10, y_line - 6, x_end, y_line))
                p.drawLine(QRectF(x_end - 10, y_line + 6, x_end, y_line))
            spacing = (x_end - x_start) / max(ne, 1)
            for i in range(ne):
                ex = x_start + i * spacing + spacing / 2
                p.setPen(QPen(QColor(c), lw)); p.setBrush(QBrush(QColor(c)))
                p.drawEllipse(QRectF(ex - ms/2, y_line - ms/2, ms, ms))
                p.setPen(QPen(QColor(c), lw * 0.5))
                if i % 2 == 0:
                    p.drawLine(QRectF(ex, y_line + ms/2, ex, y_line + ms/2 + 20))
                    if show_dates:
                        p.setFont(QFont("Helvetica", 7)); p.drawText(QRectF(ex - 25, y_line + ms/2 + 22, 50, 12), Qt.AlignCenter, "Date")
                else:
                    p.drawLine(QRectF(ex, y_line - ms/2 - 20, ex, y_line - ms/2))
                    if show_dates:
                        p.setFont(QFont("Helvetica", 7)); p.drawText(QRectF(ex - 25, y_line - ms/2 - 32, 50, 12), Qt.AlignCenter, "Date")
                if show_years and i % 5 == 0:
                    p.setFont(QFont("Helvetica", 6)); p.setPen(QPen(QColor(sc)))
                    p.drawText(QRectF(ex - 15, y_line + ms/2 + 34, 30, 10), Qt.AlignCenter, str(2020 + i * 5))
        else:
            x_line = m + 60
            y_start = m + 40; y_end = h - m - 20
            p.setPen(QPen(QColor(c), lw))
            p.drawLine(QRectF(x_line, y_start, x_line, y_end))
            if arrow:
                p.drawLine(QRectF(x_line - 6, y_end - 10, x_line, y_end))
                p.drawLine(QRectF(x_line + 6, y_end - 10, x_line, y_end))
            spacing = (y_end - y_start) / max(ne, 1)
            for i in range(ne):
                ey = y_start + i * spacing + spacing / 2
                p.setPen(QPen(QColor(c), lw)); p.setBrush(QBrush(QColor(c)))
                p.drawEllipse(QRectF(x_line - ms/2, ey - ms/2, ms, ms))
                p.setPen(QPen(QColor(c), lw * 0.5))
                p.drawLine(QRectF(x_line + ms/2, ey, x_line + ms/2 + 20, ey))
                if show_dates:
                    p.setFont(QFont("Helvetica", 7)); p.drawText(QRectF(x_line + ms/2 + 22, ey - 6, 60, 12), Qt.AlignLeft, "Date")

    # ── Insect Observation Log ──
    def _draw_insect_observation_log(self, p, w, h):
        nr = int(self._params["num_rows"])
        rh = self._params["row_height"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#16A34A")
        lw = self._params["line_width"]; m = 30; y = m
        p.setFont(QFont("Helvetica", 14, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2 * m, 20), Qt.AlignLeft, "Insect Observation Log"); y += 24
        p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(sc)))
        p.drawText(QRectF(m, y, 200, 14), Qt.AlignLeft, "Location:")
        p.drawLine(QRectF(m + 60, y + 12, m + 200, y + 12))
        p.drawText(QRectF(m + 250, y, 200, 14), Qt.AlignLeft, "Date:")
        p.drawLine(QRectF(m + 285, y + 12, m + 420, y + 12)); y += 20
        cols = ["#", "Species", "Date/Time"]
        if self._params.get("show_habitat_col", True): cols.append("Habitat")
        if self._params.get("show_behavior_col", True): cols.append("Behavior")
        if self._params.get("show_weather_col", True): cols.append("Weather")
        ncols = len(cols); col_w = (w - 2 * m - (rh if self._params.get("show_drawing_area", True) else 0)) / ncols
        draw_w = rh if self._params.get("show_drawing_area", True) else 0
        p.setFont(QFont("Helvetica", 7, QFont.Bold)); p.setPen(QPen(QColor(c)))
        for ci, cn in enumerate(cols):
            p.drawText(QRectF(m + ci * col_w, y, col_w, 12), Qt.AlignCenter, cn)
        if draw_w: p.drawText(QRectF(w - m - draw_w, y, draw_w, 12), Qt.AlignCenter, "Drawing")
        y += 14; p.setPen(QPen(QColor(c), lw)); p.drawLine(QRectF(m, y, w - m, y)); y += 2
        for r in range(nr):
            if y + rh > h - m: break
            p.setPen(QPen(QColor(c), lw * 0.3)); p.drawLine(QRectF(m, y + rh, w - m, y + rh))
            for ci in range(1, ncols):
                x = m + ci * col_w; p.drawLine(QRectF(x, y, x, y + rh))
            if draw_w: p.drawLine(QRectF(w - m - draw_w, y, w - m - draw_w, y + rh))
            y += rh

    # ── Medication Log ──
    def _draw_medication_log(self, p, w, h):
        nr = int(self._params["num_rows"])
        rh = self._params["row_height"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#7C3AED")
        lw = self._params["line_width"]; m = 30; y = m
        p.setFont(QFont("Helvetica", 14, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2 * m, 20), Qt.AlignLeft, "Medication Log"); y += 24
        if self._params.get("show_header_info", True):
            p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m, y, 200, 14), Qt.AlignLeft, "Patient:")
            p.drawLine(QRectF(m + 50, y + 12, m + 200, y + 12))
            p.drawText(QRectF(m + 250, y, 200, 14), Qt.AlignLeft, "Doctor:")
            p.drawLine(QRectF(m + 295, y + 12, m + 440, y + 12)); y += 20
        cols = ["Date", "Medication"]
        if self._params.get("show_time_col", True): cols.append("Time")
        if self._params.get("show_dosage_col", True): cols.append("Dosage")
        cols.append("Taken")
        if self._params.get("show_notes_col", True): cols.append("Notes")
        ncols = len(cols); col_w = (w - 2 * m) / ncols
        p.setFont(QFont("Helvetica", 7, QFont.Bold)); p.setPen(QPen(QColor(c)))
        for ci, cn in enumerate(cols):
            p.drawText(QRectF(m + ci * col_w, y, col_w, 12), Qt.AlignCenter, cn)
        y += 14; p.setPen(QPen(QColor(c), lw)); p.drawLine(QRectF(m, y, w - m, y)); y += 2
        for r in range(nr):
            if y + rh > h - m: break
            p.setPen(QPen(QColor(c), lw * 0.3)); p.drawLine(QRectF(m, y + rh, w - m, y + rh))
            for ci in range(1, ncols):
                x = m + ci * col_w; p.drawLine(QRectF(x, y, x, y + rh))
            # Checkbox in "Taken" column
            taken_idx = cols.index("Taken")
            cx = m + taken_idx * col_w + col_w / 2
            cy = y + rh / 2
            p.setPen(QPen(QColor(sc), lw * 0.5)); p.setBrush(Qt.NoBrush)
            p.drawRect(QRectF(cx - 4, cy - 4, 8, 8))
            y += rh

    # ── Number Bonds ──
    def _draw_number_bonds(self, p, w, h):
        np = int(self._params["num_problems"])
        c = self._params["color"]; sc = self._params.get("secondary_color", "#F59E0B")
        lw = self._params["line_width"]; m = 40
        layout = self._params.get("problem_layout", "2x5")
        cols_l, rows_l = (5, 2) if layout == "2x5" else (4, 3) if layout == "3x4" else (5, 2)
        p.setFont(QFont("Helvetica", 14, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, m - 10, w - 2 * m, 20), Qt.AlignCenter, "Number Bonds")
        y_start = m + 26
        cell_w = (w - 2 * m) / cols_l
        cell_h = (h - y_start - m) / max(rows_l, 1)
        r = min(cell_w, cell_h) * 0.25
        for idx in range(min(np, cols_l * rows_l)):
            row = idx // cols_l; col = idx % cols_l
            cx = m + col * cell_w + cell_w / 2
            cy = y_start + row * cell_h + cell_h / 2
            # Top circle (part)
            p.setPen(QPen(QColor(c), lw)); p.setBrush(Qt.NoBrush)
            p.drawEllipse(QRectF(cx - r, cy - r * 2.5, r * 2, r * 2))
            # Bottom-left circle (part)
            p.drawEllipse(QRectF(cx - r * 2.5, cy + r * 0.5, r * 2, r * 2))
            # Bottom-right circle (whole)
            p.drawEllipse(QRectF(cx + r * 0.5, cy + r * 0.5, r * 2, r * 2))
            # Lines connecting them
            p.drawLine(QRectF(cx, cy - r * 0.5, cx - r, cy + r * 0.5))
            p.drawLine(QRectF(cx, cy - r * 0.5, cx + r, cy + r * 0.5))
            if self._params.get("show_addition", True):
                p.setFont(QFont("Helvetica", 8)); p.setPen(QPen(QColor(sc)))
                p.drawText(QRectF(cx + r * 2.5, cy + r, cell_w - r * 3, 12), Qt.AlignLeft, "+  =")

    # ── Stargazing Log ──
    def _draw_stargazing_log(self, p, w, h):
        nr = int(self._params["num_rows"])
        rh = self._params["row_height"] * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#1E3A5F")
        lw = self._params["line_width"]; m = 30; y = m
        p.setFont(QFont("Helvetica", 14, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2 * m, 20), Qt.AlignLeft, "Stargazing Log"); y += 24
        p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(sc)))
        p.drawText(QRectF(m, y, 200, 14), Qt.AlignLeft, "Location:")
        p.drawLine(QRectF(m + 60, y + 12, m + 200, y + 12))
        p.drawText(QRectF(m + 250, y, 200, 14), Qt.AlignLeft, "Date:")
        p.drawLine(QRectF(m + 285, y + 12, m + 420, y + 12)); y += 20
        cols = ["#", "Object", "Date/Time"]
        if self._params.get("show_constellation_col", True): cols.append("Constellation")
        if self._params.get("show_magnitude_col", True): cols.append("Mag")
        if self._params.get("show_weather_col", True): cols.append("Conditions")
        ncols = len(cols); draw_w = rh if self._params.get("show_drawing_area", True) else 0
        col_w = (w - 2 * m - draw_w) / ncols
        p.setFont(QFont("Helvetica", 7, QFont.Bold)); p.setPen(QPen(QColor(c)))
        for ci, cn in enumerate(cols):
            p.drawText(QRectF(m + ci * col_w, y, col_w, 12), Qt.AlignCenter, cn)
        if draw_w: p.drawText(QRectF(w - m - draw_w, y, draw_w, 12), Qt.AlignCenter, "Sketch")
        y += 14; p.setPen(QPen(QColor(c), lw)); p.drawLine(QRectF(m, y, w - m, y)); y += 2
        for r in range(nr):
            if y + rh > h - m: break
            p.setPen(QPen(QColor(c), lw * 0.3)); p.drawLine(QRectF(m, y + rh, w - m, y + rh))
            for ci in range(1, ncols):
                x = m + ci * col_w; p.drawLine(QRectF(x, y, x, y + rh))
            if draw_w: p.drawLine(QRectF(w - m - draw_w, y, w - m - draw_w, y + rh))
            y += rh

    # ── Writing Sprint Tracker ──
    def _draw_writing_sprint_tracker(self, p, w, h):
        ns = int(self._params["num_sprints"])
        tw = int(self._params.get("target_words", 1667))
        c = self._params["color"]; sc = self._params.get("secondary_color", "#DC2626")
        lw = self._params["line_width"]; m = 36; y = m
        p.setFont(QFont("Helvetica", 14, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2 * m, 20), Qt.AlignLeft, "Writing Sprint Tracker"); y += 24
        if self._params.get("show_project_name", True):
            p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m, y, 200, 14), Qt.AlignLeft, "Project:")
            p.drawLine(QRectF(m + 55, y + 12, w - m - 20, y + 12)); y += 20
        p.setFont(QFont("Helvetica", 8)); p.setPen(QPen(QColor(sc)))
        p.drawText(QRectF(m, y, 300, 14), Qt.AlignLeft, f"Daily Target: {tw} words"); y += 20
        cols = ["#", "Sprint Start", "Sprint End", "Words"]
        if self._params.get("show_cumulative", True): cols.append("Cumulative")
        if self._params.get("show_daily_total", True): cols.append("Notes")
        ncols = len(cols); col_w = (w - 2 * m) / ncols
        p.setFont(QFont("Helvetica", 7, QFont.Bold)); p.setPen(QPen(QColor(c)))
        for ci, cn in enumerate(cols):
            p.drawText(QRectF(m + ci * col_w, y, col_w, 12), Qt.AlignCenter, cn)
        y += 14; p.setPen(QPen(QColor(c), lw)); p.drawLine(QRectF(m, y, w - m, y)); y += 2
        row_h = 16
        for r in range(ns):
            if y + row_h > h - m: break
            p.setPen(QPen(QColor(c), lw * 0.3)); p.drawLine(QRectF(m, y + row_h, w - m, y + row_h))
            for ci in range(1, ncols):
                x = m + ci * col_w; p.drawLine(QRectF(x, y, x, y + row_h))
            p.setFont(QFont("Helvetica", 7)); p.setPen(QPen(QColor(sc), lw * 0.3))
            p.drawText(QRectF(m + 2, y + 2, col_w - 4, 12), Qt.AlignCenter, str(r + 1))
            y += row_h
        if self._params.get("show_daily_total", True) and y + 22 < h - m:
            p.setPen(QPen(QColor(c), lw)); p.drawLine(QRectF(m, y, w - m, y)); y += 3
            p.setFont(QFont("Helvetica", 8, QFont.Bold)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(m, y, col_w * 3, 14), Qt.AlignRight, "Daily Total:")

    # ── Attendance Register ──
    def _draw_attendance_register(self, p, w, h):
        nst = int(self._params["num_students"])
        ndays = int(self._params["num_days"])
        c = self._params["color"]; sc = self._params.get("secondary_color", "#16A34A")
        lw = self._params["line_width"]; m = 24; y = m
        p.setFont(QFont("Helvetica", 12, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2 * m, 18), Qt.AlignLeft, "Attendance Register"); y += 22
        p.setFont(QFont("Helvetica", 8)); p.setPen(QPen(QColor(sc)))
        p.drawText(QRectF(m, y, 200, 14), Qt.AlignLeft, "Class:")
        p.drawLine(QRectF(m + 40, y + 12, m + 180, y + 12))
        p.drawText(QRectF(m + 220, y, 200, 14), Qt.AlignLeft, "Month:")
        p.drawLine(QRectF(m + 260, y + 12, m + 400, y + 12)); y += 20
        cols = []
        if self._params.get("show_student_id", True): cols.append("ID")
        cols.append("Student Name")
        for d in range(1, ndays + 1):
            cols.append(str(d))
        if self._params.get("show_totals_col", True): cols.append("Total")
        ncols = len(cols)
        id_w = 40 if self._params.get("show_student_id", True) else 0
        name_w = 120; day_w = (w - 2 * m - id_w - name_w - (50 if self._params.get("show_totals_col", True) else 0)) / max(ndays, 1)
        total_w = 50 if self._params.get("show_totals_col", True) else 0
        col_positions = [m]
        if id_w: col_positions.append(col_positions[-1] + id_w)
        col_positions.append(col_positions[-1] + name_w)
        for d in range(ndays):
            col_positions.append(col_positions[-1] + day_w)
        if total_w: col_positions.append(col_positions[-1] + total_w)
        # Header
        p.setFont(QFont("Helvetica", 6, QFont.Bold)); p.setPen(QPen(QColor(c)))
        for ci, cn in enumerate(cols):
            cx = col_positions[ci]; cw = col_positions[ci + 1] - cx if ci + 1 < len(col_positions) else day_w
            p.drawText(QRectF(cx, y, cw, 12), Qt.AlignCenter, cn)
        y += 14; p.setPen(QPen(QColor(c), lw)); p.drawLine(QRectF(m, y, col_positions[-1], y)); y += 2
        row_h = max(14, (h - y - m) / max(nst, 1))
        for r in range(nst):
            if y + row_h > h - m: break
            p.setPen(QPen(QColor(c), lw * 0.3)); p.drawLine(QRectF(m, y + row_h, col_positions[-1], y + row_h))
            for ci in range(1, len(col_positions)):
                x = col_positions[ci]; p.drawLine(QRectF(x, y, x, y + row_h))
            if r % 2 == 1:
                p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(sc)))
                p.setOpacity(0.04); p.drawRect(QRectF(m, y, col_positions[-1] - m, row_h)); p.setOpacity(1.0)
            y += row_h
        # Legend
        if self._params.get("show_absence_codes", True) and y + 20 < h - m:
            y += 4; p.setFont(QFont("Helvetica", 6)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(m, y, 200, 10), Qt.AlignLeft, "P=Present  A=Absent  T=Tardy  E=Excused")

    # ── Chess Score Sheet ──
    def _draw_chess_score_sheet(self, p, w, h):
        nr = int(self._params["num_rows"])
        mw_col = self._params.get("move_number_width", 0.5) * IN_TO_PT
        c = self._params["color"]; sc = self._params.get("secondary_color", "#78716C")
        lw = self._params["line_width"]; m = self._params.get("margin", 0.5) * IN_TO_PT; y = m
        row_h = self._params.get("row_height", 14)
        lfs = int(self._params.get("label_font_size", 7))
        if self._params.get("show_player_names", True):
            p.setFont(QFont("Helvetica", 12, QFont.Bold)); p.setPen(QPen(QColor(c)))
            p.drawText(QRectF(m, y, w / 2 - m, 16), Qt.AlignLeft, "White:")
            p.drawLine(QRectF(m + 45, y + 14, w / 2 - m, y + 14))
            p.drawText(QRectF(w / 2, y, w / 2 - m, 16), Qt.AlignLeft, "Black:")
            p.drawLine(QRectF(w / 2 + 45, y + 14, w - m, y + 14)); y += 24
        if self._params.get("show_date_location", True):
            p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(sc)))
            p.drawText(QRectF(m, y, 120, 14), Qt.AlignLeft, "Date:")
            p.drawLine(QRectF(m + 35, y + 12, m + 150, y + 12))
            p.drawText(QRectF(m + 180, y, 120, 14), Qt.AlignLeft, "Location:")
            p.drawLine(QRectF(m + 245, y + 12, m + 380, y + 12)); y += 20
        # Two columns: White moves | Black moves
        half_w = (w - 2 * m - mw_col) / 2
        p.setFont(QFont("Helvetica", 8, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m + mw_col, y, half_w / 2, 14), Qt.AlignCenter, "White")
        p.drawText(QRectF(m + mw_col + half_w, y, half_w / 2, 14), Qt.AlignCenter, "Black")
        p.drawText(QRectF(m, y, mw_col, 14), Qt.AlignCenter, "#")
        y += 14; p.setPen(QPen(QColor(c), lw)); p.drawLine(QRectF(m, y, w - m, y))
        p.drawLine(QRectF(m + mw_col, y - 14, m + mw_col, y + nr * row_h)); y += 2
        p.drawLine(QRectF(m + mw_col + half_w, y - 16, m + mw_col + half_w, y + nr * row_h))
        for r in range(nr):
            if y + row_h > h - m: break
            p.setPen(QPen(QColor(c), lw * 0.3)); p.drawLine(QRectF(m, y + row_h, w - m, y + row_h))
            p.setFont(QFont("Helvetica", lfs)); p.setPen(QPen(QColor(sc), lw * 0.3))
            p.drawText(QRectF(m + 2, y + 1, mw_col - 4, row_h - 2), Qt.AlignCenter, str(r + 1))
            y += row_h

    # ── Wish List ──
    def _draw_wish_list(self, p, w, h):
        nr = int(self._params["num_rows"])
        c = self._params["color"]; sc = self._params.get("secondary_color", "#EC4899")
        lw = self._params["line_width"]; m = 36; y = m
        p.setFont(QFont("Helvetica", 14, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2 * m, 20), Qt.AlignLeft, "Wish List"); y += 24
        p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(sc)))
        p.drawText(QRectF(m, y, 200, 14), Qt.AlignLeft, "For:")
        p.drawLine(QRectF(m + 30, y + 12, m + 200, y + 12))
        p.drawText(QRectF(m + 250, y, 200, 14), Qt.AlignLeft, "Occasion:")
        p.drawLine(QRectF(m + 310, y + 12, m + 480, y + 12)); y += 22
        cols = ["#", "Item"]
        if self._params.get("show_priority_col", True): cols.append("Priority")
        if self._params.get("show_price_col", True): cols.append("Price")
        if self._params.get("show_store_col", True): cols.append("Store/Link")
        if self._params.get("show_status_col", True): cols.append("Status")
        if self._params.get("show_notes_col", True): cols.append("Notes")
        ncols = len(cols); col_w = (w - 2 * m) / ncols
        p.setFont(QFont("Helvetica", 7, QFont.Bold)); p.setPen(QPen(QColor(c)))
        for ci, cn in enumerate(cols):
            p.drawText(QRectF(m + ci * col_w, y, col_w, 12), Qt.AlignCenter, cn)
        y += 14; p.setPen(QPen(QColor(c), lw)); p.drawLine(QRectF(m, y, w - m, y)); y += 2
        for r in range(nr):
            if y + 16 > h - m: break
            p.setPen(QPen(QColor(c), lw * 0.3)); p.drawLine(QRectF(m, y + 16, w - m, y + 16))
            for ci in range(1, ncols):
                x = m + ci * col_w; p.drawLine(QRectF(x, y, x, y + 16))
            # Heart icon in first col
            if r < 3:
                p.setFont(QFont("Helvetica", 10)); p.setPen(QPen(QColor(sc)))
            else:
                p.setFont(QFont("Helvetica", 7)); p.setPen(QPen(QColor(c), lw * 0.3))
            p.drawText(QRectF(m + 2, y + 1, col_w - 4, 14), Qt.AlignCenter, str(r + 1))
            y += 16

    # ── Gratitude Journal ──
    def _draw_gratitude_journal(self, p, w, h):
        ne = int(self._params["num_entries"])
        npr = int(self._params.get("prompts_per_entry", 3))
        c = self._params["color"]; sc = self._params.get("secondary_color", "#F59E0B")
        lw = self._params["line_width"]; m = 36; y = m
        p.setFont(QFont("Helvetica", 14, QFont.Bold)); p.setPen(QPen(QColor(c)))
        p.drawText(QRectF(m, y, w - 2 * m, 20), Qt.AlignLeft, "Gratitude Journal"); y += 24
        p.setFont(QFont("Helvetica", 9)); p.setPen(QPen(QColor(sc)))
        p.drawText(QRectF(m, y, 200, 14), Qt.AlignLeft, "Week of:")
        p.drawLine(QRectF(m + 55, y + 12, m + 200, y + 12)); y += 22
        entry_h = (h - y - m) / max(ne, 1)
        prompts = ["I am grateful for...", "Today I appreciated...", "A positive moment was..."]
        for ei in range(ne):
            if y + entry_h > h - m - 10: break
            # Day header
            p.setPen(QPen(QColor(sc), lw)); p.setBrush(Qt.NoBrush)
            p.drawLine(QRectF(m, y + 16, w - m, y + 16))
            if self._params.get("show_date_field", True):
                p.setFont(QFont("Helvetica", 9, QFont.Bold)); p.setPen(QPen(QColor(c)))
                p.drawText(QRectF(m, y + 2, 150, 14), Qt.AlignLeft, f"Day {ei + 1}:")
                p.setPen(QPen(QColor(c), lw * 0.3))
                p.drawLine(QRectF(m + 50, y + 14, m + 180, y + 14))
            if self._params.get("show_mood_check", True):
                p.setFont(QFont("Helvetica", 7)); p.setPen(QPen(QColor(sc)))
                p.drawText(QRectF(w - m - 160, y + 2, 160, 14), Qt.AlignRight, "Mood:  [ ] [ ] [ ] [ ] [ ]")
            py = y + 20
            for pi in range(min(npr, len(prompts))):
                if py + 16 > y + entry_h: break
                p.setFont(QFont("Helvetica", 7)); p.setPen(QPen(QColor(sc), lw * 0.5))
                p.drawText(QRectF(m + 8, py, w - 2 * m - 16, 12), Qt.AlignLeft, prompts[pi % len(prompts)])
                py += 14
                # Writing lines
                for wl in range(2):
                    if py + 12 > y + entry_h: break
                    p.setPen(QPen(QColor(c), lw * 0.2)); p.drawLine(QRectF(m + 8, py, w - m - 8, py))
                    py += 12
            if self._params.get("show_rating_col", True) and py + 14 < y + entry_h:
                p.setFont(QFont("Helvetica", 7)); p.setPen(QPen(QColor(sc)))
                p.drawText(QRectF(m + 8, py, 200, 12), Qt.AlignLeft, "Gratitude level:  1   2   3   4   5")
            y += entry_h

    def _draw_blank(self, p, w, h):
        pass


# ─────────────────────────────────────────────────────────────
# PDF Generator
# ─────────────────────────────────────────────────────────────
class PaperPDFGenerator:
    def __init__(self, paper_type, page_size_pt, orientation, params, pages=1,
                 bg_color="#FFFFFF", show_page_numbers=False, double_sided=False):
        self.paper_type = paper_type
        pw, ph = page_size_pt
        if orientation == "Landscape": pw, ph = ph, pw
        self.page_w = pw; self.page_h = ph
        self.params = params; self.pages = pages
        self.bg_color = bg_color
        self.show_page_numbers = show_page_numbers
        self.double_sided = double_sided

    def generate(self, output_path, progress_cb=None):
        pdf = FPDF(orientation="P", unit="pt", format=(self.page_w, self.page_h))
        pdf.set_auto_page_break(False); pdf.set_margins(0, 0, 0)
        for pg in range(1, self.pages + 1):
            pdf.add_page()
            r, g, b = hex_to_rgb(self.bg_color)
            pdf.set_fill_color(r, g, b)
            pdf.rect(0, 0, self.page_w, self.page_h, style="F")
            if self.double_sided and pg % 2 == 0:
                saved = dict(self.params)
                if "margin_left" in self.params:
                    self.params["margin_left"] = self.page_w / IN_TO_PT - self.params["margin_left"]
            fn = getattr(self, f"_draw_{self.paper_type.lower().replace(' ', '_')}", None)
            if fn: fn(pdf, self.page_w, self.page_h, pg)
            if self.double_sided and pg % 2 == 0: self.params = saved
            if self.show_page_numbers:
                pdf.set_font("Helvetica", "", 9); pdf.set_text_color(153, 153, 153)
                pdf.text(self.page_w / 2 - 5, self.page_h - 24, str(pg))
            if progress_cb: progress_cb(pg)
        pdf.output(output_path)

    def _set_c(self, pdf, color, lw):
        pdf.set_draw_color(*hex_to_rgb(color)); pdf.set_line_width(lw)

    # ── Graph Paper ──
    def _draw_graph_paper(self, pdf, w, h, pg=1):
        gs = self.params["grid_size"] * IN_TO_PT
        major = int(self.params["major_every"])
        c = self.params["color"]; sc = self.params.get("secondary_color", darken_color(c))
        lw = self.params["line_width"]; mw = self.params["major_width"]
        ls = self.params.get("line_style", "solid")
        dash = None
        if ls == "dashed": dash = (2, 2)
        elif ls == "dotted": dash = (0.3, 1.2)
        elif ls == "dashdot": dash = (3, 1.5, 0.5, 1.5)
        self._set_c(pdf, sc, lw)
        if dash: pdf.set_dash_pattern(*dash)
        x = gs
        while x < w: pdf.line(x, 0, x, h); x += gs
        y = gs
        while y < h: pdf.line(0, y, w, y); y += gs
        if dash: pdf.set_dash_pattern()
        self._set_c(pdf, c, mw)
        x = gs * major
        while x < w: pdf.line(x, 0, x, h); x += gs * major
        y = gs * major
        while y < h: pdf.line(0, y, w, y); y += gs * major
        if self.params.get("show_axis"):
            aw = self.params.get("axis_width", 1.5)
            self._set_c(pdf, c, aw)
            pdf.line(w/2, 0, w/2, h); pdf.line(0, h/2, w, h/2)
        if self.params.get("show_labels"):
            fs = int(self.params.get("label_font_size", 7))
            pdf.set_font("Helvetica", "", fs); pdf.set_text_color(*hex_to_rgb(c))
            x = gs * major; idx = major
            while x < w:
                pdf.text(x - 4, h/2 + 4, str(int(idx))); x += gs * major; idx += major
            y = gs * major; idx = major
            while y < h:
                pdf.text(w/2 + 4, y + 2, str(int(idx))); y += gs * major; idx += major

    # ── Ruled ──
    def _draw_college_ruled(self, pdf, w, h, pg=1): self._draw_ruled(pdf, w, h, pg)
    def _draw_wide_ruled(self, pdf, w, h, pg=1): self._draw_ruled(pdf, w, h, pg)
    def _draw_lined_paper(self, pdf, w, h, pg=1): self._draw_ruled(pdf, w, h, pg)

    def _draw_ruled(self, pdf, w, h, pg=1):
        ls = self.params["line_spacing"] * IN_TO_PT
        ml = self.params["margin_left"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#FF0000")
        lw = self.params["line_width"]; line_st = self.params.get("line_style", "solid")
        op = self.params.get("line_opacity", 1.0)
        oc = apply_opacity(c, op) if op < 1.0 else c
        top_m = self.params.get("top_margin", 1.0) * IN_TO_PT if self.params.get("show_top_margin") else 72
        dash = None
        if line_st == "dashed": dash = (2, 2)
        elif line_st == "dotted": dash = (0.3, 1.2)
        elif line_st == "dashdot": dash = (3, 1.5, 0.5, 1.5)
        rm = self.params.get("right_margin", 1.0) * IN_TO_PT
        self._set_c(pdf, oc, lw)
        if dash: pdf.set_dash_pattern(*dash)
        y = top_m
        while y < h - 72:
            pdf.line(ml, y, w - rm, y)
            if self.params.get("double_line"): pdf.line(ml, y + lw * 2, w - rm, y + lw * 2)
            y += ls
        if dash: pdf.set_dash_pattern()
        self._set_c(pdf, sc, lw); pdf.line(ml, 0, ml, h)
        if self.params.get("show_top_margin"):
            self._set_c(pdf, sc, lw * 0.5); pdf.line(0, top_m, w, top_m)

    # ── Dot Grid ──
    def _draw_dot_grid(self, pdf, w, h, pg=1):
        sp = self.params["dot_spacing"] * IN_TO_PT
        r = self.params["dot_radius"]
        dot_style = self.params.get("dot_style", "filled")
        major_every = int(self.params.get("major_dots_every", 5))
        major_r = self.params.get("major_dot_radius", r * 1.8)
        op = self.params.get("dot_opacity", 1.0)
        color = apply_opacity(self.params["color"], op) if op < 1.0 else self.params["color"]
        rgb = hex_to_rgb(color)
        pdf.set_fill_color(*rgb); pdf.set_draw_color(*rgb)
        off_x = self.params.get("offset_x", 0.0) * IN_TO_PT
        off_y = self.params.get("offset_y", 0.0) * IN_TO_PT
        xi = off_x; col_idx = 0
        while xi < w:
            yi = off_y; row_idx = 0
            while yi < h:
                is_major = (row_idx % major_every == 0 and col_idx % major_every == 0)
                cr = major_r if is_major else r
                if dot_style == "filled":
                    pdf.ellipse(xi - cr, yi - cr, 2*cr, 2*cr, style="F")
                elif dot_style == "ring":
                    pdf.set_line_width(0.4); pdf.ellipse(xi - cr, yi - cr, 2*cr, 2*cr, style="D")
                elif dot_style == "cross":
                    pdf.set_line_width(0.4)
                    pdf.line(xi - cr, yi, xi + cr, yi); pdf.line(xi, yi - cr, xi, yi + cr)
                yi += sp; row_idx += 1
            xi += sp; col_idx += 1

    # ── Isometric ──
    def _draw_isometric(self, pdf, w, h, pg=1):
        gs = self.params["grid_size"] * IN_TO_PT
        c = self.params["color"]; lw = self.params["line_width"]
        mg = self.params.get("margin", 0.0) * IN_TO_PT
        dy = gs * math.sin(math.radians(60)); dx = gs * math.cos(math.radians(60))
        self._set_c(pdf, c, lw)
        y = mg
        while y < h: pdf.line(0, y, w, y); y += gs
        for sx_i in range(0, int(w + h) + 1, max(int(gs), 1)):
            sx, sy = float(sx_i), 0.0
            while sy <= h and sx >= -w:
                if 0 <= sx <= w:
                    ex, ey = sx - dx, sy + dy
                    if ey > h: ratio = (h - sy) / dy if dy else 0; ex, ey = sx - dx * ratio, h
                    pdf.line(max(sx, 0), sy, max(ex, 0), ey)
                sx -= dx; sy += dy
        for sx_i in range(0, int(w + h) + 1, max(int(gs), 1)):
            sx, sy = float(sx_i), 0.0
            while sy <= h and sx <= w + h:
                if 0 <= sx <= w:
                    ex, ey = sx + dx, sy + dy
                    if ey > h: ratio = (h - sy) / dy if dy else 0; ex, ey = sx + dx * ratio, h
                    pdf.line(sx, sy, min(ex, w), ey)
                sx += dx; sy += dy
        if self.params.get("show_axis"):
            aw = self.params.get("axis_width", 1.5)
            self._set_c(pdf, c, aw)
            pdf.line(w/2, 0, w/2, h)

    # ── Cornell Notes ──
    def _draw_cornell_notes(self, pdf, w, h, pg=1):
        ls = self.params["line_spacing"] * IN_TO_PT
        ratio = self.params.get("column_split_ratio", 0.3)
        cw = (w - 144) * ratio
        sh = self.params["summary_height"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#94A3B8")
        lw = self.params["line_width"]; m = 72; bottom = h - sh - 36
        nls = self.params.get("notes_line_style", "dashed")
        self._set_c(pdf, sc, lw * 0.6)
        if nls == "dashed": pdf.set_dash_pattern(2, 2)
        y = m
        while y < bottom: pdf.line(m, y, w - m, y); y += ls
        pdf.set_dash_pattern()
        self._set_c(pdf, c, lw * 2)
        pdf.line(m + cw, m, m + cw, bottom); pdf.line(m, bottom, w - m, bottom)
        if self.params.get("show_labels", True):
            pdf.set_font("Helvetica", "", 10); pdf.set_text_color(136, 136, 136)
            pdf.text(m + 2, m + 8, "Cue Column"); pdf.text(m + cw + 2, m + 8, "Notes")
            pdf.text(m + 2, bottom - 10, "Summary")
        if self.params.get("show_date_field", True):
            pdf.set_font("Helvetica", "", 7); pdf.set_text_color(170, 170, 170)
            pdf.text(w - 180, m + 8, "Date: ________")

    # ── Engineering Paper ──
    def _draw_engineering_paper(self, pdf, w, h, pg=1):
        gs = self.params["grid_size"] * IN_TO_PT
        major = int(self.params["major_every"])
        c = self.params["color"]; sc = self.params.get("secondary_color", lighten_color(c))
        lw = self.params["line_width"]; mlw = self.params["major_width"]; m = 36
        if self.params.get("border"):
            self._set_c(pdf, c, 1.5); pdf.rect(m, m, w-2*m, h-2*m)
        self._set_c(pdf, sc, lw)
        x = m
        while x <= w - m: pdf.line(x, m, x, h - m); x += gs
        y = m
        while y <= h - m: pdf.line(m, y, w - m, y); y += gs
        self._set_c(pdf, c, mlw)
        x = m + gs * major
        while x < w - m: pdf.line(x, m, x, h - m); x += gs * major
        y = m + gs * major
        while y < h - m: pdf.line(m, y, w - m, y); y += gs * major
        if self.params.get("zone_labels"):
            pdf.set_font("Helvetica", "", 6); pdf.set_text_color(*hex_to_rgb(c))
            col_labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            xi = 0
            while xi < 26:
                cx = m + gs * major * xi + gs * major / 2
                if cx > w - m: break
                pdf.text(cx - 4, m + 10, col_labels[xi]); pdf.text(cx - 4, h - m - 4, col_labels[xi])
                xi += 1
        if self.params.get("show_title_block"):
            tbw = self.params.get("title_block_width", 2.5) * IN_TO_PT
            tbh = self.params.get("title_block_height", 1.0) * IN_TO_PT
            self._set_c(pdf, c, 1.5); pdf.rect(w - m - tbw, h - m - tbh, tbw, tbh)
            pdf.line(w - m - tbw, h - m - tbh/2, w - m, h - m - tbh/2)

    # ── Hexagonal Grid ──
    def _draw_hexagonal_grid(self, pdf, w, h, pg=1):
        size = self.params["hex_size"] * IN_TO_PT
        c = self.params["color"]; orient = self.params.get("orientation", "flat_top")
        fill = self.params.get("fill_hexagons", False)
        fill_c = self.params.get("secondary_color", "#E8D5F5")
        rgb = hex_to_rgb(c); pdf.set_draw_color(*rgb); pdf.set_line_width(self.params["line_width"])
        if orient == "pointy_top":
            hex_h = 2 * size; vert = hex_h * 0.75; horiz = size * math.sqrt(3)
        else:
            hex_h = size * math.sqrt(3); vert = hex_h * 0.75; horiz = 2 * size
        row = 0; y = 0
        while y < h + hex_h:
            offset = (horiz / 2) if row % 2 else 0; x = offset
            while x < w + horiz:
                pts = []
                for i in range(6):
                    angle = math.radians(60 * i - 30) if orient == "flat_top" else math.radians(60 * i)
                    pts.append((x + size * math.cos(angle), y + size * math.sin(angle)))
                if fill:
                    pdf.set_fill_color(*hex_to_rgb(fill_c)); pdf.polygon(pts, style="DF")
                else:
                    pdf.polygon(pts, style="D")
                x += horiz
            y += vert; row += 1

    # ── Music Staff ──
    def _draw_music_staff(self, pdf, w, h, pg=1):
        ss = self.params["staff_spacing"] * IN_TO_PT
        gs = self.params["group_spacing"] * IN_TO_PT
        ns = int(self.params["num_staves"])
        show_bar = self.params.get("show_barlines", False)
        bar_int = self.params.get("barline_interval", 2.0) * IN_TO_PT
        show_clef = self.params.get("show_clef", False)
        show_ts = self.params.get("show_time_signature", False)
        lfont = int(self.params.get("staff_label_font", 8))
        self._set_c(pdf, self.params["color"], self.params["line_width"])
        group_h = 4 * ss; total = ns * (group_h + gs) - gs
        start_y = (h - total) / 2
        for i in range(ns):
            base = start_y + i * (group_h + gs)
            for j in range(5): pdf.line(54, base + j * ss, w - 54, base + j * ss)
            if show_clef:
                pdf.set_font("Helvetica", "B", lfont + 8); pdf.set_text_color(*hex_to_rgb(self.params["color"]))
                pdf.text(58, base + group_h / 2 + 3, "K")
            if show_ts:
                pdf.set_font("Helvetica", "B", lfont + 4); pdf.set_text_color(*hex_to_rgb(self.params["color"]))
                tx = 78 if show_clef else 62
                pdf.text(tx, base + group_h / 4 + 2, "4")
                pdf.text(tx, base + 3 * group_h / 4 + 2, "4")
            if show_bar and bar_int > 0:
                bx = 54 + bar_int
                while bx < w - 54: pdf.line(bx, base, bx, base + 4 * ss); bx += bar_int

    # ── Calligraphy Guide ──
    def _draw_calligraphy_guide(self, pdf, w, h, pg=1):
        sp = self.params["guide_spacing"] * IN_TO_PT
        desc = self.params["descender"] * IN_TO_PT
        asc = self.params.get("ascender", 0.2) * IN_TO_PT
        angle = self.params["slant_angle"]; show_slant = self.params.get("show_slant", True)
        c = self.params["color"]; sc = self.params.get("secondary_color", lighten_color(c, 0.5))
        lw = self.params["line_width"]; mx = 72
        show_xh = self.params.get("show_x_height", True)
        y = 72
        while y < h - 72 - desc:
            self._set_c(pdf, c, lw * 1.5); pdf.line(mx, y, w - mx, y)
            if show_xh:
                self._set_c(pdf, sc, lw * 0.7); pdf.line(mx, y - asc, w - mx, y - asc)
            self._set_c(pdf, sc, lw); pdf.line(mx, y - sp, w - mx, y - sp)
            pdf.line(mx, y + desc, w - mx, y + desc)
            if show_slant:
                slant_c = hex_to_rgb(lighten_color(c, 0.6))
                pdf.set_draw_color(*slant_c); pdf.set_line_width(lw * 0.4)
                rad = math.radians(angle); tan_a = math.tan(rad)
                step = sp / tan_a if tan_a != 0 else sp
                x = mx
                while x < w - mx: pdf.line(x, y - sp, x + step, y); x += max(step, 1)
            y += sp + desc

    # ── To-Do List ──
    def _draw_to_do_list(self, pdf, w, h, pg=1):
        ls = self.params["line_spacing"] * IN_TO_PT
        ml = self.params["margin_left"] * IN_TO_PT
        cbs = self.params["checkbox_size"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#2563EB")
        lw = self.params["line_width"]; m = 72
        show_date = self.params.get("show_date_column", False)
        show_pri = self.params.get("show_priority", False)
        date_w = self.params.get("date_col_width", 0.8) * IN_TO_PT if show_date else 0
        pri_w = 24 if show_pri else 0
        x_start = ml + cbs + 8 + date_w + pri_w
        y = m + ls; num = 1
        while y < h - m:
            self._set_c(pdf, c, lw); pdf.line(x_start, y, w - m, y)
            self._set_c(pdf, sc, lw * 0.8)
            pdf.set_draw_color(*hex_to_rgb(sc)); pdf.set_line_width(lw * 0.8)
            pdf.rect(ml + 2, y - ls * 0.65, cbs, cbs)
            if show_pri:
                pdf.set_font("Helvetica", "", 7); pdf.set_text_color(*hex_to_rgb("#AAAAAA"))
                pdf.text(ml + cbs + 8 + date_w + 2, y - ls * 0.45, "A")
            if self.params.get("show_numbers"):
                pdf.set_font("Helvetica", "", 7); pdf.set_text_color(*hex_to_rgb("#BBBBBB"))
                pdf.text(ml + cbs + 12, y - ls * 0.45, str(num))
            y += ls; num += 1

    # ── Kanban Board ──
    def _draw_kanban_board(self, pdf, w, h, pg=1):
        nc = int(self.params["num_columns"])
        gap = self.params["column_spacing"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#94A3B8")
        lw = self.params["line_width"]; m = 36; header_h = 36
        card_h = self.params.get("card_height", 0.7) * IN_TO_PT
        col_w = (w - 2*m - (nc-1)*gap) / nc
        labels = ["To Do", "In Progress", "Done", "Review", "Backlog"]
        x = m
        for i in range(nc):
            self._set_c(pdf, c, lw); pdf.set_fill_color(248, 250, 252)
            pdf.rect(x, m, col_w, h - 2*m, style="DF")
            pdf.set_fill_color(*hex_to_rgb(sc)); pdf.rect(x, m, col_w, header_h, style="F")
            pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(255, 255, 255)
            label = labels[i] if i < len(labels) else f"Col {i+1}"
            pdf.text(x + 6, m + 22, label)
            card_y = m + header_h + 16
            max_cards = int(self.params.get("cards_per_col", 99))
            for _ in range(max_cards):
                if card_y + card_h > h - m - 10: break
                pdf.set_draw_color(*hex_to_rgb(lighten_color(sc, 0.7))); pdf.set_line_width(lw * 0.3)
                pdf.set_fill_color(255, 255, 255)
                pdf.rect(x + 6, card_y, col_w - 12, card_h, style="DF")
                card_y += card_h + 20
            x += col_w + gap

    # ── Penmanship ──
    def _draw_penmanship(self, pdf, w, h, pg=1):
        ls = self.params["line_spacing"] * IN_TO_PT
        mid = self.params["midline_offset"] * IN_TO_PT
        desc_d = self.params["descender_depth"] * IN_TO_PT
        asc_h = self.params.get("ascender_height", 0.0) * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#AAAAAA")
        lw = self.params["line_width"]; m = 72
        show_asc = self.params.get("show_ascender", True)
        color_mode = self.params.get("line_color_mode", "single")
        if mid == 0: mid = ls * 0.4
        if desc_d == 0: desc_d = ls * 0.3
        if asc_h == 0 and show_asc: asc_h = ls * 0.3
        y = m + ls
        while y < h - m:
            self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y)
            mc = sc if color_mode == "dual" else c
            pdf.set_draw_color(*hex_to_rgb(mc)); pdf.set_line_width(lw * 0.7)
            dash_len = 6; gap_len = 3; x = m
            while x < w - m:
                x_end = min(x + dash_len, w - m); pdf.line(x, y - mid, x_end, y - mid); x = x_end + gap_len
            x = m
            while x < w - m:
                pdf.ellipse(x, y + desc_d - 0.5, 1, 1, style="F"); x += 4
            if show_asc and asc_h > 0:
                x = m
                while x < w - m:
                    x_end = min(x + dash_len, w - m)
                    pdf.line(x, y - mid - asc_h, x_end, y - mid - asc_h); x = x_end + gap_len
            y += ls + desc_d

    # ── Cross Stitch ──
    def _draw_cross_stitch(self, pdf, w, h, pg=1):
        gs = self.params["grid_size"] * IN_TO_PT
        major = int(self.params.get("major_every", 10))
        c = self.params["color"]; mc = self.params.get("major_color", darken_color(c))
        lw = self.params["line_width"]; mw = self.params.get("major_width", lw * 2.5)
        bm = self.params.get("border_width", 0.5) * IN_TO_PT; m = bm
        self._set_c(pdf, c, lw)
        x = m
        while x <= w - m: pdf.line(x, m, x, h - m); x += gs
        y = m
        while y <= h - m: pdf.line(m, y, w - m, y); y += gs
        self._set_c(pdf, mc, mw)
        x = m
        while x <= w - m: pdf.line(x, m, x, h - m); x += gs * major
        y = m
        while y <= h - m: pdf.line(m, y, w - m, y); y += gs * major
        if self.params.get("center_marks"):
            cx, cy = w / 2, h / 2
            self._set_c(pdf, c, lw * 2)
            pdf.line(cx, cy - 8, cx, cy + 8); pdf.line(cx - 8, cy, cx + 8, cy)

    # ── Piano Keys ──
    def _draw_piano_keys(self, pdf, w, h, pg=1):
        no = int(self.params["num_octaves"])
        kh = self.params["key_height"] * IN_TO_PT
        show_labels = self.params.get("show_labels", True)
        show_oct = self.params.get("show_octave_numbers", True)
        start_oct = int(self.params.get("start_octave", 3))
        c = self.params["color"]; sc = self.params.get("secondary_color", "#FFFFFF")
        lw = self.params["line_width"]; m = 54
        key_style = self.params.get("key_style", "classic")
        white_notes = ["C", "D", "E", "F", "G", "A", "B"]
        black_pattern = [True, True, False, True, True, True, False]
        total_white = 7 * no; key_w = (w - 2*m) / total_white; x = m
        for octave in range(no):
            for i, note in enumerate(white_notes):
                self._set_c(pdf, c, lw); pdf.set_fill_color(*hex_to_rgb(sc))
                pdf.rect(x, m, key_w, kh, style="DF")
                if black_pattern[i]:
                    pdf.set_fill_color(*hex_to_rgb(c))
                    pdf.rect(x + key_w * 0.65, m, key_w * 0.7, kh * 0.6, style="F")
                if show_labels and key_style != "blank":
                    pdf.set_font("Helvetica", "", 7); pdf.set_text_color(*hex_to_rgb(c))
                    pdf.text(x + 2, m + kh - 6, f"{note}{start_oct + octave}")
                x += key_w
            if show_oct and key_style != "blank":
                pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(*hex_to_rgb("#999999"))
                pdf.text(x - 7*key_w/2 - 10, m + kh + 14, str(start_oct + octave))

    # ── Storyboard ──
    def _draw_storyboard(self, pdf, w, h, pg=1):
        pw_c = int(self.params["num_panels_w"]); ph_c = int(self.params["num_panels_h"])
        gap = self.params["panel_gap"] * IN_TO_PT; label_h = self.params["label_height"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#94A3B8")
        lw = self.params["line_width"]; m = 36
        show_ro3 = self.params.get("show_rule_of_thirds", False)
        show_ar = self.params.get("show_aspect_ratio", True)
        avail_w = w - 2*m; avail_h = h - 2*m
        panel_w = (avail_w - (pw_c-1)*gap) / pw_c; panel_h = (avail_h - (ph_c-1)*gap) / ph_c
        x = m; y = m; panel_num = 1
        for row in range(ph_c):
            for col in range(pw_c):
                draw_h = panel_h - label_h
                br = self.params.get("panel_border_radius", 0.0) * IN_TO_PT
                self._set_c(pdf, c, lw); pdf.set_fill_color(250, 250, 250)
                if br > 0:
                    # Rounded rect: fill then stroke with corner clips
                    pdf.rect(x, y, panel_w, draw_h, style="F")
                    self._set_c(pdf, c, lw)
                    r = min(br, panel_w / 2, draw_h / 2)
                    # Draw straight edge segments (skip corners by r)
                    pdf.line(x + r, y, x + panel_w - r, y)  # top
                    pdf.line(x + panel_w, y + r, x + panel_w, y + draw_h - r)  # right
                    pdf.line(x + r, y + draw_h, x + panel_w - r, y + draw_h)  # bottom
                    pdf.line(x, y + r, x, y + draw_h - r)  # left
                else:
                    pdf.rect(x, y, panel_w, draw_h, style="DF")
                pdf.set_fill_color(*hex_to_rgb(sc))
                pdf.rect(x, y + draw_h, panel_w, label_h, style="F")
                pdf.set_font("Helvetica", "", 7); pdf.set_text_color(255, 255, 255)
                lbl = f"Panel {panel_num}" + (f"  ({pw_c}:{ph_c})" if show_ar else "")
                pdf.text(x + 4, y + draw_h + label_h / 2 + 2, lbl)
                panel_num += 1; x += panel_w + gap
            x = m; y += panel_h + gap

    # ── Grid Diary ──
    def _draw_grid_diary(self, pdf, w, h, pg=1):
        cols = int(self.params["grid_cols"]); rows = int(self.params["grid_rows"])
        header_h = self.params["header_height"] * IN_TO_PT
        tcw = self.params["time_col_width"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#94A3B8")
        lw = self.params["line_width"]; m = 36
        alt_shade = self.params.get("alternate_row_shading", True)
        avail_w = w - 2*m - tcw; avail_h = h - 2*m - header_h
        cell_w = avail_w / cols; cell_h = avail_h / rows
        pdf.set_fill_color(*hex_to_rgb(sc)); pdf.rect(m, m, w - 2*m, header_h, style="F")
        pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(255, 255, 255)
        all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        all_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        start = self.params.get("start_day", "Monday")
        start_idx = all_days.index(start) if start in all_days else 0
        rotated = all_short[start_idx:] + all_short[:start_idx]
        day_names = (rotated * 3)[:max(cols, 7)]
        x = m + tcw
        for i in range(cols):
            label = day_names[i] if i < len(day_names) else f"D{i+1}"
            pdf.text(x + 2, m + header_h / 2 + 3, label); x += cell_w
        pdf.text(m + 2, m + header_h / 2 + 3, "Time")
        self._set_c(pdf, c, lw)
        for r in range(rows + 1):
            y = m + header_h + r * cell_h
            pdf.set_line_width(lw * 1.5 if r == 0 else lw); pdf.line(m, y, w - m, y)
        pdf.set_line_width(lw * 0.5)
        for col in range(cols + 1):
            x = m + tcw + col * cell_w; pdf.line(x, m + header_h, x, h - m)
        self._set_c(pdf, c, lw * 1.5); pdf.line(m + tcw, m, m + tcw, h - m)
        if alt_shade:
            for r in range(rows):
                if r % 2 == 0:
                    pdf.set_fill_color(248, 250, 252)
                    pdf.rect(m, m + header_h + r * cell_h, w - 2*m, cell_h, style="F")

    # ── Japanese Genkoyoushi ──
    def _draw_japanese_genkoyoushi(self, pdf, w, h, pg=1):
        cs = self.params["cell_size"] * IN_TO_PT; ms = self.params["margin_size"] * IN_TO_PT
        show_title = self.params.get("show_title_space", True)
        num_title = int(self.params.get("num_title_rows", 3))
        c = self.params["color"]; sc = self.params.get("secondary_color", "#AAAAAA")
        lw = self.params["line_width"]; m = 36
        grid_style = self.params.get("grid_style", "full")
        start_y = m + (num_title * cs if show_title else 0)
        self._set_c(pdf, c, lw * 2); pdf.line(m + ms, m, m + ms, h - m)
        if grid_style != "none":
            pdf.set_dash_pattern(2, 2); self._set_c(pdf, sc, lw * 0.7)
            cx = w / 2; pdf.line(cx, start_y, cx, h - m); pdf.set_dash_pattern()
            if grid_style == "full":
                y = start_y
                while y <= h - m:
                    is_first = (y == start_y)
                    self._set_c(pdf, c if is_first else sc, lw if is_first else lw * 0.5)
                    pdf.line(m, y, w - m, y); y += cs
                x = m
                while x <= w - m:
                    is_first = (x == m)
                    self._set_c(pdf, c if is_first else sc, lw if is_first else lw * 0.5)
                    pdf.line(x, start_y, x, h - m); x += cs
        if show_title:
            pdf.set_font("Helvetica", "", 8); pdf.set_text_color(187, 187, 187)
            pdf.text(m + 4, m + cs * 0.7 + 5, "Title")
        if self.params.get("show_field_guide"):
            gx = m + ms + cs / 2; gy = start_y + cs / 2; d = cs * 0.3
            self._set_c(pdf, sc, lw * 0.5)
            pdf.line(gx - d, gy - d, gx + d, gy + d); pdf.line(gx + d, gy - d, gx - d, gy + d)

    # ── Meeting Notes ──
    def _draw_meeting_notes(self, pdf, w, h, pg=1):
        ta_h = self.params["title_area_height"] * IN_TO_PT
        agenda_rows = int(self.params["agenda_rows"]); nls = self.params["notes_line_spacing"] * IN_TO_PT
        action_rows = int(self.params["action_rows"]); show_fields = self.params.get("show_fields", True)
        show_decision = self.params.get("show_decision_box", False)
        show_timer = self.params.get("show_timer_section", False)
        c = self.params["color"]; sc = self.params.get("secondary_color", "#2563EB")
        lw = self.params["line_width"]; m = 36; y = m
        self._set_c(pdf, c, lw * 1.5); pdf.rect(m, y, w - 2*m, ta_h)
        if show_timer:
            pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(w - m - 120, y + 10, "Start Time: ________")
            pdf.text(w - m - 120, y + 26, "End Time:   ________")
        if show_fields:
            pdf.set_font("Helvetica", "", 8); pdf.set_text_color(170, 170, 170)
            pdf.text(m + 4, y + 8, "Date:"); pdf.text(m + 4, y + 24, "Time:")
            pdf.text(m + w/4, y + 8, "Location:"); pdf.text(m + w/4, y + 24, "Attendees:")
        y += ta_h + 8
        pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*hex_to_rgb(sc))
        pdf.text(m, y + 10, "Agenda"); y += 18
        for i in range(agenda_rows):
            self._set_c(pdf, c, lw * 0.5); pdf.line(m, y, w - m, y); y += 18
        y += 8
        pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*hex_to_rgb(sc))
        pdf.text(m, y + 10, "Notes"); y += 18
        notes_bottom = h - m - action_rows * 22 - 40
        if show_decision: notes_bottom -= 80
        self._set_c(pdf, c, lw * 0.3)
        while y < notes_bottom: pdf.line(m, y, w - m, y); y += nls
        if show_decision:
            y += 8; pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m, y + 10, "Decisions / Outcomes"); y += 18
            for i in range(3):
                if y + 16 > h - m - action_rows * 22 - 20: break
                self._set_c(pdf, c, lw * 0.3); pdf.line(m + 18, y + 14, w - m, y + 14)
                self._set_c(pdf, sc, lw * 0.7); pdf.rect(m + 2, y + 1, 12, 12); y += 18
        y += 8; pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*hex_to_rgb(sc))
        pdf.text(m, y + 10, "Action Items"); y += 18
        for i in range(action_rows):
            if y + 18 > h - m: break
            self._set_c(pdf, c, lw * 0.3); pdf.line(m + 18, y + 14, w - m, y + 14)
            self._set_c(pdf, sc, lw * 0.7); pdf.rect(m + 2, y + 1, 12, 12); y += 22

    # ── Weekly Planner ──
    def _draw_weekly_planner(self, pdf, w, h, pg=1):
        sh = int(self.params["start_hour"]); eh = int(self.params["end_hour"])
        tcw = self.params["time_col_width"] * IN_TO_PT
        show_we = self.params.get("show_weekend", True)
        interval = int(self.params.get("time_interval", 1))
        tf = self.params.get("time_format", "12h")
        cl = self.params.get("column_labels", "short")
        c = self.params["color"]; sc = self.params.get("secondary_color", "#2563EB")
        lw = self.params["line_width"]; m = 36
        num_days = 7 if show_we else 5
        dn_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        dn_full = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_names = dn_full if cl == "full" else dn_short
        if not show_we: day_names = day_names[:5]
        hours = list(range(sh, eh + 1)); header_h = 24
        row_h = (h - 2*m - header_h) / len(hours) if hours else 1
        col_w = (w - 2*m - tcw) / num_days
        pdf.set_fill_color(*hex_to_rgb(sc)); pdf.rect(m, m, w - 2*m, header_h, style="F")
        pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(255, 255, 255)
        x = m + tcw
        for i, dn in enumerate(day_names):
            pdf.text(x + 2, m + header_h / 2 + 3, dn); x += col_w
        pdf.text(m + 2, m + header_h / 2 + 3, "Time")
        for idx, hr in enumerate(hours):
            y = m + header_h + idx * row_h
            self._set_c(pdf, c, lw * 1.2 if hr % interval == 0 else lw * 0.3)
            pdf.line(m, y, w - m, y)
            if hr % interval == 0:
                pdf.set_font("Helvetica", "", 7); pdf.set_text_color(153, 153, 153)
                if tf == "24h": hr_str = f"{hr:02d}:00"
                else: hr_str = f"{hr % 12 or 12}:00 {'AM' if hr < 12 else 'PM'}"
                pdf.text(m + 2, y + row_h / 2 + 2, hr_str)
        for col in range(num_days + 1):
            x = m + tcw + col * col_w; pdf.line(x, m + header_h, x, h - m)
        self._set_c(pdf, c, lw * 1.5); pdf.line(m + tcw, m, m + tcw, h - m)
        if self.params.get("show_current_hour_line"):
            noon_y = m + header_h + (12 - sh) * row_h
            if m + header_h < noon_y < h - m:
                self._set_c(pdf, sc, lw * 2); pdf.line(m, noon_y, w - m, noon_y)

    # ── Budget Tracker ──
    def _draw_budget_tracker(self, pdf, w, h, pg=1):
        inc_rows = int(self.params["income_rows"])
        exp_rows = int(self.params["expense_rows"])
        hdr_h = self.params["header_height"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#16A34A")
        lw = self.params["line_width"]; m = 36
        cat_w = self.params.get("category_col_width", 0.4)
        remaining = 1.0 - cat_w
        col_widths = [cat_w, remaining * 0.416, remaining * 0.333, remaining * 0.251]
        cols = ["Category", "Budgeted", "Actual", "Difference"]
        y = m
        pdf.set_fill_color(*hex_to_rgb(sc)); pdf.rect(m, y, w - 2*m, hdr_h, style="F")
        pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(255, 255, 255)
        pdf.text(m + 4, y + hdr_h / 2 + 3, "INCOME"); y += hdr_h
        x = m
        for cw_frac, col_name in zip(col_widths, cols):
            cw_pt = (w - 2*m) * cw_frac
            self._set_c(pdf, c, lw); pdf.set_font("Helvetica", "B", 7); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(x + 2, y + 10, col_name); x += cw_pt
        y += 16
        for r in range(inc_rows):
            x = m
            for cw_frac in col_widths:
                cw_pt = (w - 2*m) * cw_frac
                self._set_c(pdf, c, lw * 0.3)
                pdf.line(x, y + 14, x + cw_pt, y + 14); pdf.line(x, y, x, y + 14); x += cw_pt
            y += 18
        if self.params.get("show_savings_section"):
            y += 10; sav_rows = int(self.params.get("savings_rows", 3))
            pdf.set_fill_color(*hex_to_rgb("#2563EB")); pdf.rect(m, y, w - 2*m, hdr_h, style="F")
            pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(255, 255, 255)
            pdf.text(m + 4, y + hdr_h / 2 + 3, "SAVINGS"); y += hdr_h
            x = m
            for cw_frac, col_name in zip(col_widths, cols):
                cw_pt = (w - 2*m) * cw_frac
                self._set_c(pdf, c, lw); pdf.set_font("Helvetica", "B", 7); pdf.set_text_color(*hex_to_rgb(c))
                pdf.text(x + 2, y + 10, col_name); x += cw_pt
            y += 16
            for r in range(sav_rows):
                x = m
                for cw_frac in col_widths:
                    cw_pt = (w - 2*m) * cw_frac
                    self._set_c(pdf, c, lw * 0.3)
                    pdf.line(x, y + 14, x + cw_pt, y + 14); pdf.line(x, y, x, y + 14); x += cw_pt
                y += 18
        y += 10
        pdf.set_fill_color(220, 38, 38); pdf.rect(m, y, w - 2*m, hdr_h, style="F")
        pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(255, 255, 255)
        pdf.text(m + 4, y + hdr_h / 2 + 3, "EXPENSES"); y += hdr_h
        x = m
        for cw_frac, col_name in zip(col_widths, cols):
            cw_pt = (w - 2*m) * cw_frac
            self._set_c(pdf, c, lw); pdf.set_font("Helvetica", "B", 7); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(x + 2, y + 10, col_name); x += cw_pt
        y += 16
        for r in range(exp_rows):
            x = m
            for cw_frac in col_widths:
                cw_pt = (w - 2*m) * cw_frac
                self._set_c(pdf, c, lw * 0.3)
                pdf.line(x, y + 14, x + cw_pt, y + 14); pdf.line(x, y, x, y + 14); x += cw_pt
            y += 18
        if self.params.get("show_total_row"):
            self._set_c(pdf, c, lw * 1.5); pdf.line(m, y, w - m, y)
            pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m + 2, y + 10, "TOTAL")

    # ── Reading Log ──
    def _draw_reading_log(self, pdf, w, h, pg=1):
        rows = int(self.params["entry_rows"]); hdr_h = self.params["header_height"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#94A3B8")
        lw = self.params["line_width"]; m = 36
        rh = self.params.get("row_height", 0.25) * IN_TO_PT
        show_genre = self.params.get("show_genre_column", False)
        if show_genre:
            col_fracs = [0.03, 0.18, 0.14, 0.10, 0.10, 0.08, 0.08, 0.10, 0.19]
            col_names = ["#", "Title", "Author", "Started", "Finished", "Rating", "Genre", "Progress", "Notes"]
        else:
            col_fracs = [0.04, 0.22, 0.18, 0.12, 0.12, 0.10, 0.22]
            col_names = ["#", "Title", "Author", "Started", "Finished", "Rating", "Notes"]
        y = m
        pdf.set_fill_color(*hex_to_rgb(sc)); pdf.rect(m, y, w - 2*m, hdr_h, style="F")
        pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(255, 255, 255)
        pdf.text(m + 4, y + hdr_h / 2 + 3, "Reading Log"); y += hdr_h
        x = m
        for frac, name in zip(col_fracs, col_names):
            cw_pt = (w - 2*m) * frac
            self._set_c(pdf, c, lw); pdf.set_font("Helvetica", "B", 7); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(x + 2, y + 10, name); x += cw_pt
        y += 16
        for r in range(rows):
            if y + rh > h - m: break
            x = m
            for frac in col_fracs:
                cw_pt = (w - 2*m) * frac
                self._set_c(pdf, c, lw * 0.3); pdf.line(x, y, x, y + rh); x += cw_pt
            pdf.line(x, y, x, y + rh); pdf.line(m, y + rh, w - m, y + rh)
            if r % 2 == 0:
                pdf.set_fill_color(248, 250, 252); pdf.rect(m, y, w - 2*m, rh, style="F")
            y += rh

    # ── Seyes French Ruled ──
    def _draw_seyes_french_ruled(self, pdf, w, h, pg=1):
        ls = self.params["line_spacing"] * IN_TO_PT
        ml = self.params["margin_left"] * IN_TO_PT
        num_l = int(self.params.get("num_lines", 8))
        c = self.params["color"]; sc = self.params.get("secondary_color", "#FF6699")
        lw = self.params["line_width"]; m = 36
        pink_off = self.params.get("pink_line_offset", 2.0) * MM_TO_PT
        ms = self.params.get("margin_style", "single")
        y = m; row_in_group = 0
        while y < h - m:
            if row_in_group % num_l == 0:
                self._set_c(pdf, c, lw * 2.5); pdf.line(ml, y, w - m, y)
                self._set_c(pdf, sc, lw * 1.0); pdf.line(ml, y + pink_off, w - m, y + pink_off)
            elif row_in_group % (num_l // 2) == 0:
                self._set_c(pdf, c, lw * 1.2); pdf.line(ml, y, w - m, y)
            else:
                self._set_c(pdf, c, lw * 0.5); pdf.set_dash_pattern(1, 1.5)
                pdf.line(ml, y, w - m, y); pdf.set_dash_pattern()
            y += ls; row_in_group += 1
            if row_in_group >= num_l: row_in_group = 0
        self._set_c(pdf, sc, lw * 1.5); pdf.line(ml, m, ml, h - m)
        if ms == "double":
            self._set_c(pdf, sc, lw * 0.7); pdf.line(ml + 4, m, ml + 4, h - m)
        if self.params.get("show_top_margin"):
            self._set_c(pdf, c, lw * 1.0); pdf.line(0, m, w, m)

    # ── NEW: Polar Coordinate ──
    def _draw_polar_coordinate(self, pdf, w, h, pg=1):
        rs = self.params["radius_step"] * IN_TO_PT
        nr = int(self.params["num_radials"])
        show_lbl = self.params.get("show_labels", True)
        c = self.params["color"]; sc = self.params.get("secondary_color", "#99BBDD")
        lw = self.params["line_width"]
        cx, cy = w / 2, h / 2; max_r = math.sqrt(cx*cx + cy*cy)
        r = rs
        while r < max_r:
            self._set_c(pdf, sc, lw); pdf.ellipse(cx - r, cy - r, 2*r, 2*r, style="D")
            if show_lbl:
                pdf.set_font("Helvetica", "", 6); pdf.set_text_color(*hex_to_rgb(c))
                pdf.text(cx - 10, cy - r - 2, f"{r/IN_TO_PT:.1f}")
            r += rs
        start_ang = self.params.get("start_angle", 0)
        for i in range(nr):
            angle = math.radians(start_ang + 360 / nr * i)
            ex = cx + max_r * math.cos(angle); ey = cy - max_r * math.sin(angle)
            self._set_c(pdf, sc, lw * 0.7); pdf.line(cx, cy, ex, ey)
            if show_lbl:
                pdf.set_font("Helvetica", "", 6); pdf.set_text_color(*hex_to_rgb(c))
                lx = cx + (max_r * 0.15) * math.cos(angle)
                ly = cy - (max_r * 0.15) * math.sin(angle)
                pdf.text(lx - 6, ly + 2, f"{int((start_ang + 360/nr*i) % 360)}")

    # ── NEW: Logarithmic Paper ──
    def _draw_logarithmic_paper(self, pdf, w, h, pg=1):
        cycles = int(self.params["log_cycles"]); gs = self.params["grid_size"] * IN_TO_PT
        show_lbl = self.params.get("show_labels", True)
        c = self.params["color"]; sc = self.params.get("secondary_color", "#66BB66")
        lw = self.params["line_width"]; m = self.params.get("margin", 1.0) * IN_TO_PT
        lfs = int(self.params.get("label_font_size", 7))
        log_w = w - 2 * m
        for cyc in range(cycles):
            base_x = m + (log_w / cycles) * cyc
            for sub in range(1, 10):
                x = base_x + (log_w / cycles) * math.log10(sub + 1)
                self._set_c(pdf, sc, lw * 0.5); pdf.line(x, m, x, h - m)
            major_x = m + (log_w / cycles) * (cyc + 1)
            self._set_c(pdf, c, lw); pdf.line(major_x, m, major_x, h - m)
        self._set_c(pdf, c, lw); pdf.line(m, m, m, h - m)
        y = m
        while y <= h - m: self._set_c(pdf, sc, lw * 0.5); pdf.line(m, y, w - m, y); y += gs
        if show_lbl:
            pdf.set_font("Helvetica", "", lfs); pdf.set_text_color(*hex_to_rgb(c))
            for cyc in range(cycles + 1):
                x = m + (log_w / cycles) * cyc
                pdf.text(x - 8, h - m + 4, f"1e{cyc}" if cyc > 0 else "1")

    # ── NEW: Probability Paper ──
    def _draw_probability_paper(self, pdf, w, h, pg=1):
        gs = self.params["grid_size"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#BB99DD")
        lw = self.params["line_width"]; m = self.params.get("margin", 1.0) * IN_TO_PT
        lfs = int(self.params.get("label_font_size", 7))
        show_lbl = self.params.get("show_labels", True)
        x = m
        while x <= w - m: self._set_c(pdf, sc, lw * 0.5); pdf.line(x, m, x, h - m); x += gs
        y = m
        while y <= h - m: self._set_c(pdf, sc, lw * 0.5); pdf.line(m, y, w - m, y); y += gs
        if show_lbl:
            import math as _m
            pdf.set_font("Helvetica", "", lfs); pdf.set_text_color(*hex_to_rgb(c))
            probs = [0.1, 0.5, 1, 2, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 98, 99, 99.5, 99.9]
            usable_h = h - 2 * m
            for prob in probs:
                if prob < 50:
                    z = -_norm_ppf(prob / 100.0)
                else:
                    z = _norm_ppf(1.0 - prob / 100.0)
                y_pos = m + usable_h * (1 - (z + 3.5) / 7.0)
                if m < y_pos < h - m:
                    self._set_c(pdf, c, lw); pdf.line(m, y_pos, w - m, y_pos)
                    pdf.text(m - 36, y_pos + 3, f"{prob}%")

    # ── NEW: Seam Allowance ──
    def _draw_seam_allowance(self, pdf, w, h, pg=1):
        gs = self.params["grid_size"] * IN_TO_PT
        mw = self.params["margin_width"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#FF9999")
        lw = self.params["line_width"]; m = self.params.get("margin", 0.5) * IN_TO_PT
        self._set_c(pdf, sc, lw * 0.3)
        x = m
        while x <= w - m: pdf.line(x, m, x, h - m); x += gs
        y = m
        while y <= h - m: pdf.line(m, y, w - m, y); y += gs
        qm = 0.25 * IN_TO_PT; fe = 0.625 * IN_TO_PT
        if self.params.get("show_quarter_mark"):
            self._set_c(pdf, c, lw); pdf.set_dash_pattern(2, 2)
            pdf.line(m + qm, m, m + qm, h - m); pdf.line(w - m - qm, m, w - m - qm, h - m)
            pdf.line(m, m + qm, w - m, m + qm); pdf.line(m, h - m - qm, w - m, h - m - qm)
            pdf.set_dash_pattern()
        if self.params.get("show_five_eighths_mark"):
            self._set_c(pdf, c, lw * 1.5); pdf.set_dash_pattern(3, 2)
            pdf.line(m + fe, m, m + fe, h - m); pdf.line(w - m - fe, m, w - m - fe, h - m)
            pdf.line(m, m + fe, w - m, m + fe); pdf.line(m, h - m - fe, w - m, h - m - fe)
            pdf.set_dash_pattern()
        self._set_c(pdf, c, lw)
        pdf.line(m + mw, m, m + mw, h - m); pdf.line(w - m - mw, m, w - m - mw, h - m)
        pdf.line(m + mw, m + mw, w - m - mw, m + mw)
        pdf.line(m + mw, h - m - mw, w - m - mw, h - m - mw)

    # ── NEW: Knitting Grid ──
    def _draw_knitting_grid(self, pdf, w, h, pg=1):
        gs = self.params["grid_size"] * IN_TO_PT
        major = int(self.params.get("major_every", 10))
        show_rn = self.params.get("show_row_numbers", True)
        show_cn = self.params.get("show_col_numbers", True)
        c = self.params["color"]; sc = self.params.get("secondary_color", "#DDBBCC")
        mlw = self.params.get("major_line_weight", 2.0)
        lw = self.params["line_width"]; m = self.params.get("margin", 0.5) * IN_TO_PT
        lfs = int(self.params.get("label_font_size", 6))
        self._set_c(pdf, sc, lw)
        x = m
        while x <= w - m: pdf.line(x, m, x, h - m); x += gs
        y = m
        while y <= h - m: pdf.line(m, y, w - m, y); y += gs
        self._set_c(pdf, c, lw * mlw)
        x = m
        while x <= w - m: pdf.line(x, m, x, h - m); x += gs * major
        y = m
        while y <= h - m: pdf.line(m, y, w - m, y); y += gs * major
        if show_rn:
            pdf.set_font("Helvetica", "", lfs); pdf.set_text_color(*hex_to_rgb(c))
            row = 0; y = m
            while y <= h - m:
                if row % major == 0 and row > 0:
                    pdf.text(m - 28, y + 2, str(row))
                y += gs; row += 1

    # ── NEW: Circuit / Schematic ──
    def _draw_circuit___schematic(self, pdf, w, h, pg=1):
        gs = self.params["grid_size"] * IN_TO_PT
        ds = self.params.get("dot_size", 1.0)
        major = int(self.params.get("major_every", 5))
        snap = self.params.get("snap_dots", True)
        c = self.params["color"]; sc = self.params.get("secondary_color", "#6699CC")
        mlw = self.params.get("major_line_weight", 2.0)
        lw = self.params["line_width"]; m = self.params.get("margin", 0.25) * IN_TO_PT
        self._set_c(pdf, sc, lw)
        x = m
        while x <= w - m: pdf.line(x, m, x, h - m); x += gs
        y = m
        while y <= h - m: pdf.line(m, y, w - m, y); y += gs
        self._set_c(pdf, c, lw * mlw)
        x = m
        while x <= w - m: pdf.line(x, m, x, h - m); x += gs * major
        y = m
        while y <= h - m: pdf.line(m, y, w - m, y); y += gs * major
        if snap:
            pdf.set_fill_color(*hex_to_rgb(c))
            x = m
            while x <= w - m:
                y = m
                while y <= h - m:
                    pdf.ellipse(x - ds/2, y - ds/2, ds, ds, style="F")
                    y += gs * major
                x += gs * major

    # ── NEW: Braille Practice ──
    def _draw_braille_practice(self, pdf, w, h, pg=1):
        cs = self.params["cell_spacing"] * IN_TO_PT
        ds = self.params["dot_spacing"] * IN_TO_PT
        cell_sz = self.params["cell_size"] * IN_TO_PT
        show_guide = self.params.get("show_guide_dots", True)
        c = self.params["color"]; sc = self.params.get("secondary_color", "#AAAAAA")
        lw = self.params["line_width"]; m = self.params.get("margin", 1.0) * IN_TO_PT
        dot_r = self.params.get("dot_radius", 1.5)
        y = m
        while y < h - m - cell_sz:
            x = m
            while x < w - m - cell_sz:
                self._set_c(pdf, sc, lw * 0.3); pdf.rect(x, y, cell_sz, cell_sz, style="D")
                if show_guide:
                    pdf.set_fill_color(*hex_to_rgb(sc))
                    for col in range(2):
                        for row in range(3):
                            dx = x + cell_sz * 0.35 + col * ds
                            dy = y + cell_sz * 0.2 + row * ds
                            pdf.ellipse(dx - dot_r, dy - dot_r, 2*dot_r, 2*dot_r, style="F")
                x += cs
            y += cs

    # ── NEW: Musical TAB ──
    def _draw_musical_tab(self, pdf, w, h, pg=1):
        ns = int(self.params["num_staves"])
        ss = self.params["staff_spacing"] * IN_TO_PT
        gs = self.params["group_spacing"] * IN_TO_PT
        show_bar = self.params.get("show_barlines", True)
        bar_int = self.params.get("barline_interval", 2.0) * IN_TO_PT
        c = self.params["color"]
        self._set_c(pdf, c, self.params["line_width"])
        staff_h = 5 * ss; total = ns * (staff_h + gs) - gs
        start_y = (h - total) / 2
        for i in range(ns):
            base = start_y + i * (staff_h + gs)
            for j in range(6): pdf.line(54, base + j * ss, w - 54, base + j * ss)
            pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(10, base + staff_h / 2 + 3, "TAB")
            if show_bar and bar_int > 0:
                bx = 54 + bar_int
                while bx < w - 54: pdf.line(bx, base, bx, base + 5 * ss); bx += bar_int

    # ── NEW: Ledger / Accounting ──
    def _draw_ledger___accounting(self, pdf, w, h, pg=1):
        num_rows = int(self.params["num_rows"])
        ndc = int(self.params["num_debit_cols"]); ncc = int(self.params["num_credit_cols"])
        hdr_h = self.params["header_height"] * IN_TO_PT
        show_total = self.params.get("show_totals_row", True)
        c = self.params["color"]; sc = self.params.get("secondary_color", "#16A34A")
        lw = self.params["line_width"]; m = 36
        total_data_cols = ndc + ncc
        acct_w = (w - 2*m) * 0.25; data_w = (w - 2*m - acct_w) / total_data_cols
        y = m
        pdf.set_fill_color(*hex_to_rgb(sc)); pdf.rect(m, y, w - 2*m, hdr_h, style="F")
        pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(255, 255, 255)
        pdf.text(m + 4, y + hdr_h / 2 + 3, "Account"); y += hdr_h
        row_h = (h - m - y) / (num_rows + (1 if show_total else 0))
        for r in range(num_rows):
            self._set_c(pdf, c, lw * 0.5); pdf.line(m, y + row_h, w - m, y + row_h)
            x = m + acct_w
            for i in range(total_data_cols + 1):
                self._set_c(pdf, c, lw * 0.3); pdf.line(x, y, x, y + row_h); x += data_w
            if r % 2 == 0:
                pdf.set_fill_color(248, 250, 252); pdf.rect(m, y, w - 2*m, row_h, style="F")
            y += row_h
        if show_total:
            self._set_c(pdf, c, lw * 1.5); pdf.line(m, y, w - m, y)
            pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m + 4, y + 10, "TOTAL")

    # ── NEW: Daily Schedule ──
    def _draw_daily_schedule(self, pdf, w, h, pg=1):
        sh = int(self.params["start_hour"]); eh = int(self.params["end_hour"])
        slot_h = self.params["slot_height"] * IN_TO_PT
        tcw = self.params["time_col_width"] * IN_TO_PT
        show_15 = self.params.get("show_15min", False)
        c = self.params["color"]; sc = self.params.get("secondary_color", "#2563EB")
        lw = self.params["line_width"]; m = 36
        hours = list(range(sh, eh + 1)); header_h = 28
        pdf.set_fill_color(*hex_to_rgb(sc)); pdf.rect(m, m, w - 2*m, header_h, style="F")
        pdf.set_font("Helvetica", "B", 12); pdf.set_text_color(255, 255, 255)
        pdf.text(m + 8, m + 16, "Daily Schedule"); y = m + header_h
        for hr in hours:
            self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y)
            pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb("#666666"))
            ampm = "AM" if hr < 12 else "PM"; hr12 = hr % 12 or 12
            pdf.text(m + 4, y + 4, f"{hr12}:00 {ampm}")
            if show_15:
                self._set_c(pdf, sc, lw * 0.2); pdf.set_dash_pattern(0.3, 1.2)
                for q in range(1, 4):
                    pdf.line(m + tcw, y + slot_h * q / 4, w - m, y + slot_h * q / 4)
                pdf.set_dash_pattern()
            y += slot_h
        self._set_c(pdf, c, lw); pdf.line(m + tcw, m + header_h, m + tcw, h - m)

    # ── NEW: Habit Tracker ──
    def _draw_habit_tracker(self, pdf, w, h, pg=1):
        nh = int(self.params["num_habits"])
        show_wd = self.params.get("show_weekday_headers", True)
        show_mh = self.params.get("show_month_header", True)
        cbs = self.params["checkbox_size"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#2563EB")
        lw = self.params["line_width"]; m = 36; dim = int(self.params.get("days_in_month", 31))
        header_h = 32 if show_mh else 0; wd_h = 20 if show_wd else 0
        habit_label_w = self.params.get("label_width", 100)
        row_pad = self.params.get("row_padding", 12)
        day_col_w = (w - 2*m - habit_label_w) / dim
        y = m
        if show_mh:
            pdf.set_fill_color(*hex_to_rgb(sc)); pdf.rect(m, y, w - 2*m, header_h, style="F")
            pdf.set_font("Helvetica", "B", 11); pdf.set_text_color(255, 255, 255)
            pdf.text(m + 8, y + 20, "Habit Tracker"); y += header_h
        if show_wd:
            day_names = ["M", "T", "W", "T", "F", "S", "S"]
            pdf.set_font("Helvetica", "", 6); pdf.set_text_color(*hex_to_rgb(c))
            for d in range(dim):
                x = m + habit_label_w + d * day_col_w
                pdf.text(x, y + 12, day_names[d % 7])
            y += wd_h
        for i in range(nh):
            row_y = y + i * (cbs + row_pad)
            if row_y + cbs + row_pad > h - m: break
            self._set_c(pdf, c, lw * 0.3); pdf.line(m, row_y + cbs + 12, w - m, row_y + cbs + 12)
            for d in range(dim):
                cx = m + habit_label_w + d * day_col_w + day_col_w / 2 - cbs / 2
                cy = row_y
                self._set_c(pdf, sc, lw * 0.5); pdf.rect(cx, cy, cbs, cbs, style="D")

    # ── NEW: Recipe Card ──
    def _draw_recipe_card(self, pdf, w, h, pg=1):
        c = self.params["color"]; sc = self.params.get("secondary_color", "#D97706")
        lw = self.params["line_width"]; m = 54
        show_prep = self.params.get("show_prep_time", True)
        show_cook = self.params.get("show_cook_time", True)
        show_serv = self.params.get("show_servings", True)
        show_diff = self.params.get("show_difficulty", True)
        ing_rows = int(self.params.get("ingredients_rows", 12))
        inst_lines = int(self.params.get("instructions_lines", 15))
        y = m
        self._set_c(pdf, sc, lw * 1.5); pdf.rect(m, y, w - 2*m, 28)
        pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*hex_to_rgb("#AAAAAA"))
        pdf.text(m + 4, y + 16, "Recipe Title: ________________________"); y += 36
        fields = []
        if show_prep: fields.append(("Prep Time:", 0.2))
        if show_cook: fields.append(("Cook Time:", 0.2))
        if show_serv: fields.append(("Servings:", 0.15))
        if show_diff: fields.append(("Difficulty:", 0.15))
        if fields:
            x = m
            for label, frac in fields:
                fw = (w - 2*m) * frac
                pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*hex_to_rgb(c))
                pdf.text(x, y + 10, label)
                self._set_c(pdf, c, lw * 0.3); pdf.line(x + 60, y + 16, x + fw, y + 16)
                x += fw
            y += 24
        pdf.set_font("Helvetica", "B", 11); pdf.set_text_color(*hex_to_rgb(sc))
        pdf.text(m, y + 12, "Ingredients"); y += 20
        for i in range(ing_rows):
            if y + 16 > h - m - inst_lines * 16 - 40: break
            self._set_c(pdf, sc, lw * 0.7); pdf.rect(m + 2, y, 10, 10, style="D")
            self._set_c(pdf, c, lw * 0.3); pdf.line(m + 16, y + 5, w - m, y + 5)
            y += 16
        y += 10
        pdf.set_font("Helvetica", "B", 11); pdf.set_text_color(*hex_to_rgb(sc))
        pdf.text(m, y + 12, "Instructions"); y += 20
        for i in range(inst_lines):
            if y + 16 > h - m: break
            pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m + 4, y + 8, f"{i+1}.")
            self._set_c(pdf, c, lw * 0.3); pdf.line(m + 24, y + 8, w - m, y + 8)
            y += 16


    # ── Perspective Grid ──
    def _draw_perspective_grid(self, pdf, w, h, pg=1):
        npts = int(self.params["num_points"])
        gs = self.params["grid_size"] * IN_TO_PT
        horizon_pct = self.params["horizon_position"] / 100.0
        c = self.params["color"]; sc = self.params.get("secondary_color", "#99BBDD")
        lw = self.params["line_width"]
        vp_size = self.params.get("vanishing_point_size", 4.0)
        horizon_y = h * horizon_pct
        if self.params.get("show_horizon", True):
            self._set_c(pdf, sc, lw * 1.5); pdf.line(0, horizon_y, w, horizon_y)
        if self.params.get("show_ground_line", True):
            ground_y = horizon_y + (h - horizon_y) * 0.15
            self._set_c(pdf, sc, lw * 0.5); pdf.line(0, ground_y, w, ground_y)
        if npts == 1:
            vx, vy = w / 2, horizon_y
            self._set_c(pdf, c, lw * 0.5)
            x = 0
            while x <= w:
                pdf.line(vx, vy, x, 0); pdf.line(vx, vy, x, h)
                x += gs * 2
            self._set_c(pdf, sc, lw * 0.3)
            num_h = int((h - horizon_y) / gs)
            for i in range(1, num_h + 1):
                y = horizon_y + (h - horizon_y) * (i / num_h) ** 1.5
                if y < h: pdf.line(0, y, w, y)
            num_h2 = int(horizon_y / gs)
            for i in range(1, num_h2 + 1):
                y = horizon_y - horizon_y * (i / num_h2) ** 1.5
                if y > 0: pdf.line(0, y, w, y)
            pdf.set_fill_color(*hex_to_rgb(c)); pdf.set_draw_color(*hex_to_rgb(c))
            pdf.ellipse(vx - vp_size, vy - vp_size, 2 * vp_size, 2 * vp_size, style="F")
        elif npts == 2:
            vx1, vy1 = 0, horizon_y; vx2, vy2 = w, horizon_y
            self._set_c(pdf, c, lw * 0.5)
            x = 0
            while x <= w:
                pdf.line(vx1, vy1, x, h); pdf.line(vx2, vy2, x, h)
                x += gs * 2
            self._set_c(pdf, sc, lw * 0.3)
            x = gs * 2
            while x < w:
                pdf.line(x, horizon_y, x, h); x += gs * 2
            num_h = int((h - horizon_y) / gs)
            for i in range(1, num_h + 1):
                y = horizon_y + (h - horizon_y) * (i / num_h) ** 1.5
                if y < h: pdf.line(0, y, w, y)
            pdf.set_fill_color(*hex_to_rgb(c)); pdf.set_draw_color(*hex_to_rgb(c))
            pdf.ellipse(vx1 - vp_size, vy1 - vp_size, 2 * vp_size, 2 * vp_size, style="F")
            pdf.ellipse(vx2 - vp_size, vy2 - vp_size, 2 * vp_size, 2 * vp_size, style="F")

    # ── Mandala Guide ──
    def _draw_mandala_guide(self, pdf, w, h, pg=1):
        nradials = int(self.params["num_radials"])
        nrings = int(self.params["num_rings"])
        rs = self.params["ring_spacing"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#F0C0D0")
        lw = self.params["line_width"]
        cx, cy = w / 2, h / 2
        max_r = min(w, h) / 2 - 20
        if self.params.get("show_concentric_circles", True):
            self._set_c(pdf, sc, lw * 0.5)
            for i in range(1, nrings + 1):
                r = rs * i
                if r > max_r: break
                pdf.ellipse(cx - r, cy - r, 2 * r, 2 * r, style="D")
        self._set_c(pdf, c, lw)
        for i in range(nradials):
            angle = 2 * math.pi * i / nradials
            ex = cx + max_r * math.cos(angle)
            ey = cy + max_r * math.sin(angle)
            pdf.line(cx, cy, ex, ey)
        if self.params.get("show_center_dot", True):
            cds = self.params.get("center_dot_size", 3.0)
            pdf.set_fill_color(*hex_to_rgb(c)); pdf.set_draw_color(*hex_to_rgb(c))
            pdf.ellipse(cx - cds, cy - cds, 2 * cds, 2 * cds, style="F")

    # ── Guitar Chord Diagram ──
    def _draw_guitar_chord_diagram(self, pdf, w, h, pg=1):
        dw = int(self.params["diagrams_w"])
        dh = int(self.params["diagrams_h"])
        ds = self.params["diagram_size"] * IN_TO_PT
        nfrets = int(self.params.get("num_frets", 5))
        c = self.params["color"]; sc = self.params.get("secondary_color", "#94A3B8")
        lw = self.params["line_width"]
        m = 36
        total_w_needed = dw * ds + (dw - 1) * m
        total_h_needed = dh * (ds + 36) + (dh - 1) * m
        start_x = max((w - total_w_needed) / 2, m)
        start_y = max((h - total_h_needed) / 2, m)
        names = ["E", "A", "D", "G", "B", "e"]
        for row in range(dh):
            for col in range(dw):
                x = start_x + col * (ds + m)
                y = start_y + row * (ds + 36)
                fret_h = ds / nfrets
                # Nut
                self._set_c(pdf, c, lw * 2); pdf.line(x, y, x + ds, y)
                # Frets
                self._set_c(pdf, c, lw)
                for f in range(1, nfrets + 1):
                    pdf.line(x, y + f * fret_h, x + ds, y + f * fret_h)
                # Strings
                string_spacing = ds / 5
                for s in range(6):
                    sx = x + s * string_spacing
                    pdf.line(sx, y, sx, y + ds)
                # String names
                if self.params.get("show_string_names", True):
                    pdf.set_font("Helvetica", "", 7); pdf.set_text_color(*hex_to_rgb(sc))
                    for s in range(6):
                        pdf.text(x + s * string_spacing - 3, y - 8, names[s])
                # Fret numbers
                if self.params.get("show_fret_numbers", True):
                    pdf.set_font("Helvetica", "", 7); pdf.set_text_color(*hex_to_rgb(sc))
                    for f in range(1, nfrets + 1):
                        pdf.text(x - 16, y + (f - 0.5) * fret_h + 2, str(f))

    # ── Venn Diagram ──
    def _draw_venn_diagram(self, pdf, w, h, pg=1):
        nc = int(self.params["num_circles"])
        cr = self.params["circle_radius"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#D0E0F0")
        lw = self.params["line_width"]
        cx, cy = w / 2, h / 2
        max_r = min(w, h) / 3.5
        if cr > max_r: cr = max_r
        positions = []
        overlap = self.params.get("overlap_ratio", 0.5)
        if nc == 2:
            off = cr * overlap
            positions = [(cx - off, cy), (cx + off, cy)]
        elif nc == 3:
            off = cr * overlap
            for i in range(3):
                angle = math.pi / 2 + 2 * math.pi * i / 3
                positions.append((cx + off * math.cos(angle), cy - off * math.sin(angle)))
        elif nc >= 4:
            off = cr * overlap
            positions = [
                (cx - off, cy - off * 0.7), (cx + off, cy - off * 0.7),
                (cx - off, cy + off * 0.7), (cx + off, cy + off * 0.7),
            ]
        if self.params.get("show_shading", False):
            self._set_c(pdf, sc, lw)
            pdf.set_fill_color(*hex_to_rgb(sc))
            for (px, py) in positions:
                pdf.ellipse(px - cr, py - cr, 2 * cr, 2 * cr, style="DF")
        self._set_c(pdf, c, lw)
        for (px, py) in positions:
            pdf.ellipse(px - cr, py - cr, 2 * cr, 2 * cr, style="D")
        if self.params.get("show_labels", True):
            lfs = int(self.params.get("label_font_size", 9))
            pdf.set_font("Helvetica", "", lfs); pdf.set_text_color(*hex_to_rgb(c))
            labels = [chr(65 + i) for i in range(min(nc, 4))]
            for i, (px, py) in enumerate(positions):
                lx = px + (cr * 0.6 if i % 2 == 0 else -cr * 0.6)
                pdf.text(lx - 4, py - cr - 6, labels[i] if i < len(labels) else "")

    # ── Study Notes ──
    def _draw_study_notes(self, pdf, w, h, pg=1):
        ls = self.params["line_spacing"] * IN_TO_PT
        ml = self.params["margin_left"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#94A3B8")
        lw = self.params["line_width"]
        sh = self.params.get("summary_height", 2.0) * IN_TO_PT
        m = 54; y = m
        if self.params.get("show_date_field", True):
            pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m, y + 6, "Date:")
            self._set_c(pdf, c, lw * 0.5); pdf.line(m + 45, y + 12, m + 220, y + 12)
            y += 22
        if self.params.get("show_topic_field", True):
            pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m, y + 6, "Topic:")
            self._set_c(pdf, c, lw * 0.5); pdf.line(m + 50, y + 12, w - m, y + 12)
            y += 24
        if self.params.get("show_key_concepts", True):
            pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m, y + 8, "Key Concepts"); y += 18
            concepts = int(self.params.get("concepts_rows", 5))
            for i in range(concepts):
                if y > h - sh - 20: break
                self._set_c(pdf, c, lw * 0.3); pdf.line(m + 8, y + 12, w - m, y + 12)
                y += ls * 0.8
            y += 8
        self._set_c(pdf, sc, lw * 0.5); pdf.line(m, y, w - m, y); y += 8
        bottom = h - sh - 10
        self._set_c(pdf, c, lw * 0.5)
        while y < bottom:
            pdf.line(ml, y, w - m, y); y += ls
        if self.params.get("show_summary_section", True):
            self._set_c(pdf, c, lw * 1.5); pdf.line(m, h - sh, w - m, h - sh)
            pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m + 4, h - sh + 12, "Summary")
            sy = h - sh + 22
            self._set_c(pdf, sc, lw * 0.3)
            while sy < h - 10:
                pdf.line(m, sy, w - m, sy); sy += ls * 0.8

    # ── Project Planner ──
    def _draw_project_planner(self, pdf, w, h, pg=1):
        nph = int(self.params["num_phases"])
        tpp = int(self.params["tasks_per_phase"])
        c = self.params["color"]; sc = self.params.get("secondary_color", "#2563EB")
        lw = self.params["line_width"]; m = 36; y = m
        pdf.set_font("Helvetica", "B", 14); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 14, "Project Planner"); y += 26
        self._set_c(pdf, c, lw * 0.5); pdf.line(m, y, w - m, y); y += 8
        cols = ["Phase / Task"]
        if self.params.get("show_priority_col", True): cols.append("Priority")
        if self.params.get("show_status_col", True): cols.append("Status")
        if self.params.get("show_deadline_col", True): cols.append("Deadline")
        cols.append("Notes")
        num_cols = len(cols); col_w = (w - 2 * m) / num_cols
        pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(*hex_to_rgb(c))
        for ci, cn in enumerate(cols):
            pdf.text(m + ci * col_w + 4, y + 8, cn)
        y += 16; self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y); y += 4
        row_h = 18
        for phase in range(nph):
            if y + row_h > h - m: break
            pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m + 4, y + 12, f"Phase {phase + 1}"); y += row_h
            for task in range(tpp):
                if y + row_h > h - m: break
                self._set_c(pdf, c, lw * 0.3); pdf.line(m, y + row_h, w - m, y + row_h)
                x = m + col_w
                for ci in range(1, num_cols):
                    pdf.line(x, y, x, y + row_h); x += col_w
                y += row_h
            self._set_c(pdf, c, lw * 0.8); pdf.line(m, y, w - m, y); y += 4
        if self.params.get("show_timeline", True) and y + 40 < h - m:
            y += 8
            pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m, y + 10, "Timeline"); y += 18
            self._set_c(pdf, sc, lw); pdf.line(m, y + 8, w - m, y + 8)

    # ── Fitness Log ──
    def _draw_fitness_log(self, pdf, w, h, pg=1):
        nex = int(self.params["num_exercises"])
        nsets = int(self.params["num_sets"])
        c = self.params["color"]; sc = self.params.get("secondary_color", "#16A34A")
        lw = self.params["line_width"]; m = 36; y = m
        pdf.set_font("Helvetica", "B", 13); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 14, "Fitness Log"); y += 24
        if self.params.get("show_date_field", True):
            pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m, y + 6, "Date:")
            self._set_c(pdf, c, lw * 0.5); pdf.line(m + 40, y + 10, m + 200, y + 10)
            y += 20
        cols = ["Exercise"]
        for s in range(1, nsets + 1): cols.append(f"Set {s}")
        if self.params.get("show_weight_col", True): cols.append("Wt")
        if self.params.get("show_reps_col", True): cols.append("Reps")
        if self.params.get("show_rest_col", True): cols.append("Rest")
        if self.params.get("show_notes_col", True): cols.append("Notes")
        num_cols = len(cols); col_w = (w - 2 * m) / num_cols
        pdf.set_font("Helvetica", "B", 7); pdf.set_text_color(*hex_to_rgb(c))
        for ci, cn in enumerate(cols):
            pdf.text(m + ci * col_w + 2, y + 8, cn)
        y += 14; self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y); y += 2
        row_h = 20
        for ex in range(nex):
            if y + row_h > h - m: break
            pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m + 4, y + 12, f"{ex + 1}.")
            self._set_c(pdf, c, lw * 0.3); pdf.line(m, y + row_h, w - m, y + row_h)
            x = m + col_w
            for ci in range(1, num_cols):
                pdf.line(x, y, x, y + row_h); x += col_w
            y += row_h

    # ── Weight Tracker ──
    def _draw_weight_tracker(self, pdf, w, h, pg=1):
        nw = int(self.params["num_weeks"])
        rh = self.params["row_height"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#2563EB")
        lw = self.params["line_width"]; m = 36; y = m
        pdf.set_font("Helvetica", "B", 13); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 14, "Weight Tracker"); y += 26
        cols = ["Week"]
        if self.params.get("show_date_col", True): cols.append("Date")
        if self.params.get("show_weight_col", True): cols.append("Weight")
        if self.params.get("show_change_col", True): cols.append("Change")
        if self.params.get("show_bmi_col", False): cols.append("BMI")
        cols.append("Notes")
        num_cols = len(cols); col_w = (w - 2 * m) / num_cols
        pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(*hex_to_rgb(c))
        for ci, cn in enumerate(cols):
            pdf.text(m + ci * col_w + 2, y + 8, cn)
        y += 14; self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y); y += 2
        for week in range(1, nw + 1):
            if y + rh > h - m: break
            pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m + 4, y + rh / 2 + 2, str(week))
            self._set_c(pdf, c, lw * 0.3); pdf.line(m, y + rh, w - m, y + rh)
            x = m + col_w
            for ci in range(1, num_cols):
                pdf.line(x, y, x, y + rh); x += col_w
            y += rh
        if self.params.get("show_goal_line", True):
            goal = self.params.get("goal_weight", 150.0)
            if y + 16 < h - 10:
                pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb(c))
                pdf.text(m, y + 12, f"Goal: {goal} lbs")

    # ── Travel Journal ──
    def _draw_travel_journal(self, pdf, w, h, pg=1):
        c = self.params["color"]; sc = self.params.get("secondary_color", "#D97706")
        lw = self.params["line_width"]; m = 40; y = m
        pdf.set_font("Helvetica", "B", 16); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 16, "Travel Journal"); y += 28
        if self.params.get("show_date_field", True):
            pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m, y + 6, "Date:")
            self._set_c(pdf, c, lw * 0.5); pdf.line(m + 45, y + 10, m + 230, y + 10)
        if self.params.get("show_location_field", True):
            pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m + 250, y + 6, "Location:")
            self._set_c(pdf, c, lw * 0.5); pdf.line(m + 320, y + 10, w - m, y + 10)
        y += 22; self._set_c(pdf, sc, lw * 0.5); pdf.line(m, y, w - m, y); y += 8
        entry_lines = int(self.params.get("num_entry_lines", 20))
        ls = 0.375 * IN_TO_PT
        bottom_needed = 0
        if self.params.get("show_weather_section", True): bottom_needed += 50
        if self.params.get("show_highlights_section", True): bottom_needed += 24 + int(self.params.get("highlights_rows", 5)) * 16
        if self.params.get("show_expenses_section", True): bottom_needed += 24 + int(self.params.get("expense_rows", 5)) * 16
        max_y = h - m - bottom_needed
        self._set_c(pdf, c, lw * 0.3)
        while y < max_y and entry_lines > 0:
            pdf.line(m, y, w - m, y); y += ls; entry_lines -= 1
        y += 6
        if self.params.get("show_weather_section", True) and y + 40 < h - m:
            pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m, y + 8, "Weather"); y += 14
            pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*hex_to_rgb(sc))
            for label, xo in [("Temp:", 0), ("Condition:", 150), ("High/Low:", 320)]:
                pdf.text(m + xo, y + 6, label)
                self._set_c(pdf, c, lw * 0.3); pdf.line(m + xo + 55, y + 10, m + xo + 130, y + 10)
            y += 20
        if self.params.get("show_highlights_section", True) and y + 30 < h - m:
            pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m, y + 8, "Highlights"); y += 16
            self._set_c(pdf, c, lw * 0.3)
            for i in range(int(self.params.get("highlights_rows", 5))):
                if y + 14 > h - m: break
                pdf.line(m + 8, y + 12, w - m, y + 12); y += 16
            y += 4
        if self.params.get("show_expenses_section", True) and y + 30 < h - m:
            self._set_c(pdf, sc, lw * 0.5); pdf.line(m, y, w - m, y); y += 6
            pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m, y + 8, "Expenses"); y += 14
            pdf.set_font("Helvetica", "B", 7); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m, y + 6, "Item"); pdf.text(m + 140, y + 6, "Amount"); y += 12
            self._set_c(pdf, c, lw * 0.3)
            for i in range(int(self.params.get("expense_rows", 5))):
                if y + 14 > h - m: break
                pdf.line(m, y + 12, m + 130, y + 12); pdf.line(m + 135, y + 12, m + 200, y + 12)
                y += 16

    # ── Essay Outline ──
    def _draw_essay_outline(self, pdf, w, h, pg=1):
        nbp = int(self.params["num_body_paragraphs"])
        c = self.params["color"]; sc = self.params.get("secondary_color", "#94A3B8")
        lw = self.params["line_width"]; m = 50; y = m
        pdf.set_font("Helvetica", "B", 13); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 14, "Essay Outline"); y += 26
        pdf.set_font("Helvetica", "", 10); pdf.set_text_color(*hex_to_rgb(sc))
        pdf.text(m, y + 6, "Essay Title:")
        self._set_c(pdf, c, lw * 0.5); pdf.line(m, y + 14, w - m, y + 14); y += 24
        if self.params.get("show_hook_section", True):
            pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m, y + 8, "I. Introduction"); y += 18
            pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m + 16, y + 6, "Hook / Attention Grabber:")
            y += 12; self._set_c(pdf, c, lw * 0.3); pdf.line(m + 16, y, w - m, y); y += 16
        if self.params.get("show_thesis_section", True):
            pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m + 16, y + 6, "Thesis Statement:")
            y += 12; self._set_c(pdf, c, lw * 0.5); pdf.line(m + 16, y, w - m, y)
            y += 10; self._set_c(pdf, c, lw * 0.3); pdf.line(m + 16, y, w - m, y); y += 18
        evidence = int(self.params.get("evidence_lines_per_para", 3))
        romans = ["II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
        avail = h - m - y
        if self.params.get("show_conclusion_section", True): avail -= 80
        if self.params.get("show_counter_argument", True): avail -= 60
        para_h = min(avail / max(nbp, 1), 160)
        for i in range(nbp):
            if y + para_h > h - m - 40: break
            label = romans[i] if i < len(romans) else f"{i + 2}"
            pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m, y + 8, f"{label}. Body Paragraph {i + 1}"); y += 16
            pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m + 16, y + 6, "Topic Sentence:")
            y += 10; self._set_c(pdf, c, lw * 0.3); pdf.line(m + 16, y, w - m, y); y += 12
            for e in range(evidence):
                if y + 12 > h - m - 40: break
                pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*hex_to_rgb(sc))
                pdf.text(m + 24, y + 6, f"Evidence {e + 1}:")
                y += 10; self._set_c(pdf, c, lw * 0.3); pdf.line(m + 24, y, w - m, y); y += 12
            pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m + 24, y + 6, "Analysis:")
            y += 10; self._set_c(pdf, c, lw * 0.3); pdf.line(m + 24, y, w - m, y); y += 16
        if self.params.get("show_counter_argument", True) and y + 50 < h - m:
            ri = nbp
            label = romans[ri] if ri < len(romans) else f"{ri + 2}"
            pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m, y + 8, f"{label}. Counter Argument"); y += 16
            pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m + 16, y + 6, "Opposing View:")
            y += 10; self._set_c(pdf, c, lw * 0.3); pdf.line(m + 16, y, w - m, y); y += 12
            pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m + 16, y + 6, "Rebuttal:")
            y += 10; self._set_c(pdf, c, lw * 0.3); pdf.line(m + 16, y, w - m, y); y += 18
        if self.params.get("show_conclusion_section", True) and y + 50 < h - m:
            ri2 = nbp + (1 if self.params.get("show_counter_argument", True) else 0)
            more_romans = ["IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
            label = more_romans[ri2] if ri2 < len(more_romans) else f"{ri2 + 2}"
            pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m, y + 8, f"{label}. Conclusion"); y += 16
            pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*hex_to_rgb(sc))
            for label_text in ["Restate Thesis:", "Summary of Points:", "Final Thought:"]:
                pdf.text(m + 16, y + 6, label_text)
                y += 10; self._set_c(pdf, c, lw * 0.3); pdf.line(m + 16, y, w - m, y); y += 14


    # ── Grand Staff Paper ──
    def _draw_grand_staff_paper(self, pdf, w, h, pg=1):
        ss = self.params["staff_spacing"] * IN_TO_PT
        gs_gap = self.params["group_spacing"] * IN_TO_PT
        nsys = int(self.params["num_systems"])
        c = self.params["color"]; sc = self.params.get("secondary_color", "#666666")
        lw = self.params["line_width"]
        m = 54
        system_h = 10 * ss + gs_gap
        total_h = nsys * system_h
        start_y = max((h - total_h) / 2, m)
        self._set_c(pdf, c, lw)
        for s in range(nsys):
            y = start_y + s * system_h
            if y + 10 * ss > h - 20: break
            for i in range(5):
                pdf.line(m, y + i * ss, w - m, y + i * ss)
            bass_y = y + 6 * ss
            for i in range(5):
                pdf.line(m, bass_y + i * ss, w - m, bass_y + i * ss)
            bstyle = self.params.get("bracket_style", "brace")
            if bstyle == "brace":
                self._set_c(pdf, c, lw * 2)
                pdf.line(m - 6, y, m - 6, bass_y + 4 * ss)
            if self.params.get("show_barlines", False):
                bi = self.params.get("barline_interval", 2.0) * IN_TO_PT
                self._set_c(pdf, c, lw * 0.5)
                bx = m + bi
                while bx < w - m:
                    pdf.line(bx, y, bx, bass_y + 4 * ss); bx += bi

    # ── Dotted Lined ──
    def _draw_dotted_lined(self, pdf, w, h, pg=1):
        ls = self.params["line_spacing"] * IN_TO_PT
        ds = self.params["dot_spacing"] * IN_TO_PT
        dr = self.params["dot_radius"]
        ml = self.params["margin_left"] * IN_TO_PT
        c = self.params["color"]
        dc = self.params.get("dot_color", "#999999")
        lw = self.params["line_width"]; m = 54
        dot_style = self.params.get("dot_style", "filled")
        self._set_c(pdf, c, lw * 0.5)
        y = m
        while y < h - m:
            pdf.line(ml, y, w - m, y)
            y += ls
        # Dots
        rgb = hex_to_rgb(dc)
        pdf.set_fill_color(*rgb); pdf.set_draw_color(*rgb)
        y = m
        while y < h - m:
            xi = ml
            while xi < w - m:
                if dot_style == "filled":
                    pdf.ellipse(xi - dr, y - dr, 2 * dr, 2 * dr, style="F")
                else:
                    pdf.set_line_width(0.4); pdf.ellipse(xi - dr, y - dr, 2 * dr, 2 * dr, style="D")
                xi += ds
            y += ls
        if self.params.get("show_margin_line", True):
            self._set_c(pdf, c, lw); pdf.line(ml, 0, ml, h)

    # ── Weekly Meal Planner ──
    def _draw_weekly_meal_planner(self, pdf, w, h, pg=1):
        c = self.params["color"]; sc = self.params.get("secondary_color", "#16A34A")
        lw = self.params["line_width"]; m = 36
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        meals = ["Breakfast", "Lunch", "Dinner"]
        if self.params.get("show_snack_row", True): meals.append("Snacks")
        num_cols = len(days) + 1
        col_w = (w - 2 * m) / num_cols
        y = m
        if self.params.get("show_week_header", True):
            pdf.set_font("Helvetica", "B", 14); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m, y + 14, "Weekly Meal Planner"); y += 30
        pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(*hex_to_rgb(c))
        for di, day in enumerate(days):
            pdf.text(m + (di + 1) * col_w + 4, y + 10, day)
        self._set_c(pdf, c, lw); pdf.line(m, y + 16, w - m, y + 16); y += 16
        for ci in range(num_cols + 1):
            pdf.line(m + ci * col_w, y, m + ci * col_w, h - m)
        avail_h = h - m - y
        row_h = avail_h / len(meals)
        for mi, meal in enumerate(meals):
            ry = y + mi * row_h
            pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m + 4, ry + row_h / 2 + 2, meal)
            self._set_c(pdf, c, lw * 0.5); pdf.line(m, ry + row_h, w - m, ry + row_h)
            if self.params.get("show_calorie_col", True):
                pdf.set_font("Helvetica", "", 6); pdf.set_text_color(*hex_to_rgb(sc))
                for di in range(len(days)):
                    pdf.text(m + (di + 1) * col_w + 4, ry + 10, "Cal:")

    # ── Sleep Tracker ──
    def _draw_sleep_tracker(self, pdf, w, h, pg=1):
        nd = int(self.params["num_days"])
        rh = self.params["row_height"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#6366F1")
        lw = self.params["line_width"]; m = 36; y = m
        pdf.set_font("Helvetica", "B", 14); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 14, "Sleep Tracker"); y += 28
        cols = ["Day"]
        if self.params.get("show_nap_col", True): cols.append("Nap")
        cols.extend(["Bedtime", "Wake", "Hours"])
        if self.params.get("show_quality_col", True): cols.append("Quality")
        if self.params.get("show_mood_col", True): cols.append("Mood")
        if self.params.get("show_notes_col", True): cols.append("Notes")
        num_cols = len(cols); col_w = (w - 2 * m) / num_cols
        pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(*hex_to_rgb(c))
        for ci, cn in enumerate(cols):
            pdf.text(m + ci * col_w + 4, y + 8, cn)
        y += 14; self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y); y += 2
        for d in range(1, nd + 1):
            if y + rh > h - m: break
            pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m + 4, y + rh / 2 + 2, str(d))
            self._set_c(pdf, c, lw * 0.3); pdf.line(m, y + rh, w - m, y + rh)
            x = m + col_w
            for ci in range(1, num_cols):
                pdf.line(x, y, x, y + rh); x += col_w
            y += rh

    # ── Mood Tracker ──
    def _draw_mood_tracker(self, pdf, w, h, pg=1):
        nd = int(self.params["num_days"])
        gs = self.params["grid_size"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#F59E0B")
        lw = self.params["line_width"]; m = 50; y = m
        pdf.set_font("Helvetica", "B", 14); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 14, "Mood Tracker"); y += 28
        if self.params.get("show_month_header", True):
            pdf.set_font("Helvetica", "", 10); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m, y + 8, "Month: _______________"); y += 18
            self._set_c(pdf, c, lw * 0.5); pdf.line(m, y, w - m, y); y += 6
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        num_cols = 7; col_w = (w - 2 * m) / num_cols; row_h = gs * 2.5
        pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(*hex_to_rgb(c))
        for di, dn in enumerate(day_names):
            pdf.text(m + di * col_w + col_w / 2 - 10, y + 6, dn)
        y += 14; day = 1
        while day <= nd and y + row_h < h - m:
            for di in range(num_cols):
                if day > nd: break
                if self.params.get("show_day_numbers", True):
                    pdf.set_font("Helvetica", "", 7); pdf.set_text_color(*hex_to_rgb(sc))
                    pdf.text(m + di * col_w + col_w / 2 - 3, y + 8, str(day))
                self._set_c(pdf, c, lw * 0.3)
                pdf.rect(m + di * col_w + 2, y + 12, col_w - 4, row_h - 14, style="D")
                day += 1
            y += row_h

    # ── Lesson Plan ──
    def _draw_lesson_plan(self, pdf, w, h, pg=1):
        nper = int(self.params["num_periods"])
        c = self.params["color"]; sc = self.params.get("secondary_color", "#2563EB")
        lw = self.params["line_width"]; m = 36; y = m
        pdf.set_font("Helvetica", "B", 14); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 14, "Lesson Plan"); y += 26
        pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb(sc))
        pdf.text(m, y + 6, "Date:"); self._set_c(pdf, c, lw * 0.5); pdf.line(m + 40, y + 10, m + 220, y + 10)
        pdf.set_text_color(*hex_to_rgb(sc)); pdf.text(w / 2, y + 6, "Subject:")
        pdf.line(w / 2 + 50, y + 10, w - m, y + 10)
        y += 20; self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y); y += 6
        sections = ["Topic / Objective"]
        if self.params.get("show_objectives", True): sections.append("Objectives")
        if self.params.get("show_materials", True): sections.append("Materials")
        sections.append("Activities / Notes")
        if self.params.get("show_assessment", True): sections.append("Assessment")
        if self.params.get("show_homework", True): sections.append("Homework")
        avail_h = h - m - y - 10; per_h = avail_h / nper
        for per in range(1, nper + 1):
            if y + per_h > h - m: break
            pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m, y + 8, f"Period {per}")
            self._set_c(pdf, c, lw * 0.5); pdf.line(m, y + 14, w - m, y + 14); y += 16
            sec_h = (per_h - 16) / len(sections)
            for si, sec_name in enumerate(sections):
                sy = y + si * sec_h
                pdf.set_font("Helvetica", "", 7); pdf.set_text_color(*hex_to_rgb(sc))
                pdf.text(m + 4, sy + 8, sec_name)
                self._set_c(pdf, c, lw * 0.2); pdf.line(m, sy + sec_h, w - m, sy + sec_h)
            y += per_h - 16

    # ── Expense Tracker ──
    def _draw_expense_tracker(self, pdf, w, h, pg=1):
        nr = int(self.params["num_rows"])
        rh = self.params["row_height"] * IN_TO_PT
        hdr_h = self.params.get("header_height", 0.5) * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#DC2626")
        lw = self.params["line_width"]; m = 36; y = m
        pdf.set_font("Helvetica", "B", 14); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 14, "Expense Tracker"); y += 26
        pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb(sc))
        pdf.text(m, y + 6, "Month:"); self._set_c(pdf, c, lw * 0.5)
        pdf.line(m + 45, y + 10, m + 250, y + 10); y += 20
        cols = ["Date", "Description"]
        if self.params.get("show_category_col", True): cols.append("Category")
        cols.append("Amount")
        if self.params.get("show_payment_col", True): cols.append("Payment")
        cols.append("Notes")
        num_cols = len(cols); col_w = (w - 2 * m) / num_cols
        pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(*hex_to_rgb(c))
        for ci, cn in enumerate(cols):
            pdf.text(m + ci * col_w + 4, y + 8, cn)
        y += 12; self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y); y += 2
        for r in range(nr):
            if y + rh > h - m: break
            self._set_c(pdf, c, lw * 0.3); pdf.line(m, y + rh, w - m, y + rh)
            x = m + col_w
            for ci in range(1, num_cols):
                pdf.line(x, y, x, y + rh); x += col_w
            y += rh
        if y + 30 < h - m:
            y += 4; self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y); y += 4
            pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m + col_w * 2.5, y + 8, "Total:")

    # ── Baseball Scorecard ──
    def _draw_baseball_scorecard(self, pdf, w, h, pg=1):
        nin = int(self.params["num_innings"])
        npt = int(self.params["players_per_team"])
        c = self.params["color"]; sc = self.params.get("secondary_color", "#2563EB")
        lw = self.params["line_width"]; m = 30; y = m
        pdf.set_font("Helvetica", "B", 13); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 12, "Baseball Scorecard"); y += 22
        pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb(sc))
        pdf.text(m, y + 6, "Team:"); self._set_c(pdf, c, lw * 0.5)
        pdf.line(m + 40, y + 10, m + 200, y + 10)
        pdf.set_text_color(*hex_to_rgb(sc)); pdf.text(w / 2, y + 6, "Opp:")
        pdf.line(w / 2 + 35, y + 10, w - m, y + 10); y += 20
        stat_cols = self.params.get("stat_columns", "R,H,RBI").split(",")
        total_cols = 2 + nin + len(stat_cols)
        col_w = (w - 2 * m) / total_cols
        pdf.set_font("Helvetica", "B", 7); pdf.set_text_color(*hex_to_rgb(c))
        headers = ["#", "Player"] + [str(i) for i in range(1, nin + 1)] + stat_cols
        for ci, hdr in enumerate(headers):
            pdf.text(m + ci * col_w + 4, y + 8, hdr)
        y += 12; self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y); y += 2
        row_h = self.params.get("row_height", 20)
        for pl in range(npt):
            if y + row_h > h - m: break
            pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m + 4, y + 10, str(pl + 1))
            self._set_c(pdf, c, lw * 0.3); pdf.line(m, y + row_h, w - m, y + row_h)
            x = m + col_w
            for ci in range(1, total_cols):
                pdf.line(x, y, x, y + row_h); x += col_w
            if self.params.get("show_sub_rows", True):
                pdf.line(m, y + row_h + 12, w - m, y + row_h + 12)
                y += row_h + 12
            else:
                y += row_h
        if self.params.get("show_totals_row", True) and y + 20 < h - m:
            self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y)
            pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m + 4, y + 14, "TOTALS")

    # ── Atom Diagram ──
    def _draw_atom_diagram(self, pdf, w, h, pg=1):
        gs = self.params["grid_size"] * IN_TO_PT
        nsh = int(self.params["num_shells"])
        c = self.params["color"]; sc = self.params.get("secondary_color", "#2563EB")
        lw = self.params["line_width"]
        ns = self.params.get("nucleus_size", 0.3) * IN_TO_PT
        m = 50; max_shell_r = gs / 2 - 10
        atoms_w = max(1, int((w - 2 * m) / gs))
        atoms_h = max(1, int((h - 2 * m) / gs))
        total_w = atoms_w * gs; total_h = atoms_h * gs
        sx = (w - total_w) / 2; sy = (h - total_h) / 2
        for row in range(atoms_h):
            for col in range(atoms_w):
                cx = sx + col * gs + gs / 2
                cy = sy + row * gs + gs / 2
                self._set_c(pdf, c, lw * 0.3)
                pdf.rect(sx + col * gs, sy + row * gs, gs, gs, style="D")
                shell_r = max_shell_r / nsh
                self._set_c(pdf, sc, lw * 0.5)
                for s in range(1, nsh + 1):
                    r = shell_r * s
                    pdf.ellipse(cx - r, cy - r, 2 * r, 2 * r, style="D")
                if self.params.get("show_nucleus", True):
                    self._set_c(pdf, c, lw)
                    pdf.set_fill_color(*hex_to_rgb(c))
                    pdf.ellipse(cx - ns / 2, cy - ns / 2, ns, ns, style="DF")
                if self.params.get("show_shell_labels", True):
                    pdf.set_font("Helvetica", "", 6); pdf.set_text_color(*hex_to_rgb(c))
                    shell_names = ["K", "L", "M", "N", "O", "P", "Q"]
                    for s in range(min(nsh, len(shell_names))):
                        r = shell_r * (s + 1)
                        pdf.text(cx + r - 10, cy - 4, shell_names[s])

    # ── Quadrille Paper ──
    def _draw_quadrille_paper(self, pdf, w, h, pg=1):
        gs = self.params["grid_size"] * IN_TO_PT
        major = int(self.params["major_every"])
        c = self.params["color"]; sc = self.params.get("secondary_color", "#AAAAAA")
        lw = self.params["line_width"]; mw = self.params["major_width"]
        dot_mode = self.params.get("dot_mode", False)
        if dot_mode:
            pdf.set_fill_color(*hex_to_rgb(c))
            x = gs * major
            while x < w:
                y = gs * major
                while y < h:
                    mdr = self.params.get("major_dot_radius", 1.0)
                    pdf.ellipse(x - mdr/2, y - mdr/2, mdr, mdr, style="F")
                    y += gs * major
                x += gs * major
            pdf.set_fill_color(*hex_to_rgb(sc))
            mdr2 = self.params.get("minor_dot_radius", 0.5)
            x = gs
            while x < w:
                y = gs
                while y < h:
                    is_major = (int(x / gs) % major == 0 and int(y / gs) % major == 0)
                    if not is_major:
                        pdf.ellipse(x - mdr2/2, y - mdr2/2, mdr2, mdr2, style="F")
                    y += gs
                x += gs
        else:
            self._set_c(pdf, sc, lw)
            x = gs
            while x < w: pdf.line(x, 0, x, h); x += gs
            y = gs
            while y < h: pdf.line(0, y, w, y); y += gs
            self._set_c(pdf, c, mw)
            x = gs * major
            while x < w: pdf.line(x, 0, x, h); x += gs * major
            y = gs * major
            while y < h: pdf.line(0, y, w, y); y += gs * major

    # ── Spiral Grid ──
    def _draw_spiral_grid(self, pdf, w, h, pg=1):
        ns = int(self.params["num_spirals"])
        turns = int(self.params["turns"])
        gs = self.params["grid_size"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#C4B5FD")
        lw = self.params["line_width"]
        show_rad = self.params.get("show_radials", True)
        nrad = int(self.params.get("num_radials", 12))
        cx, cy = w / 2, h / 2
        max_r = min(w, h) / 2 - 20
        # Concentric circles
        self._set_c(pdf, sc, lw * 0.5)
        r = gs
        while r < max_r:
            pdf.ellipse(cx - r, cy - r, 2 * r, 2 * r)
            r += gs
        # Radials
        if show_rad:
            self._set_c(pdf, sc, lw * 0.3)
            for i in range(nrad):
                a = 2 * math.pi * i / nrad
                ex = cx + max_r * math.cos(a)
                ey = cy + max_r * math.sin(a)
                pdf.line(cx, cy, ex, ey)
        # Spirals
        self._set_c(pdf, c, lw)
        for s in range(ns):
            offset = 2 * math.pi * s / ns
            pts = []
            steps = turns * 120
            for i in range(steps + 1):
                t = i / 120.0
                a = offset + t * 2 * math.pi
                r = t * gs * 0.8
                if r > max_r: break
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
            for i in range(len(pts) - 1):
                pdf.line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1])

    # ── Basketball Stat Sheet ──
    def _draw_basketball_stat_sheet(self, pdf, w, h, pg=1):
        nplayers = int(self.params["num_players"])
        nq = int(self.params["num_quarters"])
        stats = self.params.get("stat_categories", "Points,Rebounds,Assists,Steals,Blocks").split(",")
        c = self.params["color"]; sc = self.params.get("secondary_color", "#EA580C")
        lw = self.params["line_width"]; m = 30; y = m
        tfs = int(self.params.get("title_font_size", 16))
        pdf.set_font("Helvetica", "B", tfs); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 14, "Basketball Stat Sheet"); y += 28
        pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb(sc))
        pdf.text(m, y + 6, "Date:"); self._set_c(pdf, sc, lw * 0.5)
        pdf.line(m + 35, y + 10, m + 150, y + 10)
        pdf.text(m + 170, y + 6, "Opponent:")
        pdf.line(m + 230, y + 10, m + 350, y + 10)
        pdf.text(m + 370, y + 6, "Location:")
        pdf.line(m + 425, y + 10, m + 540, y + 10); y += 22
        cols = ["#", "Player"]
        for q in range(1, nq + 1):
            for st in stats:
                cols.append(f"Q{q} {st.strip()[:3]}")
        cols.append("TOT")
        ncols = len(cols); col_w = (w - 2 * m) / ncols
        pdf.set_font("Helvetica", "B", 6); pdf.set_text_color(*hex_to_rgb(c))
        for ci, cn in enumerate(cols):
            pdf.text(m + ci * col_w + 2, y + 8, cn)
        y += 12; self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y); y += 2
        pdf.set_font("Helvetica", "", 7)
        rh = self.params.get("row_height", 16)
        for r in range(nplayers):
            if y + rh > h - m: break
            self._set_c(pdf, c, lw * 0.3); pdf.line(m, y + rh, w - m, y + rh)
            for ci in range(1, ncols):
                x = m + ci * col_w
                pdf.line(x, y, x, y + rh)
            pdf.set_text_color(*hex_to_rgb(sc)); pdf.set_font("Helvetica", "", 7)
            pdf.text(m + 2, y + 10, str(r + 1))
            y += rh
        if self.params.get("show_totals", True) and y + 18 < h - m:
            self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y); y += 2
            pdf.set_font("Helvetica", "B", 7); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m + col_w * 0.5, y + 8, "TEAM TOTALS")

    # ── Chore Chart ──
    def _draw_chore_chart(self, pdf, w, h, pg=1):
        nchores = int(self.params["num_chores"])
        dm = self.params.get("days_mode", "weekday")
        c = self.params["color"]; sc = self.params.get("secondary_color", "#16A34A")
        lw = self.params["line_width"]; m = 36
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] if dm == "weekday" else [f"Day {i}" for i in range(1, 8)]
        show_pts = self.params.get("show_points_col", True)
        show_pi = self.params.get("show_parent_initials", False)
        num_data_cols = len(days) + (1 if show_pts else 0) + (1 if show_pi else 0)
        clw = self.params.get("label_column_width", 120)
        cbs = self.params.get("checkbox_size", 10)
        mrh = self.params.get("min_row_height", 18)
        col_w = (w - 2 * m - clw) / num_data_cols; y = m
        pdf.set_font("Helvetica", "B", 16); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 14, "Weekly Chore Chart"); y += 28
        pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb(sc))
        pdf.text(m, y + 6, "Week of:"); self._set_c(pdf, sc, lw * 0.5)
        pdf.line(m + 55, y + 10, m + 200, y + 10); y += 22
        pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m + 40, y + 10, "Chore")
        for ci, d in enumerate(days):
            pdf.text(m + clw + ci * col_w + 4, y + 10, d)
        off = len(days)
        if show_pts: pdf.text(m + clw + off * col_w + 4, y + 10, "Pts"); off += 1
        if show_pi: pdf.text(m + clw + off * col_w + 4, y + 10, "Initials")
        y += 16; self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y); y += 2
        row_h = max(mrh, (h - y - m) / max(nchores, 1))
        for r in range(nchores):
            if y + row_h > h - m: break
            self._set_c(pdf, c, lw * 0.3)
            pdf.line(m, y + row_h, w - m, y + row_h)
            pdf.line(m + clw, y, m + clw, y + row_h)
            for ci in range(1, num_data_cols):
                x = m + clw + ci * col_w
                pdf.line(x, y, x, y + row_h)
            # Checkboxes
            self._set_c(pdf, sc, lw * 0.5)
            for ci in range(min(num_data_cols, len(days))):
                cx = m + 120 + ci * col_w + col_w / 2 - 4
                cy = y + row_h / 2 - 4
                pdf.rect(cx, cy, cbs, cbs)
            y += row_h

    # ── Water Intake Tracker ──
    def _draw_water_intake_tracker(self, pdf, w, h, pg=1):
        nd = int(self.params["num_days"])
        tgt = int(self.params["glasses_target"])
        c = self.params["color"]; sc = self.params.get("secondary_color", "#0EA5E9")
        lw = self.params["line_width"]; m = 36
        show_notes = self.params.get("show_notes_col", True)
        y = m
        pdf.set_font("Helvetica", "B", 16); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 14, "Water Intake Tracker"); y += 24
        pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb(sc))
        oz = self.params.get("glass_size_oz", 8)
        pdf.text(m, y + 6, f"Goal: {tgt} glasses/day ({oz} oz each)"); y += 20
        notes_w = 120 if show_notes else 0
        total_w = 80; day_w = 80
        avail = w - 2 * m - day_w - total_w - notes_w - 20
        cb_size = min(18, avail / max(tgt, 1))
        row_h = max(24, cb_size + 8)
        pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(*hex_to_rgb(c))
        x = m
        pdf.text(x + 20, y + 10, "Day"); x += day_w
        for g in range(1, tgt + 1):
            pdf.text(x + cb_size/2 - 2, y + 10, str(g)); x += cb_size
        pdf.text(x + 20, y + 10, "Total"); x += total_w
        if show_notes: pdf.text(x + 20, y + 10, "Notes")
        y += 16; self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y); y += 2
        for r in range(nd):
            if y + row_h > h - m: break
            self._set_c(pdf, c, lw * 0.3); pdf.line(m, y + row_h, w - m, y + row_h)
            pdf.line(m + day_w, y, m + day_w, y + row_h)
            if show_notes:
                x_note = m + day_w + tgt * cb_size + total_w
                pdf.line(x_note, y, x_note, y + row_h)
            pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m + 20, y + row_h/2 + 3, f"Day {r+1}")
            # Circles for glasses
            self._set_c(pdf, sc, lw * 0.4)
            for g in range(tgt):
                cx = m + day_w + g * cb_size + cb_size / 2
                cy = y + row_h / 2
                pdf.ellipse(cx - 4, cy - 4, 8, 8)
            y += row_h
        if self.params.get("show_total_row", True) and y + 20 < h - m:
            self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y); y += 3
            pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m + day_w + tgt * cb_size - 80, y + 8, "Weekly Total:")

    # ── Phone Call Log ──
    def _draw_phone_call_log(self, pdf, w, h, pg=1):
        nr = int(self.params["num_rows"])
        rh = self.params["row_height"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#2563EB")
        lw = self.params["line_width"]; m = 36; y = m
        pdf.set_font("Helvetica", "B", 16); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 14, "Phone Call Log"); y += 26
        pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb(sc))
        pdf.text(m, y + 6, "Month/Year:"); self._set_c(pdf, sc, lw * 0.5)
        pdf.line(m + 80, y + 10, m + 200, y + 10); y += 22
        cols = ["Date/Time", "Contact", "Phone #", "Type"]
        if self.params.get("show_duration_col", True): cols.append("Duration")
        if self.params.get("show_outcome_col", True): cols.append("Outcome")
        if self.params.get("show_followup_col", True): cols.append("Follow-Up")
        ncols = len(cols); col_w = (w - 2 * m) / ncols
        pdf.set_font("Helvetica", "B", 7); pdf.set_text_color(*hex_to_rgb(c))
        for ci, cn in enumerate(cols):
            pdf.text(m + ci * col_w + 4, y + 8, cn)
        y += 12; self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y); y += 2
        for r in range(nr):
            if y + rh > h - m: break
            self._set_c(pdf, c, lw * 0.3); pdf.line(m, y + rh, w - m, y + rh)
            for ci in range(1, ncols):
                x = m + ci * col_w
                pdf.line(x, y, x, y + rh)
            y += rh

    # ── Blood Pressure Log ──
    def _draw_blood_pressure_log(self, pdf, w, h, pg=1):
        nr = int(self.params["num_rows"])
        rh = self.params["row_height"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#DC2626")
        lw = self.params["line_width"]; m = 36; y = m
        pdf.set_font("Helvetica", "B", 16); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 14, "Blood Pressure Log"); y += 26
        if self.params.get("show_header_info", True):
            pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m, y + 6, "Name:"); self._set_c(pdf, sc, lw * 0.5)
            pdf.line(m + 40, y + 10, m + 200, y + 10)
            pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m + 250, y + 6, "Doctor:")
            pdf.line(m + 290, y + 10, m + 440, y + 10); y += 22
        cols = ["Date/Time" if self.params.get("show_date_time", True) else "Date", "Systolic", "Diastolic"]
        if self.params.get("show_pulse_col", True): cols.append("Pulse")
        cols.append("Notes")
        ncols = len(cols); col_w = (w - 2 * m) / ncols
        pdf.set_font("Helvetica", "B", 7); pdf.set_text_color(*hex_to_rgb(c))
        for ci, cn in enumerate(cols):
            pdf.text(m + ci * col_w + 4, y + 8, cn)
        y += 12; self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y); y += 2
        for r in range(nr):
            if y + rh > h - m: break
            self._set_c(pdf, c, lw * 0.3); pdf.line(m, y + rh, w - m, y + rh)
            for ci in range(1, ncols):
                x = m + ci * col_w
                pdf.line(x, y, x, y + rh)
            y += rh
        # BP zones legend
        if y + 40 < h - m:
            y += 8; pdf.set_font("Helvetica", "", 6); pdf.set_text_color(*hex_to_rgb(c))
            zones = [("Normal: <120/<80", (22, 163, 74)), ("Elevated: 120-129/<80", (245, 158, 11)),
                     ("High S1: 130-139/80-89", (234, 88, 12)), ("High S2: >=140/>=90", (220, 38, 38))]
            for zi, (zt, zc) in enumerate(zones):
                xz = m + zi * 130
                pdf.set_fill_color(*zc)
                pdf.rect(xz, y, 8, 8, style="F")
                pdf.set_text_color(*hex_to_rgb(c))
                pdf.text(xz + 12, y + 6, zt)

    # ── SWOT Analysis ──
    def _draw_swot_analysis(self, pdf, w, h, pg=1):
        c = self.params["color"]; sc = self.params.get("secondary_color", "#2563EB")
        lw = self.params["line_width"]; m = 36
        hdr_h = self.params.get("header_height", 0.4) * IN_TO_PT
        nlines = int(self.params.get("lines_per_section", 8))
        y = m
        pdf.set_font("Helvetica", "B", 16); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 14, "SWOT Analysis"); y += 26
        pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb(sc))
        pdf.text(m, y + 6, "Topic / Project:"); self._set_c(pdf, sc, lw * 0.5)
        pdf.line(m + 90, y + 10, w - m - 20, y + 10); y += 24
        qw = (w - 2 * m) / 2; qh = (h - y - m) / 2
        labels = ["S - Strengths", "W - Weaknesses", "O - Opportunities", "T - Threats"]
        label_colors = [sc, "#DC2626", "#16A34A", "#F59E0B"]
        positions = [(m, y), (m + qw, y), (m, y + qh), (m + qw, y + qh)]
        line_sp = (qh - hdr_h - 10) / max(nlines, 1)
        for qi, ((qx, qy), label, lc) in enumerate(zip(positions, labels, label_colors)):
            self._set_c(pdf, c, lw); pdf.rect(qx, qy, qw, qh)
            # Header shading
            r2, g2, b2 = hex_to_rgb(lc)
            pdf.set_fill_color(r2, g2, b2); pdf.rect(qx, qy, qw, hdr_h, style="F")
            if self.params.get("show_headers", True):
                pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(255, 255, 255)
                pdf.text(qx + 8, qy + hdr_h / 2 + 4, label)
            if self.params.get("show_prompt_lines", True):
                self._set_c(pdf, c, lw * 0.3)
                ly = qy + hdr_h + line_sp
                for li in range(nlines):
                    if ly + line_sp > qy + qh - 4: break
                    pdf.line(qx + 8, ly, qx + qw - 8, ly)
                    ly += line_sp

    # ── Doodle Pad ──
    def _draw_doodle_pad(self, pdf, w, h, pg=1):
        c = self.params["color"]; sc = self.params.get("secondary_color", "#E5E7EB")
        lw = self.params["line_width"]
        density_map = {"light": 0.3, "medium": 0.6, "heavy": 1.0}
        density = density_map.get(self.params.get("density", "medium"), 0.6)
        shapes = self.params.get("shape_types", "circles,squares,triangles").split(",")
        m = self.params.get("margin", 0.33) * IN_TO_PT
        min_sz = self.params.get("min_shape_size", 8)
        max_sz = self.params.get("max_shape_size", 38)
        if self.params.get("show_border_frame", True):
            self._set_c(pdf, c, lw); pdf.rect(m, m, w - 2*m, h - 2*m)
        seed = 42
        def rng():
            nonlocal seed
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            return seed / 0x7FFFFFFF
        self._set_c(pdf, c, lw * 0.5)
        num_shapes = int(density * 60)
        inner_w = w - 2*m - 20; inner_h = h - 2*m - 20
        for i in range(num_shapes):
            sx = m + 10 + rng() * inner_w
            sy = m + 10 + rng() * inner_h
            size = min_sz + rng() * (max_sz - min_sz)
            shape = shapes[i % len(shapes)].strip()
            if shape == "circles":
                pdf.ellipse(sx - size/2, sy - size/2, size, size)
            elif shape == "squares":
                pdf.rect(sx - size/2, sy - size/2, size, size)
            elif shape == "triangles":
                pts = [(sx, sy - size/2), (sx - size/2, sy + size/2), (sx + size/2, sy + size/2), (sx, sy - size/2)]
                pdf.polygon(pts)

    # ── Comic Panel Layout ──
    def _draw_comic_panel_layout(self, pdf, w, h, pg=1):
        style = self.params.get("layout_style", "classic")
        nrows = int(self.params.get("num_rows", 3))
        gw = self.params.get("gutter_width", 0.15) * IN_TO_PT
        pbw = self.params.get("panel_border_width", 1.5)
        c = self.params["color"]; sc = self.params.get("secondary_color", "#94A3B8")
        lw = self.params["line_width"]; m = 24
        if style == "classic":
            row_configs = []
            for r in range(nrows):
                if r % 3 == 2 and r > 0:
                    row_configs.append([1.0])
                else:
                    row_configs.append([0.5, 0.5])
        elif style == "grid":
            row_configs = [[0.5, 0.5] for _ in range(nrows)]
        else:
            patterns = [[0.6, 0.4], [0.33, 0.34, 0.33], [1.0], [0.4, 0.6]]
            row_configs = [patterns[r % len(patterns)] for r in range(nrows)]
        avail_w = w - 2 * m; avail_h = h - 2 * m
        row_h = avail_h / max(len(row_configs), 1)
        y = m
        for ri, row in enumerate(row_configs):
            x = m; npanels = len(row)
            for pi, ratio in enumerate(row):
                pw = (avail_w - gw * (npanels - 1)) * ratio
                ph = row_h - gw
                self._set_c(pdf, c, pbw)
                pdf.rect(x, y, pw, ph)
                if self.params.get("show_gutter_labels", False):
                    pdf.set_font("Helvetica", "", 7); pdf.set_text_color(*hex_to_rgb(sc))
                    pdf.text(x + 3, y + 8, f"P{ri*npanels+pi+1}")
                x += pw + gw
            y += row_h

    # ── Gardening Planner ──
    def _draw_gardening_planner(self, pdf, w, h, pg=1):
        nbeds = int(self.params["num_beds"])
        gs = self.params["grid_size"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#16A34A")
        lw = self.params["line_width"]; m = 30; y = m
        pdf.set_font("Helvetica", "B", 16); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 14, "Gardening Planner"); y += 24
        pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb(sc))
        pdf.text(m, y + 6, "Season:"); self._set_c(pdf, sc, lw * 0.5)
        pdf.line(m + 50, y + 10, m + 180, y + 10)
        pdf.set_text_color(*hex_to_rgb(sc))
        pdf.text(m + 220, y + 6, "Year:")
        pdf.line(m + 260, y + 10, m + 380, y + 10); y += 22
        beds_per_row = min(nbeds, 2)
        num_bed_rows = math.ceil(nbeds / beds_per_row)
        bed_w = (w - 2 * m - 20) / beds_per_row
        extra = 100 if self.params.get("show_plant_list", True) else 0
        bed_h = min(bed_w * 0.75, (h - y - m - extra) / max(num_bed_rows, 1))
        bed_h = max(bed_h, 80)
        for bi in range(nbeds):
            br = bi // beds_per_row; bc = bi % beds_per_row
            bx = m + bc * (bed_w + 20); by = y + br * (bed_h + 16)
            if by + bed_h > h - m - 60: break
            self._set_c(pdf, c, lw); pdf.rect(bx, by, bed_w, bed_h)
            pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(bx + 4, by + 10, f"Bed {bi+1}")
            self._set_c(pdf, sc, lw * 0.3)
            gx = bx + gs
            while gx < bx + bed_w:
                pdf.line(gx, by, gx, by + bed_h); gx += gs
            gy = by + gs
            while gy < by + bed_h:
                pdf.line(bx, gy, bx + bed_w, gy); gy += gs
        y_next = y + num_bed_rows * (bed_h + 16) + 10
        if self.params.get("show_plant_list", True) and y_next + 60 < h - m:
            pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m, y_next + 10, "Plant List"); y_next += 16
            plrows = int(self.params.get("plant_list_rows", 10))
            plrh = 14
            cols_pl = ["Plant", "Variety", "Qty", "Plant Date", "Harvest"]
            col_w_pl = (w - 2 * m) / len(cols_pl)
            pdf.set_font("Helvetica", "B", 7); pdf.set_text_color(*hex_to_rgb(c))
            for ci, cn in enumerate(cols_pl):
                pdf.text(m + ci * col_w_pl + 4, y_next + 8, cn)
            y_next += 12; self._set_c(pdf, c, lw * 0.5); pdf.line(m, y_next, w - m, y_next); y_next += 2
            for r in range(plrows):
                if y_next + plrh > h - m: break
                self._set_c(pdf, c, lw * 0.2); pdf.line(m, y_next + plrh, w - m, y_next + plrh)
                for ci in range(1, len(cols_pl)):
                    x = m + ci * col_w_pl
                    pdf.line(x, y_next, x, y_next + plrh)
                y_next += plrh

    # ── Timeline ──
    def _draw_timeline(self, pdf, w, h, pg=1):
        orient = self.params.get("orientation", "horizontal")
        ne = int(self.params["num_events"])
        ms = self.params["marker_size"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#93C5FD")
        lw = self.params["line_width"]; m = 36
        show_dates = self.params.get("show_date_fields", True)
        arrow = self.params.get("arrow_style", True)
        pdf.set_font("Helvetica", "B", 14); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, m + 14, "Timeline")
        if orient == "horizontal":
            y_line = h / 2; x_start = m + 40; x_end = w - m - 20
            self._set_c(pdf, c, lw); pdf.line(x_start, y_line, x_end, y_line)
            if arrow:
                pdf.line(x_end - 10, y_line - 6, x_end, y_line)
                pdf.line(x_end - 10, y_line + 6, x_end, y_line)
            spacing = (x_end - x_start) / max(ne, 1)
            for i in range(ne):
                ex = x_start + i * spacing + spacing / 2
                self._set_c(pdf, c, lw); pdf.ellipse(ex - ms/2, y_line - ms/2, ms, ms)
                self._set_c(pdf, c, lw * 0.5)
                if i % 2 == 0:
                    pdf.line(ex, y_line + ms/2, ex, y_line + ms/2 + 20)
                    if show_dates:
                        pdf.set_font("Helvetica", "", 7); pdf.set_text_color(*hex_to_rgb(c))
                        pdf.text(ex - 20, y_line + ms/2 + 32, "Date")
                else:
                    pdf.line(ex, y_line - ms/2 - 20, ex, y_line - ms/2)
                    if show_dates:
                        pdf.set_font("Helvetica", "", 7); pdf.set_text_color(*hex_to_rgb(c))
                        pdf.text(ex - 20, y_line - ms/2 - 22, "Date")
        else:
            x_line = m + 60; y_start = m + 40; y_end = h - m - 20
            self._set_c(pdf, c, lw); pdf.line(x_line, y_start, x_line, y_end)
            if arrow:
                pdf.line(x_line - 6, y_end - 10, x_line, y_end)
                pdf.line(x_line + 6, y_end - 10, x_line, y_end)
            spacing = (y_end - y_start) / max(ne, 1)
            for i in range(ne):
                ey = y_start + i * spacing + spacing / 2
                self._set_c(pdf, c, lw); pdf.ellipse(x_line - ms/2, ey - ms/2, ms, ms)
                self._set_c(pdf, c, lw * 0.5)
                pdf.line(x_line + ms/2, ey, x_line + ms/2 + 20, ey)
                if show_dates:
                    pdf.set_font("Helvetica", "", 7); pdf.set_text_color(*hex_to_rgb(c))
                    pdf.text(x_line + ms/2 + 24, ey + 3, "Date")

    # ── Insect Observation Log ──
    def _draw_insect_observation_log(self, pdf, w, h, pg=1):
        nr = int(self.params["num_rows"]); rh = self.params["row_height"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#16A34A")
        lw = self.params["line_width"]; m = 30; y = m
        pdf.set_font("Helvetica", "B", 14); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 14, "Insect Observation Log"); y += 24
        pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb(sc))
        pdf.text(m, y + 6, "Location:"); self._set_c(pdf, sc, lw * 0.5)
        pdf.line(m + 60, y + 10, m + 200, y + 10)
        pdf.set_text_color(*hex_to_rgb(sc)); pdf.text(m + 250, y + 6, "Date:")
        pdf.line(m + 285, y + 10, m + 420, y + 10); y += 20
        cols = ["#", "Species", "Date/Time"]
        if self.params.get("show_habitat_col", True): cols.append("Habitat")
        if self.params.get("show_behavior_col", True): cols.append("Behavior")
        if self.params.get("show_weather_col", True): cols.append("Weather")
        ncols = len(cols)
        draw_w = rh if self.params.get("show_drawing_area", True) else 0
        col_w = (w - 2 * m - draw_w) / ncols
        pdf.set_font("Helvetica", "B", 7); pdf.set_text_color(*hex_to_rgb(c))
        for ci, cn in enumerate(cols):
            pdf.text(m + ci * col_w + 4, y + 8, cn)
        if draw_w: pdf.text(w - m - draw_w + 4, y + 8, "Drawing")
        y += 12; self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y); y += 2
        for r in range(nr):
            if y + rh > h - m: break
            self._set_c(pdf, c, lw * 0.3); pdf.line(m, y + rh, w - m, y + rh)
            for ci in range(1, ncols):
                x = m + ci * col_w; pdf.line(x, y, x, y + rh)
            if draw_w: pdf.line(w - m - draw_w, y, w - m - draw_w, y + rh)
            y += rh

    # ── Medication Log ──
    def _draw_medication_log(self, pdf, w, h, pg=1):
        nr = int(self.params["num_rows"]); rh = self.params["row_height"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#7C3AED")
        lw = self.params["line_width"]; m = 30; y = m
        pdf.set_font("Helvetica", "B", 14); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 14, "Medication Log"); y += 24
        if self.params.get("show_header_info", True):
            pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m, y + 6, "Patient:"); self._set_c(pdf, sc, lw * 0.5)
            pdf.line(m + 50, y + 10, m + 200, y + 10)
            pdf.set_text_color(*hex_to_rgb(sc)); pdf.text(m + 250, y + 6, "Doctor:")
            pdf.line(m + 295, y + 10, m + 440, y + 10); y += 20
        cols = ["Date", "Medication"]
        if self.params.get("show_time_col", True): cols.append("Time")
        if self.params.get("show_dosage_col", True): cols.append("Dosage")
        cols.append("Taken")
        if self.params.get("show_notes_col", True): cols.append("Notes")
        ncols = len(cols); col_w = (w - 2 * m) / ncols
        pdf.set_font("Helvetica", "B", 7); pdf.set_text_color(*hex_to_rgb(c))
        for ci, cn in enumerate(cols):
            pdf.text(m + ci * col_w + 4, y + 8, cn)
        y += 12; self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y); y += 2
        for r in range(nr):
            if y + rh > h - m: break
            self._set_c(pdf, c, lw * 0.3); pdf.line(m, y + rh, w - m, y + rh)
            for ci in range(1, ncols):
                x = m + ci * col_w; pdf.line(x, y, x, y + rh)
            taken_idx = cols.index("Taken")
            cx = m + taken_idx * col_w + col_w / 2 - 4
            cy = y + rh / 2 - 4
            self._set_c(pdf, sc, lw * 0.5); pdf.rect(cx, cy, 8, 8)
            y += rh

    # ── Number Bonds ──
    def _draw_number_bonds(self, pdf, w, h, pg=1):
        np = int(self.params["num_problems"])
        c = self.params["color"]; sc = self.params.get("secondary_color", "#F59E0B")
        lw = self.params["line_width"]; m = 40
        layout = self.params.get("problem_layout", "2x5")
        cols_l, rows_l = (5, 2) if layout == "2x5" else (4, 3)
        pdf.set_font("Helvetica", "B", 14); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, m + 14, "Number Bonds")
        y_start = m + 30
        cell_w = (w - 2 * m) / cols_l; cell_h = (h - y_start - m) / max(rows_l, 1)
        r = min(cell_w, cell_h) * 0.22
        for idx in range(min(np, cols_l * rows_l)):
            row = idx // cols_l; col = idx % cols_l
            cx = m + col * cell_w + cell_w / 2
            cy = y_start + row * cell_h + cell_h / 2
            self._set_c(pdf, c, lw)
            pdf.ellipse(cx - r, cy - r * 2.5, r * 2, r * 2)
            pdf.ellipse(cx - r * 2.5, cy + r * 0.5, r * 2, r * 2)
            pdf.ellipse(cx + r * 0.5, cy + r * 0.5, r * 2, r * 2)
            pdf.line(cx, cy - r * 0.5, cx - r, cy + r * 0.5)
            pdf.line(cx, cy - r * 0.5, cx + r, cy + r * 0.5)
            if self.params.get("show_addition", True):
                pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*hex_to_rgb(sc))
                pdf.text(cx + r * 2.5, cy + r + 3, "+  =")

    # ── Stargazing Log ──
    def _draw_stargazing_log(self, pdf, w, h, pg=1):
        nr = int(self.params["num_rows"]); rh = self.params["row_height"] * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#1E3A5F")
        lw = self.params["line_width"]; m = 30; y = m
        pdf.set_font("Helvetica", "B", 14); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 14, "Stargazing Log"); y += 24
        pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb(sc))
        pdf.text(m, y + 6, "Location:"); self._set_c(pdf, sc, lw * 0.5)
        pdf.line(m + 60, y + 10, m + 200, y + 10)
        pdf.set_text_color(*hex_to_rgb(sc)); pdf.text(m + 250, y + 6, "Date:")
        pdf.line(m + 285, y + 10, m + 420, y + 10); y += 20
        cols = ["#", "Object", "Date/Time"]
        if self.params.get("show_constellation_col", True): cols.append("Constellation")
        if self.params.get("show_magnitude_col", True): cols.append("Mag")
        if self.params.get("show_weather_col", True): cols.append("Conditions")
        ncols = len(cols)
        draw_w = rh if self.params.get("show_drawing_area", True) else 0
        col_w = (w - 2 * m - draw_w) / ncols
        pdf.set_font("Helvetica", "B", 7); pdf.set_text_color(*hex_to_rgb(c))
        for ci, cn in enumerate(cols):
            pdf.text(m + ci * col_w + 4, y + 8, cn)
        if draw_w: pdf.text(w - m - draw_w + 4, y + 8, "Sketch")
        y += 12; self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y); y += 2
        for r in range(nr):
            if y + rh > h - m: break
            self._set_c(pdf, c, lw * 0.3); pdf.line(m, y + rh, w - m, y + rh)
            for ci in range(1, ncols):
                x = m + ci * col_w; pdf.line(x, y, x, y + rh)
            if draw_w: pdf.line(w - m - draw_w, y, w - m - draw_w, y + rh)
            y += rh

    # ── Writing Sprint Tracker ──
    def _draw_writing_sprint_tracker(self, pdf, w, h, pg=1):
        ns = int(self.params["num_sprints"])
        tw = int(self.params.get("target_words", 1667))
        c = self.params["color"]; sc = self.params.get("secondary_color", "#DC2626")
        lw = self.params["line_width"]; m = 36; y = m
        pdf.set_font("Helvetica", "B", 14); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 14, "Writing Sprint Tracker"); y += 24
        if self.params.get("show_project_name", True):
            pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m, y + 6, "Project:"); self._set_c(pdf, sc, lw * 0.5)
            pdf.line(m + 55, y + 10, w - m - 20, y + 10); y += 20
        pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*hex_to_rgb(sc))
        pdf.text(m, y + 6, f"Daily Target: {tw} words"); y += 18
        cols = ["#", "Start", "End", "Words"]
        if self.params.get("show_cumulative", True): cols.append("Cumulative")
        if self.params.get("show_daily_total", True): cols.append("Notes")
        ncols = len(cols); col_w = (w - 2 * m) / ncols
        pdf.set_font("Helvetica", "B", 7); pdf.set_text_color(*hex_to_rgb(c))
        for ci, cn in enumerate(cols):
            pdf.text(m + ci * col_w + 4, y + 8, cn)
        y += 12; self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y); y += 2
        row_h = 16
        for r in range(ns):
            if y + row_h > h - m: break
            self._set_c(pdf, c, lw * 0.3); pdf.line(m, y + row_h, w - m, y + row_h)
            for ci in range(1, ncols):
                x = m + ci * col_w; pdf.line(x, y, x, y + row_h)
            pdf.set_font("Helvetica", "", 7); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m + 4, y + 10, str(r + 1)); y += row_h
        if self.params.get("show_daily_total", True) and y + 22 < h - m:
            self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y); y += 3
            pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m + col_w, y + 8, "Daily Total:")

    # ── Attendance Register ──
    def _draw_attendance_register(self, pdf, w, h, pg=1):
        nst = int(self.params["num_students"]); ndays = int(self.params["num_days"])
        c = self.params["color"]; sc = self.params.get("secondary_color", "#16A34A")
        lw = self.params["line_width"]; m = 24; y = m
        pdf.set_font("Helvetica", "B", 12); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 12, "Attendance Register"); y += 22
        pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*hex_to_rgb(sc))
        pdf.text(m, y + 6, "Class:"); self._set_c(pdf, sc, lw * 0.5)
        pdf.line(m + 40, y + 10, m + 180, y + 10)
        pdf.set_text_color(*hex_to_rgb(sc)); pdf.text(m + 220, y + 6, "Month:")
        pdf.line(m + 260, y + 10, m + 400, y + 10); y += 20
        id_w = 40 if self.params.get("show_student_id", True) else 0
        name_w = 120; total_w = 50 if self.params.get("show_totals_col", True) else 0
        day_w = (w - 2 * m - id_w - name_w - total_w) / max(ndays, 1)
        # Header
        x = m; pdf.set_font("Helvetica", "B", 6); pdf.set_text_color(*hex_to_rgb(c))
        if id_w: pdf.text(x + 4, y + 8, "ID"); x += id_w
        pdf.text(x + 4, y + 8, "Student Name"); x += name_w
        for d in range(1, ndays + 1):
            pdf.text(x + day_w/2 - 4, y + 8, str(d)); x += day_w
        if total_w: pdf.text(x + 4, y + 8, "Total")
        y += 12; self._set_c(pdf, c, lw); pdf.line(m, y, m + id_w + name_w + ndays * day_w + total_w, y); y += 2
        row_h = max(14, (h - y - m - 16) / max(nst, 1))
        for r in range(nst):
            if y + row_h > h - m: break
            self._set_c(pdf, c, lw * 0.3)
            pdf.line(m, y + row_h, m + id_w + name_w + ndays * day_w + total_w, y + row_h)
            x = m
            if id_w: x += id_w
            pdf.line(x, y, x, y + row_h); x += name_w
            for d in range(ndays):
                pdf.line(x, y, x, y + row_h); x += day_w
            if total_w: pdf.line(x, y, x, y + row_h)
            if r % 2 == 1:
                r2, g2, b2 = hex_to_rgb(sc)
                pdf.set_fill_color(r2, g2, b2)
                pdf.rect(m, y, id_w + name_w + ndays * day_w + total_w, row_h, style="F")
            y += row_h
        if self.params.get("show_absence_codes", True) and y + 14 < h - m:
            y += 4; pdf.set_font("Helvetica", "", 6); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m, y + 4, "P=Present  A=Absent  T=Tardy  E=Excused")

    # ── Chess Score Sheet ──
    def _draw_chess_score_sheet(self, pdf, w, h, pg=1):
        nr = int(self.params["num_rows"])
        mw_col = self.params.get("move_number_width", 0.5) * IN_TO_PT
        c = self.params["color"]; sc = self.params.get("secondary_color", "#78716C")
        lw = self.params["line_width"]; m = self.params.get("margin", 0.5) * IN_TO_PT; y = m
        row_h = self.params.get("row_height", 14)
        lfs = int(self.params.get("label_font_size", 7))
        if self.params.get("show_player_names", True):
            pdf.set_font("Helvetica", "B", 12); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m, y + 12, "White:"); self._set_c(pdf, sc, lw * 0.5)
            pdf.line(m + 45, y + 14, w / 2 - m, y + 14)
            pdf.set_text_color(*hex_to_rgb(c)); pdf.text(w / 2, y + 12, "Black:")
            self._set_c(pdf, sc, lw * 0.5)
            pdf.line(w / 2 + 45, y + 14, w - m, y + 14); y += 24
        if self.params.get("show_date_location", True):
            pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m, y + 6, "Date:"); self._set_c(pdf, sc, lw * 0.5)
            pdf.line(m + 35, y + 10, m + 150, y + 10)
            pdf.set_text_color(*hex_to_rgb(sc)); pdf.text(m + 180, y + 6, "Location:")
            pdf.line(m + 245, y + 10, m + 380, y + 10); y += 20
        half_w = (w - 2 * m - mw_col) / 2
        pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m + mw_col + 4, y + 8, "White")
        pdf.text(m + mw_col + half_w + 4, y + 8, "Black")
        pdf.text(m + 4, y + 8, "#")
        y += 12; self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y)
        pdf.line(m + mw_col, y - 12, m + mw_col, y + nr * row_h)
        pdf.line(m + mw_col + half_w, y - 14, m + mw_col + half_w, y + nr * row_h)
        y += 2
        for r in range(nr):
            if y + row_h > h - m: break
            self._set_c(pdf, c, lw * 0.3); pdf.line(m, y + row_h, w - m, y + row_h)
            pdf.set_font("Helvetica", "", lfs); pdf.set_text_color(*hex_to_rgb(sc))
            pdf.text(m + 4, y + 10, str(r + 1)); y += row_h

    # ── Wish List ──
    def _draw_wish_list(self, pdf, w, h, pg=1):
        nr = int(self.params["num_rows"])
        c = self.params["color"]; sc = self.params.get("secondary_color", "#EC4899")
        lw = self.params["line_width"]; m = 36; y = m
        pdf.set_font("Helvetica", "B", 14); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 14, "Wish List"); y += 24
        pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb(sc))
        pdf.text(m, y + 6, "For:"); self._set_c(pdf, sc, lw * 0.5)
        pdf.line(m + 30, y + 10, m + 200, y + 10)
        pdf.set_text_color(*hex_to_rgb(sc)); pdf.text(m + 250, y + 6, "Occasion:")
        pdf.line(m + 310, y + 10, m + 480, y + 10); y += 22
        cols = ["#", "Item"]
        if self.params.get("show_priority_col", True): cols.append("Priority")
        if self.params.get("show_price_col", True): cols.append("Price")
        if self.params.get("show_store_col", True): cols.append("Store/Link")
        if self.params.get("show_status_col", True): cols.append("Status")
        if self.params.get("show_notes_col", True): cols.append("Notes")
        ncols = len(cols); col_w = (w - 2 * m) / ncols
        pdf.set_font("Helvetica", "B", 7); pdf.set_text_color(*hex_to_rgb(c))
        for ci, cn in enumerate(cols):
            pdf.text(m + ci * col_w + 4, y + 8, cn)
        y += 12; self._set_c(pdf, c, lw); pdf.line(m, y, w - m, y); y += 2
        for r in range(nr):
            if y + 16 > h - m: break
            self._set_c(pdf, c, lw * 0.3); pdf.line(m, y + 16, w - m, y + 16)
            for ci in range(1, ncols):
                x = m + ci * col_w; pdf.line(x, y, x, y + 16)
            pdf.set_font("Helvetica", "", 7); pdf.set_text_color(*hex_to_rgb(c))
            pdf.text(m + 4, y + 10, str(r + 1)); y += 16

    # ── Gratitude Journal ──
    def _draw_gratitude_journal(self, pdf, w, h, pg=1):
        ne = int(self.params["num_entries"])
        npr = int(self.params.get("prompts_per_entry", 3))
        c = self.params["color"]; sc = self.params.get("secondary_color", "#F59E0B")
        lw = self.params["line_width"]; m = 36; y = m
        pdf.set_font("Helvetica", "B", 14); pdf.set_text_color(*hex_to_rgb(c))
        pdf.text(m, y + 14, "Gratitude Journal"); y += 24
        pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*hex_to_rgb(sc))
        pdf.text(m, y + 6, "Week of:"); self._set_c(pdf, sc, lw * 0.5)
        pdf.line(m + 55, y + 10, m + 200, y + 10); y += 22
        entry_h = (h - y - m) / max(ne, 1)
        prompts = ["I am grateful for...", "Today I appreciated...", "A positive moment was..."]
        for ei in range(ne):
            if y + entry_h > h - m - 10: break
            self._set_c(pdf, sc, lw); pdf.line(m, y + 16, w - m, y + 16)
            if self.params.get("show_date_field", True):
                pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(*hex_to_rgb(c))
                pdf.text(m, y + 10, f"Day {ei + 1}:")
                self._set_c(pdf, c, lw * 0.3); pdf.line(m + 50, y + 12, m + 180, y + 12)
            if self.params.get("show_mood_check", True):
                pdf.set_font("Helvetica", "", 7); pdf.set_text_color(*hex_to_rgb(sc))
                pdf.text(w - m - 160, y + 10, "Mood:  [ ] [ ] [ ] [ ] [ ]")
            py = y + 20
            for pi in range(min(npr, len(prompts))):
                if py + 16 > y + entry_h: break
                pdf.set_font("Helvetica", "", 7); pdf.set_text_color(*hex_to_rgb(sc))
                pdf.text(m + 8, py + 6, prompts[pi % len(prompts)]); py += 14
                for wl in range(2):
                    if py + 12 > y + entry_h: break
                    self._set_c(pdf, c, lw * 0.2); pdf.line(m + 8, py, w - m - 8, py)
                    py += 12
            if self.params.get("show_rating_col", True) and py + 14 < y + entry_h:
                pdf.set_font("Helvetica", "", 7); pdf.set_text_color(*hex_to_rgb(sc))
                pdf.text(m + 8, py + 6, "Gratitude level:  1   2   3   4   5")
            y += entry_h

    def _draw_blank(self, pdf, w, h, pg=1):
        pass


# ─────────────────────────────────────────────────────────────
# Color Button
# ─────────────────────────────────────────────────────────────
class ColorButton(QPushButton):
    color_changed = Signal(str)
    def __init__(self, color="#000000", parent=None):
        super().__init__(parent)
        self._color = color; self.setFixedSize(36, 28)
        self.setCursor(Qt.PointingHandCursor); self.setToolTip("Click to pick a color")
        self._update_style(); self.clicked.connect(self._pick_color)
    def _update_style(self):
        self.setStyleSheet(f"QPushButton {{ background-color: {self._color}; border: 2px solid #CBD5E1; border-radius: 4px; min-width: 30px; }} QPushButton:hover {{ border-color: #2563EB; }}")
    def color(self): return self._color
    def set_color(self, c): self._color = c; self._update_style()
    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self._color), self, "Select Color")
        if c.isValid(): self._color = c.name(); self._update_style(); self.color_changed.emit(self._color)


# ─────────────────────────────────────────────────────────────
# Settings Panel
# ─────────────────────────────────────────────────────────────
class SettingsPanel(QScrollArea):
    settings_changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui(); self.setWidgetResizable(True)
        self.setMinimumWidth(310); self.setMaximumWidth(400)

    def _build_ui(self):
        container = QWidget(); layout = QVBoxLayout(container); layout.setSpacing(6)
        # Paper type
        grp = QGroupBox("Paper Type"); gl = QVBoxLayout(grp)
        self.combo_type = QComboBox(); self.combo_type.addItems(PAPER_TYPES)
        self.combo_type.currentTextChanged.connect(self._on_type_changed)
        gl.addWidget(self.combo_type); layout.addWidget(grp)
        # Page setup
        grp = QGroupBox("Page Setup"); fl = QFormLayout(grp)
        self.combo_pagesize = QComboBox(); self.combo_pagesize.addItems(PAGE_SIZES.keys())
        self.combo_pagesize.currentIndexChanged.connect(self.settings_changed)
        fl.addRow("Size:", self.combo_pagesize)
        self.combo_orient = QComboBox(); self.combo_orient.addItems(["Portrait", "Landscape"])
        self.combo_orient.currentTextChanged.connect(self.settings_changed)
        fl.addRow("Orientation:", self.combo_orient)
        self.spin_pages = QSpinBox(); self.spin_pages.setRange(1, 500); self.spin_pages.setValue(1)
        fl.addRow("Pages:", self.spin_pages); layout.addWidget(grp)
        # Dynamic settings
        self.grp_settings = QGroupBox("Paper Settings")
        self.settings_layout = QFormLayout(self.grp_settings); layout.addWidget(self.grp_settings)
        # Colors
        grp = QGroupBox("Colors"); cl = QFormLayout(grp)
        row1 = QHBoxLayout()
        self.combo_color = QComboBox()
        self.combo_color.addItems(["#000080","#000000","#4472C4","#006633","#CC6600","#6600CC","#CC0000","#666666","#999999","#FF6600"])
        self.combo_color.currentTextChanged.connect(self._on_color_changed)
        self.btn_color_picker = ColorButton("#000080")
        self.btn_color_picker.color_changed.connect(self._on_custom_color)
        row1.addWidget(self.combo_color, stretch=1); row1.addWidget(self.btn_color_picker)
        cl.addRow("Primary:", row1)
        row2 = QHBoxLayout()
        self.combo_secondary = QComboBox()
        self.combo_secondary.addItems(["#FF0000","#FFFFFF","#000040","#94A3B8","#00994D","#AAAAAA","#FF8888","#2563EB","#999999","#555555"])
        self.combo_secondary.currentTextChanged.connect(self.settings_changed)
        self.btn_secondary_picker = ColorButton("#FF0000")
        self.btn_secondary_picker.color_changed.connect(self._on_secondary_custom)
        row2.addWidget(self.combo_secondary, stretch=1); row2.addWidget(self.btn_secondary_picker)
        cl.addRow("Secondary:", row2)
        row3 = QHBoxLayout()
        self.combo_bg = QComboBox()
        self.combo_bg.addItems(["#FFFFFF","#FFF9E6","#F0FFF0","#F0F0FF","#FFF0F5","#F5F5F5","#FFFFF0"])
        self.combo_bg.currentTextChanged.connect(self.settings_changed)
        self.btn_bg_picker = ColorButton("#FFFFFF")
        self.btn_bg_picker.color_changed.connect(self._on_bg_custom)
        row3.addWidget(self.combo_bg, stretch=1); row3.addWidget(self.btn_bg_picker)
        cl.addRow("Background:", row3); layout.addWidget(grp)
        # Options
        grp = QGroupBox("Options"); ol = QVBoxLayout(grp)
        self.check_page_numbers = QCheckBox("Show page numbers")
        self.check_page_numbers.stateChanged.connect(self.settings_changed); ol.addWidget(self.check_page_numbers)
        self.check_double_sided = QCheckBox("Double-sided (mirror margin on even pages)")
        self.check_double_sided.stateChanged.connect(self.settings_changed); ol.addWidget(self.check_double_sided)
        layout.addWidget(grp)
        layout.addStretch()
        btn_row = QHBoxLayout()
        self.btn_generate = QPushButton("Generate PDF")
        self.btn_generate.setStyleSheet("QPushButton { background-color: #2563EB; color: white; font-size: 15px; font-weight: bold; padding: 12px; border-radius: 8px; border: none; } QPushButton:hover { background-color: #1D4ED8; } QPushButton:pressed { background-color: #1E40AF; }")
        btn_row.addWidget(self.btn_generate); layout.addLayout(btn_row)
        self.setWidget(container)

    def _on_type_changed(self, text):
        self._build_paper_settings(text); self.settings_changed.emit()
    def _on_color_changed(self, _):
        self.btn_color_picker.set_color(self.combo_color.currentText()); self.settings_changed.emit()
    def _on_custom_color(self, color):
        idx = self.combo_color.findText(color)
        if idx < 0: self.combo_color.insertItem(0, color); self.combo_color.setCurrentIndex(0)
        else: self.combo_color.setCurrentIndex(idx)
        self.settings_changed.emit()
    def _on_secondary_custom(self, color):
        idx = self.combo_secondary.findText(color)
        if idx < 0: self.combo_secondary.insertItem(0, color); self.combo_secondary.setCurrentIndex(0)
        else: self.combo_secondary.setCurrentIndex(idx)
        self.settings_changed.emit()
    def _on_bg_custom(self, color):
        idx = self.combo_bg.findText(color)
        if idx < 0: self.combo_bg.insertItem(0, color); self.combo_bg.setCurrentIndex(0)
        else: self.combo_bg.setCurrentIndex(idx)
        self.settings_changed.emit()

    def _clear_settings(self):
        while self.settings_layout.rowCount() > 0: self.settings_layout.removeRow(0)
    def _add_spin(self, key, label, min_v, max_v, default, step, decimals):
        spin = QDoubleSpinBox(); spin.setRange(min_v, max_v); spin.setValue(default)
        spin.setSingleStep(step); spin.setDecimals(decimals)
        spin.valueChanged.connect(lambda: self.settings_changed.emit())
        setattr(self, f"spin_{key}", spin); self.settings_layout.addRow(label, spin)
    def _add_checkbox(self, key, label, default):
        cb = QCheckBox(label); cb.setChecked(default)
        cb.stateChanged.connect(lambda: self.settings_changed.emit())
        setattr(self, f"check_{key}", cb); self.settings_layout.addRow(cb)
    def _add_text_input(self, key, label, default=""):
        """Add a text input field for a string parameter."""
        row = QWidget()
        lbl = QLabel(label)
        lbl.setFixedWidth(180)
        edit = QLineEdit(default)
        edit.setFixedWidth(200)
        edit.setProperty("param_key", key)
        edit.editingFinished.connect(lambda: self._param_changed())
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.addWidget(lbl)
        lay.addWidget(edit)
        self._setting_rows.append((key, "text_input", edit))
        self._settings_layout.addWidget(row)
        self._param_widgets[key] = edit

    def _add_combo(self, key, label, options, default):
        combo = QComboBox(); combo.addItems(options)
        idx = combo.findText(default)
        if idx >= 0: combo.setCurrentIndex(idx)
        combo.currentTextChanged.connect(lambda: self.settings_changed.emit())
        setattr(self, f"combo_{key}", combo); self.settings_layout.addRow(label, combo)

    def _build_paper_settings(self, pt):
        self._clear_settings()
        if pt == "Graph Paper":
            self._add_spin("grid_size", "Grid Size (in):", 0.1, 2.0, 0.25, 0.05, 2)
            self._add_spin("major_every", "Major Every (cells):", 2, 20, 4, 1, 0)
            self._add_combo("line_style", "Line Style:", ["solid","dashed","dotted","dashdot"], "solid")
            self._add_spin("line_width", "Line Width (pt):", 0.1, 3.0, 0.3, 0.1, 1)
            self._add_spin("major_width", "Major Width (pt):", 0.3, 5.0, 0.7, 0.1, 1)
            self._add_checkbox("show_axis", "Show X/Y Axis", False)
            self._add_spin("axis_width", "Axis Width (pt):", 0.5, 5.0, 1.5, 0.1, 1)
            self._add_checkbox("show_labels", "Show Grid Labels", False)
            self._add_spin("label_font_size", "Label Font Size:", 5, 14, 7, 1, 0)
            self.combo_color.setCurrentText("#000080"); self.combo_secondary.setCurrentText("#000040")
        elif pt in ("College Ruled", "Wide Ruled", "Lined Paper"):
            defaults = {"College Ruled":(0.375,1.5,"#4472C4","#FF0000"),"Wide Ruled":(0.5,1.25,"#4472C4","#FF0000"),"Lined Paper":(0.5,1.0,"#666666","#999999")}
            ls_d,ml_d,c_d,sc_d = defaults[pt]
            self._add_spin("line_spacing", "Line Spacing (in):", 0.2, 1.5, ls_d, 0.0125, 4)
            self._add_spin("margin_left", "Left Margin (in):", 0.5, 3.0, ml_d, 0.125, 3)
            self._add_combo("line_style", "Line Style:", ["solid","dashed","dotted","dashdot"], "solid")
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self._add_checkbox("show_top_margin", "Show Top Margin", True)
            self._add_spin("top_margin", "Top Margin (in):", 0.5, 3.0, 1.0, 0.125, 3)
            self._add_checkbox("double_line", "Double Line Style", False)
            self._add_spin("line_opacity", "Line Opacity:", 0.1, 1.0, 1.0, 0.05, 2)
            self._add_spin("right_margin", "Right Margin (in):", 0.5, 3.0, 1.0, 0.125, 3)
            self.combo_color.setCurrentText(c_d); self.combo_secondary.setCurrentText(sc_d)
        elif pt == "Dot Grid":
            self._add_spin("dot_spacing", "Dot Spacing (in):", 0.1, 1.0, 0.2, 0.05, 2)
            self._add_spin("dot_radius", "Dot Radius (pt):", 0.3, 3.0, 0.8, 0.1, 1)
            self._add_combo("dot_style", "Dot Style:", ["filled","ring","cross"], "filled")
            self._add_spin("major_dots_every", "Major Dots Every:", 2, 20, 5, 1, 0)
            self._add_spin("major_dot_radius", "Major Dot Radius (pt):", 0.5, 5.0, 1.5, 0.1, 1)
            self._add_spin("dot_opacity", "Dot Opacity:", 0.1, 1.0, 1.0, 0.05, 2)
            self._add_spin("offset_x", "Offset X (in):", 0.0, 1.0, 0.0, 0.05, 2)
            self._add_spin("offset_y", "Offset Y (in):", 0.0, 1.0, 0.0, 0.05, 2)
            self.combo_color.setCurrentText("#999999")
        elif pt == "Isometric":
            self._add_spin("grid_size", "Grid Size (in):", 0.1, 2.0, 0.25, 0.05, 2)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 3.0, 0.3, 0.1, 1)
            self._add_checkbox("show_axis", "Show Principal Axes", False)
            self._add_spin("axis_width", "Axis Width (pt):", 0.5, 5.0, 1.5, 0.1, 1)
            self._add_checkbox("triangle_size", "Show Triangle Markers", False)
            self._add_spin("margin", "Margin (in):", 0.0, 1.5, 0.0, 0.125, 3)
            self.combo_color.setCurrentText("#CC6600")
        elif pt == "Cornell Notes":
            self._add_spin("line_spacing", "Line Spacing (in):", 0.2, 1.0, 0.375, 0.0125, 4)
            self._add_spin("column_split_ratio", "Cue Column Ratio:", 0.15, 0.5, 0.3, 0.05, 2)
            self._add_spin("summary_height", "Summary Height (in):", 0.5, 5.0, 2.0, 0.25, 2)
            self._add_checkbox("show_labels", "Show Labels", True)
            self._add_combo("notes_line_style", "Notes Line Style:", ["solid","dashed","dotted"], "dashed")
            self._add_combo("cue_line_style", "Cue Line Style:", ["solid","dashed"], "solid")
            self._add_spin("cue_width", "Cue Column Width (in):", 1.0, 5.0, 2.5, 0.25, 2)
            self._add_checkbox("show_date_field", "Show Date Field", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#4472C4"); self.combo_secondary.setCurrentText("#94A3B8")
        elif pt == "Engineering Paper":
            self._add_spin("grid_size", "Grid Size (in):", 0.05, 1.0, 0.2, 0.05, 2)
            self._add_spin("major_every", "Major Every (cells):", 2, 20, 5, 1, 0)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.2, 0.1, 1)
            self._add_spin("major_width", "Major Width (pt):", 0.3, 5.0, 0.6, 0.1, 1)
            self._add_checkbox("border", "Show Border", True)
            self._add_checkbox("show_title_block", "Show Title Block", False)
            self._add_spin("title_block_width", "Title Block W (in):", 1.0, 5.0, 2.5, 0.25, 2)
            self._add_spin("title_block_height", "Title Block H (in):", 0.5, 3.0, 1.0, 0.25, 2)
            self._add_checkbox("zone_labels", "Show Zone Labels", False)
            self.combo_color.setCurrentText("#006633"); self.combo_secondary.setCurrentText("#00994D")
        elif pt == "Hexagonal Grid":
            self._add_spin("hex_size", "Hex Size (in):", 0.1, 1.0, 0.25, 0.05, 2)
            self._add_combo("orientation", "Orientation:", ["flat_top","pointy_top"], "flat_top")
            self._add_checkbox("fill_hexagons", "Fill Hexagons", False)
            self._add_checkbox("border_hexes", "Border Hexes", False)
            self._add_spin("opacity", "Line Opacity:", 0.1, 1.0, 1.0, 0.05, 2)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 3.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#6600CC"); self.combo_secondary.setCurrentText("#E8D5F5")
        elif pt == "Music Staff":
            self._add_spin("staff_spacing", "Staff Spacing (in):", 0.05, 0.25, 0.125, 0.0125, 4)
            self._add_spin("group_spacing", "Group Gap (in):", 0.3, 2.0, 0.6, 0.05, 2)
            self._add_spin("num_staves", "Number of Staves:", 1, 12, 6, 1, 0)
            self._add_checkbox("show_barlines", "Show Barlines", False)
            self._add_spin("barline_interval", "Barline Interval (in):", 0.5, 4.0, 2.0, 0.25, 2)
            self._add_checkbox("show_clef", "Show Clef Symbol", False)
            self._add_checkbox("show_time_signature", "Show Time Signature", False)
            self._add_spin("staff_label_font", "Label Font Size:", 5, 14, 8, 1, 0)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#000000")
        elif pt == "Calligraphy Guide":
            self._add_spin("guide_spacing", "Guide Spacing (in):", 0.25, 2.0, 0.5, 0.05, 2)
            self._add_spin("ascender", "Ascender (in):", 0.1, 1.0, 0.2, 0.05, 2)
            self._add_spin("descender", "Descender (in):", 0.1, 1.0, 0.2, 0.05, 2)
            self._add_spin("slant_angle", "Slant Angle (deg):", 30, 75, 52, 1, 0)
            self._add_checkbox("show_slant", "Show Slant Lines", True)
            self._add_checkbox("show_x_height", "Show X-Height Line", True)
            self._add_spin("num_nibs", "Number of Nib Guides:", 1, 4, 1, 1, 0)
            self._add_spin("nib_width", "Nib Width (in):", 0.05, 0.5, 0.1, 0.05, 2)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.25, 0.05, 2)
            self.combo_color.setCurrentText("#CC0000"); self.combo_secondary.setCurrentText("#FF8888")
        elif pt == "To-Do List":
            self._add_spin("line_spacing", "Line Spacing (in):", 0.3, 1.5, 0.5, 0.05, 2)
            self._add_spin("margin_left", "Left Margin (in):", 0.5, 3.0, 0.75, 0.125, 3)
            self._add_spin("checkbox_size", "Checkbox Size (in):", 0.1, 0.5, 0.25, 0.05, 2)
            self._add_checkbox("show_numbers", "Show Numbers", False)
            self._add_checkbox("show_date_column", "Show Date Column", False)
            self._add_spin("date_col_width", "Date Col Width (in):", 0.4, 2.0, 0.8, 0.1, 1)
            self._add_checkbox("show_priority", "Show Priority (A/B/C)", False)
            self._add_checkbox("priority_col", "Show Priority Column", False)
            self._add_checkbox("category_column", "Show Category Column", False)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#2563EB")
        elif pt == "Kanban Board":
            self._add_spin("num_columns", "Columns:", 2, 6, 3, 1, 0)
            self._add_spin("column_spacing", "Column Gap (in):", 0.1, 1.0, 0.25, 0.05, 2)
            self._add_spin("card_height", "Card Height (in):", 0.3, 2.0, 0.7, 0.1, 1)
            self._add_checkbox("show_due_date", "Show Due Date Line", False)
            self._add_checkbox("show_priority_badge", "Show Priority Badge", False)
            self._add_spin("cards_per_col", "Cards per Column:", 1, 15, 3, 1, 0)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 3.0, 0.5, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#94A3B8")
        elif pt == "Penmanship":
            self._add_spin("line_spacing", "Line Spacing (in):", 0.25, 1.5, 0.5, 0.05, 2)
            self._add_spin("midline_offset", "Midline Offset (in):", 0.0, 1.0, 0.0, 0.05, 2)
            self._add_spin("descender_depth", "Descender Depth (in):", 0.0, 1.0, 0.0, 0.05, 2)
            self._add_checkbox("show_ascender", "Show Ascender Line", True)
            self._add_spin("ascender_height", "Ascender Height (in):", 0.0, 1.0, 0.0, 0.05, 2)
            self._add_combo("line_color_mode", "Color Mode:", ["single","dual"], "single")
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.2, 0.05, 2)
            self.combo_color.setCurrentText("#0000CC"); self.combo_secondary.setCurrentText("#AAAAAA")
        elif pt == "Cross Stitch":
            self._add_spin("grid_size", "Grid Size (in):", 0.05, 0.5, 0.1, 0.01, 2)
            self._add_spin("major_every", "Major Every (cells):", 5, 20, 10, 1, 0)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.2, 0.05, 2)
            self._add_spin("major_width", "Major Width (pt):", 0.3, 5.0, 0.6, 0.1, 1)
            self._add_checkbox("show_numbers", "Show Block Numbers", False)
            self._add_checkbox("show_symbols", "Show Symbols at Majors", False)
            self._add_combo("major_color", "Major Line Color:", ["#555555","#333333","#000000","#880000"], "#555555")
            self._add_spin("border_width", "Border Width (in):", 0.2, 2.0, 0.5, 0.1, 1)
            self._add_checkbox("center_marks", "Show Center Marks", True)
            self.combo_color.setCurrentText("#AAAAAA"); self.combo_secondary.setCurrentText("#555555")
        elif pt == "Piano Keys":
            self._add_spin("num_octaves", "Octaves:", 1, 4, 2, 1, 0)
            self._add_spin("key_height", "Key Height (in):", 0.3, 2.0, 0.6, 0.1, 1)
            self._add_combo("key_style", "Key Style:", ["classic","label","blank"], "classic")
            self._add_spin("start_octave", "Start Octave:", 1, 6, 3, 1, 0)
            self._add_checkbox("show_labels", "Show Note Labels", True)
            self._add_checkbox("show_octave_numbers", "Show Octave Numbers", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 3.0, 0.5, 0.1, 1)
            self.combo_color.setCurrentText("#000000"); self.combo_secondary.setCurrentText("#FFFFFF")
        elif pt == "Storyboard":
            self._add_spin("num_panels_w", "Panels Wide:", 1, 5, 2, 1, 0)
            self._add_spin("num_panels_h", "Panels Tall:", 1, 6, 3, 1, 0)
            self._add_spin("panel_gap", "Panel Gap (in):", 0.05, 0.5, 0.2, 0.05, 2)
            self._add_spin("label_height", "Label Height (in):", 0.1, 0.8, 0.3, 0.05, 2)
            self._add_checkbox("show_numbers", "Show Panel Numbers", True)
            self._add_checkbox("show_rule_of_thirds", "Rule of Thirds", False)
            self._add_checkbox("show_aspect_ratio", "Show Aspect Ratio", True)
            self._add_spin("panel_border_radius", "Panel Corner Radius (in):", 0.0, 0.5, 0.0, 0.05, 2)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 3.0, 0.5, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#94A3B8")
        elif pt == "Grid Diary":
            self._add_spin("grid_cols", "Columns:", 2, 10, 7, 1, 0)
            self._add_spin("grid_rows", "Rows:", 2, 15, 5, 1, 0)
            self._add_spin("header_height", "Header Height (in):", 0.2, 1.5, 0.5, 0.1, 1)
            self._add_spin("time_col_width", "Time Col Width (in):", 0.3, 2.0, 0.6, 0.1, 1)
            self._add_checkbox("show_week_numbers", "Show Week Numbers", False)
            self._add_combo("row_labels", "Row Labels:", ["time","period","blank"], "time")
            self._add_combo("start_day", "Week Starts On:", ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"], "Monday")
            self._add_checkbox("alternate_row_shading", "Alternate Row Shading", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#94A3B8")
        elif pt == "Japanese Genkoyoushi":
            self._add_spin("cell_size", "Cell Size (in):", 0.2, 0.6, 0.394, 0.01, 3)
            self._add_spin("margin_size", "Margin Size (in):", 0.3, 1.5, 0.591, 0.01, 3)
            self._add_checkbox("show_title_space", "Show Title Space", True)
            self._add_spin("num_title_rows", "Title Rows:", 1, 6, 3, 1, 0)
            self._add_combo("grid_style", "Grid Style:", ["full","center_only","none"], "full")
            self._add_checkbox("show_field_guide", "Show Field Guide", False)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 1.0, 0.2, 0.05, 2)
            self.combo_color.setCurrentText("#CC0000"); self.combo_secondary.setCurrentText("#AAAAAA")
        elif pt == "Meeting Notes":
            self._add_spin("title_area_height", "Title Area Height (in):", 0.4, 2.0, 0.8, 0.1, 1)
            self._add_spin("agenda_rows", "Agenda Rows:", 2, 15, 5, 1, 0)
            self._add_spin("notes_line_spacing", "Notes Spacing (in):", 0.2, 0.75, 0.375, 0.0125, 3)
            self._add_spin("action_rows", "Action Item Rows:", 2, 15, 5, 1, 0)
            self._add_checkbox("show_fields", "Show Field Labels", True)
            self._add_combo("notes_columns", "Notes Columns:", [1,2,3], "1")
            self._add_checkbox("show_decision_box", "Show Decisions Section", False)
            self._add_checkbox("show_timer_section", "Show Timer Section", False)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#2563EB")
        elif pt == "Weekly Planner":
            self._add_spin("start_hour", "Start Hour:", 0, 12, 6, 1, 0)
            self._add_spin("end_hour", "End Hour:", 13, 24, 22, 1, 0)
            self._add_spin("time_col_width", "Time Col Width (in):", 0.3, 2.0, 0.6, 0.1, 1)
            self._add_checkbox("show_weekend", "Show Weekend", True)
            self._add_spin("time_interval", "Hour Interval:", 1, 4, 1, 1, 0)
            self._add_combo("time_format", "Time Format:", ["12h","24h"], "12h")
            self._add_combo("column_labels", "Column Labels:", ["short","full"], "short")
            self._add_checkbox("show_current_hour_line", "Show Noon Highlight", False)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#2563EB")
        elif pt == "Budget Tracker":
            self._add_spin("income_rows", "Income Rows:", 1, 15, 5, 1, 0)
            self._add_spin("expense_rows", "Expense Rows:", 1, 20, 10, 1, 0)
            self._add_spin("header_height", "Header Height (in):", 0.2, 1.5, 0.5, 0.1, 1)
            self._add_spin("category_col_width", "Category Col Width:", 0.2, 0.6, 0.4, 0.05, 2)
            self._add_checkbox("show_savings_section", "Show Savings Section", False)
            self._add_spin("savings_rows", "Savings Rows:", 1, 10, 3, 1, 0)
            self._add_checkbox("show_total_row", "Show Total Row", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#16A34A")
        elif pt == "Reading Log":
            self._add_spin("entry_rows", "Entry Rows:", 3, 30, 15, 1, 0)
            self._add_spin("header_height", "Header Height (in):", 0.2, 1.5, 0.5, 0.1, 1)
            self._add_spin("row_height", "Row Height (in):", 0.15, 0.5, 0.25, 0.05, 2)
            self._add_checkbox("show_genre_column", "Show Genre Column", False)
            self._add_checkbox("show_progress_bar", "Show Progress Column", False)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#94A3B8")
        elif pt == "Seyes French Ruled":
            self._add_spin("line_spacing", "Line Spacing (in):", 0.2, 0.5, 0.315, 0.005, 3)
            self._add_spin("margin_left", "Left Margin (in):", 0.25, 2.0, 0.5, 0.05, 2)
            self._add_spin("num_lines", "Lines Per Group:", 4, 12, 8, 1, 0)
            self._add_combo("margin_style", "Margin Style:", ["single","double"], "single")
            self._add_spin("pink_line_offset", "Pink Line Offset (mm):", 1.0, 5.0, 2.0, 0.5, 1)
            self._add_checkbox("show_top_margin", "Show Top Margin", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 1.0, 0.2, 0.05, 2)
            self.combo_color.setCurrentText("#0066CC"); self.combo_secondary.setCurrentText("#FF6699")
        elif pt == "Polar Coordinate":
            self._add_spin("radius_step", "Radius Step (in):", 0.2, 3.0, 0.5, 0.1, 1)
            self._add_spin("num_radials", "Number of Radials:", 4, 36, 12, 1, 0)
            self._add_checkbox("show_labels", "Show Labels", True)
            self._add_spin("start_angle", "Start Angle (deg):", 0, 359, 0, 15, 0)
            self._add_spin("label_radius", "Label Radius (in):", 0.1, 1.0, 0.3, 0.1, 1)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#336699"); self.combo_secondary.setCurrentText("#99BBDD")
        elif pt == "Logarithmic Paper":
            self._add_spin("log_cycles", "Log Cycles:", 1, 5, 3, 1, 0)
            self._add_spin("grid_size", "Grid Size (in):", 0.1, 1.0, 0.25, 0.05, 2)
            self._add_spin("margin", "Margin (in):", 0.25, 2.0, 1.0, 0.125, 3)
            self._add_spin("label_font_size", "Label Font Size:", 5, 14, 7, 1, 0)
            self._add_checkbox("show_labels", "Show Labels", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.2, 0.1, 1)
            self.combo_color.setCurrentText("#006633"); self.combo_secondary.setCurrentText("#66BB66")
        elif pt == "Probability Paper":
            self._add_spin("grid_size", "Grid Size (in):", 0.2, 2.0, 0.5, 0.1, 1)
            self._add_spin("margin", "Margin (in):", 0.25, 2.0, 1.0, 0.125, 3)
            self._add_spin("label_font_size", "Label Font Size:", 5, 14, 7, 1, 0)
            self._add_checkbox("show_labels", "Show Labels", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#663399"); self.combo_secondary.setCurrentText("#BB99DD")
        elif pt == "Seam Allowance":
            self._add_spin("grid_size", "Grid Size (in):", 0.1, 1.0, 0.25, 0.05, 2)
            self._add_checkbox("show_quarter_mark", "Show 1/4\" Mark", True)
            self._add_checkbox("show_five_eighths_mark", "Show 5/8\" Mark", True)
            self._add_spin("margin", "Outer Margin (in):", 0.1, 1.0, 0.5, 0.05, 2)
            self._add_spin("label_font_size", "Label Font Size:", 5, 12, 7, 1, 0)
            self._add_spin("margin_width", "Margin Width (in):", 0.5, 3.0, 1.0, 0.25, 2)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.2, 0.05, 2)
            self.combo_color.setCurrentText("#CC3333"); self.combo_secondary.setCurrentText("#FF9999")
        elif pt == "Knitting Grid":
            self._add_spin("grid_size", "Grid Size (in):", 0.1, 1.0, 0.25, 0.05, 2)
            self._add_spin("major_every", "Major Every (cells):", 5, 20, 10, 1, 0)
            self._add_checkbox("show_row_numbers", "Show Row Numbers", True)
            self._add_spin("margin", "Margin (in):", 0.1, 1.0, 0.5, 0.05, 2)
            self._add_spin("major_line_weight", "Major Line Weight x:", 1.0, 5.0, 2.0, 0.25, 1)
            self._add_spin("label_font_size", "Label Font Size:", 4, 10, 6, 1, 0)
            self._add_checkbox("show_col_numbers", "Show Col Numbers", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.2, 0.05, 2)
            self.combo_color.setCurrentText("#993366"); self.combo_secondary.setCurrentText("#DDBBCC")
        elif pt == "Circuit / Schematic":
            self._add_spin("grid_size", "Grid Size (in):", 0.05, 0.5, 0.1, 0.01, 2)
            self._add_spin("dot_size", "Snap Dot Size (pt):", 0.5, 3.0, 1.0, 0.1, 1)
            self._add_spin("major_every", "Major Every (cells):", 2, 20, 5, 1, 0)
            self._add_spin("margin", "Margin (in):", 0.05, 1.0, 0.25, 0.05, 2)
            self._add_spin("major_line_weight", "Major Line Weight x:", 1.0, 5.0, 2.0, 0.25, 1)
            self._add_checkbox("snap_dots", "Show Snap Dots", True)
            self._add_spin("line_width", "Line Width (pt):", 0.05, 1.0, 0.15, 0.05, 2)
            self.combo_color.setCurrentText("#003366"); self.combo_secondary.setCurrentText("#6699CC")
        elif pt == "Braille Practice":
            self._add_spin("cell_spacing", "Cell Spacing (in):", 0.2, 1.0, 0.4, 0.05, 2)
            self._add_spin("cell_size", "Cell Size (in):", 0.1, 0.5, 0.25, 0.05, 2)
            self._add_spin("dot_spacing", "Dot Spacing (in):", 0.04, 0.2, 0.08, 0.01, 2)
            self._add_spin("margin", "Margin (in):", 0.25, 2.0, 1.0, 0.125, 3)
            self._add_spin("dot_radius", "Dot Radius (pt):", 0.5, 4.0, 1.5, 0.25, 1)
            self._add_checkbox("show_guide_dots", "Show Guide Dots", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#AAAAAA")
        elif pt == "Musical TAB":
            self._add_spin("num_staves", "Number of Staves:", 1, 12, 8, 1, 0)
            self._add_spin("staff_spacing", "String Spacing (in):", 0.08, 0.25, 0.15, 0.01, 2)
            self._add_spin("group_spacing", "Staff Gap (in):", 0.2, 2.0, 0.5, 0.05, 2)
            self._add_checkbox("show_barlines", "Show Barlines", True)
            self._add_spin("barline_interval", "Barline Interval (in):", 0.5, 4.0, 2.0, 0.25, 2)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#000000"); self.combo_secondary.setCurrentText("#666666")
        elif pt == "Ledger / Accounting":
            self._add_spin("num_rows", "Number of Rows:", 5, 40, 20, 1, 0)
            self._add_spin("num_debit_cols", "Debit Columns:", 1, 5, 2, 1, 0)
            self._add_spin("num_credit_cols", "Credit Columns:", 1, 5, 2, 1, 0)
            self._add_spin("header_height", "Header Height (in):", 0.2, 1.5, 0.5, 0.1, 1)
            self._add_checkbox("show_totals_row", "Show Total Row", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#16A34A")
        elif pt == "Daily Schedule":
            self._add_spin("start_hour", "Start Hour:", 0, 12, 6, 1, 0)
            self._add_spin("end_hour", "End Hour:", 13, 24, 22, 1, 0)
            self._add_spin("slot_height", "Slot Height (in):", 0.3, 2.0, 0.6, 0.1, 1)
            self._add_spin("time_col_width", "Time Col Width (in):", 0.3, 2.0, 0.7, 0.1, 1)
            self._add_checkbox("show_15min", "Show 15-Min Intervals", False)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#2563EB")
        elif pt == "Habit Tracker":
            self._add_spin("num_habits", "Number of Habits:", 1, 20, 8, 1, 0)
            self._add_spin("checkbox_size", "Checkbox Size (in):", 0.1, 0.5, 0.2, 0.05, 2)
            self._add_checkbox("show_weekday_headers", "Show Weekday Headers", True)
            self._add_spin("days_in_month", "Days in Month:", 28, 31, 31, 1, 0)
            self._add_spin("label_width", "Label Column Width (pt):", 40, 200, 100, 5, 0)
            self._add_spin("row_padding", "Row Padding (pt):", 4, 24, 12, 1, 0)
            self._add_checkbox("show_month_header", "Show Month Header", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#2563EB")
        elif pt == "Recipe Card":
            self._add_checkbox("show_prep_time", "Show Prep Time", True)
            self._add_checkbox("show_cook_time", "Show Cook Time", True)
            self._add_checkbox("show_servings", "Show Servings", True)
            self._add_checkbox("show_difficulty", "Show Difficulty", True)
            self._add_spin("ingredients_rows", "Ingredients Rows:", 3, 30, 12, 1, 0)
            self._add_spin("instructions_lines", "Instructions Lines:", 5, 30, 15, 1, 0)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#D97706")
        elif pt == "Perspective Grid":
            self._add_combo("num_points", "Vanishing Points:", ["1", "2"], "1")
            self._add_spin("grid_size", "Grid Size (in):", 0.2, 2.0, 0.5, 0.1, 2)
            self._add_spin("horizon_position", "Horizon Position (%):", 20, 80, 50, 5, 0)
            self._add_checkbox("show_horizon", "Show Horizon Line", True)
            self._add_checkbox("show_ground_line", "Show Ground Line", True)
            self._add_spin("vanishing_point_size", "VP Dot Size (pt):", 2.0, 10.0, 4.0, 0.5, 1)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#336699"); self.combo_secondary.setCurrentText("#99BBDD")
        elif pt == "Mandala Guide":
            self._add_spin("num_rings", "Number of Rings:", 2, 20, 8, 1, 0)
            self._add_spin("num_radials", "Number of Radials:", 3, 36, 12, 1, 0)
            self._add_spin("ring_spacing", "Ring Spacing (in):", 0.1, 1.5, 0.4, 0.05, 2)
            self._add_checkbox("show_center_dot", "Show Center Dot", True)
            self._add_spin("center_dot_size", "Center Dot Size (pt):", 1.0, 8.0, 3.0, 0.5, 1)
            self._add_checkbox("show_concentric_circles", "Show Concentric Circles", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.25, 0.05, 2)
            self.combo_color.setCurrentText("#CC3366"); self.combo_secondary.setCurrentText("#F0C0D0")
        elif pt == "Guitar Chord Diagram":
            self._add_spin("diagrams_w", "Diagrams Wide:", 1, 5, 3, 1, 0)
            self._add_spin("diagrams_h", "Diagrams Tall:", 1, 5, 3, 1, 0)
            self._add_spin("diagram_size", "Diagram Size (in):", 1.0, 3.0, 1.8, 0.1, 1)
            self._add_spin("num_frets", "Number of Frets:", 3, 8, 5, 1, 0)
            self._add_checkbox("show_fret_numbers", "Show Fret Numbers", True)
            self._add_checkbox("show_string_names", "Show String Names", True)
            self._add_checkbox("show_open_mute", "Show Open/Mute Markers", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 3.0, 0.5, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#94A3B8")
        elif pt == "Venn Diagram":
            self._add_combo("num_circles", "Number of Circles:", ["2", "3", "4"], "3")
            self._add_spin("circle_radius", "Circle Radius (in):", 0.5, 3.0, 1.5, 0.1, 1)
            self._add_checkbox("show_labels", "Show Labels", True)
            self._add_spin("overlap_ratio", "Overlap Ratio:", 0.1, 0.9, 0.5, 0.05, 2)
            self._add_spin("label_font_size", "Label Font Size:", 6, 16, 9, 1, 0)
            self._add_checkbox("show_shading", "Show Shading", False)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 3.0, 0.5, 0.1, 1)
            self.combo_color.setCurrentText("#3366CC"); self.combo_secondary.setCurrentText("#D0E0F0")
        elif pt == "Study Notes":
            self._add_spin("line_spacing", "Line Spacing (in):", 0.2, 1.0, 0.375, 0.0125, 3)
            self._add_spin("margin_left", "Left Margin (in):", 0.5, 3.0, 1.0, 0.125, 2)
            self._add_spin("concepts_rows", "Key Concepts Rows:", 2, 15, 5, 1, 0)
            self._add_spin("summary_height", "Summary Height (in):", 0.5, 4.0, 2.0, 0.25, 1)
            self._add_checkbox("show_date_field", "Show Date Field", True)
            self._add_checkbox("show_topic_field", "Show Topic Field", True)
            self._add_checkbox("show_key_concepts", "Show Key Concepts", True)
            self._add_spin("section_header_height", "Section Header H (in):", 0.2, 1.5, 0.5, 0.1, 1)
            self._add_checkbox("show_summary_section", "Show Summary", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#4472C4"); self.combo_secondary.setCurrentText("#94A3B8")
        elif pt == "Project Planner":
            self._add_spin("num_phases", "Number of Phases:", 1, 8, 4, 1, 0)
            self._add_spin("tasks_per_phase", "Tasks per Phase:", 2, 15, 5, 1, 0)
            self._add_checkbox("show_timeline", "Show Timeline", True)
            self._add_checkbox("show_deadline_col", "Show Deadline Column", True)
            self._add_checkbox("show_priority_col", "Show Priority Column", True)
            self._add_checkbox("show_status_col", "Show Status Column", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#2563EB")
        elif pt == "Fitness Log":
            self._add_spin("num_exercises", "Number of Exercises:", 2, 20, 8, 1, 0)
            self._add_spin("num_sets", "Sets per Exercise:", 1, 8, 4, 1, 0)
            self._add_checkbox("show_weight_col", "Show Weight Column", True)
            self._add_checkbox("show_reps_col", "Show Reps Column", True)
            self._add_checkbox("show_rest_col", "Show Rest Column", True)
            self._add_checkbox("show_notes_col", "Show Notes Column", True)
            self._add_checkbox("show_date_field", "Show Date Field", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#16A34A")
        elif pt == "Weight Tracker":
            self._add_spin("num_weeks", "Number of Weeks:", 4, 52, 12, 1, 0)
            self._add_spin("row_height", "Row Height (in):", 0.2, 0.5, 0.3, 0.05, 2)
            self._add_checkbox("show_date_col", "Show Date Column", True)
            self._add_checkbox("show_weight_col", "Show Weight Column", True)
            self._add_checkbox("show_change_col", "Show Change Column", True)
            self._add_checkbox("show_bmi_col", "Show BMI Column", False)
            self._add_checkbox("show_goal_line", "Show Goal Line", True)
            self._add_spin("goal_weight", "Goal Weight (lbs):", 50, 400, 150, 1, 0)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#2563EB")
        elif pt == "Travel Journal":
            self._add_checkbox("show_date_field", "Show Date Field", True)
            self._add_checkbox("show_location_field", "Show Location Field", True)
            self._add_checkbox("show_weather_section", "Show Weather Section", True)
            self._add_checkbox("show_expenses_section", "Show Expenses Section", True)
            self._add_spin("expense_rows", "Expense Rows:", 2, 15, 5, 1, 0)
            self._add_spin("num_entry_lines", "Journal Entry Lines:", 5, 40, 20, 1, 0)
            self._add_checkbox("show_highlights_section", "Show Highlights", True)
            self._add_spin("highlights_rows", "Highlights Rows:", 2, 15, 5, 1, 0)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#D97706")
        elif pt == "Essay Outline":
            self._add_spin("num_body_paragraphs", "Body Paragraphs:", 1, 8, 3, 1, 0)
            self._add_spin("evidence_lines_per_para", "Evidence Lines/Para:", 1, 6, 3, 1, 0)
            self._add_checkbox("show_hook_section", "Show Hook Section", True)
            self._add_checkbox("show_thesis_section", "Show Thesis Section", True)
            self._add_checkbox("show_conclusion_section", "Show Conclusion", True)
            self._add_checkbox("show_counter_argument", "Show Counter Argument", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#4472C4"); self.combo_secondary.setCurrentText("#94A3B8")
        elif pt == "Grand Staff Paper":
            self._add_spin("staff_spacing", "Staff Spacing (in):", 0.05, 0.25, 0.125, 0.0125, 4)
            self._add_spin("group_spacing", "System Gap (in):", 0.3, 2.0, 0.8, 0.05, 2)
            self._add_spin("num_systems", "Number of Systems:", 1, 10, 5, 1, 0)
            self._add_combo("bracket_style", "Bracket Style:", ["brace", "bracket", "none"], "brace")
            self._add_checkbox("show_barlines", "Show Barlines", False)
            self._add_spin("barline_interval", "Barline Interval (in):", 0.5, 4.0, 2.0, 0.25, 2)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#000000"); self.combo_secondary.setCurrentText("#666666")
        elif pt == "Dotted Lined":
            self._add_spin("line_spacing", "Line Spacing (in):", 0.25, 1.5, 0.5, 0.05, 2)
            self._add_spin("dot_spacing", "Dot Spacing (in):", 0.1, 1.0, 0.25, 0.05, 2)
            self._add_spin("dot_radius", "Dot Radius (pt):", 0.3, 3.0, 0.6, 0.1, 1)
            self._add_spin("margin_left", "Left Margin (in):", 0.5, 3.0, 1.0, 0.125, 2)
            self._add_combo("dot_style", "Dot Style:", ["filled", "ring"], "filled")
            self._add_combo("dot_color", "Dot Color:", ["#999999","#BBBBBB","#666666","#CC0000"], "#999999")
            self._add_checkbox("show_margin_line", "Show Margin Line", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.25, 0.05, 2)
            self.combo_color.setCurrentText("#4472C4"); self.combo_secondary.setCurrentText("#999999")
        elif pt == "Weekly Meal Planner":
            self._add_checkbox("show_snack_row", "Show Snacks Row", True)
            self._add_spin("meal_col_width", "Meal Col Width (in):", 0.8, 3.0, 1.5, 0.1, 1)
            self._add_checkbox("show_calorie_col", "Show Calorie Fields", True)
            self._add_checkbox("show_notes_col", "Show Notes Fields", True)
            self._add_checkbox("show_week_header", "Show Week Title", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#16A34A")
        elif pt == "Sleep Tracker":
            self._add_spin("num_days", "Number of Days:", 7, 31, 14, 1, 0)
            self._add_spin("row_height", "Row Height (in):", 0.2, 0.6, 0.35, 0.05, 2)
            self._add_checkbox("show_nap_col", "Show Nap Column", True)
            self._add_checkbox("show_quality_col", "Show Quality Column", True)
            self._add_checkbox("show_mood_col", "Show Mood Column", True)
            self._add_checkbox("show_notes_col", "Show Notes Column", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#6366F1")
        elif pt == "Mood Tracker":
            self._add_spin("num_days", "Number of Days:", 14, 31, 31, 1, 0)
            self._add_combo("mood_labels", "Mood Labels:", ["Emoji", "Text"], "Emoji")
            self._add_spin("grid_size", "Cell Size (in):", 0.15, 0.5, 0.25, 0.05, 2)
            self._add_checkbox("show_day_numbers", "Show Day Numbers", True)
            self._add_checkbox("show_month_header", "Show Month Header", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#F59E0B")
        elif pt == "Lesson Plan":
            self._add_spin("num_periods", "Number of Periods:", 1, 10, 6, 1, 0)
            self._add_checkbox("show_objectives", "Show Objectives", True)
            self._add_checkbox("show_materials", "Show Materials", True)
            self._add_checkbox("show_assessment", "Show Assessment", True)
            self._add_checkbox("show_homework", "Show Homework", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#2563EB")
        elif pt == "Expense Tracker":
            self._add_spin("num_rows", "Number of Rows:", 5, 50, 25, 1, 0)
            self._add_spin("row_height", "Row Height (in):", 0.15, 0.5, 0.25, 0.05, 2)
            self._add_spin("header_height", "Header Height (in):", 0.2, 1.5, 0.5, 0.1, 1)
            self._add_checkbox("show_category_col", "Show Category Column", True)
            self._add_checkbox("show_payment_col", "Show Payment Column", True)
            self._add_checkbox("show_balance_col", "Show Balance Row", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#DC2626")
        elif pt == "Baseball Scorecard":
            self._add_spin("num_innings", "Innings:", 3, 12, 9, 1, 0)
            self._add_spin("players_per_team", "Players per Team:", 5, 15, 9, 1, 0)
            self._add_checkbox("show_sub_rows", "Show Sub Rows", True)
            self._add_spin("row_height", "Row Height (pt):", 12, 32, 20, 1, 0)
            self._add_text_input("stat_columns", "Stat Columns (comma-sep):", "R,H,RBI")
            self._add_checkbox("show_totals_row", "Show Totals Row", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#2563EB")
        elif pt == "Atom Diagram":
            self._add_spin("grid_size", "Cell Size (in):", 1.0, 5.0, 2.5, 0.25, 2)
            self._add_spin("num_shells", "Electron Shells:", 1, 7, 4, 1, 0)
            self._add_checkbox("show_electron_dots", "Show Electron Dots", True)
            self._add_checkbox("show_shell_labels", "Show Shell Labels", True)
            self._add_checkbox("show_nucleus", "Show Nucleus", True)
            self._add_spin("nucleus_size", "Nucleus Size (in):", 0.1, 0.8, 0.3, 0.05, 2)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#2563EB")
        elif pt == "Quadrille Paper":
            self._add_spin("grid_size", "Grid Size (in):", 0.05, 1.0, 0.2, 0.05, 2)
            self._add_spin("major_every", "Major Every (cells):", 2, 20, 5, 1, 0)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.2, 0.05, 2)
            self._add_spin("major_dot_radius", "Major Dot Radius (pt):", 0.5, 4.0, 1.0, 0.25, 1)
            self._add_spin("minor_dot_radius", "Minor Dot Radius (pt):", 0.2, 2.0, 0.5, 0.1, 1)
            self._add_spin("major_width", "Major Width (pt):", 0.3, 5.0, 0.6, 0.1, 1)
            self._add_checkbox("dot_mode", "Dot Mode (at intersections)", False)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#AAAAAA")
        elif pt == "Spiral Grid":
            self._add_spin("num_spirals", "Number of Spirals:", 1, 6, 3, 1, 0)
            self._add_spin("turns", "Turns per Spiral:", 1, 10, 4, 1, 0)
            self._add_spin("grid_size", "Grid/Ring Spacing (in):", 0.2, 2.0, 0.5, 0.1, 1)
            self._add_checkbox("show_radials", "Show Radial Lines", True)
            self._add_spin("num_radials", "Number of Radials:", 4, 36, 12, 1, 0)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#6B21A8"); self.combo_secondary.setCurrentText("#C4B5FD")
        elif pt == "Basketball Stat Sheet":
            self._add_spin("num_players", "Number of Players:", 5, 20, 12, 1, 0)
            self._add_spin("num_quarters", "Quarters:", 2, 6, 4, 1, 0)
            self._add_checkbox("show_totals", "Show Totals Row", True)
            self._add_text_input("stat_categories", "Stat Categories (comma-sep):", "Points,Rebounds,Assists,Steals,Blocks")
            self._add_spin("row_height", "Row Height (pt):", 10, 28, 16, 1, 0)
            self._add_spin("title_font_size", "Title Font Size:", 10, 24, 16, 1, 0)
            self._add_checkbox("show_per_minute", "Show Per-Minute Stats", False)
            self._add_checkbox("show_per_minute", "Show Per-Minute Stats", False)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#EA580C")
        elif pt == "Chore Chart":
            self._add_spin("num_chores", "Number of Chores:", 2, 20, 8, 1, 0)
            self._add_combo("days_mode", "Days Mode:", ["weekday", "numbered"], "weekday")
            self._add_checkbox("show_points_col", "Show Points Column", True)
            self._add_spin("label_column_width", "Label Column Width (pt):", 60, 200, 120, 5, 0)
            self._add_spin("checkbox_size", "Checkbox Size (pt):", 4, 20, 10, 1, 0)
            self._add_spin("min_row_height", "Min Row Height (pt):", 10, 40, 18, 1, 0)
            self._add_checkbox("show_parent_initials", "Show Parent Initials", False)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#16A34A")
        elif pt == "Water Intake Tracker":
            self._add_spin("num_days", "Number of Days:", 5, 14, 7, 1, 0)
            self._add_spin("glasses_target", "Glasses/Day Target:", 4, 16, 8, 1, 0)
            self._add_spin("glass_size_oz", "Glass Size (oz):", 4, 16, 8, 1, 0)
            self._add_checkbox("show_total_row", "Show Weekly Total", True)
            self._add_checkbox("show_notes_col", "Show Notes Column", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#0EA5E9")
        elif pt == "Phone Call Log":
            self._add_spin("num_rows", "Number of Rows:", 5, 50, 20, 1, 0)
            self._add_spin("row_height", "Row Height (in):", 0.2, 0.6, 0.3, 0.05, 2)
            self._add_checkbox("show_duration_col", "Show Duration Column", True)
            self._add_checkbox("show_outcome_col", "Show Outcome Column", True)
            self._add_checkbox("show_followup_col", "Show Follow-Up Column", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#2563EB")
        elif pt == "Blood Pressure Log":
            self._add_spin("num_rows", "Number of Rows:", 10, 60, 30, 1, 0)
            self._add_spin("row_height", "Row Height (in):", 0.15, 0.5, 0.25, 0.05, 2)
            self._add_checkbox("show_pulse_col", "Show Pulse Column", True)
            self._add_checkbox("show_notes_col", "Show Notes Column", True)
            self._add_checkbox("show_date_time", "Show Date/Time", True)
            self._add_checkbox("show_header_info", "Show Header Info", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#DC2626")
        elif pt == "SWOT Analysis":
            self._add_combo("layout", "Layout:", ["quadrant", "2x2"], "quadrant")
            self._add_spin("header_height", "Section Header (in):", 0.2, 1.0, 0.4, 0.1, 1)
            self._add_spin("lines_per_section", "Lines Per Section:", 3, 20, 8, 1, 0)
            self._add_checkbox("show_headers", "Show Section Headers", True)
            self._add_checkbox("show_prompt_lines", "Show Writing Lines", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 3.0, 0.5, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#2563EB")
        elif pt == "Doodle Pad":
            self._add_combo("density", "Shape Density:", ["light", "medium", "heavy"], "medium")
            self._add_combo("shape_types", "Shape Types:", ["circles,squares,triangles", "circles", "squares", "triangles", "circles,squares"], "circles,squares,triangles")
            self._add_checkbox("show_border_frame", "Show Border Frame", True)
            self._add_spin("margin", "Margin (in):", 0.1, 1.5, 0.33, 0.05, 2)
            self._add_spin("min_shape_size", "Min Shape Size (pt):", 2, 30, 8, 1, 0)
            self._add_spin("max_shape_size", "Max Shape Size (pt):", 10, 100, 38, 1, 0)
            self._add_spin("corner_radius", "Corner Radius (in):", 0.0, 1.0, 0.0, 0.1, 1)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#D1D5DB"); self.combo_secondary.setCurrentText("#E5E7EB")
        elif pt == "Comic Panel Layout":
            self._add_combo("layout_style", "Layout Style:", ["classic", "grid", "varied"], "classic")
            self._add_spin("num_rows", "Number of Rows:", 1, 8, 3, 1, 0)
            self._add_spin("gutter_width", "Gutter Width (in):", 0.05, 0.5, 0.15, 0.05, 2)
            self._add_spin("panel_border_width", "Panel Border (pt):", 0.5, 5.0, 1.5, 0.5, 1)
            self._add_checkbox("show_gutter_labels", "Show Panel Numbers", False)
            self._add_spin("line_width", "Line Width (pt):", 0.5, 5.0, 1.5, 0.1, 1)
            self.combo_color.setCurrentText("#000000"); self.combo_secondary.setCurrentText("#94A3B8")
        elif pt == "Gardening Planner":
            self._add_spin("num_beds", "Number of Beds:", 1, 8, 4, 1, 0)
            self._add_spin("grid_size", "Bed Grid Size (in):", 0.1, 1.0, 0.25, 0.05, 2)
            self._add_checkbox("show_plant_list", "Show Plant List", True)
            self._add_spin("plant_list_rows", "Plant List Rows:", 3, 20, 10, 1, 0)
            self._add_checkbox("show_sun_indicator", "Show Sun Indicator", True)
            self._add_checkbox("show_notes_section", "Show Notes Section", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#16A34A")
        elif pt == "Timeline":
            self._add_combo("orientation", "Orientation:", ["horizontal", "vertical"], "horizontal")
            self._add_spin("num_events", "Number of Events:", 3, 20, 8, 1, 0)
            self._add_spin("marker_size", "Marker Size (in):", 0.05, 0.5, 0.15, 0.05, 2)
            self._add_checkbox("show_date_fields", "Show Date Fields", True)
            self._add_checkbox("show_year_markers", "Show Year Markers", False)
            self._add_checkbox("arrow_style", "Arrow at End", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.5, 0.1, 1)
            self.combo_color.setCurrentText("#2563EB"); self.combo_secondary.setCurrentText("#93C5FD")
        elif pt == "Insect Observation Log":
            self._add_spin("num_rows", "Number of Rows:", 3, 20, 10, 1, 0)
            self._add_spin("row_height", "Row Height (in):", 0.3, 1.0, 0.6, 0.1, 1)
            self._add_checkbox("show_habitat_col", "Show Habitat Column", True)
            self._add_checkbox("show_behavior_col", "Show Behavior Column", True)
            self._add_checkbox("show_weather_col", "Show Weather Column", True)
            self._add_checkbox("show_drawing_area", "Show Drawing Area", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#16A34A")
        elif pt == "Medication Log":
            self._add_spin("num_rows", "Number of Rows:", 5, 40, 20, 1, 0)
            self._add_spin("row_height", "Row Height (in):", 0.15, 0.5, 0.3, 0.05, 2)
            self._add_checkbox("show_time_col", "Show Time Column", True)
            self._add_checkbox("show_dosage_col", "Show Dosage Column", True)
            self._add_checkbox("show_notes_col", "Show Notes Column", True)
            self._add_checkbox("show_header_info", "Show Header Info", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#7C3AED")
        elif pt == "Number Bonds":
            self._add_spin("num_problems", "Number of Problems:", 4, 20, 10, 1, 0)
            self._add_combo("target_range", "Target Range:", ["1-10", "1-20", "10-100"], "1-10")
            self._add_checkbox("show_number_bonds", "Show Bond Diagrams", True)
            self._add_checkbox("show_addition", "Show Addition Signs", True)
            self._add_checkbox("show_subtraction", "Show Subtraction Signs", True)
            self._add_combo("problem_layout", "Layout:", ["2x5", "3x4", "2x5"], "2x5")
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#F59E0B")
        elif pt == "Stargazing Log":
            self._add_spin("num_rows", "Number of Rows:", 3, 20, 10, 1, 0)
            self._add_spin("row_height", "Row Height (in):", 0.3, 1.0, 0.5, 0.1, 1)
            self._add_checkbox("show_constellation_col", "Show Constellation", True)
            self._add_checkbox("show_magnitude_col", "Show Magnitude", True)
            self._add_checkbox("show_weather_col", "Show Conditions", True)
            self._add_checkbox("show_drawing_area", "Show Sketch Area", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#1E3A5F")
        elif pt == "Writing Sprint Tracker":
            self._add_spin("num_sprints", "Number of Sprints:", 5, 30, 15, 1, 0)
            self._add_spin("target_words", "Target Words/Day:", 100, 10000, 1667, 1, 0)
            self._add_checkbox("show_project_name", "Show Project Field", True)
            self._add_checkbox("show_daily_total", "Show Daily Total Row", True)
            self._add_checkbox("show_cumulative", "Show Cumulative Column", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#DC2626")
        elif pt == "Attendance Register":
            self._add_spin("num_students", "Number of Students:", 5, 50, 25, 1, 0)
            self._add_spin("num_days", "Number of Days:", 5, 31, 20, 1, 0)
            self._add_checkbox("show_student_id", "Show Student ID Column", True)
            self._add_checkbox("show_totals_col", "Show Totals Column", True)
            self._add_checkbox("show_absence_codes", "Show Absence Codes Legend", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#16A34A")
        elif pt == "Chess Score Sheet":
            self._add_spin("num_rows", "Number of Move Rows:", 20, 60, 40, 1, 0)
            self._add_spin("move_number_width", "Move # Column (in):", 0.3, 1.0, 0.5, 0.1, 1)
            self._add_checkbox("show_player_names", "Show Player Name Fields", True)
            self._add_spin("margin", "Margin (in):", 0.25, 1.5, 0.5, 0.125, 3)
            self._add_spin("row_height", "Row Height (pt):", 10, 28, 14, 1, 0)
            self._add_spin("label_font_size", "Label Font Size:", 5, 12, 7, 1, 0)
            self._add_checkbox("show_result_area", "Show Result Area", True)
            self._add_checkbox("show_date_location", "Show Date/Location", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#78716C")
        elif pt == "Wish List":
            self._add_spin("num_rows", "Number of Items:", 5, 30, 15, 1, 0)
            self._add_checkbox("show_priority_col", "Show Priority Column", True)
            self._add_checkbox("show_price_col", "Show Price Column", True)
            self._add_checkbox("show_store_col", "Show Store/Link Column", True)
            self._add_checkbox("show_status_col", "Show Status Column", True)
            self._add_checkbox("show_notes_col", "Show Notes Column", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#EC4899")
        elif pt == "Gratitude Journal":
            self._add_spin("num_entries", "Number of Entries:", 3, 14, 7, 1, 0)
            self._add_spin("prompts_per_entry", "Prompts Per Entry:", 1, 5, 3, 1, 0)
            self._add_checkbox("show_rating_col", "Show Gratitude Rating", True)
            self._add_checkbox("show_date_field", "Show Date Field", True)
            self._add_checkbox("show_mood_check", "Show Mood Check", True)
            self._add_spin("line_width", "Line Width (pt):", 0.1, 2.0, 0.3, 0.1, 1)
            self.combo_color.setCurrentText("#333333"); self.combo_secondary.setCurrentText("#F59E0B")
        elif pt == "Blank":
            pass

    def get_params(self) -> dict:
        params = {"color": self.combo_color.currentText(), "secondary_color": self.combo_secondary.currentText()}
        for attr_name in list(dir(self)):
            if attr_name.startswith("spin_"):
                key = attr_name[5:]; widget = getattr(self, attr_name)
                if isinstance(widget, (QSpinBox, QDoubleSpinBox)): params[key] = widget.value()
            elif attr_name.startswith("check_"):
                key = attr_name[6:]; widget = getattr(self, attr_name)
                if isinstance(widget, QCheckBox): params[key] = widget.isChecked()
            elif attr_name.startswith("combo_"):
                key = attr_name[6:]; widget = getattr(self, attr_name)
                if isinstance(widget, QComboBox): params[key] = widget.currentText()
        return params

    def get_page_size_pt(self) -> tuple:
        return PAGE_SIZES.get(self.combo_pagesize.currentText(), (612, 792))
    def get_bg_color(self) -> str: return self.combo_bg.currentText()
    def get_show_page_numbers(self) -> bool: return self.check_page_numbers.isChecked()
    def get_double_sided(self) -> bool: return self.check_double_sided.isChecked()


# ─────────────────────────────────────────────────────────────
# Presets Dialog
# ─────────────────────────────────────────────────────────────
class PresetsDialog(QDialog):
    def __init__(self, presets_mgr, parent=None):
        super().__init__(parent); self.pm = presets_mgr
        self.setWindowTitle("Manage Presets"); self.setMinimumSize(400, 500); self._build_ui(); self._refresh_list()
    def _build_ui(self):
        layout = QVBoxLayout(self); self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self._on_double_click); layout.addWidget(self.list)
        btn_row = QHBoxLayout()
        for text, slot in [("Load", self._load), ("Rename", self._rename), ("Delete", self._delete)]:
            btn = QPushButton(text); btn.clicked.connect(slot); btn_row.addWidget(btn)
        btn_row.addStretch(); btn_close = QPushButton("Close"); btn_close.clicked.connect(self.reject)
        btn_row.addWidget(btn_close); layout.addLayout(btn_row)
    def _refresh_list(self):
        self.list.clear()
        for name in self.pm.list_presets(): self.list.addItem(QListWidgetItem(name))
    def _load(self):
        item = self.list.currentItem()
        if not item: QMessageBox.warning(self, "Warning", "Select a preset first."); return
        self._result = "load"; self._preset_name = item.text(); self.accept()
    def _rename(self):
        item = self.list.currentItem()
        if not item: return
        old = item.text(); new, ok = QInputDialog.getText(self, "Rename Preset", "New name:", text=old)
        if ok and new and new != old: self.pm.rename_preset(old, new); self._refresh_list()
    def _delete(self):
        item = self.list.currentItem()
        if not item: return
        r = QMessageBox.question(self, "Delete", f"Delete preset '{item.text()}'?", QMessageBox.Yes | QMessageBox.No)
        if r == QMessageBox.Yes: self.pm.delete_preset(item.text()); self._refresh_list()
    def _on_double_click(self, item):
        self._result = "load"; self._preset_name = item.text(); self.accept()


# ─────────────────────────────────────────────────────────────
# Batch Export Dialog
# ─────────────────────────────────────────────────────────────
class BatchExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("Batch Export"); self.setMinimumSize(350, 450)
        self._selected = []; self._build_ui()
    def _build_ui(self):
        layout = QVBoxLayout(self); layout.addWidget(QLabel("Select paper types to include:"))
        self.list = QListWidget(); self.list.setSelectionMode(QListWidget.MultiSelection)
        self.list.addItems(PAPER_TYPES); layout.addWidget(self.list)
        pages_row = QHBoxLayout()
        pages_row.addWidget(QLabel("Pages per type:"))
        self.spin_pages = QSpinBox(); self.spin_pages.setRange(1, 100); self.spin_pages.setValue(1)
        pages_row.addWidget(self.spin_pages); pages_row.addStretch()
        layout.addLayout(pages_row)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._accept); btns.rejected.connect(self.reject); layout.addWidget(btns)
    def _accept(self):
        self._selected = [item.text() for item in self.list.selectedItems()]
        if not self._selected: QMessageBox.warning(self, "Warning", "Select at least one."); return
        self.accept()
    def get_selected(self): return self._selected


# ─────────────────────────────────────────────────────────────
# Styles
# ─────────────────────────────────────────────────────────────
LIGHT_STYLE = """
    QMainWindow { background-color: #F1F5F9; }
    QGroupBox { font-weight: bold; font-size: 13px; border: 1px solid #CBD5E1; border-radius: 8px; margin-top: 12px; padding: 16px 10px 10px 10px; background-color: #FFFFFF; }
    QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #334155; }
    QComboBox, QSpinBox, QDoubleSpinBox { padding: 6px 10px; border: 1px solid #CBD5E1; border-radius: 6px; background: #F8FAFC; font-size: 13px; color: #1E293B; }
    QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border-color: #2563EB; }
    QComboBox QAbstractItemView { background: #FFFFFF; color: #1E293B; selection-background-color: #2563EB; selection-color: white; }
    QLabel { font-size: 13px; color: #475569; }
    QCheckBox { font-size: 13px; color: #475569; spacing: 6px; }
    QCheckBox::indicator { width: 16px; height: 16px; }
    QScrollArea { border: none; background: transparent; }
    QStatusBar { background: #E2E8F0; color: #475569; font-size: 12px; }
    QToolBar { background: #FFFFFF; border-bottom: 1px solid #E2E8F0; spacing: 6px; padding: 4px; }
    QToolButton { color: #334155; padding: 6px; border-radius: 4px; }
    QToolButton:hover { background: #F1F5F9; }
    QMenuBar { background: #FFFFFF; color: #334155; }
    QMenuBar::item:selected { background: #F1F5F9; }
    QMenu { background: #FFFFFF; color: #334155; border: 1px solid #E2E8F0; }
    QMenu::item:selected { background: #2563EB; color: white; }
    QMessageBox { background: #FFFFFF; }
"""
DARK_STYLE = """
    QMainWindow { background-color: #0F172A; }
    QGroupBox { font-weight: bold; font-size: 13px; border: 1px solid #334155; border-radius: 8px; margin-top: 12px; padding: 16px 10px 10px 10px; background-color: #1E293B; }
    QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #CBD5E1; }
    QComboBox, QSpinBox, QDoubleSpinBox { padding: 6px 10px; border: 1px solid #475569; border-radius: 6px; background: #334155; font-size: 13px; color: #E2E8F0; }
    QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border-color: #3B82F6; }
    QComboBox QAbstractItemView { background: #334155; color: #E2E8F0; selection-background-color: #3B82F6; selection-color: white; }
    QLabel { font-size: 13px; color: #94A3B8; }
    QCheckBox { font-size: 13px; color: #94A3B8; spacing: 6px; }
    QScrollArea { border: none; background: transparent; }
    QStatusBar { background: #1E293B; color: #64748B; font-size: 12px; }
    QToolBar { background: #1E293B; border-bottom: 1px solid #334155; spacing: 6px; padding: 4px; }
    QToolButton { color: #CBD5E1; padding: 6px; border-radius: 4px; }
    QToolButton:hover { background: #334155; }
    QMenuBar { background: #1E293B; color: #CBD5E1; }
    QMenuBar::item:selected { background: #334155; }
    QMenu { background: #1E293B; color: #CBD5E1; border: 1px solid #334155; }
    QMenu::item:selected { background: #3B82F6; color: white; }
"""


# ─────────────────────────────────────────────────────────────
# Main Window
# ─────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v7")
        self.setMinimumSize(1100, 750); self.resize(1280, 860)
        self._dark_mode = False; self._presets_mgr = PresetsManager()
        self._build_ui(); self._build_toolbar(); self._build_menubar()
        self._connect_signals(); self._apply_theme(LIGHT_STYLE)
        self.settings_panel._build_paper_settings("Graph Paper")

    def _build_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        main_layout = QHBoxLayout(central); main_layout.setContentsMargins(8, 8, 8, 8); main_layout.setSpacing(8)
        left = QFrame(); left.setFrameShape(QFrame.StyledPanel); self._left_frame = left
        ll = QVBoxLayout(left); ll.setContentsMargins(4, 4, 4, 4)
        self.preview = PaperPreviewWidget()
        header = QHBoxLayout()
        lbl = QLabel("Preview"); lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #1E293B; padding: 2px 0;")
        header.addWidget(lbl); header.addStretch()
        self.btn_zoom_in = QToolButton(); self.btn_zoom_in.setText("+"); self.btn_zoom_in.setToolTip("Zoom In")
        self.btn_zoom_in.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px 10px; border-radius: 4px; border: 1px solid #CBD5E1;")
        self.btn_zoom_in.clicked.connect(self.preview.zoom_in); header.addWidget(self.btn_zoom_in)
        self.btn_zoom_out = QToolButton(); self.btn_zoom_out.setText("-"); self.btn_zoom_out.setToolTip("Zoom Out")
        self.btn_zoom_out.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px 10px; border-radius: 4px; border: 1px solid #CBD5E1;")
        self.btn_zoom_out.clicked.connect(self.preview.zoom_out); header.addWidget(self.btn_zoom_out)
        self.btn_zoom_fit = QToolButton(); self.btn_zoom_fit.setText("Fit"); self.btn_zoom_fit.setToolTip("Fit to View")
        self.btn_zoom_fit.setStyleSheet("font-size: 12px; padding: 4px 10px; border-radius: 4px; border: 1px solid #CBD5E1;")
        self.btn_zoom_fit.clicked.connect(self.preview.zoom_fit); header.addWidget(self.btn_zoom_fit)
        ll.addLayout(header); ll.addWidget(self.preview); main_layout.addWidget(left, stretch=3)
        self.settings_panel = SettingsPanel(); main_layout.addWidget(self.settings_panel, stretch=0)
        self.statusBar().showMessage("Ready  --  select a paper type and click Generate PDF")

    def _build_toolbar(self):
        tb = QToolBar("Main Toolbar"); tb.setMovable(False); self.addToolBar(tb)
        act_reset = QAction("Reset", self); act_reset.setToolTip("Reset to defaults"); act_reset.setShortcut(QKeySequence("Ctrl+R"))
        act_reset.triggered.connect(self._reset_defaults); tb.addAction(act_reset); tb.addSeparator()
        act_save = QAction("Save Preset", self); act_save.setShortcut(QKeySequence("Ctrl+S"))
        act_save.triggered.connect(self._save_preset); tb.addAction(act_save)
        act_load = QAction("Load Preset", self); act_load.setShortcut(QKeySequence("Ctrl+L"))
        act_load.triggered.connect(self._load_preset); tb.addAction(act_load); tb.addSeparator()
        act_batch = QAction("Batch Export", self); act_batch.triggered.connect(self._batch_export); tb.addAction(act_batch)
        tb.addSeparator()
        act_dark = QAction("Dark Mode", self); act_dark.setCheckable(True); act_dark.setShortcut(QKeySequence("Ctrl+D"))
        act_dark.triggered.connect(self._toggle_dark_mode); tb.addAction(act_dark); self._dark_action = act_dark

    def _build_menubar(self):
        mb = self.menuBar()
        fm = mb.addMenu("File")
        fm.addAction("Generate PDF...", self._generate_pdf, QKeySequence("Ctrl+G"))
        fm.addAction("Batch Export...", self._batch_export); fm.addSeparator()
        fm.addAction("Print...", self._print_pdf, QKeySequence("Ctrl+P")); fm.addSeparator()
        fm.addAction("Exit", self.close, QKeySequence("Ctrl+Q"))
        em = mb.addMenu("Edit")
        em.addAction("Reset to Defaults", self._reset_defaults, QKeySequence("Ctrl+R"))
        em.addAction("Save Preset", self._save_preset, QKeySequence("Ctrl+S"))
        em.addAction("Load Preset", self._load_preset, QKeySequence("Ctrl+L"))
        vm = mb.addMenu("View")
        vm.addAction("Zoom In", self.preview.zoom_in, QKeySequence.ZoomIn)
        vm.addAction("Zoom Out", self.preview.zoom_out, QKeySequence.ZoomOut)
        vm.addAction("Fit to View", self.preview.zoom_fit, QKeySequence("Ctrl+0")); vm.addSeparator()
        vm.addAction("Dark Mode", self._toggle_dark_mode, QKeySequence("Ctrl+D"))
        hm = mb.addMenu("Help"); hm.addAction("About", self._show_about)

    def _connect_signals(self):
        sp = self.settings_panel; sp.settings_changed.connect(self._update_preview)
        sp.combo_type.currentTextChanged.connect(self._on_type_changed)
        sp.btn_generate.clicked.connect(self._generate_pdf)

    def _on_type_changed(self, text):
        self.preview.set_paper_type(text); self._update_preview()

    def _update_preview(self):
        self.preview.set_page_size(self.settings_panel.get_page_size_pt())
        self.preview.set_orientation(self.settings_panel.combo_orient.currentText())
        self.preview.set_bg_color(self.settings_panel.get_bg_color())
        self.preview.set_page_numbers(self.settings_panel.get_show_page_numbers())
        for k, v in self.settings_panel.get_params().items(): self.preview.update_param(k, v)
        self.preview.update()

    def _apply_theme(self, style): self.setStyleSheet(style)

    def _toggle_dark_mode(self):
        self._dark_mode = not self._dark_mode; self._dark_action.setChecked(self._dark_mode)
        self._apply_theme(DARK_STYLE if self._dark_mode else LIGHT_STYLE)
        if self._dark_mode: self._left_frame.setStyleSheet("QFrame { background: #0F172A; border-radius: 12px; }")
        else: self._left_frame.setStyleSheet("QFrame { background: #FFFFFF; border-radius: 12px; }")

    def _reset_defaults(self):
        pt = self.settings_panel.combo_type.currentText()
        self.settings_panel.combo_pagesize.setCurrentIndex(0)
        self.settings_panel.combo_orient.setCurrentText("Portrait")
        self.settings_panel.spin_pages.setValue(1)
        self.settings_panel.check_page_numbers.setChecked(False)
        self.settings_panel.check_double_sided.setChecked(False)
        self.settings_panel.combo_bg.setCurrentText("#FFFFFF")
        self.settings_panel._build_paper_settings(pt)
        self.statusBar().showMessage("Settings reset to defaults")

    def _save_preset(self):
        name, ok = QInputDialog.getText(self, "Save Preset", "Preset name:")
        if ok and name.strip():
            name = name.strip()
            self._presets_mgr.save_preset(name, self.settings_panel.combo_type.currentText(),
                self.settings_panel.get_params(), self.settings_panel.combo_pagesize.currentText(),
                self.settings_panel.combo_orient.currentText())
            self.statusBar().showMessage(f"Preset '{name}' saved")

    def _load_preset(self):
        dlg = PresetsDialog(self._presets_mgr, self)
        if dlg.exec() == QDialog.Accepted and dlg._result == "load":
            data = self._presets_mgr.load_preset(dlg._preset_name)
            if data:
                idx = self.settings_panel.combo_type.findText(data["paper_type"])
                if idx >= 0: self.settings_panel.combo_type.setCurrentIndex(idx)
                idx = self.settings_panel.combo_pagesize.findText(data["page_size_key"])
                if idx >= 0: self.settings_panel.combo_pagesize.setCurrentIndex(idx)
                idx = self.settings_panel.combo_orient.findText(data["orientation"])
                if idx >= 0: self.settings_panel.combo_orient.setCurrentIndex(idx)
                self.settings_panel._build_paper_settings(data["paper_type"])
                params = data.get("params", {})
                for key, value in params.items():
                    spin = getattr(self.settings_panel, f"spin_{key}", None)
                    if spin and isinstance(spin, (QSpinBox, QDoubleSpinBox)): spin.setValue(value)
                    chk = getattr(self.settings_panel, f"check_{key}", None)
                    if chk and isinstance(chk, QCheckBox): chk.setChecked(value)
                    cmb = getattr(self.settings_panel, f"combo_{key}", None)
                    if cmb and isinstance(cmb, QComboBox):
                        idx = cmb.findText(str(value))
                        if idx >= 0: cmb.setCurrentIndex(idx)
                if "color" in params:
                    self.settings_panel.combo_color.setCurrentText(params["color"])
                    self.settings_panel.btn_color_picker.set_color(params["color"])
                if "secondary_color" in params:
                    self.settings_panel.combo_secondary.setCurrentText(params["secondary_color"])
                    self.settings_panel.btn_secondary_picker.set_color(params["secondary_color"])
                self.statusBar().showMessage(f"Preset '{dlg._preset_name}' loaded")

    def _generate_pdf(self):
        pt = self.settings_panel.combo_type.currentText()
        psz = self.settings_panel.get_page_size_pt()
        orient = self.settings_panel.combo_orient.currentText()
        params = self.settings_panel.get_params()
        pages = self.settings_panel.spin_pages.value()
        bg = self.settings_panel.get_bg_color()
        pn = self.settings_panel.get_show_page_numbers()
        ds = self.settings_panel.get_double_sided()
        default_name = f"{pt.lower().replace(' ', '_').replace('/', '_')}.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", default_name, "PDF Files (*.pdf)")
        if not path: return
        try:
            if pages > 10:
                progress = QProgressDialog("Generating PDF...", "Cancel", 0, pages, self)
                progress.setWindowTitle("Generating..."); progress.setWindowModality(Qt.WindowModal)
                progress.setMinimumDuration(0); progress.show()
                def cb(pg):
                    progress.setValue(pg)
                    if progress.wasCanceled(): raise InterruptedError("Cancelled")
                    QApplication.processEvents()
                gen = PaperPDFGenerator(pt, psz, orient, params, pages, bg, pn, ds)
                gen.generate(path, progress_cb=cb); progress.close()
            else:
                gen = PaperPDFGenerator(pt, psz, orient, params, pages, bg, pn, ds)
                gen.generate(path)
            self.statusBar().showMessage(f"PDF saved: {path}")
            QMessageBox.information(self, "Success", f"Generated {pages} page(s) of {pt}!\nSaved to:\n{path}")
        except InterruptedError: self.statusBar().showMessage("Generation cancelled")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate PDF:\n{e}")
            self.statusBar().showMessage("Error generating PDF")

    def _batch_export(self):
        dlg = BatchExportDialog(self)
        if dlg.exec() != QDialog.Accepted: return
        selected = dlg.get_selected()
        pages_per = dlg.spin_pages.value()
        path, _ = QFileDialog.getSaveFileName(self, "Save Batch PDF", "batch_paper.pdf", "PDF Files (*.pdf)")
        if not path: return
        try:
            psz = self.settings_panel.get_page_size_pt()
            orient = self.settings_panel.combo_orient.currentText()
            bg = self.settings_panel.get_bg_color()
            pn = self.settings_panel.get_show_page_numbers()
            ds = self.settings_panel.get_double_sided()
            total = len(selected) * pages_per
            progress = QProgressDialog(f"Generating {total} pages...", "Cancel", 0, total, self)
            progress.setWindowTitle("Batch Export"); progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0); progress.show()
            pdf = FPDF(orientation="P", unit="pt", format=(psz[0], psz[1]))
            if orient == "Landscape": pdf = FPDF(orientation="L", unit="pt", format=(psz[1], psz[0]))
            pdf.set_auto_page_break(False); pdf.set_margins(0, 0, 0)
            pg_count = 0
            for pt_name in selected:
                params = dict(DEFAULT_PARAMS.get(pt_name, {}))
                gen = PaperPDFGenerator(pt_name, psz, orient, params, pages_per, bg, pn, ds)
                for pg in range(1, pages_per + 1):
                    pdf.add_page()
                    r, g, b = hex_to_rgb(bg); pdf.set_fill_color(r, g, b)
                    pw, ph = psz
                    if orient == "Landscape": pw, ph = ph, pw
                    pdf.rect(0, 0, pw, ph, style="F")
                    draw_fn = getattr(gen, f"_draw_{pt_name.lower().replace(' ', '_')}", None)
                    if draw_fn: draw_fn(pdf, pw, ph, pg)
                    if pn:
                        pdf.set_font("Helvetica", "", 9); pdf.set_text_color(153, 153, 153)
                        pdf.text(pw / 2 - 4, ph - 20, str(pg_count + 1))
                    pg_count += 1
                    progress.setValue(pg_count)
                    if progress.wasCanceled(): break
                QApplication.processEvents()
                if progress.wasCanceled(): break
            pdf.output(path); progress.close()
            self.statusBar().showMessage(f"Batch PDF saved: {path}")
            QMessageBox.information(self, "Success", f"Batch PDF with {len(selected)} types x {pages_per} pages = {pg_count} pages saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Batch export failed:\n{e}")

    def _print_pdf(self):
        pt = self.settings_panel.combo_type.currentText()
        psz = self.settings_panel.get_page_size_pt()
        orient = self.settings_panel.combo_orient.currentText()
        params = self.settings_panel.get_params()
        pages = self.settings_panel.spin_pages.value()
        bg = self.settings_panel.get_bg_color()
        pn = self.settings_panel.get_show_page_numbers()
        ds = self.settings_panel.get_double_sided()
        tmp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_print_temp.pdf")
        try:
            gen = PaperPDFGenerator(pt, psz, orient, params, pages, bg, pn, ds); gen.generate(tmp_path)
            from PySide6.QtPrintDialog import QPrintDialog
            from PySide6.QtGui import QPrinter
            printer = QPrinter(QPrinter.HighResolution)
            dlg = QPrintDialog(printer, self)
            if dlg.exec() == QDialog.Accepted: self.statusBar().showMessage("Sent to printer")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Print failed:\n{e}")

    def _show_about(self):
        QMessageBox.about(self, f"About {APP_NAME}",
            f"<h2>{APP_NAME} v7</h2>"
            "<p>A full-featured PySide6 desktop app for creating printable paper PDFs.</p>"
            f"<p><b>{len(PAPER_TYPES)} paper types</b> with extensive customization options.</p>"
            "<p>v7: All settings now fully wired to draw methods. Added cards_per_col,<br>"
            "panel_border_radius, start_day, start_angle, show_timer_section,<br>"
            "show_week_header, corner_radius controls. Batch export now supports<br>"
            "pages-per-type with custom colors and page numbers.</p>"
            "<p>Built with PySide6 + fpdf2.</p>")

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.ZoomIn): self.preview.zoom_in()
        elif event.matches(QKeySequence.ZoomOut): self.preview.zoom_out()
        elif event.key() == Qt.Key_0 and event.modifiers() & Qt.ControlModifier: self.preview.zoom_fit()
        else: super().keyPressEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
