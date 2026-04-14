import pymem
import pymem.process
import win32gui

from bot import config


class GameClient:
    def __init__(self):
        self.pm = pymem.Pymem(config.PROCESS_NAME)
        module = pymem.process.module_from_name(
            self.pm.process_handle, config.PROCESS_NAME
        )
        self.base = module.lpBaseOfDll
        self.hwnd = win32gui.FindWindow(None, config.WINDOW_NAME)

        if self.hwnd == 0:
            raise RuntimeError("Janela nao encontrada")

    def get_position(self):
        pos_ptr = self.pm.read_int(self.base + config.POS_BASE_OFFSET)
        x = self.pm.read_int(pos_ptr + config.OFFSET_X)
        y = self.pm.read_int(pos_ptr + config.OFFSET_Y)
        z = self.pm.read_int(pos_ptr + config.OFFSET_Z)
        return x, y, z

    def get_window_rect(self):
        left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
        return left, top, right, bottom
