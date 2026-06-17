import numpy as np

class AngleController:

    def __init__(self, spacing_x, spacing_y, spacing_z):
        self.spacing_x = spacing_x
        self.spacing_y = spacing_y
        self.spacing_z = spacing_z
        self.active = False
        self.point_a = None
        self.point_b = None
        self.point_c = None
        self.line_artist_1 = None
        self.line_artist_2 = None
        self.text_artist = None

    def clear(self):
        self.point_a = None
        self.point_b = None
        self.point_c = None
        if self.line_artist_1 is not None:
            self.line_artist_1.remove()
            self.line_artist_1 = None
        if self.line_artist_2 is not None:
            self.line_artist_2.remove()
            self.line_artist_2 = None
        if self.text_artist is not None:
            self.text_artist.remove()
            self.text_artist = None

    def add_point(self, plane, x, y):
        if self.point_a is None:
            self.point_a = (plane, x, y)
        elif self.point_b is None:
            self.point_b = (plane, x, y)
        elif self.point_c is None:
            self.point_c = (plane, x, y)
        else:
            self.clear()
            self.point_a = (plane, x, y)

    def has_measurement(self):
        return (
            self.point_a is not None
            and self.point_b is not None
            and self.point_c is not None
        )

    def calculate_angle_degrees(self):
        if not self.has_measurement():
            return None
        plane_a, x1, y1 = self.point_a
        plane_b, x2, y2 = self.point_b
        plane_c, x3, y3 = self.point_c
        if plane_a != plane_b | plane_a != plane_c:
            return None
        if plane_a == 0:      # axial
            u1 = (x1 - x2) * self.spacing_x
            u2 = (y1 - y2) * self.spacing_y
            v1 = (x3 - x2) * self.spacing_x
            v2 = (y3 - y2) * self.spacing_y
        elif plane_a == 1:    # coronal
            u1 = (x1 - x2) * self.spacing_x
            u2 = (y1 - y2) * self.spacing_z
            v1 = (x3 - x2) * self.spacing_x
            v2 = (y3 - y2) * self.spacing_z
        else:                 # sagittal
            u1 = (x1 - x2)* self.spacing_y
            u2 = (y1 - y2) * self.spacing_z
            v1 = (x3 - x2)* self.spacing_y
            v2 = (y3 - y2) * self.spacing_z
        return np.arccos( ((u1*v1) + (u2*v2)) / ((np.sqrt(u1**2 + u2**2)) * (np.sqrt(v1**2 + v2**2))))