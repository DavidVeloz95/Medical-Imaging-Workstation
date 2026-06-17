from core.presets import WINDOW_PRESETS

class WindowLevelController:
    
    def __init__(self):
        
        # Window presets
        self.presets_list = [
            WINDOW_PRESETS["soft_tissue"],
            WINDOW_PRESETS["lung"],
            WINDOW_PRESETS["bone"],
            WINDOW_PRESETS["brain"]
        ]
        
        self.current_window = 0
        
        preset = self.get_current_preset()
        self.window_level = preset["wl"]
        self.window_width = preset["ww"]
    
    def change_window(self, delta):
        new_window = self.current_window + delta
        if 0 <= new_window < len(self.presets_list):
            self.current_window = new_window
            preset = self.get_current_preset()
            self.window_level = preset["wl"]
            self.window_width = preset["ww"]
            
    def get_current_preset(self):
        return self.presets_list[self.current_window]
    
    def adjust(self, dx, dy):
        self.window_width += dx * 3
        self.window_level -= dy
        self.window_width = max(1, self.window_width)
        
    def set_preset(self, preset_name):
        preset = WINDOW_PRESETS[preset_name]
        self.window_width = preset["ww"]
        self.window_level = preset["wl"]