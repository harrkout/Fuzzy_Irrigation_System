import numpy as np
import skfuzzy as fuzz
from skfuzzy.control import Antecedent, Consequent, Rule, ControlSystem, ControlSystemSimulation
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QMessageBox, QTextEdit, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import logging
import sys

class QTextEditLogger(logging.Handler):
    def __init__(self, text_edit_widget):
        super().__init__()
        self.text_edit_widget = text_edit_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_edit_widget.append(msg)
        self.text_edit_widget.verticalScrollBar().setValue(
            self.text_edit_widget.verticalScrollBar().maximum())

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Define fuzzy variables and their membership functions
logger.debug("Defining fuzzy variables and their membership functions.")
soil_moisture = Antecedent(np.arange(0, 101, 1), 'soil_moisture')
temperature = Antecedent(np.arange(0, 41, 1), 'temperature')
weather = Antecedent(np.arange(0, 3, 1), 'weather')  # 0: Rainy, 1: Cloudy, 2: Sunny
water_supply = Consequent(np.arange(0, 61, 1), 'water_supply')

# Define fuzzy membership functions with overlap
logger.debug("Defining fuzzy membership functions.")
soil_moisture['dry'] = fuzz.trimf(soil_moisture.universe, [0, 0, 50])
soil_moisture['moderate'] = fuzz.trimf(soil_moisture.universe, [30, 50, 70])
soil_moisture['wet'] = fuzz.trimf(soil_moisture.universe, [50, 100, 100])

temperature['low'] = fuzz.trimf(temperature.universe, [0, 0, 20])
temperature['medium'] = fuzz.trimf(temperature.universe, [15, 25, 35])
temperature['high'] = fuzz.trimf(temperature.universe, [30, 40, 40])

weather['rainy'] = fuzz.trimf(weather.universe, [0, 0, 1])
weather['cloudy'] = fuzz.trimf(weather.universe, [0.5, 1, 1.5])
weather['sunny'] = fuzz.trimf(weather.universe, [1.5, 2, 2])

water_supply['none'] = fuzz.trimf(water_supply.universe, [0, 0, 15])
water_supply['low'] = fuzz.trimf(water_supply.universe, [10, 20, 30])
water_supply['moderate'] = fuzz.trimf(water_supply.universe, [25, 40, 50])
water_supply['high'] = fuzz.trimf(water_supply.universe, [40, 60, 60])

# Define fuzzy rules
logger.debug("Defining fuzzy rules.")
rule1 = Rule(soil_moisture['dry'] & temperature['high'] & weather['sunny'], water_supply['high'])
rule2 = Rule(soil_moisture['wet'] & weather['rainy'], water_supply['none'])
rule3 = Rule(soil_moisture['moderate'] & weather['cloudy'], water_supply['low'])
rule4 = Rule(soil_moisture['moderate'] & temperature['medium'] & weather['sunny'], water_supply['moderate'])
rule5 = Rule(soil_moisture['dry'] & temperature['high'], water_supply['high'])
rule6 = Rule(soil_moisture['dry'] & weather['sunny'], water_supply['moderate'])
rule7 = Rule(soil_moisture['wet'] & temperature['low'], water_supply['none'])
rule8 = Rule(soil_moisture['wet'] & weather['cloudy'], water_supply['low'])
rule9 = Rule(soil_moisture['moderate'] & temperature['high'], water_supply['moderate'])
rule10 = Rule(soil_moisture['dry'] & temperature['medium'] & weather['rainy'], water_supply['low'])
rule11 = Rule(soil_moisture['wet'] & temperature['high'] & weather['sunny'], water_supply['moderate'])
rule12 = Rule(soil_moisture['moderate'] & temperature['high'] & weather['rainy'], water_supply['high'])
rule13 = Rule(soil_moisture['moderate'] & temperature['low'] & weather['sunny'], water_supply['low'])

# Create a control system and simulation
logger.debug("Creating control system and simulation.")
irrigation_ctrl = ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9, rule10, rule11, rule12, rule13])
irrigation_sim = ControlSystemSimulation(irrigation_ctrl)

class IrrigationApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.water_supply_input_value = None

        logger.info("Initializing IrrigationApp GUI.")
        self.setWindowTitle("Fuzzy Irrigation System")
        self.setGeometry(100, 100, 1200, 800)
        
        self.setStyleSheet("""
            QLabel {
                font-size: 14px;
                margin: 5px;
            }
            QLineEdit, QComboBox {
                font-size: 14px;
                padding: 5px;
                margin: 5px;
            }
            QPushButton {
                font-size: 14px;
                padding: 10px;
                margin: 5px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        main_layout = QVBoxLayout()

        input_layout = QHBoxLayout()
        self.soil_moisture_input = QLineEdit()
        self.soil_moisture_input.setPlaceholderText("0-100")
        input_layout.addWidget(QLabel("Soil Moisture"))
        input_layout.addWidget(self.soil_moisture_input)

        self.temperature_input = QLineEdit()
        self.temperature_input.setPlaceholderText("0-40")
        input_layout.addWidget(QLabel("Temperature"))
        input_layout.addWidget(self.temperature_input)

        self.weather_input = QComboBox()
        self.weather_input.addItems(["Rainy", "Cloudy", "Sunny"])
        input_layout.addWidget(QLabel("Weather"))
        input_layout.addWidget(self.weather_input)

        main_layout.addLayout(input_layout)

        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.run_button = QPushButton("Run Simulation")
        self.run_button.clicked.connect(self.run_simulation)
        main_layout.addWidget(self.run_button)

        self.result_label = QLabel("Recommended Water Supply: N/A")
        main_layout.addWidget(self.result_label)

        self.fig, self.axs = plt.subplots(2, 2, figsize=(12, 8))
        plt.subplots_adjust(hspace=0.4, top=0.9)

        self.canvas = FigureCanvas(self.fig)
        main_layout.addWidget(self.canvas)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        main_layout.addWidget(self.log_display)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        logger.info("IrrigationApp GUI initialized.")

        log_handler = QTextEditLogger(self.log_display)
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(log_handler)

        # Initialize input value attributes
        self.soil_moisture_input_value = None
        self.temperature_input_value = None
        self.weather_input_value = None

    def run_simulation(self):
        logger.debug("Running simulation.")
        # Get the input values
        try:
            soil_moisture_value = float(self.soil_moisture_input.text())
            temperature_value = float(self.temperature_input.text())
            weather_value = self.weather_input.currentIndex()  # 0: Rainy, 1: Cloudy, 2: Sunny
            
            logger.info(f"Input values: Soil Moisture={soil_moisture_value}, Temperature={temperature_value}, Weather={weather_value}")

            if not (0 <= soil_moisture_value <= 100):
                self.show_error("Soil Moisture should be between 0 and 100.")
                logger.error(f"Invalid Soil Moisture input: {soil_moisture_value}")
                return
            if not (0 <= temperature_value <= 40):
                self.show_error("Temperature should be between 0 and 40.")
                logger.error(f"Invalid Temperature input: {temperature_value}")
                return
            if weather_value not in [0, 1, 2]:
                self.show_error("Weather should be Rainy, Cloudy, or Sunny.")
                logger.error(f"Invalid Weather input: {weather_value}")
                return

            irrigation_sim.input['soil_moisture'] = soil_moisture_value
            irrigation_sim.input['temperature'] = temperature_value
            irrigation_sim.input['weather'] = weather_value

            # Compute the output
            irrigation_sim.compute()

            if 'water_supply' in irrigation_sim.output:
                water_supply_value = irrigation_sim.output['water_supply']
                self.water_supply_input_value = water_supply_value  # Set the value here
                self.result_label.setText(f"Recommended Water Supply: {water_supply_value:.2f} minutes")
                logger.info(f"Simulation result: Recommended Water Supply = {water_supply_value:.2f} minutes")
            else:
                self.result_label.setText("Error: Water supply not computed.")
                logger.error("Water supply not computed.")

        except ValueError:
            self.show_error("Please enter valid numeric values for Soil Moisture and Temperature.")
            logger.error("Invalid numeric input.")
        except Exception as e:
            self.show_error(f"Error during simulation: {e}")
            logger.error(f"Error during simulation: {e}")

        self.update_plots()

    def show_error(self, message):
        QMessageBox.critical(self, "Input Error", message)
        self.result_label.setText("Error during simulation.")
        logger.error(f"Input error: {message}")

    def update_plots(self):
        logger.debug("Updating plots.")
        
        # Clear previous plots
        for ax in self.axs.flat:
            ax.cla()
        
        # Plot Soil Moisture
        soil_moisture_range = np.arange(0, 101, 1)
        self.axs[0, 0].plot(soil_moisture_range, fuzz.interp_membership(soil_moisture_range, soil_moisture['dry'].mf, soil_moisture_range), label='Dry')
        self.axs[0, 0].plot(soil_moisture_range, fuzz.interp_membership(soil_moisture_range, soil_moisture['moderate'].mf, soil_moisture_range), label='Moderate')
        self.axs[0, 0].plot(soil_moisture_range, fuzz.interp_membership(soil_moisture_range, soil_moisture['wet'].mf, soil_moisture_range), label='Wet')
        if self.soil_moisture_input_value is not None:
            self.axs[0, 0].axvline(self.soil_moisture_input_value, color='r', linestyle='--', label='Input Value')
        self.axs[0, 0].set_title('Soil Moisture', fontsize=10)
        self.axs[0, 0].legend()
        self.axs[0, 0].grid(True)

        # Plot Temperature
        temperature_range = np.arange(0, 41, 1)
        self.axs[0, 1].plot(temperature_range, fuzz.interp_membership(temperature_range, temperature['low'].mf, temperature_range), label='Low')
        self.axs[0, 1].plot(temperature_range, fuzz.interp_membership(temperature_range, temperature['medium'].mf, temperature_range), label='Medium')
        self.axs[0, 1].plot(temperature_range, fuzz.interp_membership(temperature_range, temperature['high'].mf, temperature_range), label='High')
        if self.temperature_input_value is not None:
            self.axs[0, 1].axvline(self.temperature_input_value, color='r', linestyle='--', label='Input Value')
        self.axs[0, 1].set_title('Temperature', fontsize=10)
        self.axs[0, 1].legend()
        self.axs[0, 1].grid(True)

        # Plot Weather
        weather_range = np.arange(0, 3, 1)
        self.axs[1, 0].plot(weather_range, fuzz.interp_membership(weather_range, weather['rainy'].mf, weather_range), label='Rainy')
        self.axs[1, 0].plot(weather_range, fuzz.interp_membership(weather_range, weather['cloudy'].mf, weather_range), label='Cloudy')
        self.axs[1, 0].plot(weather_range, fuzz.interp_membership(weather_range, weather['sunny'].mf, weather_range), label='Sunny')
        if self.weather_input_value is not None:
            self.axs[1, 0].axvline(self.weather_input_value, color='r', linestyle='--', label='Input Value')
        self.axs[1, 0].set_title('Weather', fontsize=10)
        self.axs[1, 0].legend()
        self.axs[1, 0].grid(True)

        # Plot Water Supply
        water_supply_range = np.arange(0, 61, 1)
        self.axs[1, 1].plot(water_supply_range, fuzz.interp_membership(water_supply_range, water_supply['none'].mf, water_supply_range), label='None')
        self.axs[1, 1].plot(water_supply_range, fuzz.interp_membership(water_supply_range, water_supply['low'].mf, water_supply_range), label='Low')
        self.axs[1, 1].plot(water_supply_range, fuzz.interp_membership(water_supply_range, water_supply['moderate'].mf, water_supply_range), label='Moderate')
        self.axs[1, 1].plot(water_supply_range, fuzz.interp_membership(water_supply_range, water_supply['high'].mf, water_supply_range), label='High')
        if self.water_supply_input_value is not None:
            self.axs[1, 1].axvline(self.water_supply_input_value, color='r', linestyle='--', label='Input Value')
        self.axs[1, 1].set_title('Water Supply', fontsize=10)
        self.axs[1, 1].legend()
        self.axs[1, 1].grid(True)

        # Redraw the canvas to reflect the updated plots
        self.canvas.draw()


if __name__ == "__main__":
    logger.info("Starting the application.")
    app = QApplication(sys.argv)
    window = IrrigationApp()
    window.show()
    sys.exit(app.exec_())
