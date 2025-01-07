"""
Frontend part
"""

from collections import deque
from typing import Optional, Callable

import flet as ft

from src.utils import trigonometry
from src.utils.logging_meta import LoggingMeta
from src.service import Service, Grid, Pitch, MelodyData, Triad, MAJOR_CHORDS, MINOR_CHORDS


class AppBar(ft.AppBar, metaclass=LoggingMeta):

    def __init__(self,
                 on_btn_settings_click: Callable,
                 on_btn_refresh_click: Callable,
                 on_btn_folder_click: Callable
                 ) -> None:

        self._btn_theme = ft.IconButton(ft.Icons.BRIGHTNESS_3, on_click=self._on_btn_theme_click)
        self._btn_settings = ft.IconButton(ft.Icons.SETTINGS, on_click=on_btn_settings_click)
        self._btn_refresh = ft.IconButton(ft.Icons.REFRESH, on_click=on_btn_refresh_click)
        self._btn_folder = ft.IconButton(ft.Icons.FOLDER, on_click=on_btn_folder_click)

        super(AppBar, self).__init__(
            actions=[
                self._btn_theme,
                self._btn_settings,
                self._btn_refresh,
                self._btn_folder,
                ft.Container(width=10)
            ]
        )

    def _on_btn_theme_click(self, e: ft.ControlEvent) -> None:

        if self.page.theme_mode == ft.ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.DARK
            self._btn_theme.icon = ft.Icons.BRIGHTNESS_3
        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self._btn_theme.icon = ft.Icons.BRIGHTNESS_5

        self.page.update()


class BarsContainer(ft.UserControl, metaclass=LoggingMeta):

    class BarRow(ft.UserControl):

        class Cell(ft.UserControl):

            def __init__(self, grid: Grid, dark: bool, active: bool = True, pitch: Optional[Pitch] = None) -> None:
                super(BarsContainer.BarRow.Cell, self).__init__()
                self._grid = grid
                self._dark = dark
                self._pitch = pitch
                self._active = active

            def build(self) -> ft.Container:

                if self._grid == Grid.SIXTEENTHS:
                    width = 36
                else:
                    width = 72

                if self._pitch:
                    content = ft.ElevatedButton(self._pitch.name)
                else:
                    content = None

                bgcolor = self._get_bgcolor()

                return ft.Container(
                    alignment=ft.alignment.center,
                    padding=3,
                    border_radius=3,
                    width=width,
                    height=36,
                    bgcolor=bgcolor,
                    content=content
                )

            def switch_active(self) -> None:
                self._active = not self._active
                bgcolor = self._get_bgcolor()
                self.controls[0].bgcolor = bgcolor
                self.update()

            def _get_bgcolor(self) -> ft.Colors:

                light_color, dark_color = [ft.Colors.PRIMARY, ft.Colors.INVERSE_PRIMARY]
                light_grey, dark_grey = [ft.Colors.OUTLINE, ft.Colors.OUTLINE_VARIANT]

                if self._active:
                    return dark_color if self._dark else light_color
                else:
                    return dark_grey if self._dark else light_grey

        def __init__(self, grid: Grid) -> None:
            super(BarsContainer.BarRow, self).__init__()
            self._grid = grid
            self._melody_data = MelodyData.empty(grid)
            self._btn_chord: ft.OutlinedButton = ...
            self._row_cells: ft.Row = ...
            self._switch: ft.Switch = ...
            self.on_btn_chord_click: Callable = ...

        def build(self) -> ft.Row:

            self._btn_chord = ft.OutlinedButton(
                text=" ",
                width=64,
                height=64,
                style=ft.ButtonStyle(padding=ft.padding.all(5)),
                on_click=self._on_btn_chord_click
            )

            self._switch = ft.Switch(value=True, on_change=self._on_switch_change)

            self._row_cells = ft.Row(
                controls=self._build_cells_for_melody_data(),
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )

            return ft.Row(
                controls=[
                    self._btn_chord,
                    ft.Container(width=600, height=36, content=self._row_cells),
                    self._switch
                ],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY
            )

        @property
        def cells(self) -> list[Cell]:
            return self._row_cells.controls

        @property
        def chord(self) -> Optional[Triad]:
            return self._btn_chord.data

        @chord.setter
        def chord(self, chord: Optional[Triad]) -> None:
            self._btn_chord.data = chord
            self._btn_chord.text = chord.name
            self._btn_chord.update()

        @property
        def active(self) -> bool:
            return self._switch.value

        @property
        def melody_data(self) -> MelodyData:
            return self._melody_data

        @melody_data.setter
        def melody_data(self, melody_data: MelodyData) -> None:
            self._melody_data = melody_data
            self._row_cells.clean()
            self._row_cells.controls = self._build_cells_for_melody_data()
            self._row_cells.update()

        @property
        def params(self) -> dict:
            return {
                "chord": self.chord,
                "active": self.active,
                "melody_data": self.melody_data
            }

        def reset_grid(self, grid: Grid) -> None:
            self._grid = grid
            self.melody_data = MelodyData.empty(grid)

        def _build_cells_for_melody_data(self) -> list[Cell]:

            if self._grid == Grid.EIGHTS:
                darks = [0, 0, 1, 1, 0, 0, 1, 1]
            else:
                darks = [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1]
            darks = [bool(d) for d in darks]

            return [
                BarsContainer.BarRow.Cell(
                    grid=self._grid,
                    dark=dark,
                    active=self.active,
                    pitch=pitch
                )
                for dark, pitch in zip(darks, self._melody_data.scheme)
            ]

        def _on_btn_chord_click(self, e: ft.ControlEvent) -> None:
            if callable(self.on_btn_chord_click):
                self.on_btn_chord_click(self)

        def _on_switch_change(self, e: ft.ControlEvent) -> None:
            for cell in self.cells:
                cell.switch_active()

    def __init__(self, grid: Grid) -> None:
        super(BarsContainer, self).__init__()
        self._grid = grid
        self._bar_1: BarsContainer.BarRow = ...
        self._bar_2: BarsContainer.BarRow = ...
        self._bar_3: BarsContainer.BarRow = ...
        self._bar_4: BarsContainer.BarRow = ...
        self.on_btn_chord_click: Callable = ...

    def build(self) -> ft.Container:

        self._bar_1 = BarsContainer.BarRow(self._grid)
        self._bar_2 = BarsContainer.BarRow(self._grid)
        self._bar_3 = BarsContainer.BarRow(self._grid)
        self._bar_4 = BarsContainer.BarRow(self._grid)

        self._bar_1.on_btn_chord_click = self._on_btn_chord_click
        self._bar_2.on_btn_chord_click = self._on_btn_chord_click
        self._bar_3.on_btn_chord_click = self._on_btn_chord_click
        self._bar_4.on_btn_chord_click = self._on_btn_chord_click

        return ft.Container(
            bgcolor=ft.Colors.SURFACE,
            width=800,
            height=400,
            border_radius=15,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            padding=10,
            content=ft.Column(
                [
                    self._bar_1, ft.Divider(),
                    self._bar_2, ft.Divider(),
                    self._bar_3, ft.Divider(),
                    self._bar_4
                ],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY
            )
        )

    @property
    def bars(self) -> list[BarRow]:
        return [self._bar_1, self._bar_2, self._bar_3, self._bar_4]

    @property
    def melody_data(self) -> list[MelodyData]:
        return [b.melody_data for b in self.bars]

    @melody_data.setter
    def melody_data(self, melody_data: list[MelodyData]) -> None:
        for bar, md in zip(self.bars, melody_data):
            bar.melody_data = md

    @property
    def bar_params(self) -> list[dict]:
        return [b.params for b in self.bars]

    def reset_grid(self, grid: Grid) -> None:
        self._grid = grid
        for bar in self.bars:
            bar.reset_grid(grid)

    def set_chords(self, chords: list[Triad]) -> None:
        for bar, chord in zip(self.bars, chords):
            bar.chord = chord

    def set_chord(self, chord: Triad, idx: int) -> None:
        self.bars[idx].chord = chord

    def _on_btn_chord_click(self, bar: BarRow) -> None:
        idx = self.bars.index(bar)
        if callable(self.on_btn_chord_click):
            self.on_btn_chord_click(idx)


class SettingsContainer(ft.UserControl, metaclass=LoggingMeta):

    def __init__(self, grid: Grid):
        super(SettingsContainer, self).__init__()
        self._grid = grid
        self._rg_grid: ft.RadioGroup = ...
        self._sld_note_count: ft.Slider = ...
        self._sld_ct_threshold: ft.Slider = ...
        self._dd_scale: ft.Dropdown = ...
        self._dd_rhythm: ft.Dropdown = ...
        self.on_grid_change: Callable = ...

    def build(self) -> ft.Container:

        self._rg_grid = ft.RadioGroup(
            content=ft.Column([
                ft.Radio(value="8", label="8"),
                ft.Radio(value="16", label="16")
            ]),
            value=str(self._grid.value),
            on_change=self._on_rg_grid_change
        )

        self._sld_note_count = ft.Slider(
            min=1,
            max=self._grid.value,
            divisions=self._grid.value - 1,
            label="{value}",
            value=6 if self._grid.value == 16 else 4
        )

        self._sld_ct_threshold = ft.Slider(
            min=0,
            max=100,
            divisions=10,
            label="{value}%",
            value=30
        )

        scales = Service.get_scale_names()
        self._dd_scale = ft.Dropdown(
            options=[ft.dropdown.Option(s) for s in scales],
            label="Scale",
            value=scales[0] if scales else None,
            border=ft.InputBorder.OUTLINE,
            border_color=ft.Colors.PRIMARY
        )

        rhythms = Service.get_rhythm_names()
        self._dd_rhythm = ft.Dropdown(
            options=[ft.dropdown.Option(r) for r in rhythms],
            label="Rhythm",
            value=rhythms[0] if rhythms else None,
            border=ft.InputBorder.OUTLINE,
            border_color=ft.Colors.PRIMARY
        )

        return ft.Container(
            bgcolor=ft.Colors.SURFACE,
            width=800,
            height=400,
            border_radius=15,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            padding=10,
            content=ft.Column([
                ft.Text("Grid"),
                self._rg_grid,
                ft.Text("Note count"),
                self._sld_note_count,
                ft.Text("Chord tones treshold"),
                self._sld_ct_threshold,
                ft.Row(
                    controls=[self._dd_scale, self._dd_rhythm],
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY
                )
            ])
        )

    @property
    def settings(self) -> dict:
        return {
            "grid": Grid.EIGHTS if self._rg_grid.value == "8" else Grid.SIXTEENTHS,
            "note_count": int(self._sld_note_count.value),
            "chord_tones_threshold": self._sld_ct_threshold.value * 0.01,
            "scale": self._dd_scale.value,
            "rhythm": self._dd_rhythm.value
        }

    def _on_rg_grid_change(self, e: ft.ControlEvent) -> None:

        self._grid = self.settings["grid"]

        self._sld_note_count.max = self._grid.value
        self._sld_note_count.divisions = self._grid.value - 1
        self._sld_note_count.value = 6 if self._grid.value == 16 else 4
        self._sld_note_count.update()

        if callable(self.on_grid_change):
            self.on_grid_change(self._grid)


class CircleContainer(ft.UserControl, metaclass=LoggingMeta):

    def __init__(self):
        super(CircleContainer, self).__init__()
        self.on_btn_chord_click: Callable = ...

    def build(self) -> ft.Container:

        major_chords = deque(MAJOR_CHORDS)
        minor_chords = deque(MINOR_CHORDS)
        major_chords.rotate(-3)
        minor_chords.rotate(-3)

        cont_bg = ft.Container(
            bgcolor=ft.Colors.SURFACE,
            width=800,
            height=400,
            border_radius=15,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            padding=10
        )

        maj_coords = trigonometry.circle_coords(
            center=(400, 200),
            r=160,
            n=12
        )

        maj_buttons = []
        for chord, coords in zip(major_chords, maj_coords):
            btn = ft.OutlinedButton(
                text=chord,
                height=60,
                width=60,
                style=ft.ButtonStyle(padding=ft.padding.all(5)),
                data=Triad(chord),
                on_click=self._on_btn_chord_click
            )
            x, y = coords
            btn.top = y - 30
            btn.left = x - 30
            maj_buttons.append(btn)

        min_coords = trigonometry.circle_coords(
            center=(400, 200),
            r=100,
            n=12
        )

        min_buttons = []
        for chord, coords in zip(minor_chords, min_coords):
            btn = ft.OutlinedButton(
                text=chord,
                height=50,
                width=50,
                style=ft.ButtonStyle(padding=ft.padding.all(5)),
                data=Triad(chord),
                on_click=self._on_btn_chord_click
            )
            x, y = coords
            btn.top = y - 25
            btn.left = x - 25
            min_buttons.append(btn)

        return ft.Container(
            content=ft.Stack([
                cont_bg,
                *maj_buttons,
                *min_buttons
            ])
        )

    def _on_btn_chord_click(self, e: ft.ControlEvent) -> None:
        if callable(self.on_btn_chord_click):
            self.on_btn_chord_click(e.control.data)


class MainStack(ft.UserControl, metaclass=LoggingMeta):

    def __init__(self):
        super(MainStack, self).__init__()
        self._cont_bars: BarsContainer = ...
        self._cont_settings: SettingsContainer = ...
        self._cont_circle: CircleContainer = ...
        self._bar_idx_to_set_chord: Optional[int] = None

    def build(self) -> ft.Stack:

        self._cont_bars = BarsContainer(grid=Grid.EIGHTS)
        self._cont_settings = SettingsContainer(grid=Grid.EIGHTS)
        self._cont_circle = CircleContainer()

        self._cont_settings.visible = False
        self._cont_circle.visible = False

        self._cont_bars.on_btn_chord_click = self._on_bars_chord_click
        self._cont_settings.on_grid_change = self._on_settings_grid_change
        self._cont_circle.on_btn_chord_click = self._on_circle_chord_click

        return ft.Stack([
            self._cont_bars,
            self._cont_settings,
            self._cont_circle
        ])

    @property
    def melody_data(self) -> list[MelodyData]:
        return self._cont_bars.melody_data

    @melody_data.setter
    def melody_data(self, melody_data: MelodyData) -> None:
        self._cont_bars.melody_data = melody_data

    @property
    def settings(self) -> dict:
        return {
            "settings": self._cont_settings.settings,
            "bars": self._cont_bars.bar_params
        }

    def on_btn_settings_click(self, e: ft.ControlEvent) -> None:
        self._cont_circle.visible = False
        self._cont_settings.visible = not self._cont_settings.visible
        self.update()

    def on_btn_refresh_click(self, e: ft.ControlEvent) -> None:
        params = self._collect_params()
        result = Service.process_four_bars(params)
        self.melody_data = result

    def on_btn_folder_click(self, e: ft.ControlEvent) -> None:
        Service.open_app_folder()

    def _on_bars_chord_click(self, idx: int) -> None:
        self._bar_idx_to_set_chord = idx
        self._cont_circle.visible = True
        self.update()

    def _on_settings_grid_change(self, grid: Grid) -> None:
        self._cont_bars.reset_grid(grid)

    def _on_circle_chord_click(self, chord: Triad) -> None:
        self._cont_bars.set_chord(chord, self._bar_idx_to_set_chord)
        self._cont_circle.visible = False
        self.update()

    def _collect_params(self) -> Service.Params:
        settings = self.settings
        params = Service.Params(
            bars=[
                Service.Params.BarParams(
                    chord=bar["chord"],
                    active=bar["active"],
                    melody_data=bar["melody_data"]
                )
                for bar in settings["bars"]
            ],
            scale_name=settings["settings"]["scale"],
            note_count=settings["settings"]["note_count"],
            grid=settings["settings"]["grid"],
            chord_tones_threshold=settings["settings"]["chord_tones_threshold"],
            rhythm_name=settings["settings"]["rhythm"],
        )
        return params
