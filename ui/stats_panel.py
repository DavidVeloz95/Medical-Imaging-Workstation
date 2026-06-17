from PyQt5.QtWidgets import QTextEdit


class StatsPanel(QTextEdit):

    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.clear_stats()

    def clear_stats(self):
        self.setPlainText("No statistics available.")
    
    def update_roi(self, stats):

        if stats is None:
            return

        text = (
            "ROI\n"
            "----------------------\n\n"
            f"Mean HU: {stats['mean']:.1f}\n"
            f"Std HU : {stats['std']:.1f}\n"
            f"Min HU : {stats['min']:.1f}\n"
            f"Max HU : {stats['max']:.1f}\n\n"
            f"Area : {stats['area']:.1f} mm²\n"
        )
        self.setPlainText(text)
    
    def update_segmentation(self, volume_cm3, mean, std, classif):
        text = (
            "SEGMENTATION\n"
            "----------------------\n\n"
            f"Volume: {volume_cm3:.1f} cm³\n"
            f"Mean Density: {mean:.1f} HU\n"
            f"Std Density: {std:.1f}\n"
            f"Classification: {classif}"
            )
        self.setPlainText(text)
        
    def update_density(self, mean_hu):
        text = (
            "BONE DENSITY\n"
            "----------------------\n\n"
            f"Mean Density: {mean_hu:.1f} HU")
        self.setPlainText(text)