import keyboard

from bot import config
from bot.core.game_client import GameClient
from bot.core.input import InputController
from bot.core.navigation import Navigator
from bot.features.autocatch import AutoCatchService
from bot.features.battle_monitor import BattleMonitor
from bot.features.pathing import PathManager
from bot.features.region_selector import RegionSelector


class BotApplication:
    def __init__(self):
        self.game_client = GameClient()
        self.input = InputController(self.game_client.hwnd)
        self.navigator = Navigator(self.game_client, self.input)
        self.path_manager = PathManager(self.game_client, self.navigator, self.input)
        self.autocatch = AutoCatchService(
            self.game_client, self.input, self.path_manager
        )
        self.region_selector = RegionSelector()
        self.battle_monitor = BattleMonitor(self.input, self.path_manager)

    def register_hotkeys(self):
        keyboard.add_hotkey(config.HOTKEY_RECORD, self.path_manager.start_record_thread)
        keyboard.add_hotkey(config.HOTKEY_STOP, self.path_manager.stop_record)
        keyboard.add_hotkey(config.HOTKEY_PLAY, self.path_manager.play_path)
        keyboard.add_hotkey(config.HOTKEY_CATCH, self.autocatch.start_auto_catch)
        keyboard.add_hotkey(config.HOTKEY_MARK_TOP_LEFT, self.region_selector.mark_top_left)
        keyboard.add_hotkey(
            config.HOTKEY_MARK_BOTTOM_RIGHT, self.region_selector.mark_bottom_right
        )
        keyboard.add_hotkey(config.HOTKEY_CLEAR_REGION, self.region_selector.clear_region)
        keyboard.add_hotkey(
            config.HOTKEY_MARK_BATTLE_TOP_LEFT, self.region_selector.mark_battle_top_left
        )
        keyboard.add_hotkey(
            config.HOTKEY_MARK_BATTLE_BOTTOM_RIGHT,
            self.region_selector.mark_battle_bottom_right,
        )
        keyboard.add_hotkey(
            config.HOTKEY_CAPTURE_BATTLE_BASELINE,
            self.region_selector.capture_battle_baseline,
        )
        keyboard.add_hotkey(config.HOTKEY_START_BATTLE_MONITOR, self.battle_monitor.start)
        keyboard.add_hotkey(config.HOTKEY_STOP_BATTLE_MONITOR, self.battle_monitor.stop)
        keyboard.add_hotkey(
            config.HOTKEY_CLEAR_BATTLE_CONFIG, self.region_selector.clear_battle_config
        )

    def run(self):
        self.register_hotkeys()
        print("Janela encontrada")
        print(
            "SHIFT+R = Gravar | SHIFT+S = Parar | SHIFT+P = Caminho | SHIFT+C = Auto Catch"
        )
        print(
            "SHIFT+1 = Marcar topo esquerdo | SHIFT+2 = Marcar canto inferior direito | SHIFT+3 = Limpar regiao"
        )
        print(
            "SHIFT+4 = Marcar battle topo esquerdo | SHIFT+5 = Marcar battle canto inferior direito"
        )
        print(
            "SHIFT+6 = Salvar foto base | SHIFT+B = Iniciar monitor | SHIFT+N = Parar monitor | SHIFT+0 = Limpar battle"
        )
        current_region = config.get_detection_region_override()
        if current_region:
            print(f"Regiao de deteccao atual: {current_region}")
        battle_region = config.get_battle_region()
        if battle_region:
            print(f"Regiao de battle atual: {battle_region}")
        if config.has_battle_baseline_image():
            print(f"Imagem base do battle atual: {config.BATTLE_BASELINE_PATH}")
        keyboard.wait()
