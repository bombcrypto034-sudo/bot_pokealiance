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
        self.battle_monitor = BattleMonitor(
            self.input, self.path_manager, self.autocatch
        )
        self.path_manager.set_flow_executor(self.battle_monitor.execute_flow_at_point)

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
        keyboard.add_hotkey(
            config.HOTKEY_MARK_FLOW_POINT, self.path_manager.mark_flow_point
        )
        keyboard.add_hotkey(config.HOTKEY_START_BATTLE_MONITOR, self.battle_monitor.start)
        keyboard.add_hotkey(config.HOTKEY_STOP_BATTLE_MONITOR, self.battle_monitor.stop)
        keyboard.add_hotkey(
            config.HOTKEY_CLEAR_BATTLE_CONFIG, self.region_selector.clear_battle_config
        )

    def run(self):
        self.register_hotkeys()
        print("Janela encontrada")
        print("")
        print("=== CONTROLES DA ROTA ===")
        print("SHIFT+R -> Iniciar gravacao do caminho")
        print("SHIFT+S -> Parar gravacao e salvar em route.json")
        print("SHIFT+P -> Reproduzir caminho salvo")
        print("SHIFT+7 -> Marcar coordenada atual como ponto de fluxo")
        print("")
        print("=== AUTO CATCH ===")
        print("SHIFT+C -> Iniciar auto catch fora da rota")
        print("")
        print("=== REGIAO DE DETECCAO DOS POKEMONS ===")
        print("SHIFT+1 -> Marcar topo esquerdo")
        print("SHIFT+2 -> Marcar canto inferior direito")
        print("SHIFT+3 -> Limpar regiao de deteccao")
        print("")
        print("=== BATTLE MONITOR ===")
        print("SHIFT+4 -> Marcar topo esquerdo da area de battle")
        print("SHIFT+5 -> Marcar canto inferior direito da area de battle")
        print("SHIFT+6 -> Salvar foto base do battle")
        print("SHIFT+B -> Iniciar monitor de battle")
        print("SHIFT+N -> Parar monitor de battle")
        print("SHIFT+0 -> Limpar configuracao de battle")
        print("")
        print("=== OBSERVACOES ===")
        print("Pontos de fluxo executam o fluxo padrao ao chegar na coordenada marcada.")
        print("O monitor de battle usa mudanca de imagem para disparar o fluxo.")
        current_region = config.get_detection_region_override()
        if current_region:
            print(f"Regiao de deteccao atual: {current_region}")
        battle_region = config.get_battle_region()
        if battle_region:
            print(f"Regiao de battle atual: {battle_region}")
        if config.has_battle_baseline_image():
            print(f"Imagem base do battle atual: {config.BATTLE_BASELINE_PATH}")
        if self.path_manager.flow_points:
            print(f"Pontos de fluxo carregados: {len(self.path_manager.flow_points)}")
        keyboard.wait()
