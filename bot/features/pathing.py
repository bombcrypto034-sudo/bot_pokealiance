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
        self.flow_points = []
        self.flow_executor = None
        self.recording = False
        self.playing = False
        self.paused_for_battle = False
        self.last_resume_key_time = 0
        self.state_lock = threading.Lock()

    def set_defense_mode(self):
        self.input.press_game_key("i")
        print("Modo defesa ativado")

    def wait_until_character_stops(self):
        deadline = time.time() + config.BATTLE_STOP_WAIT_TIMEOUT_SECONDS
        last_pos = None
        stable_reads = 0

        while time.time() < deadline:
            current_pos = self.game_client.get_position()

            if current_pos == last_pos:
                stable_reads += 1
                if stable_reads >= config.BATTLE_STOP_STABLE_READS:
                    print(f"Personagem parado em: {current_pos}")
                    return True
            else:
                stable_reads = 0
                last_pos = current_pos

            time.sleep(config.BATTLE_STOP_POLL_INTERVAL_SECONDS)

        print("Timeout aguardando o personagem parar")
        return False

    def try_detour(self, target_pos):
        current_x, current_y, _ = self.game_client.get_position()
        target_x, target_y, _ = target_pos
        detour_distance = config.PATH_DETOUR_DISTANCE
        detour_points = [
            (current_x + detour_distance, current_y),
            (current_x - detour_distance, current_y),
            (current_x, current_y + detour_distance),
            (current_x, current_y - detour_distance),
        ]

        print(f"Tentando desvio para contornar o bloqueio em: {target_pos}")

        for detour_x, detour_y in detour_points:
            if (detour_x, detour_y) == (current_x, current_y):
                continue

            if not self.navigator.move_to(detour_x, detour_y):
                with self.state_lock:
                    if self.paused_for_battle:
                        print("Desvio interrompido para battle")
                        return False
                continue

            print(f"Desvio concluido em: {(detour_x, detour_y)}")
            if self.navigator.move_to(target_x, target_y):
                return True

            with self.state_lock:
                if self.paused_for_battle:
                    print("Retorno do desvio interrompido para battle")
                    return False

        print(f"Desvio falhou para: {target_pos}")
        return False

    def record_path(self):
        print("Gravando caminho... (SHIFT+S para parar)")

        with self.state_lock:
            self.path = []
            self.flow_points = []

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

    def mark_flow_point(self):
        current_pos = self.game_client.get_position()

        with self.state_lock:
            if not self.recording:
                print("So e possivel marcar fluxo durante a gravacao")
                return

            if current_pos in self.flow_points:
                print(f"Ponto de fluxo ja marcado: {current_pos}")
                return

            self.flow_points.append(current_pos)

        print(f"Ponto de fluxo salvo: {current_pos}")

    def should_execute_flow_at_current_position(self):
        with self.state_lock:
            if not self.flow_points:
                return True

        current_pos = self.game_client.get_position()
        with self.state_lock:
            return current_pos in self.flow_points

    def should_execute_flow_for_position(self, position):
        with self.state_lock:
            return position in self.flow_points

    def set_flow_executor(self, flow_executor):
        self.flow_executor = flow_executor

    def execute_flow_if_needed(self, position):
        if not self.should_execute_flow_for_position(position):
            return

        if self.flow_executor is None:
            print(f"Ponto de fluxo alcancado sem executor configurado: {position}")
            return

        self.flow_executor(position)

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

        self.set_defense_mode()
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

                    if self.try_detour(pos):
                        print(f"Chegou em: {pos} apos desvio")
                        retry_count = 0
                        index += 1
                        continue

                    print(f"Pulando ponto bloqueado: {pos}")
                    retry_count = 0
                    index += 1
                    continue

                print(f"Chegou em: {pos}")
                self.execute_flow_if_needed(pos)
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

        with self.state_lock:
            self.paused_for_battle = False
        self.set_defense_mode()
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
        serializable_flow_points = [
            {"x": pos[0], "y": pos[1], "z": pos[2]}
            for pos in self.flow_points
        ]

        with config.ROUTE_PATH.open("w", encoding="utf-8") as file:
            json.dump(
                {
                    "path": serializable_path,
                    "flow_points": serializable_flow_points,
                },
                file,
                indent=2,
            )

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

        if isinstance(data, dict):
            path_data = data.get("path", [])
            flow_points_data = data.get("flow_points", [])
        else:
            path_data = data
            flow_points_data = []

        loaded_path = []
        for item in path_data:
            if not isinstance(item, dict):
                continue

            try:
                loaded_path.append((int(item["x"]), int(item["y"]), int(item["z"])))
            except (KeyError, TypeError, ValueError):
                continue

        loaded_flow_points = []
        for item in flow_points_data:
            if not isinstance(item, dict):
                continue

            try:
                loaded_flow_points.append(
                    (int(item["x"]), int(item["y"]), int(item["z"]))
                )
            except (KeyError, TypeError, ValueError):
                continue

        if loaded_path:
            self.path = loaded_path
            self.flow_points = loaded_flow_points
            print(f"Rota carregada de {config.ROUTE_PATH}")
            if self.flow_points:
                print(f"Pontos de fluxo carregados: {len(self.flow_points)}")
