import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.patches import Rectangle
from matplotlib.patches import Polygon
from matplotlib.patches import Ellipse

from viewer.viewer_3d import Viewer3D

from core.windowing import DICOMWindowing
from core.segmentation import SegmentationDICOM

from controllers.viewport_controller import ViewportController
from controllers.window_controller import WindowLevelController
from controllers.crosshair_controller import CrosshairController
from controllers.measurement_controller import MeasurementController
from controllers.roi_controller import ROIController
from controllers.cine_controller import CineController
from controllers.angle_controller import AngleController
from controllers.hu_probe_controller import HUProbeController

class MedicalImageViewer:
    def __init__(self, image_stack):
        
        self.stack = image_stack
        
        self.viewer3d = Viewer3D(self.stack)
        
        # Objects
        self.viewport = ViewportController()
        self.controller = WindowLevelController()
        self.hu_probe = HUProbeController()
        self.segmentation = SegmentationDICOM()
        
        # Plane state
        self.current_plane = 0                 # 0 - axial; 1 - coronal; 2 - sagittal
        
        self.pos_x = 1.00
        self.pos_y = 140.00
        
        self.crosshair = {
            0: None,   # axial
            1: None,   # coronal
            2: None    # sagittal
        }
        
        self.right_mouse_pressed = False
        self.last_mouse_x = None
        self.last_mouse_y = None
               
        # Key state
        self.ctrl = False
        self.stats_panel = None
        self.statistics_dirty = True
        
        self.show_histogram = True
        self.histogram_dirty = True
        
        # Figure
        self.fig, axes = plt.subplots(2,2)
        
        self.axial_ax = axes[0,0]
        self.coronal_ax = axes[0,1]
        self.sagittal_ax = axes[1,0]
        self.extra_ax = axes[1,1]
        
        self.ax = {
            "axial": self.axial_ax,
            "coronal": self.coronal_ax,
            "sagittal": self.sagittal_ax,
            "extra": self.extra_ax,
        }
        
        self.plane_axes = {
            0: self.ax["axial"],
            1: self.ax["coronal"],
            2: self.ax["sagittal"]
        }        
        
        self.plane_names = {
            0: "AXIAL",
            1: "CORONAL",
            2: "SAGITTAL"
        }
        
        self.axis_to_plane = {
            self.axial_ax: 0,
            self.coronal_ax: 1,
            self.sagittal_ax: 2,
        }
        
        for ax in self.ax.values():
            ax.set_xticks([])
            ax.set_yticks([])
    
        # Objects No. 2
        self.crossctrl = CrosshairController(self.stack, self.ax, self.viewport)
        self.measurement = MeasurementController(self.stack.spacing_x, self.stack.spacing_y, self.stack.spacing_z)
        self.angle = AngleController(self.stack.spacing_x, self.stack.spacing_y, self.stack.spacing_z)
        self.roi = ROIController(self.stack.spacing_x, self.stack.spacing_y)
        
        self.cine = CineController(fps=30)
        self.timer = self.fig.canvas.new_timer(interval=self.cine.interval_ms)
        self.timer.add_callback(self.cine_step)
        
        initial_image_ax, initial_image_co, initial_image_sa = self.apply_windowing()
        self.im_artist_ax = self.axial_ax.imshow(initial_image_ax, cmap="gray", aspect=self.stack.aspect_ratio_ax)
        self.im_artist_co = self.coronal_ax.imshow(initial_image_co, cmap="gray", aspect=self.stack.aspect_ratio_co)
        self.im_artist_sa = self.sagittal_ax.imshow(initial_image_sa, cmap="gray", aspect=self.stack.aspect_ratio_sa)
        
        self.segmentation_artist = self.axial_ax.imshow(np.zeros_like(initial_image_ax), cmap="Reds", alpha=0.4, visible=False)
        
        self.reset_view()
        
        self.render()

        # Keyboard event
        self.fig.canvas.mpl_connect('key_press_event', self.on_press)
        self.fig.canvas.mpl_connect('key_release_event', self.on_release)
        # Scroll event
        self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        # Click event
        self.fig.canvas.mpl_connect('button_press_event', self.on_mouse_click)
        self.fig.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

    def on_press(self, event):
        sys.stdout.flush()
        
        # control
        if event.key == 'control':
            self.ctrl = True
        
        # Slice navigation
        elif event.key == 'up':
            self.change_slice(1)
        elif event.key == 'down':
            self.change_slice(-1)

        # Window navigation
        elif event.key == 'right':
            self.controller.change_window(1)
            self.render()            
        elif event.key == 'left':
            self.controller.change_window(-1)
            self.render()
        
        # Pan
        elif event.key == 'w':
            self.viewport.center_y[self.current_plane] -= self.viewport.pan_step
            self.render()
        elif event.key == 'x':
            self.viewport.center_y[self.current_plane] += self.viewport.pan_step
            self.render()
        elif event.key == 'a':
            self.viewport.center_x[self.current_plane] -= self.viewport.pan_step
            self.render()
        elif event.key == 'd':
            self.viewport.center_x[self.current_plane] += self.viewport.pan_step
            self.render()
        
        # Plane change
        elif event.key == '1':
            self.change_plane(0)        
        elif event.key == '2':
            self.change_plane(1)
        elif event.key == '3':
            self.change_plane(2)
        
        # Measurement tool
        elif event.key == 'm':
            self.measurement.active = not self.measurement.active
            if not self.measurement.active:
                self.measurement.clear()
            self.render()
            self.roi.mode = None
        
        # Angle calculator tool
        elif event.key == 't':
            self.angle.active = not self.angle.active
            if not self.angle.active:
                self.angle.clear()
            self.render()
            self.roi.mode = None
        
        # ROI
        # Circular
        elif event.key == 'o':
            if self.roi.mode == "circle":
                self.roi.mode = None
            else:
                self.roi.clear()
                self.roi.mode = "circle"
                self.measurement.active = False
        
        # Rectangular
        elif event.key == 'p':
            if self.roi.mode == "rectangle":
                self.roi.mode = None
            else:
                self.roi.clear()
                self.roi.mode = "rectangle"
                self.measurement.active = False
        
        # Free
        elif event.key == 'f':
            if self.roi.mode == "free":
                self.roi.mode = None
            else:
                self.roi.clear()
                self.roi.mode = "free"
                self.measurement.active = False
        
        # Ellipse
        elif event.key == 'e':
            if self.roi.mode == "ellipse":
                self.roi.mode = None
            else:
                self.roi.clear()
                self.roi.mode = "ellipse"
                self.measurement.active = False
        
        # 3D View
        elif event.key == 'v':
            self.open_3d()
        
        elif event.key == '8':
            Viewer3D(self.stack).show_bone()

        elif event.key == '6':
            Viewer3D(self.stack).show_volume_bone()

        elif event.key == '4':
            Viewer3D(self.stack).show_volume_lung()

        elif event.key == '5':
            Viewer3D(self.stack).show_volume_soft_tissue()       
        
        elif event.key == 'b':
            self.segmentation.active = not self.segmentation.active
            if not self.segmentation.active:
                self.segmentation.clear()
                return
            self.segmentation.threshold(self.stack.volume, 300, 3000)
            self.histogram_dirty = True
            self.statistics_dirty = True
            self.render()
            self.roi.mode = None

        elif event.key == 'l':
            self.segmentation.active = not self.segmentation.active
            if not self.segmentation.active:
                self.segmentation.clear()
                return
            self.segmentation.threshold(self.stack.volume, -1000, -400)
            self.histogram_dirty = True
            self.statistics_dirty = True
            self.render()
            self.roi.mode = None
        
        elif event.key == 'g':
            self.segmentation.active = (not self.segmentation.active)
        
        elif event.key == 'i':
            self.show_metadata()
            self.print_summary()
        
        # Cine Mode
        elif event.key == ' ':
            self.zero_slice()
            self.trigger_cine()
        
        # Reset view
        elif event.key == 'r':
            self.reset_current_view()
            
        # Close every tool
        elif event.key == 'escape':
            self.roi.mode = None
            self.measurement.active = False

    def on_release(self, event):
        if event.key == 'control':
            self.ctrl = False
            
    def on_scroll(self, event):
        if self.ctrl:
            if event.button == 'up':
                self.viewport.zoom_in(self.current_plane)
            elif event.button == 'down':
                self.viewport.zoom_out(self.current_plane)
        else:            
            if event.button == 'up':
                self.change_slice(1)
            elif event.button == 'down':
                self.change_slice(-1)
        self.render()
    
    def change_slice(self, delta):
        cursor = self.crossctrl.cursor_3d
        if self.current_plane == 0:
            cursor["z"] = np.clip(cursor["z"] + delta, 0, self.stack.shape[0] - 1)
        elif self.current_plane == 1:
            cursor["y"] = np.clip(cursor["y"] + delta, 0, self.stack.shape[1] - 1)
        elif self.current_plane == 2:
            cursor["x"] = np.clip(cursor["x"] + delta, 0, self.stack.shape[2] - 1)
        self.histogram_dirty = True
        self.statistics_dirty = True
        self.render()
    
    def zero_slice(self):
        cursor = self.crossctrl.cursor_3d
        cursor["z"] = 0
        cursor["y"] = 0
        cursor["x"] = 0
        self.render()
    
    def get_num_slices(self):
        return self.stack.shape[0], self.stack.shape[1], self.stack.shape[2]
    
    def change_plane(self, plane):
        self.current_plane = plane
        self.render()
    
    def get_current_slice(self):
        cursor = self.crossctrl.cursor_3d
        z = cursor["z"]
        y = cursor["y"]
        x = cursor["x"]
        image_ax = self.stack.volume[z, :, :]
        image_co = self.stack.volume[:, y, :]
        image_sa = self.stack.volume[:, :, x]
        return image_ax, image_co, image_sa
    
    def apply_window(self, image):
        return DICOMWindowing(image).apply_window(self.controller.window_level, self.controller.window_width)
    
    def apply_windowing(self):
        image_ax, image_co, image_sa = self.get_current_slice()
        return (self.apply_window(image_ax), self.apply_window(image_co), self.apply_window(image_sa))
    
    def reset_view(self):
        image_ax, image_co, image_sa = self.get_current_slice()
        images = {0: image_ax, 1: image_co, 2: image_sa}
        self.viewport.reset_all(images)
        self.render()
        
    def reset_current_view(self):
        cursor = self.crossctrl.cursor_3d
        images = {0: self.stack.volume[cursor["z"], :, :], 1: self.stack.volume[:, cursor["y"], :], 2: self.stack.volume[:, :, cursor["x"]]}
        image = images[self.current_plane]
        h, w = image.shape
        self.viewport.reset_plane(self.current_plane, w, h)
        self.segmentation.clear()
        self.render()
    
    def update_viewport(self, image_ax, image_co, image_sa):
        images = {0: image_ax, 1: image_co, 2: image_sa}
        for plane in range(3):
            height, width = images[plane].shape
            left, right, top, bottom = (self.viewport.get_viewport_limits(plane, width, height))
            self.plane_axes[plane].set_xlim(left, right)
            self.plane_axes[plane].set_ylim(bottom, top)
    
    def render(self):
        image_ax, image_co, image_sa = self.apply_windowing()
        self.im_artist_ax.set_data(image_ax)
        self.im_artist_co.set_data(image_co)
        self.im_artist_sa.set_data(image_sa)
        self.axial_ax.set_aspect(self.stack.aspect_ratio_ax)
        self.coronal_ax.set_aspect(self.stack.aspect_ratio_co)
        self.sagittal_ax.set_aspect(self.stack.aspect_ratio_sa)
        preset = self.controller.get_current_preset()
        
        if self.segmentation.mask is not None:
            z = self.crossctrl.cursor_3d["z"]
            mask_slice = self.segmentation.mask[z]
            # plt.figure("DEBUG MASK")
            # plt.clf()
            # plt.imshow(mask_slice, cmap="gray")
            # plt.show(block=False)
            self.segmentation_artist.set_data(mask_slice.astype(float))
            self.segmentation_artist.set_clim(0,1)
            self.segmentation_artist.set_cmap("Reds")
            self.segmentation_artist.set_alpha(0.8)
            self.segmentation_artist.set_visible(True)
        else:
            self.segmentation_artist.set_visible(False)
        
        cursor = self.crossctrl.cursor_3d
        self.axial_ax.set_title(f"AXIAL | Slice: {cursor['z']} | "f"{preset['description']} | Zoom {self.viewport.zoom_factor[0]:.2f}x")
        self.coronal_ax.set_title(f"CORONAL | Slice: {cursor['y']} | "f"{preset['description']} | Zoom {self.viewport.zoom_factor[1]:.2f}x")
        self.sagittal_ax.set_title(f"SAGITTAL | Slice: {cursor['x']} | "f"{preset['description']} | Zoom {self.viewport.zoom_factor[2]:.2f}x")

        self.update_viewport(image_ax, image_co, image_sa)
        self.crossctrl.update_crosshair()
        self.draw_measurement()
        self.draw_angle()
        self.draw_roi()
        self.draw_hu_probe()
        self.draw_segmentation()
        if self.show_histogram:
            self.draw_histogram()
        else:
            self.extra_ax.clear()
            self.extra_ax.set_xticks([])
            self.extra_ax.set_yticks([])
        self.update_status_bar()
        self.fig.canvas.draw_idle()
        
    def on_mouse_click(self, event):
        if event.inaxes not in self.ax.values():
            return
        if event.xdata is None or event.ydata is None:
            return
        plane = self.axis_to_plane.get(event.inaxes)
        if plane is None:
            return
        x = int(event.xdata)
        y = int(event.ydata)
        
        # Click con la rueda
        if event.button == 2:
            plane = self.axis_to_plane.get(event.inaxes)
            x = int(event.xdata)
            y = int(event.ydata)
            self.hu_probe.set_point(plane, x, y)
            self.render()
            return
    
        # ROI libre: cerrar con click derecho
        if event.button == 3 and self.roi.mode == "circle":
            self.roi.close_free_roi()
            self.render()
            return
        
        # ROI libre: cerrar con click derecho
        if event.button == 3 and self.roi.mode == "rectangle":
            self.roi.close_free_roi()
            self.render()
            return

        # ROI libre: cerrar con click derecho
        if event.button == 3 and self.roi.mode == "free":
            self.roi.close_free_roi()
            self.render()
            return
        
        # ROI libre: cerrar con click derecho
        if event.button == 3 and self.roi.mode == "ellipse":
            self.roi.close_free_roi()
            self.render()
            return

        # Window/Level
        if event.button == 3:
            self.right_mouse_pressed = True
            self.last_mouse_x = event.x
            self.last_mouse_y = event.y
            return

        # Solo procesamos click izquierdo desde aquí
        if event.button != 1:
            return

        # ROI tiene prioridad
        if self.roi.mode is not None:
            self.roi.add_point(plane, x, y)
            self.histogram_dirty = True
            self.statistics_dirty = True
            self.render()
            return

        # Measurement tiene prioridad sobre crosshair
        if self.measurement.active:
            self.measurement.add_point(plane, x, y)
            self.render()
            return
        
        # Angle tiene prioridad sobre crosshair
        if self.angle.active:
            self.angle.add_point(plane, x, y)
            self.render()
            return
        
        if self.segmentation.active:
            seed = (self.crossctrl.cursor_3d["z"], self.crossctrl.cursor_3d["y"], self.crossctrl.cursor_3d["x"])
            self.segmentation.region_growing(self.stack.volume, seed, 50)
            self.histogram_dirty = True
            self.statistics_dirty = True
            self.render()
            return
        
        # Crosshair (comportamiento normal)
        cursor = self.crossctrl.cursor_3d

        if plane == 0:
            x = np.clip(x, 0, self.stack.shape[2]-1)
            y = np.clip(y, 0, self.stack.shape[1]-1)

            cursor["x"] = x
            cursor["y"] = y

        elif plane == 1:
            x = np.clip(x, 0, self.stack.shape[2]-1)
            y = np.clip(y, 0, self.stack.shape[0]-1)
            cursor["x"] = x
            cursor["z"] = y

        elif plane == 2:
            x = np.clip(x, 0, self.stack.shape[1]-1)
            y = np.clip(y, 0, self.stack.shape[0]-1)
            cursor["y"] = x
            cursor["z"] = y
            
        self.crossctrl.center_views_on_cursor()
        self.render()
    
    def on_mouse_release(self, event):
        if event.button == 3:
            self.right_mouse_pressed = False
            
    def on_mouse_move(self, event):
        if not event.button == 3:
            return
        if event.x is None or event.y is None:
            return
        dx = event.x - self.last_mouse_x
        dy = event.y - self.last_mouse_y
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self.controller.adjust(dx, dy)
        self.render()
    
    def draw_measurement(self):
        if not self.measurement.has_measurement():
            return
        plane, x1, y1 = self.measurement.point_a
        _, x2, y2 = self.measurement.point_b
        distance = self.measurement.calculate_distance_mm()
        ax = self.plane_axes[plane]
        if self.measurement.line_artist is not None:
            self.measurement.line_artist.remove()
        if self.measurement.text_artist is not None:
            self.measurement.text_artist.remove()
        self.measurement.line_artist = ax.plot([x1, x2], [y1, y2], 'y-', lw=2)[0]
        self.measurement.text_artist = ax.text((x1 + x2) / 2, (y1 + y2) / 2, f"{distance:.1f} mm", color="yellow")
    
    def get_roi_image(self):
        plane = self.roi.plane
        if plane == 0:
            return self.stack.volume[self.crossctrl.cursor_3d["z"], :, :]
        if plane == 1:
            return self.stack.volume[:, self.crossctrl.cursor_3d["y"], :]
        else:
            return self.stack.volume[:, :, self.crossctrl.cursor_3d["x"]]
        
    def draw_roi(self):
        if not self.roi.is_complete():
            return
        image = self.get_roi_image()
        stats = self.roi.calculate_statistics(image)
        if self.stats_panel:
            self.stats_panel.update_roi(stats)
            
        if stats is None:
            return
        ax = self.plane_axes[self.roi.plane]
        
        if self.roi.artist:
            self.roi.artist.remove()
        if self.roi.text_artist:
            self.roi.text_artist.remove()
        
        text = (f"Mean: {stats['mean']:.1f} HU\n" f"Std: {stats['std']:.1f}\n" f"Min: {stats['min']:.1f}\n" f"Max: {stats['max']:.1f}\n" f"Area: {stats['area']:.1f} mm²")
        
        if self.roi.mode == "circle":
            cx, cy = self.roi.center
            self.roi.artist = Circle((cx, cy), self.roi.radius, fill=False, color='lime', linewidth=2)
            self.roi.text_artist = ax.text(self.pos_x, self.pos_y, text, color='lime')
            self.histogram = True
        
        if self.roi.mode == "rectangle":
            x1, y1 = self.roi.point_a
            x2, y2 = self.roi.point_b
            self.roi.artist = Rectangle( (min(x1, x2) , min(y1, y2)), abs(x2 - x1), abs(y2 - y1), fill=False, color='cyan', linewidth=2)            
            self.roi.text_artist = ax.text(self.pos_x , self.pos_y, text, color='cyan')
            self.histogram = True
            
        if self.roi.mode == "free":
            self.roi.artist = Polygon(self.roi.points, closed = True, fill = False, color = "yellow", linewidth = 2)
            x0, y0 = self.roi.points[0]
            self.roi.text_artist = ax.text(self.pos_x, self.pos_y, text, color = "yellow")
            self.histogram = True
        
        if self.roi.mode == "ellipse":
            x1, y1 = self.roi.corner_a
            x2, y2 = self.roi.corner_b
            cx = (x1 + x2)/2
            cy = (y1 + y2)/2
            self.roi.artist = Ellipse((cx, cy), abs(x2 - x1), abs(y2 - y1), fill=False, color='lime', linewidth=2)
            self.roi.text_artist = ax.text(self.pos_x, self.pos_y, text, color='red')
            self.histogram = True
        
        ax.add_patch(self.roi.artist)
        
        if self.histogram:
            hist, edges = self.roi.get_histogram(image)
            plt.figure("ROI Histogram")
            plt.clf()
            plt.stairs(hist, edges)
            plt.xlabel("HU")
            plt.ylabel("Count")
            plt.title("ROI Histogram")
            #plt.show(block=False)
            self.histogram = False
        
    def trigger_cine(self):
        self.cine.toggle()
        if self.cine.active:
            self.timer.start()
        else:
            self.timer.stop()
    
    def cine_step(self):
        if not self.cine.active:
            return
        cursor = self.crossctrl.cursor_3d
        if self.current_plane == 0:
            cursor["z"] += 1
            if cursor["z"] >= self.stack.shape[0]:
                cursor["z"] = 0
        elif self.current_plane == 1:
            cursor["y"] += 1
            if cursor["y"] >= self.stack.shape[1]:
                cursor["y"] = 0
        elif self.current_plane == 2:
            cursor["x"] += 1
            if cursor["x"] >= self.stack.shape[2]:
                cursor["x"] = 0
        self.render()
        
    def open_3d(self):
        self.viewer3d.show_bone()
    
    def draw_angle(self):
        if not self.angle.has_measurement():
            return
        plane, x1, y1 = self.angle.point_a
        _, x2, y2 = self.angle.point_b
        _, x3, y3 = self.angle.point_c
        distance = self.angle.calculate_angle_degrees()
        ax = self.plane_axes[plane]
        if self.angle.line_artist_1 is not None:
            self.angle.line_artist_1.remove()
        if self.angle.line_artist_2 is not None:
            self.angle.line_artist_2.remove()
        if self.angle.text_artist is not None:
            self.angle.text_artist.remove()
        self.angle.line_artist_1 = ax.plot([x1, x2], [y1, y2], 'y-', lw=2)[0]
        self.angle.line_artist_2 = ax.plot([x2, x3], [y2, y3], 'y-', lw=2)[0]
        self.angle.text_artist = ax.text(self.pos_x, self.pos_y, f"{distance:.1f} mm", color="yellow")
    
    def get_voxel_hu(self, plane, x, y):
        cursor = self.crossctrl.cursor_3d
        if plane == 0:  # axial
            return self.stack.volume[cursor["z"], y, x]
        elif plane == 1:  # coronal
            return self.stack.volume[y, cursor["y"], x]
        elif plane == 2:  # sagittal
            return self.stack.volume[y, x, cursor["x"]]
    
    def draw_hu_probe(self):
        if self.hu_probe.voxel is None:
            return
        plane = self.hu_probe.plane
        x, y = self.hu_probe.voxel
        hu = self.get_voxel_hu(plane, x, y)
        ax = self.plane_axes[plane]
        if self.hu_probe.text_artist is not None:
            self.hu_probe.text_artist.remove()
        self.hu_probe.text_artist = ax.text(self.pos_x, self.pos_y+350, f"({x},{y})\nHU: {hu:.0f}", color="cyan", fontsize=10)
    
    def draw_segmentation(self):
        if self.segmentation.mask is None:
            return
        stats = self.segmentation.calculate_statistics(self.stack.volume)
        volume_mm3 = self.segmentation.calculate_volume((self.stack.spacing_y, self.stack.spacing_x, self.stack.spacing_z))
        volume_cm3 = volume_mm3 / 1000.0
        analysis = self.segmentation.density_analysis(self.stack.volume)
        if analysis is not None:
            text = (f"Volume: {volume_cm3:.1f} cm³\n" f"Mean Density: {analysis['mean']:.1f} HU\n" f"Std Density: {analysis['std']:.1f} HU\n" f"Classification: {analysis['classification']}")
            self.stats_panel.update_stats("Segmentation", text)
        if stats is None:
            return
        if self.stats_panel:
            self.stats_panel.update_segmentation(volume_cm3, stats['mean'], stats['std'], stats['classification'])
        if self.segmentation.text_artist:
            self.segmentation.text_artist.remove()
        cursor = self.crossctrl.cursor_3d
        text = (f"Volume: {volume_cm3:.1f} cm3\n" f"Mean Density: {stats['mean']:.1f} HU\n" f"Std Density: {stats['std']:.1f}\n" f"Classification: {stats['classification']}")
        self.segmentation.text_artist = self.axial_ax.text(self.pos_x, self.pos_y, text, color="lime")
    
    def show_metadata(self):
        text = ""
        for key, value in self.stack.metadata.items():
            text += f"{key}: {value}\n"
        plt.figure("DICOM Metadata")
        plt.clf()
        plt.axis("off")
        plt.text(self.pos_x, self.pos_y, text, va="top", family="monospace")
        #plt.show(block=False)
        
    def print_summary(self):
        print("----- DICOM INFO -----")
        print("Patient:", self.stack.metadata["patient_id"])
        print("Modality:", self.stack.metadata["modality"])
        print("Shape:", self.stack.metadata["shape"])
        print("Spacing:", self.stack.metadata["pixel_spacing"])
        print("----------------------")
    
    def show(self):
        pass
    
    def draw_histogram(self):
        if not self.histogram_dirty:
            return
        self.extra_ax.clear()
        if self.roi.mask is not None:
            slice_img = self.stack.volume[self.crossctrl.cursor_3d["z"]]
            values = slice_img[self.roi.mask]
            title = "ROI Histogram"
        else:
            values = self.stack.volume.flatten()
            title = "Volume Histogram"
        self.extra_ax.hist(values, bins=100, range=(-1000, 2000))
        mean_hu = np.mean(values)
        self.extra_ax.axvline(mean_hu, linestyle="--")
        self.extra_ax.set_title(title)
        self.extra_ax.set_xlabel("HU")
        self.extra_ax.set_ylabel("Count")
        self.histogram_dirty = False
    
    def update_status_bar(self):
        if not hasattr(self, "status_bar"):
            return
        cursor = self.crossctrl.cursor_3d
        z = cursor["z"]
        y = cursor["y"]
        x = cursor["x"]
        hu = self.stack.volume[z, y, x]
        wl = self.controller.window_level
        ww = self.controller.window_width
        total_slices = self.stack.shape[0]
        plane_name = self.plane_names[self.current_plane]
        text = (
            f"{plane_name} | "
            f"Slice: {z+1}/{total_slices} | "
            f"WL: {wl:.0f} | "
            f"WW: {ww:.0f} | "
            f"Cursor: ({x},{y},{z}) | "
            f"HU: {hu:.0f}"
        )
        self.status_bar.showMessage(text)
    
    def run_bone_density_analysis(self):
        analysis = self.segmentation.density_analysis(self.stack.volume)
        if analysis is None:
            return
        volume_mm3 = self.segmentation.calculate_volume((self.stack.spacing_y, self.stack.spacing_x, self.stack.spacing_z))
        volume_cm3 = volume_mm3 / 1000.0
        text = (f"Volume: {volume_cm3:.1f} cm³\n" f"Mean Density: {analysis['mean']:.1f} HU\n" f"Std Density: {analysis['std']:.1f} HU\n" f"Classification: {analysis['classification']}")
        self.stats_panel.update_stats("Segmentation", text)