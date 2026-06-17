from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QToolBar, QFileDialog, QLabel, QAction, QInputDialog, QMessageBox, QComboBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from functools import partial

from ui.viewer_widget import ViewerWidget
from ui.metadata_panel import MetadataPanel
from ui.stats_panel import StatsPanel

from core.dicom_loader import DICOMLoader
from core.image_stack import ImageStack
from viewer.viewer import MedicalImageViewer

class MainWindow(QMainWindow):

    def __init__(self, viewer=None):        
        super().__init__()
        
        self.preset_map = {
            "Bone Surface": "bone",
            "Dense Bone Surface": "dense_bone",
            "Soft Tissue Surface": "soft_tissue",
            "Skin Surface": "skin",
            "Bone Volume": "volume_bone",
            "Lung Volume": "volume_lung",
            "Soft Tissue Volume": "volume_soft_tissue"
        }

        self.setWindowTitle("Medical Imaging Workstation")
        self.resize(1600, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout()
        central_widget.setLayout(layout)
        
        self.main_layout = layout
        
        self.setWindowIcon(QIcon("icons/app_icon.png"))

        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # Create panels
        self.metadata_panel = MetadataPanel()
        self.stats_panel = StatsPanel()
        
        # Viewer placeholder
        if viewer is not None:
            self.viewer = viewer         
            self.viewer_container = ViewerWidget(viewer)
            viewer.stats_panel = self.stats_panel
            viewer.metadata_panel = self.metadata_panel
            self.metadata_panel.update_metadata(viewer.stack.metadata)
        else:
            self.viewer_container = QLabel("Open a DICOM study from File → Open DICOM Folder")
            self.viewer_container.setAlignment(Qt.AlignCenter)
        
        # Add panels to right panel
        right_layout.addWidget(self.metadata_panel)
        right_layout.addWidget(self.stats_panel)
        
        layout.addWidget(self.viewer_container, stretch=4)
        layout.addWidget(right_panel, stretch=1)
        
        self.create_menu()
        self.create_toolbar()
        self.statusBar().showMessage("Ready")
        self.set_active_tool(None)
        
    def create_menu(self):
        
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        open_action = file_menu.addAction("Open DICOM Folder")
        open_action.triggered.connect(self.open_dicom_folder)
        self.export_stl_action = file_menu.addAction("Export STL")
        self.export_stl_action.triggered.connect(self.export_stl)
        self.export_stl_action = file_menu.addAction("Save Screenshot")
        self.export_stl_action.triggered.connect(self.save_screen)
        
        file_menu.addSeparator()
        
        view_menu = menu.addMenu("View")
        self.reset_action = view_menu.addAction("Reset View")
        self.fit_action = view_menu.addAction("Fit to Window")
        self.cross_action = view_menu.addAction("Show Crosshair")
        self.histogram_action = view_menu.addAction("Show Histogram")
        self.meta_action = view_menu.addAction("Show Metadata Panel")
        self.stat_action = view_menu.addAction("Show Statistics Panel")
        
        
        view_menu.addSeparator()
        self.bone_preset = view_menu.addAction("Bone Preset")
        self.lung_preset = view_menu.addAction("Lung Preset")
        self.soft_preset = view_menu.addAction("Soft Tissue Preset")
        self.abdomen_preset = view_menu.addAction("Abdomen Preset")
        
        self.reset_action.setEnabled(False)
        self.fit_action.setEnabled(False)
        self.cross_action.setEnabled(False)
        self.cross_action.setCheckable(True)
        self.cross_action.setChecked(True)
        self.histogram_action.setEnabled(False)
        self.histogram_action.setCheckable(True)
        self.histogram_action.setChecked(True)
        self.meta_action.setCheckable(True)
        self.meta_action.setChecked(True)
        self.stat_action.setCheckable(True)
        self.stat_action.setChecked(True)
        self.bone_preset.setEnabled(False)
        self.lung_preset.setEnabled(False)
        self.soft_preset.setEnabled(False)
        self.abdomen_preset.setEnabled(False)
        
        self.reset_action.triggered.connect(self.reset_view)
        
        self.cross_action.triggered.connect(self.cross_visible)
        self.histogram_action.triggered.connect(self.toggle_histogram)
        self.meta_action.triggered.connect(self.meta_visible)
        self.stat_action.triggered.connect(self.stat_visible)
        self.bone_preset.triggered.connect(lambda: self.set_window_preset("bone"))
        
        self.lung_preset.triggered.connect(lambda: self.set_window_preset("lung"))
        self.soft_preset.triggered.connect(lambda: self.set_window_preset("soft_tissue"))
        self.abdomen_preset.triggered.connect(lambda: self.set_window_preset("abdomen"))
        
        tools_menu = menu.addMenu("Tools")
        
        self.distance_action = tools_menu.addAction("Distance Measurement")
        self.angle_action = tools_menu.addAction("Angle Measurement")
        tools_menu.addSeparator()
        self.circular_action = tools_menu.addAction("Circular ROI")
        self.rectangular_action = tools_menu.addAction("Rectangular ROI")
        self.elliptical_action = tools_menu.addAction("Elliptical ROI")
        self.free_action = tools_menu.addAction("Free ROI")
        tools_menu.addSeparator()
        self.segmentation_action = tools_menu.addAction("Segmentation")
        tools_menu.addSeparator()
        #self.bone_density_action = tools_menu.addAction("Bone Density Analysis")
        #self.lung_density_action = tools_menu.addAction("Lung Density Analysis")
        
        self.distance_action.setEnabled(False)
        self.angle_action.setEnabled(False)
        self.circular_action.setEnabled(False)
        self.rectangular_action.setEnabled(False)
        self.elliptical_action.setEnabled(False)
        self.free_action.setEnabled(False)
        self.segmentation_action.setEnabled(False)
        #self.bone_density_action.setEnabled(False)
        #self.lung_density_action.setEnabled(False)
        
        self.distance_action.triggered.connect(self.activate_measure)
        self.angle_action.triggered.connect(self.activate_angle)
        self.circular_action.triggered.connect(partial(self.activate_roi, "circle"))
        self.rectangular_action.triggered.connect(partial(self.activate_roi, "rectangle"))
        self.elliptical_action.triggered.connect(partial(self.activate_roi, "ellipse"))
        self.free_action.triggered.connect(partial(self.activate_roi, "free"))
        self.segmentation_action.triggered.connect(self.activate_segmentation)
        #self.bone_density_action.triggered.connect(self.run_bone_density_analysis)
        #self.lung_density_action.triggered.connect()
        
        
        render_menu = menu.addMenu("3D")
        surface_menu = render_menu.addMenu("Surface Rendering")
        bone_action = surface_menu.addAction("Bone")
        bone_action.triggered.connect(lambda: self.show_surface("bone"))
        dense_action = surface_menu.addAction("Dense Bone")
        dense_action.triggered.connect(lambda: self.show_surface("dense_bone"))
        soft_action = surface_menu.addAction("Soft Tissue")
        soft_action.triggered.connect(lambda: self.show_surface("soft_tissue"))
        skin_action = surface_menu.addAction("Skin")
        skin_action.triggered.connect(lambda: self.show_surface("skin"))
        
        volume_menu = render_menu.addMenu("Volume Rendering")
        bone_volume_action = volume_menu.addAction("Bone")
        bone_volume_action.triggered.connect(lambda: self.show_volume("bone"))
        soft_volume_action = volume_menu.addAction("Soft Tissue")
        soft_volume_action.triggered.connect(lambda: self.show_volume("soft_tissue"))
        lung_volume_action = volume_menu.addAction("Lung")
        lung_volume_action.triggered.connect(lambda: self.show_volume("lung"))
        
        help_menu = menu.addMenu("Help")
        shortcuts_action = help_menu.addAction("Keyboard Shortcuts")
        shortcuts_action.triggered.connect(self.show_shortcuts)
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about_dialog)
        
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        
        
    def create_toolbar(self):
        toolbar = QToolBar("Tools")
        toolbar.setIconSize(QSize(16,16))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)
        
        self.measure_action = QAction(QIcon("icons/rule.png"), "Measure", self)
        self.measure_action.setStatusTip("Distance measurement tool")
        self.measure_action.triggered.connect(self.activate_measure)
        self.measure_action.setCheckable(True)
        toolbar.addAction(self.measure_action)
        
        toolbar.addSeparator()
                
        self.circle_action = QAction(QIcon("icons/circle.png"), "Circular ROI", self)
        self.circle_action.setStatusTip("Circular ROI tool")
        self.circle_action.triggered.connect(partial(self.activate_roi, "circle"))
        self.circle_action.setCheckable(True)
        toolbar.addAction(self.circle_action)
        
        toolbar.addSeparator()
        
        self.rectangle_action = QAction(QIcon("icons/rectangle.png"), "Rectangular ROI", self)
        self.rectangle_action.setStatusTip("Rectangular ROI tool")
        self.rectangle_action.triggered.connect(partial(self.activate_roi, "rectangle"))
        self.rectangle_action.setCheckable(True)
        toolbar.addAction(self.rectangle_action)
        
        toolbar.addSeparator()
        
        self.ellipse_action = QAction(QIcon("icons/ellipse.png"), "Elliptical ROI", self)
        self.ellipse_action.setStatusTip("Elliptical ROI tool")
        self.ellipse_action.triggered.connect(partial(self.activate_roi, "ellipse"))
        self.ellipse_action.setCheckable(True)
        toolbar.addAction(self.ellipse_action)
        
        toolbar.addSeparator()
        
        self.roi_action = QAction(QIcon("icons/free.png"), "Free form ROI", self)
        self.roi_action.setStatusTip("Free form ROI tool")
        self.roi_action.triggered.connect(partial(self.activate_roi, "free"))
        self.roi_action.setCheckable(True)
        toolbar.addAction(self.roi_action)
        
        toolbar.addSeparator()
                
        self.segment_action = QAction(QIcon("icons/segmentation.png"), "Segment", self)
        self.segment_action.setStatusTip("Segment tool")
        self.segment_action.triggered.connect(self.activate_segmentation)
        self.segment_action.setCheckable(True)
        toolbar.addAction(self.segment_action)
        
        toolbar.addSeparator()
        
        self.render3d_action = QAction(QIcon("icons/3d.png"), "3D", self)
        self.render3d_action.setStatusTip("Segment tool")
        self.render3d_action.triggered.connect(self.show_3d)
        self.render3d_action.setCheckable(True)
        toolbar.addAction(self.render3d_action)
        
        toolbar.addSeparator()
        
        self.preset3d_combo = QComboBox()
        self.preset3d_combo.addItems(self.preset_map.keys())
        toolbar.addWidget(self.preset3d_combo)
    
    def open_dicom_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select DICOM Folder")
        if not folder:
            return
        loader = DICOMLoader(folder)
        stack = ImageStack(loader.volume_hu, loader.spacing, loader.metadata)
        viewer = MedicalImageViewer(stack)
        self.viewer = viewer
        viewer.stats_panel = self.stats_panel
        viewer.metadata_panel = self.metadata_panel
        viewer.status_bar = self.statusBar()
        self.main_layout.removeWidget(self.viewer_container)
        self.viewer_container.deleteLater()
        self.viewer_container = ViewerWidget(viewer)
        self.main_layout.insertWidget(0, self.viewer_container, stretch=4)
        self.metadata_panel.update_metadata(loader.metadata)
        self.reset_action.setEnabled(True)
        self.fit_action.setEnabled(True)
        self.cross_action.setEnabled(True)
        self.histogram_action.setEnabled(True)
        self.bone_preset.setEnabled(True)
        self.lung_preset.setEnabled(True)
        self.soft_preset.setEnabled(True)
        self.abdomen_preset.setEnabled(True)
        self.distance_action.setEnabled(True)
        self.angle_action.setEnabled(True)
        self.circular_action.setEnabled(True)
        self.rectangular_action.setEnabled(True)
        self.elliptical_action.setEnabled(True)
        self.free_action.setEnabled(True)
        self.segmentation_action.setEnabled(True)
        self.bone_density_action.setEnabled(True)
        self.lung_density_action.setEnabled(True)
    
    def activate_measure(self):
        if not hasattr(self, "viewer"):
            return
        self.set_active_tool("measure")
    
    def activate_angle(self):
        if not hasattr(self, "viewer"):
            return
        self.set_active_tool("angle")
    
    def activate_roi(self, mode):
        if not hasattr(self, "viewer"):
            return
        self.set_active_tool(mode)
    
    def activate_segmentation(self):
        if not hasattr(self, "viewer"):
            return
        self.set_active_tool("segment")
    
    def show_3d(self):
        if not hasattr(self, "viewer"):
            return
        display_name = self.preset3d_combo.currentText()
        preset = self.preset_map[display_name]
        self.viewer.viewer3d.show_preset(preset)
        
    def set_active_tool(self, tool_name):
        if not hasattr(self, "viewer"):
            return
        current = getattr(self, "active_tool", None)
        if current == tool_name:
            self.active_tool = None
            self.viewer.measurement.active = False
            self.viewer.angle.active = False
            self.viewer.segmentation.active = False
            self.viewer.roi.mode = None
            return
        self.viewer.measurement.active = False
        self.viewer.angle.active = False
        self.viewer.segmentation.active = False
        self.viewer.roi.mode = None
        self.active_tool = tool_name
        if tool_name == "measure":
            self.viewer.measurement.active = True
        elif tool_name == "angle":
            self.viewer.angle.active = True
        elif tool_name == "circle":
            self.viewer.roi.mode = "circle"
        elif tool_name == "rectangle":
            self.viewer.roi.mode = "rectangle"
        elif tool_name == "ellipse":
            self.viewer.roi.mode = "ellipse"
        elif tool_name == "free":
            self.viewer.roi.mode = "free"
        elif tool_name == "segment":
            self.viewer.segmentation.active = True
        self.update_toolbar_checks()
            
    def update_toolbar_checks(self):
        actions = [self.measure_action, self.circle_action, self.rectangle_action, self.ellipse_action, self.roi_action, self.segment_action,]
        for action in actions:
            action.setChecked(False)
        if self.active_tool == "measure":
            self.measure_action.setChecked(True)
        elif self.active_tool == "circle":
            self.circle_action.setChecked(True)
        elif self.active_tool == "rectangle":
            self.rectangle_action.setChecked(True)
        elif self.active_tool == "ellipse":
            self.ellipse_action.setChecked(True)
        elif self.active_tool == "free":
            self.roi_action.setChecked(True)
        elif self.active_tool == "segment":
            self.segment_action.setChecked(True)
    
    def export_stl(self):
        if not hasattr(self, "viewer"):
            return
        presets = ["skin", "soft_tissue", "bone", "dense_bone"]
        preset, ok = QInputDialog.getItem(self, "Export STL", "Select structure:", presets, 2, False)
        if not ok:
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Export STL", f"{preset}.stl", "STL Files (*.stl)")
        if not filename:
            return
        self.viewer.viewer3d.export_stl(preset, filename)
        QMessageBox.information(self, "Export Complete", f"STL saved:\n{filename}")
    
    def show_surface(self, preset):
        if not hasattr(self, "viewer"):
            return
        data = self.viewer.viewer3d.SURFACE_PRESETS[preset]
        self.viewer.viewer3d.create_surface(data["threshold"], data["color"])
    
    def show_volume(self, preset):
        if not hasattr(self, "viewer"):
            return
        self.viewer.viewer3d.show_volume(preset)
    
    def save_screen(self):
        filename, _ = QFileDialog.getSaveFileName(self,"Save Screenshot", "", "PNG (*.png)")
        self.viewer.fig.savefig(filename, dpi=300, bbox_inches="tight")
    
    def reset_view(self):
        if not hasattr(self, "viewer"):
            return
        self.viewer.reset_view()
    
    def toggle_histogram(self, checked):
        if not hasattr(self, "viewer"):
            return
        self.viewer.histogram_dirty = checked
        self.viewer.render()
    
    def meta_visible(self, checked):
        self.metadata_panel.setVisible(checked)
    
    def stat_visible(self, checked):
         self.stats_panel.setVisible(checked)
    
    def cross_visible(self, checked):
        if not hasattr(self, "viewer"):
            return
        self.viewer.crossctrl.visible = checked
        self.viewer.render()
    
    def set_window_preset(self, preset_name):
        if not hasattr(self, "viewer"):
            return
        self.viewer.controller.set_preset(preset_name)
        self.viewer.render()
    
    def run_bone_density_analysis(self):
        if not hasattr(self, "viewer"):
            return
        self.viewer.run_bone_density_analysis()
    
    def show_shortcuts(self):
        QMessageBox.about(
            self,
            "Keyboard Shortcuts",
            """
            <table cellspacing="4">
            <tr><td><b>↑ / ↓</b></td><td>Previous / Next Slice</td></tr>
            <tr><td><b>← / →</b></td><td>Change Window Preset</td></tr>
            <tr><td><b>W / X / A / D</b></td><td>Pan</td></tr>
            <tr><td><b>1</b></td><td>Axial Plane</td></tr>
            <tr><td><b>2</b></td><td>Coronal Plane</td></tr>
            <tr><td><b>3</b></td><td>Sagittal Plane</td></tr>
            <tr><td><b>M</b></td><td>Measurement Tool</td></tr>
            <tr><td><b>O</b></td><td>Circular ROI</td></tr>
            <tr><td><b>P</b></td><td>Rectangular ROI</td></tr>
            <tr><td><b>E</b></td><td>Elliptical ROI</td></tr>
            <tr><td><b>F</b></td><td>Free Form ROI</td></tr>
            <tr><td><b>4</b></td><td>Lung 3D View</td></tr>
            <tr><td><b>5</b></td><td>Soft Tissue 3D View</td></tr>
            <tr><td><b>6</b></td><td>Bone 3D View</td></tr>
            <tr><td><b>Space</b></td><td>Cine Mode</td></tr>
            <tr><td><b>R</b></td><td>Reset View</td></tr>
            <tr><td><b>Esc</b></td><td>Close All Tools</td></tr>
            <tr><td><b>B</b></td><td>Bone Threshold Segmentation</td></tr>
            <tr><td><b>L</b></td><td>Lung Threshold Segmentation</td></tr>
            <tr><td><b>G</b></td><td>Region Growing Segmentation</td></tr>
            <tr><td><b>Mouse Wheel</b></td><td>Scroll Slices / Zoom</td></tr>
            <tr><td><b>Left Click</b></td><td>Measurement / ROI / Crosshair</td></tr>
            <tr><td><b>Middle Click</b></td><td>HU Probe</td></tr>
            <tr><td><b>Right Click</b></td><td>Window / Level</td></tr>
            <tr><td><b>Ctrl + Drag</b></td><td>Pan</td></tr>
            </table>
            """
        )
    
    def show_about_dialog(self):
        QMessageBox.about(
            self,
            "About Medical Imaging Workstation",
            """
            <h2>Medical Imaging Workstation</h2>

            <p><b>Version:</b> 1.0</p>

            <p>
            A DICOM workstation for medical image visualization,
            segmentation, quantitative analysis, 3D reconstruction,
            and STL export.
            </p>

            <p><b>Features</b></p>

            <ul>
                <li>DICOM Viewer</li>
                <li>MPR Reconstruction</li>
                <li>Window / Level</li>
                <li>ROI Analysis</li>
                <li>Region Growing Segmentation</li>
                <li>Volume Rendering</li>
                <li>Surface Rendering</li>
                <li>STL Export</li>
            </ul>

            <p>
            Built with Python, PyQt5, Matplotlib, NumPy and VTK.
            </p>

            <p>
            © 2026 David Enrique Veloz Renteria
            </p>
            """
        )