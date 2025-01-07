"""
Entry point
"""

import flet as ft
from loguru import logger

from src.service import APP_DIR
from src.ui import AppBar, MainStack


logger.add(APP_DIR / "error.log", format="{time} {level} {message}", level="ERROR")


def main(page: ft.Page):

    page.title = "Four Bars"
    page.window.width = 820
    page.window.height = 520
    page.window.resizable = False
    page.window.maximizable = False
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.YELLOW)
    page.dark_theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE)
    page.theme_mode = ft.ThemeMode.DARK

    main_stack = MainStack()
    app_bar = AppBar(
        on_btn_settings_click=main_stack.on_btn_settings_click,
        on_btn_refresh_click=main_stack.on_btn_refresh_click,
        on_btn_folder_click=main_stack.on_btn_folder_click
    )

    page.appbar = app_bar
    page.main_stack = main_stack
    page.add(main_stack)


if __name__ == '__main__':
    ft.app(target=main)
