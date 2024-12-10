"""
Entry point
"""

import flet as ft
from loguru import logger

from src.service import APP_DIR
from src.ui import App


logger.add(APP_DIR / "error.log", format="{time} {level} {message}", level="ERROR")


def main(page: ft.Page):

    page.title = "Four Bars"
    page.window.width = 820
    page.window.height = 540
    page.window.resizable = False
    page.window.maximizable = False
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.dark_theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE)
    page.theme_mode = ft.ThemeMode.DARK

    app = App()
    page.add(app)


if __name__ == '__main__':
    ft.app(target=main)
