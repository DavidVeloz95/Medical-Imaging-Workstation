class ImageStack:

    def __init__(self, volume, spacing, metadata):
        self.volume = volume
        self.metadata = metadata

        self.spacing_y = spacing[0]
        self.spacing_x = spacing[1]
        self.spacing_z = spacing[2]

    @property
    def shape(self):
        return self.volume.shape

    @property
    def aspect_ratio_ax(self):
        return self.spacing_y / self.spacing_x

    @property
    def aspect_ratio_co(self):
        return self.spacing_z / self.spacing_x

    @property
    def aspect_ratio_sa(self):
        return self.spacing_z / self.spacing_y