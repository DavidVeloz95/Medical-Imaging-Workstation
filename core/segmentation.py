from collections import deque
import numpy as np

class SegmentationDICOM:

    def __init__(self):
        self.mask = None
        self.active = False
        self.text_artist = None

    def threshold(self, volume, hu_min, hu_max):
        self.mask = (volume >= hu_min) & (volume <= hu_max)
        return self.mask

    def voxel_count(self):
        if self.mask is None:
            return 0
        return np.sum(self.mask)
    
    def calculate_volume(self, spacing):
        voxel_volume = (spacing[0] * spacing[1] * spacing[2])
        return (np.sum(self.mask) * voxel_volume)
    
    def clear(self):
        self.mask = None
        self.active = False
        if self.text_artist:
            self.text_artist.remove()
            self.text_artist = None

    def region_growing(self, volume, seed, tolerance):
        seed_value = volume[seed]

        mask = np.zeros(volume.shape, dtype=bool)
        visited = np.zeros(volume.shape, dtype=bool)

        queue = deque([seed])

        mask[seed] = True
        visited[seed] = True

        neighbors = [
            (-1,0,0), (1,0,0),
            (0,-1,0), (0,1,0),
            (0,0,-1), (0,0,1)
        ]
        while queue:
            z, y, x = queue.popleft()
            for dz, dy, dx in neighbors:
                nz = z + dz
                ny = y + dy
                nx = x + dx
                # bounds check
                if (nz < 0 or nz >= volume.shape[0] or ny < 0 or ny >= volume.shape[1] or nx < 0 or nx >= volume.shape[2]):
                    continue
                if visited[nz, ny, nx]:
                    continue
                visited[nz, ny, nx] = True
                if abs(volume[nz, ny, nx] - seed_value) <= tolerance:
                    mask[nz, ny, nx] = True
                    queue.append((nz, ny, nx))
        self.mask = mask
        self.active = True
        return mask
    
    def calculate_statistics(self, volume):
        pixels = volume[self.mask]
        if len(pixels) == 0:
            return None
        classif = self.classify_density(np.mean(pixels))
        return {"mean": np.mean(pixels), "std": np.std(pixels), "count": len(pixels), "classification": classif}
    
    def classify_density(self, mean_hu): # https://collectiveminds.health/articles/understanding-hounsfield-units-hu-the-complete-guide-to-ct-numbers-and-density-values
        if -1000 <= mean_hu <= -699:
            return "Air"
        elif -700 <= mean_hu <= -600:
            return "Lung"
        elif -120 <= mean_hu <= -90:
            return "Fat"
        elif -10 <= mean_hu <= 2:
            return "Water"
        elif 13 <= mean_hu <= 30:
            return "Blood"
        elif 35 <= mean_hu <= 55:
            return "Muscle"
        elif 100 <= mean_hu <= 300:
            return "Soft Tissue"
        elif 700 <= mean_hu <= 2999:
            return "Bone"
        elif mean_hu >= 3000:
            return "Metal"
        else:
            return "Unknown"
    
    def density_analysis(self, volume):
        if self.mask is None:
            return None
        voxels = volume[self.mask]
        if voxels.size == 0:
            return None
        mean_hu = np.mean(voxels)
        std_hu = np.std(voxels)
        result = {
            "mean": float(mean_hu),
            "std": float(std_hu),
            "min": float(np.min(voxels)),
            "max": float(np.max(voxels))
        }
        if mean_hu > 150:
            result["classification"] = "Bone"
        elif mean_hu < -300:
            result["classification"] = "Lung"
        else:
            result["classification"] = "Soft Tissue"
        return result