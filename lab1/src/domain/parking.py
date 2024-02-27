from domain.gps import Gps

class Parking:
    def __init__(self, empty_count: int, gps: Gps) -> None:
        self.empty_count = empty_count
        self.gps = gps
