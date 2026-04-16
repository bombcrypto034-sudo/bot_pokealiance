import time

import pyautogui
import win32api
import win32con
import win32gui

from bot import config


class InputController:
    def __init__(self, hwnd):
        self.hwnd = hwnd

    def send_key(self, key):
        win32gui.PostMessage(self.hwnd, win32con.WM_KEYDOWN, key, 0)
        time.sleep(0.05)
        win32gui.PostMessage(self.hwnd, win32con.WM_KEYUP, key, 0)

    def move_cursor(self, x, y):
        win32api.SetCursorPos((int(x), int(y)))

    def press(self, key):
        pyautogui.press(key)

    def press_game_key(self, key):
        key_map = {
            "f": config.KEY_F,
            "i": config.KEY_I,
            "o": config.KEY_O,
            "r": config.KEY_R,
            "x": config.KEY_X,
        }

        virtual_key = key_map.get(str(key).lower())
        if virtual_key is None:
            self.press(key)
            return

        self.send_key(virtual_key)
