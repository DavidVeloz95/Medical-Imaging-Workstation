import numpy as np
from matplotlib.path import Path

class ROIController:

    def __init__(self, spacing_x, spacing_y):
        self.spacing_x = spacing_x
        self.spacing_y = spacing_y
        self.mode = None
        
        # circular
        self.center = None
        self.radius = None
        # rectangular
        self.point_a = None
        self.point_b = None
        # free
        self.points = []
        self.closed = False
        # ellipse
        self.corner_a = None
        self.corner_b = None
        
        self.plane = None

        self.artist = None
        self.text_artist = None
        
        self.mask = None
        
    def clear(self):
        self.center = None
        self.radius = None
        
        self.point_a = None
        self.point_b = None
        
        self.points = []
        self.closed = False
        
        
        self.plane = None
        if self.artist:
            self.artist.remove()
            self.artist = None
        if self.text_artist:
            self.text_artist.remove()
            self.text_artist = None
    
    def add_point(self, plane, x, y):
        if self.mode == "circle":
            if self.center is None:
                self.center = (x, y)
                self.plane = plane
            elif self.radius is None:
                cx, cy = self.center
                self.radius = np.sqrt((x-cx)**2 + (y-cy)**2)
            else:
                self.clear()
                self.center = (x, y)
                self.plane = plane
        elif self.mode == "rectangle":
            if self.point_a is None:
                self.point_a = (x, y)
                self.plane = plane
            elif self.point_b is None:
                self.point_b = (x, y)
            else:
                self.clear()
                self.point_a = (x, y)
                self.plane = plane
        elif self.mode == "free":
            if self.closed:
                self.clear()
                self.points.append((x, y))
                self.plane = plane
            else:
                self.points.append((x, y))
                if self.plane is None:
                    self.plane = plane
        elif self.mode == "ellipse":
            if self.corner_a is None:
                self.corner_a = (x, y)
                self.plane = plane
            elif self.corner_b is None:
                self.corner_b = (x, y)
            else:
                self.clear()
                self.corner_a = (x, y)
                self.plane = plane
    
    def close_free_roi(self):
        if len(self.points) >= 3:
            self.closed = True

    def is_complete(self):
        if self.mode == "circle":
            return (self.center is not None and self.radius is not None )
        elif self.mode == "rectangle":
            return (self.point_a is not None and self.point_b is not None)
        elif self.mode == "free":
            return self.closed
        elif self.mode == "ellipse":
            return (self.corner_a is not None and self.corner_b is not None)
        return False

    def get_mask(self, image_shape):
        if self.mode == "circle":
            cx, cy = self.center
            y, x = np.ogrid[:image_shape[0], :image_shape[1]]
            return ((x-cx)**2 + (y-cy)**2) <= self.radius**2
        elif self.mode == "rectangle":
            x1, y1 = self.point_a
            x2, y2 = self.point_b
            xmin = min(x1, x2)
            xmax = max(x1, x2)
            ymin = min(y1, y2)
            ymax = max(y1, y2)
            self.mask = np.zeros(image_shape, dtype=bool)
            self.mask[ymin:ymax+1, xmin:xmax+1] = True
            return self.mask
        elif self.mode == "free":
            polygon = Path(self.points)
            y, x = np.mgrid[:image_shape[0], :image_shape[1]]
            coords = np.vstack((x.ravel(), y.ravel())).T
            self.mask = polygon.contains_points(coords)
            return self.mask.reshape(image_shape)
        
        elif self.mode == "ellipse":
            x1, y1 = self.corner_a
            x2, y2 = self.corner_b
            cx = (x1 + x2)/2
            cy = (y1 + y2)/2
            rx = abs(x2 - x1)/2
            ry = abs(y2 - y1)/2
            y, x = np.ogrid[:image_shape[0], :image_shape[1]]
            return ((x-cx)/rx)**2 + ((y-cy)/ry)**2 <= 1
        return None

    def get_pixels(self, image):
        self.mask = self.get_mask(image.shape)
        if self.mask is None:
            return np.array([])
        return image[self.mask]

    def calculate_statistics(self, image):
        pixels = self.get_pixels(image)
        if len(pixels) == 0:
            return None
        pixel_area = (self.spacing_x * self.spacing_y)
        area_mm2 = (len(pixels) * pixel_area)
        return {"mean": np.mean(pixels), "std": np.std(pixels), "min": np.min(pixels), "max": np.max(pixels), "count": len(pixels), "area": area_mm2}

    def get_histogram(self, image, bins=100):
        pixels = self.get_pixels(image)
        if len(pixels) == 0:
            return None
        return np.histogram(pixels, bins=bins)