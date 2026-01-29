You are a senior PyQt6 UI engineer.

I need pixel-accurate PyQt6 implementation of a control dashboard exactly as in provided mockups.

Do NOT redesign.
Do NOT choose your own styles.
Follow sizes, colors, and layout strictly.

Window:
Fixed size: 1200x700. Non-resizable.

Main layout:
Horizontal layout with 3 vertical sections:

1) Left panel — width 260px
2) Center panel — width 680px
3) Right panel — width 260px

GLOBAL FONT:
Segoe UI

COLORS:
Header green: #39B54A
Left background: #EDEDED
Terminal black: #0D0D0D
Warning yellow: #F4C542
Critical red: #E53935
Text dark: #222222

========================
LEFT PANEL (vertical layout)
========================
Top title: "Меню управления"

Under it — 3 rounded buttons:
Инструкция (purple)
Анализ (purple)
Управление (green active)

Block with date/time and status text.

Terminal block:
Black rectangle with white text lines.

Bottom block:
"Допустимое время"
Flip clock style digits, very large font.

========================
CENTER PANEL
========================
Top green header with title:
"НейроБод — Программа для мониторинга состояния водителя"

Below it:
Background image filling whole panel (road landscape).

Above background:
Large label:
"Пульс: XX"
Font size 42px bold.

Depending on state:
Normal — white
Warning — yellow
Critical — red

========================
RIGHT PANEL
========================
Title: "Идентификация"

Text:
"Оператор определен: Иванов Иван"

Below:
Square avatar with green frame corners (like camera detection frame)

========================
STATES
========================
Support 3 UI modes:

NORMAL:
green accents

WARNING:
yellow pulse text and warning label

CRITICAL:
red pulse text and critical label

Implement as separate QWidget classes:
LeftPanel, CenterPanel, RightPanel, Header.

Assemble them in MainWindow.

Use QSS stylesheets for ALL styling.
No inline styles.

Return FULL WORKING CODE.
