from controllers.viewport_controller import ViewportController

class CrosshairController:

    def __init__(self, volume, ax, viewport):
        
        self.volume = volume
        self.ax = ax
        self.viewport = viewport
        
        self.visible = True

        self.cursor_3d = {
            "x": volume.shape[2] // 2,
            "y": volume.shape[1] // 2,
            "z": volume.shape[0] // 2
        }

        self.crosshair_size = 10

        self.crosshair_lines = {
            "ax_h": ax["axial"].plot([0,0],[0,0],'r-',lw=1)[0],
            "ax_v": ax["axial"].plot([0,0],[0,0],'r-',lw=1)[0],

            "co_h": ax["coronal"].plot([0,0],[0,0],'r-',lw=1)[0],
            "co_v": ax["coronal"].plot([0,0],[0,0],'r-',lw=1)[0],

            "sa_h": ax["sagittal"].plot([0,0],[0,0],'r-',lw=1)[0],
            "sa_v": ax["sagittal"].plot([0,0],[0,0],'r-',lw=1)[0],
        }
        
    def update_crosshair(self):
        if not self.visible:
            for line in self.crosshair_lines.values():
                line.set_visible(False)
            return
        for line in self.crosshair_lines.values():
            line.set_visible(True)
        x3 = self.cursor_3d["x"]
        y3 = self.cursor_3d["y"]
        z3 = self.cursor_3d["z"]
        size = self.crosshair_size
        # AXIAL
        self.crosshair_lines["ax_h"].set_data([x3-size, x3+size], [y3, y3])
        self.crosshair_lines["ax_v"].set_data([x3, x3], [y3-size, y3+size])
        # CORONAL
        self.crosshair_lines["co_h"].set_data([x3-size, x3+size], [z3, z3])
        self.crosshair_lines["co_v"].set_data([x3, x3], [z3-size, z3+size])
        # SAGITTAL
        self.crosshair_lines["sa_h"].set_data([y3-size, y3+size], [z3, z3])
        self.crosshair_lines["sa_v"].set_data([y3, y3], [z3-size, z3+size])
        
    def center_views_on_cursor(self):
        self.viewport.center_x[0] = self.cursor_3d["x"]
        self.viewport.center_y[0] = self.cursor_3d["y"]
        self.viewport.center_x[1] = self.cursor_3d["x"]
        self.viewport.center_y[1] = self.cursor_3d["z"]
        self.viewport.center_x[2] = self.cursor_3d["y"]
        self.viewport.center_y[2] = self.cursor_3d["z"]