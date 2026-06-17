class CineController:

    def __init__(self, fps=30):
        self.active = False
        self.fps = fps

    @property
    def interval_ms(self):
        return int(1000 / self.fps)

    def toggle(self):
        self.active = not self.active