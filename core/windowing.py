import numpy as np


class DICOMWindowing:

    def __init__(self, image):

        # Original HU image
        self.image = image

        # Final display image
        self.display_image = None

    def apply_window(self, window_level, window_width):
        # Apply CT windowing.


        # Validate parameters
        if window_width <= 0:
            raise ValueError("Window width must be > 0")

        # Compute window limits
        min_window = window_level - (window_width / 2)
        max_window = window_level + (window_width / 2)

        # Clip intensities
        clipped = np.clip(self.image, min_window, max_window)

        # Normalize to [0,1]
        normalized = (clipped - min_window) / (max_window - min_window)

        # Store result
        self.display_image = normalized

        return normalized