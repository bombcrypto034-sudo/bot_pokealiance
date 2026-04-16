import threading
import time

import pyautogui
from PIL import Image, ImageChops, ImageStat

from bot import config


class BattleMonitor:
    def __init__(self, input_controller, path_manager, autocatch_service=None):
        self.input = input_controller
        self.path_manager = path_manager
        self.autocatch_service = autocatch_service
        self.running = False
        self.lock = threading.Lock()
        self.battle_active = False

    def get_current_image(self, region):
        return pyautogui.screenshot(region=region).convert("RGB")

    def get_image_difference(self, current_image, baseline_image):
        diff = ImageChops.difference(current_image, baseline_image)
        stat = ImageStat.Stat(diff)
        return sum(stat.mean) / len(stat.mean)

    def execute_flow(self, trigger_message):
        was_playing = self.path_manager.pause_for_battle()
        print(trigger_message)
        self.path_manager.wait_until_character_stops()
        time.sleep(config.BATTLE_PRE_ACTION_DELAY_SECONDS)
        self.input.press_game_key("o")
        print("Modo ofensivo ativado")
        self.input.press_game_key("x")
        print("Acao de battle executada: tecla X")
        time.sleep(config.BATTLE_POST_ACTION_DELAY_SECONDS)
        self.input.press_game_key("r")
        print("Tecla R enviada apos battle")

        if self.autocatch_service is not None:
            print("Iniciando verificacao de captura pos-battle")
            self.autocatch_service.run_autocatch_window(
                config.AUTO_CATCH_POST_BATTLE_MAX_DURATION_SECONDS
            )
            print("Verificacao de captura pos-battle finalizada")

        time.sleep(config.BATTLE_RESUME_AFTER_R_DELAY_SECONDS)
        if was_playing:
            self.path_manager.resume_after_battle()

    def handle_battle_detected(self, difference):
        if not self.path_manager.should_execute_flow_at_current_position():
            print("Battle detectado fora de um ponto de fluxo; ignorando")
            return

        self.execute_flow(
            f"Battle detectado por mudanca de imagem: diff={difference:.2f}"
        )

    def execute_flow_at_point(self, position):
        self.execute_flow(f"Executando fluxo no ponto marcado: {position}")

    def monitor_loop(self):
        region = config.get_battle_region()
        baseline_path = config.BATTLE_BASELINE_PATH

        if region is None:
            print("Regiao de battle nao configurada")
            with self.lock:
                self.running = False
            return

        if not baseline_path.exists():
            print("Imagem base do battle nao configurada")
            with self.lock:
                self.running = False
            return

        with Image.open(baseline_path) as baseline_image_file:
            baseline_image = baseline_image_file.convert("RGB")

        print(f"Monitor de battle iniciado na regiao {region} com base {baseline_path}")

        try:
            while True:
                with self.lock:
                    if not self.running:
                        return

                current_image = self.get_current_image(region)

                if current_image.size != baseline_image.size:
                    print(
                        f"Tamanho atual {current_image.size} difere da base {baseline_image.size}"
                    )
                    time.sleep(config.BATTLE_CHECK_INTERVAL_SECONDS)
                    continue

                difference = self.get_image_difference(current_image, baseline_image)

                if difference >= config.BATTLE_IMAGE_DIFF_THRESHOLD:
                    if not self.battle_active:
                        self.battle_active = True
                        self.handle_battle_detected(difference)
                else:
                    if self.battle_active:
                        print("Battle voltou ao estado base")
                    self.battle_active = False

                time.sleep(config.BATTLE_CHECK_INTERVAL_SECONDS)
        finally:
            with self.lock:
                self.running = False
                self.battle_active = False

    def start(self):
        with self.lock:
            if self.running:
                print("Monitor de battle ja esta em execucao")
                return
            self.running = True

        threading.Thread(target=self.monitor_loop, daemon=True).start()

    def stop(self):
        with self.lock:
            if not self.running:
                print("Monitor de battle nao esta em execucao")
                return
            self.running = False

        print("Monitor de battle parado")
