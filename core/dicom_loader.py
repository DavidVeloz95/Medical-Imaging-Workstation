import os
import pydicom
import numpy as np
from collections import defaultdict

class DICOMLoader:

    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.series = {}        # UID -> List of slices
        #self.files = []
        self.volume = None
        self.volume_hu = None
        self.metadata = {}
        self.spacing = None
        self.modality = None
        self.load_series()

    def load_series(self):
        grouped = defaultdict(list)
        self.series = grouped
        for filename in os.listdir(self.folder_path):
            path = os.path.join(self.folder_path, filename)
            if not os.path.isfile(path):
                continue
            try:
                ds = pydicom.dcmread(path, force = True)
                if hasattr(ds, "SeriesInstanceUID") and hasattr(ds, "PixelData"):
                    grouped[ds.SeriesInstanceUID].append(ds)
            except Exception as e:
                print(f"Skipping {filename}: {e}")
        if not grouped:
            raise ValueError("No DICOM files found.")
        first_uid = list(grouped.keys())[0]
        self.load_series_by_uid(first_uid)
    
    def load_series_by_uid(self, uid):
        self.series_uid = uid
        self.files = self.series[uid]
        self.sort_slices()
        self.build_volume()
        self.convert_to_hounsfield()
        self.extract_metadata()
        self.compute_spacing()
    
    def sort_slices(self):
        def sort_key(s):
            if hasattr(s, "ImagePositionPatient"):
                return float(s.ImagePositionPatient[2])
            return int(getattr(s, "InstanceNumber", 0))
        self.files.sort(key=sort_key)

    def build_volume(self):
        # Stack slices into a 3D numpy volume.
        self.volume = np.stack([f.pixel_array for f in self.files]).astype(np.int16)

    def convert_to_hounsfield(self):
        # Convert raw pixel values into Hounsfield Units.
        # HU = PixelValue x Slope + Intercept
        slope = float(getattr(self.files[0], "RescaleSlope", 1))
        intercept = float(getattr(self.files[0], "RescaleIntercept", 0))
        self.volume_hu = (self.volume.astype(np.float32) * slope + intercept)

    def compute_spacing(self):
        # print("Computing spacing...")
        ps = getattr(self.files[0], "PixelSpacing", [1.0, 1.0])
        positions = [
            float(s.ImagePositionPatient[2])
            for s in self.files
            if hasattr(s, "ImagePositionPatient")
        ]
        positions = np.array(sorted(positions))
        if len(positions) > 1:
            z_spacing = np.mean(np.abs(np.diff(positions)))
        else:
            z_spacing = float(getattr(self.files[0], "SliceThickness", 1.0))
        self.spacing = (float(ps[0]), float(ps[1]), float(z_spacing))
        # print("Spacing:", self.spacing)

    def extract_metadata(self):
        # Extract important DICOM metadata.
        f = self.files[0]

        self.modality = getattr(f, "Modality", "Unknown")
        
        self.metadata = {
            "patient_id": getattr(f, "PatientID", None),
            "study_uid": getattr(f, "StudyInstanceUID", None),
            "series_uid": getattr(f, "SeriesInstanceUID", None),
            "modality": self.modality,
            "shape": self.volume.shape,
            "pixel_spacing": getattr(f, "PixelSpacing", None),
            "slice_thickness": getattr(f, "SliceThickness", None),
            "orientation": getattr(f, "ImageOrientationPatient", None),
            "rows": getattr(f, "Rows", None),
            "columns": getattr(f, "Columns", None),
            "rescale_slope": getattr(f, "RescaleSlope", None),
            "rescale_intercept": getattr(f, "RescaleIntercept", None),
            "num_slices": len(self.files),
            "series_description": getattr(f, "SeriesDescription", None),
            "study_description": getattr(f, "StudyDescription", None),
            "window_center": getattr(f, "WindowCenter", None),
            "window_width": getattr(f, "WindowWidth", None),
        }
        
    def get_series_info(self):
        return {
            "modality": self.modality,
            "shape": self.volume.shape,
            "spacing": self.spacing,
            "series_uid": self.series_uid
        }
    
    def get_available_series(self):
        result = []
        for uid, slices in self.series.items():
            first = slices[0]
            result.append({"uid": uid, "description": getattr(first, "SeriesDescription", "Unknown"), "modality": getattr(first, "Modality", "Unknown"), "num_slices": len(slices)})
        return result