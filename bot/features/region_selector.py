import pyautogui

from bot import config


class RegionSelector:
    def __init__(self):
        self.top_left = None
        self.battle_top_left = None

    def mark_top_left(self):
        position = pyautogui.position()
        self.top_left = (position.x, position.y)
        print(f"Topo esquerdo marcado em {self.top_left}")

    def mark_bottom_right(self):
        if self.top_left is None:
            print("Marque o topo esquerdo primeiro com SHIFT+1")
            return

        position = pyautogui.position()
        bottom_right = (position.x, position.y)

        left = min(self.top_left[0], bottom_right[0])
        top = min(self.top_left[1], bottom_right[1])
        right = max(self.top_left[0], bottom_right[0])
        bottom = max(self.top_left[1], bottom_right[1])

        width = right - left
        height = bottom - top

        if width <= 0 or height <= 0:
            print("Area invalida. Marque dois pontos diferentes.")
            return

        region = (left, top, width, height)
        config.set_detection_region_override(region)
        print(f"Regiao de deteccao salva: {region}")

    def clear_region(self):
        self.top_left = None
        config.clear_detection_region_override()
        print("Regiao de deteccao removida")

    def mark_battle_top_left(self):
        position = pyautogui.position()
        self.battle_top_left = (position.x, position.y)
        print(f"Topo esquerdo do battle marcado em {self.battle_top_left}")

    def mark_battle_bottom_right(self):
        if self.battle_top_left is None:
            print("Marque o topo esquerdo do battle primeiro com SHIFT+4")
            return

        position = pyautogui.position()
        bottom_right = (position.x, position.y)

        left = min(self.battle_top_left[0], bottom_right[0])
        top = min(self.battle_top_left[1], bottom_right[1])
        right = max(self.battle_top_left[0], bottom_right[0])
        bottom = max(self.battle_top_left[1], bottom_right[1])

        width = right - left
        height = bottom - top

        if width <= 0 or height <= 0:
            print("Area de battle invalida. Marque dois pontos diferentes.")
            return

        region = (left, top, width, height)
        config.set_battle_region(region)
        print(f"Regiao de battle salva: {region}")

    def capture_battle_baseline(self):
        region = config.get_battle_region()
        if region is None:
            print("Defina a regiao do battle primeiro com SHIFT+4 e SHIFT+5")
            return

        screenshot = pyautogui.screenshot(region=region)
        screenshot.save(config.BATTLE_BASELINE_PATH)
        print(f"Imagem base do battle salva em {config.BATTLE_BASELINE_PATH}")

    def clear_battle_config(self):
        self.battle_top_left = None
        config.clear_battle_region()
        config.clear_battle_baseline_color()
        print("Configuracao de battle removida")
