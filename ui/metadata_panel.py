from PyQt5.QtWidgets import QTextEdit


class MetadataPanel(QTextEdit):

    def __init__(self):
        super().__init__()

        self.setReadOnly(True)
        self.setPlainText("Metadata Panel")

    def update_metadata(self, metadata):
        text = f"""
            Patient ID: {metadata.get("patient_id")}
            Modality: {metadata.get("modality")}
            Study: {metadata.get("study_description")}
            Series: {metadata.get("series_description")}
            Slices: {metadata.get("num_slices")}
            Pixel Spacing: {metadata.get("pixel_spacing")}
            Slice Thickness: {metadata.get("slice_thickness")}
            Window Center: {metadata.get("window_center")}
            Window Width: {metadata.get("window_width")}
            """
        self.setPlainText(text)