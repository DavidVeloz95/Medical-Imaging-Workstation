class ViewportController:

    def __init__(self):
        self.min_zoom = 1.0
        self.max_zoom = 8.0
        self.zoom_step = 1.2
        self.zoom_factor = {0: 1.0, 1: 1.0, 2: 1.0}
        self.pan_step = 30
        self.center_x = {0: 0, 1: 0, 2: 0}
        self.center_y = {0: 0, 1: 0, 2: 0}

    def zoom_in(self, plane):
        new_zoom = self.zoom_factor[plane] * self.zoom_step
        if new_zoom <= self.max_zoom:
            self.zoom_factor[plane] = new_zoom

    def zoom_out(self, plane):
        new_zoom = self.zoom_factor[plane] / self.zoom_step
        if new_zoom >= self.min_zoom:
            self.zoom_factor[plane] = new_zoom
    
    def reset_plane(self, plane, width, height):
        self.center_x[plane] = width / 2
        self.center_y[plane] = height / 2
        self.zoom_factor[plane] = 1.0

    def reset_all(self, images):
        for plane in range(3):
            height, width = images[plane].shape
            self.center_x[plane] = width / 2
            self.center_y[plane] = height / 2
            self.zoom_factor[plane] = 1.0
    
    def get_viewport_limits(self, plane, width, height):
        zoom = self.zoom_factor[plane]
        visible_width = width / zoom
        visible_height = height / zoom
        cx = self.center_x[plane]
        cy = self.center_y[plane]
        left = cx - visible_width / 2
        right = cx + visible_width / 2
        top = cy - visible_height / 2
        bottom = cy + visible_height / 2
        if left < 0:
            right -= left
            left = 0
        if right > width:
            left -= (right - width)
            right = width
        if top < 0:
            bottom -= top
            top = 0
        if bottom > height:
            top -= (bottom - height)
            bottom = height
        return left, right, top, bottom