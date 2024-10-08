import os
import json
import sys
import shutil
import base64
from kivy.base import runTouchApp
from kivy.lang import Builder
from kivy_garden.mapview import MapMarkerPopup, MapView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.image import Image

MARKER_DIR = "markers"

def clear_cache():
    cache_dir = os.path.join(os.path.expanduser("~"), ".kivy", "cache")
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        print("Cache telah dikosongkan.")

def convert_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def save_base64_to_json(base64_data, lat, lon):
    data = {
        "latitude": lat,
        "longitude": lon,
        "image_base64": base64_data
    }
    if not os.path.exists(MARKER_DIR):
        os.makedirs(MARKER_DIR)
    file_name = os.path.join(MARKER_DIR, f"{lat}_{lon}.json")
    with open(file_name, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def load_markers():
    markers = []
    if os.path.exists(MARKER_DIR):
        for file_name in os.listdir(MARKER_DIR):
            if file_name.endswith(".json"):
                with open(os.path.join(MARKER_DIR, file_name)) as json_file:
                    data = json.load(json_file)
                    markers.append(data)
    return markers

class MyMapView(BoxLayout):
    def __init__(self, **kwargs):
        super(MyMapView, self).__init__(**kwargs)
        self.orientation = 'vertical'

        # Create MapView
        self.map_view = MapView(
            lat=-6.8214,  # Koordinat Universitas Suryakancana
            lon=107.1432,
            zoom=13,
            map_source='osm'
        )
        self.map_view.bind(on_touch_down=self.on_map_click)

        # Create Input Text
        self.lat_input = TextInput(hint_text='Latitude', readonly=True, size_hint=(0.2, None), height=30)
        self.lon_input = TextInput(hint_text='Longitude', readonly=True, size_hint=(0.2, None), height=30)
        
        # Create Button to open file chooser
        self.file_button = Button(text='Choose Image')
        self.file_button.bind(on_release=self.open_filechooser)

        # Create Layout for Inputs
        input_layout = BoxLayout(size_hint_y=None, height=30)
        input_layout.add_widget(self.lat_input)
        input_layout.add_widget(self.lon_input)
        input_layout.add_widget(self.file_button)

        # Create ScrollView for markers
        self.marker_list = ScrollView(size_hint_y=None, height=200)
        self.marker_container = BoxLayout(orientation='vertical', size_hint_y=None)
        self.marker_container.bind(minimum_height=self.marker_container.setter('height'))
        self.marker_list.add_widget(self.marker_container)

        # Add widgets to layout
        self.add_widget(self.map_view)
        self.add_widget(self.marker_list)
        self.add_widget(input_layout)  # Input berada di bawah

        # Load existing markers
        self.update_marker_list()

    def on_map_click(self, instance, touch):
        if instance.collide_point(touch.x, touch.y):
            lat, lon = instance.lat, instance.lon
            self.lat_input.text = str(lat)
            self.lon_input.text = str(lon)

    def open_filechooser(self, instance):
        filechooser = FileChooserIconView()
        filechooser.bind(on_submit=self.on_file_selected)
        self.add_widget(filechooser)

    def on_file_selected(self, filechooser, selection, touch):
        if selection:
            image_path = selection[0]
            lat = self.lat_input.text
            lon = self.lon_input.text
            base64_data = convert_image_to_base64(image_path)
            save_base64_to_json(base64_data, lat, lon)
            self.remove_widget(filechooser)
            self.update_marker_list()

    def update_marker_list(self):
        self.marker_container.clear_widgets()
        markers = load_markers()
        for marker in markers:
            lat = marker.get("latitude")
            lon = marker.get("longitude")
            if lat is not None and lon is not None:
                popup = MapMarkerPopup(lat=float(lat), lon=float(lon), popup_size=(200, 200))

                if "image_base64" in marker:
                    image_base64 = marker["image_base64"]
                    image_data = base64.b64decode(image_base64)
                    image_file_path = os.path.join(MARKER_DIR, f"{lat}_{lon}.png")
                    with open(image_file_path, 'wb') as img_file:
                        img_file.write(image_data)

                    image_widget = Image(source=image_file_path, size_hint=(None, None), size=(200, 200))
                else:
                    image_widget = Image(source="path/to/placeholder_image.png", size_hint=(None, None), size=(200, 200))

                # Add the image widget and label to the popup
                popup.add_widget(image_widget)
                label = Label(text=f"Lat: {lat}, Lon: {lon}", size_hint_y=None, height=30)
                popup.add_widget(label)

                # Add the popup to the map
                self.map_view.add_widget(popup)

                # Create buttons for the marker list
                button_layout = BoxLayout(size_hint_y=None, height=30)
                button_layout.add_widget(Label(text=f"Lat: {lat}, Lon: {lon}"))
                go_to_button = Button(text='Go to')
                go_to_button.bind(on_release=lambda instance, lat=lat, lon=lon: self.go_to_marker(lat, lon))
                delete_button = Button(text='Hapus')
                delete_button.bind(on_release=lambda instance, lat=lat, lon=lon: self.delete_marker(lat, lon))
                button_layout.add_widget(go_to_button)
                button_layout.add_widget(delete_button)
                self.marker_container.add_widget(button_layout)

    def go_to_marker(self, lat, lon):
        self.map_view.center_on(float(lat), float(lon))

    def delete_marker(self, lat, lon):
        file_name = os.path.join(MARKER_DIR, f"{lat}_{lon}.json")
        if os.path.exists(file_name):
            os.remove(file_name)
            self.update_marker_list()

if __name__ == '__main__':
    from os import path
    clear_cache()
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

    root = MyMapView()
    runTouchApp(root)
