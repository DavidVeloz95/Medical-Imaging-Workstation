# Medical Imaging Workstation

A Python-based workstation for DICOM visualization, segmentation,
quantitative analysis and 3D reconstruction.

![Main Screenshot](screenshots/main_view.png)

## Overview

Medical Imaging Workstation is a desktop application developed in Pytho for visualization and analysis of CT studies.

The software supports multiplanar reconstruction (MPR), ROI analysis, segmentation, density analysis, 3D visualization and STL export.

## Features

### DICOM Visualization

- DICOM series loading
- Metadata viewer
- Axial, Coronal and Sagittal views
- Window / Level adjustment
- CT window presets
- Crosshair navigation
- HU Probe

### Measurements

- Distance measurement
- Angle measurement

### ROI Analysis

- Circular ROI
- Rectangular ROI
- Elliptical ROI
- Free-form ROI
- ROI statistics
- Histogram visualization

### Segmentation

- Threshold segmentation
- Region growing segmentation
- Volume calculation
- Density analysis

### 3D Visualization

- Surface rendering
- Volume rendering
- Bone preset
- Lung preset
- Soft tissue preset

### Export

- STL export
- Screenshot export

## Screenshots

![MPR Viewer](screenshots/mpr_viewer.png)

![ROI Analysis](screenshots/roi_analysis.png)

![Segmentation](screenshots/segmentation.png)

![3D Rendering](screenshots/3d_render.png)

## Technologies

- Python
- PyQt5
- NumPy
- Matplotlib
- pydicom
- VTK

## Project Structure

Medical Imaging Workstation
│
├── core
│   ├── dicom_loader.py
│   └── image_stack.py
│
├── controllers
│
├── segmentation
│
├── viewer
│
├── rendering
│
└── ui

## Installation

git clone https://github.com/yourusername/medical-imaging-workstation.git

cd medical-imaging-workstation

pip install -r requirements.txt

python main.py

---

## Keyboard Shortcuts

| Key | Action |
|------|---------|
| ↑ / ↓ | Previous / Next Slice |
| ← / → | Change Window Preset |
| M | Measurement Tool |
| O | Circular ROI |
| P | Rectangular ROI |
| E | Elliptical ROI |
| F | Free ROI |
| B | Bone Segmentation |
| L | Lung Segmentation |
| G | Region Growing |
| R | Reset View |
| Space | Cine Mode |

## STL Export

Segmented structures can be converted into polygonal meshes
using Marching Cubes and exported as STL files for:

- 3D Printing
- CAD workflows
- Point cloud processing
- Surface analysis

## Author

David Enrique Veloz Renteria

Computer Vision | Medical Imaging | Robotics | AI

LinkedIn:
https://www.linkedin.com/in/davidveloz/?locale=en-US

GitHub:
https://github.com/DavidVeloz95
