class MetadataController:

    def __init__(self, metadata):
        self.metadata = metadata

    def get_summary(self):
        return {
            "Modality": self.metadata["modality"],
            "Series": self.metadata["series_description"],
            "Slices": self.metadata["num_slices"],
            "Spacing": self.metadata["pixel_spacing"]
        }