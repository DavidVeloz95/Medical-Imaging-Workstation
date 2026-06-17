class HUProbeController:

    def __init__(self):
        self.active = False
        self.voxel = None
        self.plane = None
        self.text_artist = None
    
    def set_point(self, plane, x, y):
        self.plane = plane
        self.voxel = (x, y)

    def clear(self):
        self.voxel = None
        self.plane = None