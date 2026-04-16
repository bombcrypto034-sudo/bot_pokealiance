import threading
import time

import pyautogui
from PIL import Image, ImageChops, ImageStat

from bot import config


class AutoCatchService:
    def __init__(self, game_client, input_controller, path_manager=None):
        self.game_client = game_client
        self.input = input_controller
        self.path_manager = path_manager
        self.last_throw_time = 0
        self.auto_catch_running = False
        self.auto_catch_lock = threading.Lock()
        self.battle_capture_active = False
        self.last_background_detection_state = None

    def classify_pokemon_variant(self, screenshot_image, candidate_paths):
        best_match_path = None
        best_match_score = None

        for image_path in candidate_paths:
            try:
                with Image.open(image_path) as template_image:
                    candidate_image = template_image.convert("RGB").resize(
                        screenshot_image.size
                    )
            except Exception:
                continue

            diff = ImageChops.difference(screenshot_image, candidate_image)
            score = sum(ImageStat.Stat(diff).mean) / 3

            if best_match_score is None or score < best_match_score:
                best_match_score = score
                best_match_path = image_path

        if (
            best_match_score is not None
            and best_match_score <= config.DETECTION_COLOR_MATCH_MAX_SCORE
        ):
            return best_match_path

        return None

    def is_route_playing(self):
        if self.path_manager is None:
            return False

        with self.path_manager.state_lock:
            return self.path_manager.playing

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
        candidate_paths = []
        screenshot_image = pyautogui.screenshot(region=detection_region).convert("RGB")

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

                candidate_paths.append(image_path)
            except Exception as exc:
                error_text = repr(exc) if repr(exc) else type(exc).__name__
                print(f"Erro ao preparar {image_path}: {error_text}")

        for grayscale in (False, True):
            if grayscale and not config.DETECTION_GRAYSCALE_FALLBACK:
                continue

            for image_path in candidate_paths:
                try:
                    pos = pyautogui.locate(
                        image_path,
                        screenshot_image,
                        confidence=config.DETECTION_CONFIDENCE,
                        grayscale=grayscale,
                    )
                    if not pos:
                        continue

                    screenshot_crop = screenshot_image.crop(
                        (
                            pos.left,
                            pos.top,
                            pos.left + pos.width,
                            pos.top + pos.height,
                        )
                    )
                    matched_image_path = self.classify_pokemon_variant(
                        screenshot_crop,
                        candidate_paths,
                    )
                    if matched_image_path is None:
                        continue

                    absolute_pos = pyautogui.Box(
                        detection_region[0] + pos.left,
                        detection_region[1] + pos.top,
                        pos.width,
                        pos.height,
                    )
                    return absolute_pos, matched_image_path, detection_region
                except pyautogui.ImageNotFoundException:
                    continue
                except Exception as exc:
                    mode = "grayscale" if grayscale else "colorido"
                    error_text = repr(exc) if repr(exc) else type(exc).__name__
                    print(f"Erro ao detectar {image_path} em {mode}: {error_text}")

        return None, None, detection_region

    def jogar_pokebola(self, pos, image_path, detection_region, manage_path_pause=True):
        if time.time() - self.last_throw_time < config.AUTO_CATCH_COOLDOWN_SECONDS:
            return False

        if pos:
            was_playing = False
            if manage_path_pause and self.path_manager is not None:
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

            if was_playing:
                self.path_manager.resume_after_autocatch()

            return True

        return False

    def capturar_pokemon_se_visivel(self):
        self.battle_capture_active = True
        start_time = time.time()
        clear_deadline = time.time() + config.AUTO_CATCH_CLEAR_TIMEOUT_SECONDS
        clear_confirmations = 0
        capturou_algum = False
        last_throw_time = None

        try:
            while time.time() < clear_deadline:
                pos, image_path, detection_region = self.detectar_pokemon()

                if not pos:
                    clear_confirmations += 1
                    elapsed = time.time() - start_time

                    if not capturou_algum and elapsed < config.AUTO_CATCH_MIN_SCAN_AFTER_BATTLE_SECONDS:
                        time.sleep(config.AUTO_CATCH_CLEAR_CHECK_INTERVAL_SECONDS)
                        continue

                    if (
                        last_throw_time is not None
                        and time.time() - last_throw_time < config.AUTO_CATCH_MIN_SCAN_AFTER_THROW_SECONDS
                    ):
                        time.sleep(config.AUTO_CATCH_CLEAR_CHECK_INTERVAL_SECONDS)
                        continue

                    if clear_confirmations >= config.AUTO_CATCH_CLEAR_CONFIRMATIONS:
                        if not capturou_algum:
                            print("Nenhum pokemon visivel apos battle")
                        else:
                            print("Area limpa apos capturar os pokemons visiveis")
                        return

                    time.sleep(config.AUTO_CATCH_CLEAR_CHECK_INTERVAL_SECONDS)
                    continue

                clear_confirmations = 0
                capturou_algum = True

                if time.time() - self.last_throw_time < config.AUTO_CATCH_COOLDOWN_SECONDS:
                    time.sleep(config.AUTO_CATCH_CLEAR_CHECK_INTERVAL_SECONDS)
                    continue

                jogou = self.jogar_pokebola(
                    pos,
                    image_path,
                    detection_region,
                    manage_path_pause=False,
                )
                if jogou:
                    last_throw_time = time.time()
                    clear_deadline = last_throw_time + config.AUTO_CATCH_CLEAR_TIMEOUT_SECONDS
                time.sleep(config.AUTO_CATCH_CLEAR_CHECK_INTERVAL_SECONDS)

            print("Pokemon ainda detectado; retomando rota por timeout de espera")
        finally:
            self.battle_capture_active = False

    def run_autocatch_window(self, duration_seconds):
        self.battle_capture_active = True
        start_time = time.time()
        deadline = time.time() + max(
            duration_seconds,
            config.AUTO_CATCH_POST_BATTLE_MAX_DURATION_SECONDS,
        )
        clear_confirmations = 0
        clear_window_start = None
        last_throw_time = None
        capturou_algum = False

        try:
            print("Auto catch pos-battle ativado")
            while time.time() < deadline:
                now = time.time()
                pos, image_path, detection_region = self.detectar_pokemon()

                if not pos:
                    clear_confirmations += 1
                    if clear_window_start is None:
                        clear_window_start = now

                    if (
                        not capturou_algum
                        and now - start_time < config.AUTO_CATCH_MIN_SCAN_AFTER_BATTLE_SECONDS
                    ):
                        time.sleep(config.AUTO_CATCH_CLEAR_CHECK_INTERVAL_SECONDS)
                        continue

                    if (
                        last_throw_time is not None
                        and now - last_throw_time < config.AUTO_CATCH_MIN_SCAN_AFTER_THROW_SECONDS
                    ):
                        time.sleep(config.AUTO_CATCH_CLEAR_CHECK_INTERVAL_SECONDS)
                        continue

                    if (
                        clear_confirmations >= config.AUTO_CATCH_CLEAR_CONFIRMATIONS
                        and now - clear_window_start
                        >= config.AUTO_CATCH_REQUIRED_CLEAR_WINDOW_SECONDS
                    ):
                        if capturou_algum:
                            print("Autocatch pos-battle finalizado com area limpa")
                        else:
                            print("Nenhum pokemon visivel apos apertar R")
                        return

                    time.sleep(config.AUTO_CATCH_CLEAR_CHECK_INTERVAL_SECONDS)
                    continue

                clear_confirmations = 0
                clear_window_start = None
                capturou_algum = True

                if now - self.last_throw_time < config.AUTO_CATCH_COOLDOWN_SECONDS:
                    time.sleep(config.AUTO_CATCH_CLEAR_CHECK_INTERVAL_SECONDS)
                    continue

                jogou = self.jogar_pokebola(
                    pos,
                    image_path,
                    detection_region,
                    manage_path_pause=False,
                )
                if jogou:
                    last_throw_time = time.time()
                    deadline = max(
                        deadline,
                        last_throw_time + config.AUTO_CATCH_POST_BATTLE_MAX_DURATION_SECONDS,
                    )
                time.sleep(config.AUTO_CATCH_CLEAR_CHECK_INTERVAL_SECONDS)

            print("Autocatch pos-battle encerrado por tempo")
        finally:
            self.battle_capture_active = False
            print("Auto catch pos-battle desativado")

    def auto_catch(self):
        print("Auto catch iniciado")

        try:
            while True:
                if self.battle_capture_active:
                    time.sleep(config.AUTO_CATCH_CLEAR_CHECK_INTERVAL_SECONDS)
                    continue

                if self.is_route_playing():
                    time.sleep(config.AUTO_CATCH_LOOP_INTERVAL_SECONDS)
                    continue

                pos, image_path, detection_region = self.detectar_pokemon()

                if pos:
                    if self.last_background_detection_state != "found":
                        print("Pokemon detectado pelo auto catch")
                        self.last_background_detection_state = "found"
                    self.jogar_pokebola(pos, image_path, detection_region)
                elif self.last_background_detection_state != "clear":
                    print("Area livre para auto catch")
                    self.last_background_detection_state = "clear"

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
