import digitalio
import time

class MAX6675:
    MEASUREMENT_PERIOD_S = 0.22

    def __init__(self, sck, cs, so):
        self._sck = digitalio.DigitalInOut(sck)
        self._sck.direction = digitalio.Direction.OUTPUT
        self._sck.value = False

        self._cs = digitalio.DigitalInOut(cs)
        self._cs.direction = digitalio.Direction.OUTPUT
        self._cs.value = True

        self._so = digitalio.DigitalInOut(so)
        self._so.direction = digitalio.Direction.INPUT

        self._last_measurement_start = 0
        self._last_read_temp = 0
        self._error = 0

    def _cycle_sck(self):
        self._sck.value = True
        time.sleep(0.000001)
        self._sck.value = False
        time.sleep(0.000001)

    def refresh(self):
        self._cs.value = False
        time.sleep(0.00001)
        self._cs.value = True
        self._last_measurement_start = time.monotonic()

    def ready(self):
        return time.monotonic() - self._last_measurement_start > self.MEASUREMENT_PERIOD_S

    def error(self):
        return self._error

    def read(self):
        if self.ready():
            self._cs.value = False
            time.sleep(0.00001)

            value = 0
            for i in range(12):
                self._cycle_sck()
                value += self._so.value << (11 - i)

            self._cycle_sck()
            self._error = self._so.value

            for i in range(2):
                self._cycle_sck()

            self._cs.value = True
            self._last_measurement_start = time.monotonic()

            self._last_read_temp = value * 0.25

        return self._last_read_temp
# Usage:
# tc = MAX6675(board.SCK, board.D5, board.MISO)
# print(tc.read())