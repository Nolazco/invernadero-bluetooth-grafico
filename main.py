import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

import serial
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas

from plyer import notification

class MainWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Temperatura Bluetooth")

        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        geometry = monitor.get_geometry()
        self.resize(geometry.width, geometry.height)

        self.connect('delete-event', Gtk.main_quit)

        self.hpaned = Gtk.HPaned()
        self.add(self.hpaned)

        # Lecturas de temperatura a la izquierda
        self.readings_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.hpaned.add1(self.readings_box)

        self.temperature_label = Gtk.Label()
        self.readings_box.pack_start(self.temperature_label, False, False, 10)  # Aumentar el margen derecho

        self.max_temperature_label = Gtk.Label()
        self.readings_box.pack_start(self.max_temperature_label, False, False, 0)

        self.min_temperature_label = Gtk.Label()
        self.readings_box.pack_start(self.min_temperature_label, False, False, 0)

        self.reset_button = Gtk.Button(label="Reiniciar Gráfica")
        self.reset_button.connect("clicked", self.reset_graph)
        self.readings_box.pack_start(self.reset_button, False, False, 0)

        # Gráfica de líneas a la derecha
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.hpaned.add2(self.canvas)
        self.hpaned.set_position(200)  # Ajustar el tamaño del contenedor de la gráfica

        self.temperature_data = []  # Almacenar las lecturas de temperatura
        self.max_temperature = float('-inf')  # Inicializar temperatura máxima
        self.min_temperature = float('inf')  # Inicializar temperatura mínima

        self.serial_port = serial.Serial('/dev/rfcomm0', 9600)

        GLib.timeout_add(1000, self.receive_temperature)  # Leer los datos de temperatura cada 1 segundo
        GLib.timeout_add(1000, self.update_plot)  # Actualizar la gráfica cada segundo

    def receive_temperature(self):
        if self.serial_port.in_waiting > 0:
            # Leer los datos del Arduino
            temperature = float(self.serial_port.readline().decode().rstrip())
            self.temperature_label.set_text(f"Temperatura actual: {temperature}°C")
            self.temperature_data.append(temperature)  # Agregar la temperatura a los datos

            # Actualizar temperatura máxima y mínima
            if temperature > self.max_temperature:
                self.max_temperature = temperature
                self.max_temperature_label.set_text(f"Temperatura máxima: {self.max_temperature}°C")

            if temperature < self.min_temperature:
                self.min_temperature = temperature
                self.min_temperature_label.set_text(f"Temperatura mínima: {self.min_temperature}°C")

            # Mostrar notificación si la temperatura es mayor o igual a 35 grados
            if temperature >= 35:
                self.show_notification("Temperatura alta", f"La temperatura actual es {temperature}°C")

        return True

    def update_plot(self):
        if len(self.temperature_data) > 0:
            x = np.arange(len(self.temperature_data)) / 10  # Crear una secuencia de tiempo cada 3 minutos
            y = np.array(self.temperature_data)

            self.ax.clear()

            # Dibujar la línea principal de la gráfica
            self.ax.plot(x, y, color='blue', label='Temperatura')

            # Verificar si la temperatura es mayor o igual a 35 grados
            for i, temp in enumerate(self.temperature_data):
                # Agregar grados de lectura a cada vértice
                self.ax.annotate(f'{temp}°C', xy=(x[i], y[i]), xytext=(5, 5), textcoords='offset points')
                if temp >= 35:
                    # Dibujar un punto rojo en el vértice de la lectura
                    self.ax.plot(x[i], y[i], 'ro')
                if temp <= 25:
                    # Dibujar un punto verde en el vértice de la lectura
                    self.ax.plot(x[i], y[i], 'go')

            self.ax.set_xlabel('Tiempo (minutos)')
            self.ax.set_ylabel('Temperatura (°C)')
            self.ax.set_title('Gráfica de Temperatura')
            self.ax.legend()
            self.canvas.draw()

        return True

    def reset_graph(self, button):
        self.temperature_data = []
        self.max_temperature = float('-inf')
        self.min_temperature = float('inf')

        self.ax.clear()
        self.ax.set_xlabel('Tiempo (minutos)')
        self.ax.set_ylabel('Temperatura (°C)')
        self.ax.set_title('Gráfica de Temperatura')
        self.canvas.draw()

    def show_notification(self, title, message):
        notification.notify(title=title, message=message)

win = MainWindow()
win.show_all()
Gtk.main()
