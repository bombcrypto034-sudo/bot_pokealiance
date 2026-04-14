import json
import threading
import time

from bot import config


class PathManager:
    def __init__(self, game_client, navigator, input_controller):
        self.game_client = game_client
        self.navigator = navigator
        self.input = input_controller
        self.path = []
        self.recording = False
        self.playing = False
        self.paused_for_battle = False
        self.last_resume_key_time = 0
        self.state_lock = threading.Lock()

    def record_path(self):
        print("Gravando caminho... (SHIFT+S para parar)")

        with self.state_lock:
            self.path = []

        last_pos = None

        while True:
            with self.state_lock:
                if not self.recording:
                    break

            pos = self.game_client.get_position()

            if pos != last_pos:
                self.path.append(pos)
                print(f"Salvo: {pos}")

            last_pos = pos
            time.sleep(0.1)

    def start_record_thread(self):
        with self.state_lock:
            if self.recording:
                print("Ja esta gravando")
                return
            self.recording = True

        threading.Thread(target=self.record_path, daemon=True).start()

    def stop_record(self):
        with self.state_lock:
            self.recording = False

        self.save_path_to_file()
        print("Gravacao finalizada")

    def play_path(self):
        if not self.path:
            self.load_path_from_file()

        if not self.path:
            print("Nenhum caminho gravado")
            return

        with self.state_lock:
            self.playing = True
            self.paused_for_battle = False
        self.navigator.stop_requested = False

        print("Reproduzindo caminho...")

        try:
            index = 0
            retry_count = 0
            while index < len(self.path):
                with self.state_lock:
                    if not self.playing:
                        print("Reproducao interrompida")
                        return
                    paused_for_battle = self.paused_for_battle

                if paused_for_battle:
                    time.sleep(0.1)
                    continue

                pos = self.path[index]
                x, y, _ = pos
                if not self.navigator.move_to(x, y):
                    with self.state_lock:
                        if self.paused_for_battle:
                            print("Reproducao pausada para battle")
                            continue

                    retry_count += 1
                    if retry_count <= config.PATH_RETRY_ATTEMPTS:
                        print(
                            f"Falha ao chegar em: {pos}. "
                            f"Tentando novamente ({retry_count}/{config.PATH_RETRY_ATTEMPTS})"
                        )
                        time.sleep(config.PATH_RETRY_DELAY_SECONDS)
                        continue

                    print(f"Pulando ponto bloqueado: {pos}")
                    retry_count = 0
                    index += 1
                    continue

                print(f"Chegou em: {pos}")
                retry_count = 0
                index += 1

            print("Fim do caminho")
        finally:
            with self.state_lock:
                self.playing = False
                self.paused_for_battle = False

    def stop_playback(self):
        with self.state_lock:
            self.playing = False
            self.paused_for_battle = False
        self.navigator.request_stop()

    def pause_for_battle(self):
        with self.state_lock:
            if not self.playing:
                return False
            self.paused_for_battle = True

        self.navigator.request_stop()
        return True

    def resume_after_battle(self):
        with self.state_lock:
            if not self.playing:
                return
            if not self.paused_for_battle:
                return

        now = time.time()
        if now - self.last_resume_key_time < config.RESUME_KEY_DEBOUNCE_SECONDS:
            with self.state_lock:
                self.paused_for_battle = False
            print("Reproducao retomada apos battle")
            return

        self.last_resume_key_time = now

        self.input.press_game_key("r")
        time.sleep(config.BATTLE_RESUME_AFTER_R_DELAY_SECONDS)
        with self.state_lock:
            self.paused_for_battle = False
        print("Reproducao retomada apos battle")

    def resume_after_autocatch(self):
        with self.state_lock:
            if not self.playing:
                return
            if not self.paused_for_battle:
                return
            self.paused_for_battle = False

        print("Reproducao retomada apos captura")

    def save_path_to_file(self):
        serializable_path = [
            {"x": pos[0], "y": pos[1], "z": pos[2]}
            for pos in self.path
        ]

        with config.ROUTE_PATH.open("w", encoding="utf-8") as file:
            json.dump(serializable_path, file, indent=2)

        print(f"Rota salva em {config.ROUTE_PATH}")

    def load_path_from_file(self):
        if not config.ROUTE_PATH.exists():
            return

        try:
            with config.ROUTE_PATH.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Erro ao carregar rota: {exc}")
            return

        loaded_path = []
        for item in data:
            if not isinstance(item, dict):
                continue

            try:
                loaded_path.append((int(item["x"]), int(item["y"]), int(item["z"])))
            except (KeyError, TypeError, ValueError):
                continue

        if loaded_path:
            self.path = loaded_path
            print(f"Rota carregada de {config.ROUTE_PATH}")
