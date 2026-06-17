from vtk.util import numpy_support
import vtk
import numpy as np


class Viewer3D:

    def __init__(self, image_stack):
        self.stack = image_stack

        self.VOLUME_PRESETS = {
            "bone": {"opacity": [(-1000, 0.0), (200, 0.0), (400, 0.3), (1000, 1.0)], "color": [(-1000, 0.0, 0.0, 0.0), (400, 0.9, 0.9, 0.8), (1500, 1.0, 1.0, 1.0)]},
            "soft_tissue": {"opacity": [(-1000, 0.0), (-100, 0.0), (50, 0.3), (300, 0.8)], "color": [(-1000, 0.0, 0.0, 0.0), (50, 0.8, 0.5, 0.5), (300, 1.0, 0.8, 0.7)]},
            "lung": {"opacity": [(-1000, 0.0), (-800, 0.2), (-400, 0.6), (200, 0.0)], "color": [(-1000, 0.0, 0.0, 0.0), (-700, 0.7, 0.9, 1.0), (-400, 1.0, 1.0, 1.0)]}
        }

        self.SURFACE_PRESETS = {
            "skin": {"threshold": -300, "color": (1.0, 0.8, 0.7)},
            "soft_tissue": {"threshold": 40, "color": (0.9, 0.5, 0.5)},
            "bone": {"threshold": 400, "color": (0.95, 0.92, 0.85)},
            "dense_bone": {"threshold": 1000, "color": (1.0, 1.0, 1.0)}
        }

    def build_vtk_image(self):
        volume = self.stack.volume.astype(np.float32)
        # numpy: (z,y,x)
        # vtk:   (x,y,z)
        volume = np.transpose(volume, (2, 1, 0))
        vtk_array = numpy_support.numpy_to_vtk(volume.ravel(order="F"), deep=True, array_type=vtk.VTK_FLOAT)
        image = vtk.vtkImageData()
        image.SetDimensions(volume.shape)
        image.SetSpacing(self.stack.spacing_x, self.stack.spacing_y, self.stack.spacing_z)
        image.SetOrigin(0, 0, 0)
        image.GetPointData().SetScalars(vtk_array)
        return image

    def create_surface(self, threshold, color):
        image = self.build_vtk_image()
        mc = vtk.vtkMarchingCubes()
        mc.SetInputData(image)
        mc.SetValue(0, threshold)
        mc.Update()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(mc.GetOutputPort())
        mapper.ScalarVisibilityOff()
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)
        renderer = vtk.vtkRenderer()
        renderer.AddActor(actor)
        renderer.SetBackground(0.1, 0.1, 0.1)
        render_window = vtk.vtkRenderWindow()
        render_window.AddRenderer(renderer)
        render_window.SetSize(1200, 900)
        interactor = vtk.vtkRenderWindowInteractor()
        interactor.SetRenderWindow(render_window)
        style = vtk.vtkInteractorStyleTrackballCamera()
        interactor.SetInteractorStyle(style)
        render_window.Render()
        interactor.Start()

    def show_surface(self, preset_name="bone"):
        preset = self.SURFACE_PRESETS[preset_name]
        self.create_surface(preset["threshold"], preset["color"])

    def build_opacity_function(self, preset):
        opacity = vtk.vtkPiecewiseFunction()
        for hu, value in preset["opacity"]:
            opacity.AddPoint(hu, value)
        return opacity

    def build_color_function(self, preset):
        color = vtk.vtkColorTransferFunction()
        for hu, r, g, b in preset["color"]:
            color.AddRGBPoint(hu, r, g, b)
        return color

    def show_volume(self, preset_name="bone"):
        image = self.build_vtk_image()
        preset = self.VOLUME_PRESETS[preset_name]
        mapper = vtk.vtkSmartVolumeMapper()
        mapper.SetInputData(image)
        volume_property = vtk.vtkVolumeProperty()
        volume_property.SetScalarOpacity(self.build_opacity_function(preset))
        volume_property.SetColor(self.build_color_function(preset))
        volume_property.ShadeOn()
        volume_property.SetInterpolationTypeToLinear()
        volume = vtk.vtkVolume()
        volume.SetMapper(mapper)
        volume.SetProperty(volume_property)
        renderer = vtk.vtkRenderer()
        renderer.AddVolume(volume)
        renderer.SetBackground(0.1, 0.1, 0.1)
        render_window = vtk.vtkRenderWindow()
        render_window.AddRenderer(renderer)
        render_window.SetSize(1200, 900)
        interactor = vtk.vtkRenderWindowInteractor()
        interactor.SetRenderWindow(render_window)
        style = vtk.vtkInteractorStyleTrackballCamera()
        interactor.SetInteractorStyle(style)
        render_window.Render()
        interactor.Start()

    def show_bone(self):
        self.export_stl("bone", "bone.stl")
        self.show_surface("bone")

    def show_skin(self):
        self.export_stl("skin", "skin.stl")
        self.show_surface("skin")

    def show_soft_tissue_surface(self):
        self.export_stl("soft_tissue", "soft_tissue.stl")
        self.show_surface("soft_tissue")

    def show_volume_bone(self):
        self.export_stl("bone", "bone.stl")
        self.show_volume("bone")

    def show_volume_lung(self):
        self.export_stl("lung", "lung.stl")
        self.show_volume("lung")

    def show_volume_soft_tissue(self):
        self.export_stl("soft_tissue", "soft_tissue.stl")
        self.show_volume("soft_tissue")
        
    def export_stl(self, preset_name, filename):
        threshold = self.SURFACE_PRESETS[preset_name]["threshold"]
        image = self.build_vtk_image()
        # Surface extraction
        mc = vtk.vtkMarchingCubes()
        mc.SetInputData(image)
        mc.SetValue(0, threshold)
        mc.Update()
        # Remove duplicated points and degenerate triangles
        clean = vtk.vtkCleanPolyData()
        clean.SetInputConnection(mc.GetOutputPort())
        clean.Update()
        # Surface smoothing
        smooth = vtk.vtkSmoothPolyDataFilter()
        smooth.SetInputConnection(clean.GetOutputPort())
        smooth.SetNumberOfIterations(20)
        smooth.SetRelaxationFactor(0.1)
        smooth.FeatureEdgeSmoothingOff()
        smooth.BoundarySmoothingOn()
        smooth.Update()
        # Normal
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputConnection(smooth.GetOutputPort())
        normals.ComputePointNormalsOn()
        normals.ComputeCellNormalsOn()
        normals.Update()
        # STL export
        writer = vtk.vtkSTLWriter()
        writer.SetFileName(filename)
        writer.SetInputData(normals.GetOutput())
        writer.Write()
        print(f"STL saved: {filename}")
    
    def show_preset(self, preset_name):
        if preset_name == "bone":
            self.create_surface(self.SURFACE_PRESETS["bone"]["threshold"], self.SURFACE_PRESETS["bone"]["color"])
        elif preset_name == "dense_bone":
            self.create_surface(self.SURFACE_PRESETS["dense_bone"]["threshold"], self.SURFACE_PRESETS["dense_bone"]["color"])
        elif preset_name == "soft_tissue":
            self.create_surface(self.SURFACE_PRESETS["soft_tissue"]["threshold"], self.SURFACE_PRESETS["soft_tissue"]["color"])
        elif preset_name == "skin":
            self.create_surface(self.SURFACE_PRESETS["skin"]["threshold"], self.SURFACE_PRESETS["skin"]["color"])
        elif preset_name == "volume_bone":
            self.show_volume("bone")
        elif preset_name == "volume_lung":
            self.show_volume("lung")
        elif preset_name == "volume_soft_tissue":
            self.show_volume("soft_tissue")