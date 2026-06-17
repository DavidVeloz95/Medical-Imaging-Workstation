import numpy as np

class MeasurementController:

    def __init__(self, spacing_x, spacing_y, spacing_z):
        self.spacing_x = spacing_x
        self.spacing_y = spacing_y
        self.spacing_z = spacing_z
        self.active = False
        self.point_a = None
        self.point_b = None
        self.line_artist = None
        self.text_artist = None

    def clear(self):
        self.point_a = None
        self.point_b = None
        if self.line_artist is not None:
            self.line_artist.remove()
            self.line_artist = None
        if self.text_artist is not None:
            self.text_artist.remove()
            self.text_artist = None

    def add_point(self, plane, x, y):
        if self.point_a is None:
            self.point_a = (plane, x, y)
        elif self.point_b is None:
            self.point_b = (plane, x, y)
        else:
            self.clear()
            self.point_a = (plane, x, y)

    def has_measurement(self):
        return (
            self.point_a is not None
            and self.point_b is not None
        )

    def calculate_distance_mm(self):
        if not self.has_measurement():
            return None
        plane_a, x1, y1 = self.point_a
        plane_b, x2, y2 = self.point_b
        if plane_a != plane_b:
            return None
        if plane_a == 0:      # axial
            dx = (x2 - x1) * self.spacing_x
            dy = (y2 - y1) * self.spacing_y
        elif plane_a == 1:    # coronal
            dx = (x2 - x1) * self.spacing_x
            dy = (y2 - y1) * self.spacing_z
        else:                 # sagittal
            dx = (x2 - x1) * self.spacing_y
            dy = (y2 - y1) * self.spacing_z
        return np.sqrt(dx**2 + dy**2)