import threading
import time

import pyautogui
from PIL import Image

from bot import config


class AutoCatchService:
    def __init__(self, game_client, input_controller, path_manager=None):
        self.game_client = game_client
        self.input = input_controller
        self.path_manager = path_manager
        self.last_throw_time = 0
        self.auto_catch_running = False
        self.auto_catch_lock = threading.Lock()

    def get_detection_region(self):
        override_region = config.get_detection_region_override()
        if override_region is not None:
            return override_region

        window_left, window_top, _, _ = self.game_client.get_window_rect()
        offset_x, offset_y, width, height = config.DETECTION_REGION_OFFSET
        return (
            window_left + offset_x,
            window_top + offset_y,
            width,
            height,
        )

    def detectar_pokemon(self):
        detection_region = self.get_detection_region()
        _, _, region_width, region_height = detection_region

        for image_path in config.get_pokemon_images():
            try:
                with Image.open(image_path) as image:
                    image_width, image_height = image.size

                if image_width > region_width or image_height > region_height:
                    print(
                        f"Ignorando {image_path}: imagem {image_width}x{image_height} "
                        f"maior que a regiao {region_width}x{region_height}"
                    )
                    continue

                pos = pyautogui.locateOnScreen(
                    image_path,
                    region=detection_region,
                    confidence=config.DETECTION_CONFIDENCE,
                )
                if pos:
                    return pos, image_path, detection_region
            except Exception as exc:
                error_text = repr(exc) if repr(exc) else type(exc).__name__
                print(f"Erro ao detectar {image_path}: {error_text}")

        return None, None, detection_region

    def jogar_pokebola(self, pos, image_path, detection_region):
        if time.time() - self.last_throw_time < config.AUTO_CATCH_COOLDOWN_SECONDS:
            return

        if pos:
            was_playing = False
            if self.path_manager is not None:
                was_playing = self.path_manager.pause_for_battle()

            print(f"Pokemon encontrado com {image_path}!")

            x, y = pyautogui.center(pos)

            self.input.move_cursor(x, y)
            time.sleep(config.AUTO_CATCH_POST_MOVE_DELAY_SECONDS)
            self.input.press_game_key("f")

            print(
                f"Pokebola usada com ponteiro em {x}, {y} na regiao {detection_region}"
            )
            self.last_throw_time = time.time()

            clear_deadline = time.time() + config.AUTO_CATCH_CLEAR_TIMEOUT_SECONDS
            while time.time() < clear_deadline:
                next_pos, _, _ = self.detectar_pokemon()
                if not next_pos:
                    break

                if time.time() - self.last_throw_time >= config.AUTO_CATCH_COOLDOWN_SECONDS:
                    x, y = pyautogui.center(next_pos)
                    self.input.move_cursor(x, y)
                    time.sleep(config.AUTO_CATCH_POST_MOVE_DELAY_SECONDS)
                    self.input.press_game_key("f")
                    print(f"Pokebola extra usada com ponteiro em {x}, {y}")
                    self.last_throw_time = time.time()

                time.sleep(config.AUTO_CATCH_CLEAR_CHECK_INTERVAL_SECONDS)
            else:
                print("Pokemon ainda detectado; retomando rota por timeout de espera")

            if was_playing:
                self.path_manager.resume_after_autocatch()

    def auto_catch(self):
        print("Auto catch iniciado")

        try:
            while True:
                pos, image_path, detection_region = self.detectar_pokemon()

                if pos:
                    self.jogar_pokebola(pos, image_path, detection_region)
                else:
                    print("Nao encontrou")

                time.sleep(config.AUTO_CATCH_LOOP_INTERVAL_SECONDS)
        finally:
            with self.auto_catch_lock:
                self.auto_catch_running = False

    def start_auto_catch(self):
        with self.auto_catch_lock:
            if self.auto_catch_running:
                print("Auto catch ja esta em execucao")
                return
            self.auto_catch_running = True

        threading.Thread(target=self.auto_catch, daemon=True).start()
