import time

from bot import config


class Navigator:
    def __init__(self, game_client, input_controller):
        self.game_client = game_client
        self.input = input_controller
        self.stop_requested = False

    def move_to(self, target_x, target_y):
        self.stop_requested = False
        start_time = time.time()
        last_pos = None
        stalled_reads = 0

        while True:
            if self.stop_requested:
                print("Movimento interrompido")
                return False

            x, y, _ = self.game_client.get_position()

            if x == target_x and y == target_y:
                return True

            if time.time() - start_time > config.MOVE_TIMEOUT_SECONDS:
                print(f"Tempo limite ao tentar chegar em: {(target_x, target_y)}")
                return False

            current_pos = (x, y)
            if current_pos == last_pos:
                stalled_reads += 1
                if stalled_reads >= config.MOVE_STALL_LIMIT:
                    print(f"Movimento sem progresso para: {(target_x, target_y)}")
                    return False
            else:
                stalled_reads = 0
                last_pos = current_pos

            if x < target_x:
                self.input.send_key(config.KEY_D)
            elif x > target_x:
                self.input.send_key(config.KEY_A)

            if y < target_y:
                self.input.send_key(config.KEY_S)
            elif y > target_y:
                self.input.send_key(config.KEY_W)

            time.sleep(0.05)

    def request_stop(self):
        self.stop_requested = True
