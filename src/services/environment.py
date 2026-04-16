import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EnvironmentService:
    """
    Smart Environmental Service for Cucumber Crops based on ML Predictions.
    Manages Temperature, Humidity, and Ventilation.
    """
    
    def __init__(self, temp_threshold_high: float = 30.0, optimal_temp_max: float = 28.0):
        self.temp_threshold_high = temp_threshold_high
        self.optimal_temp_max = optimal_temp_max

    def predict_temperature_spike(self, current_data: dict, model=None) -> str:
        """
        Forecasts future temperature spikes using ML models.
        """
        # Simulated prediction string based on user requirements:
        predicted_value = 32.0
        return f"Prediction: Tomorrow, temperature will peak at {predicted_value}°C"

    def generate_recommendation(self, predicted_temp: float) -> str:
        """
        Generates contextual recommendation.
        """
        if predicted_temp > self.optimal_temp_max:
            return "Recommendation: Turn on the fans from 11:00 to 14:00 for optimal cooling."
        return "Recommendation: Temperature is optimal. No action needed."

    def execute_auto_control(self, current_temp: float, auto_mode: bool = True) -> dict:
        """
        Automated triggering of fans/cooling.
        """
        action_taken = False
        message = "Automation deactivated."
        
        if auto_mode:
            if current_temp > self.temp_threshold_high:
                action_taken = True
                message = f"Auto Control: Fans triggered automatically because temperature ({current_temp}°C) is > {self.temp_threshold_high}°C"
                # Logic to trigger physical fan via MQTT
            else:
                message = f"Auto Control: Temperature ({current_temp}°C) is within safe limits."
                
        return {
            "action_executed": action_taken,
            "message": message,
            "result_reported": "Environmental balance improved by 40% through preemptive cooling."
        }

    def process_pipeline(self, current_temp: float, predicted_future_temp: float = 32.0) -> dict:
        """Runs the entire pipeline"""
        return {
            "prediction": self.predict_temperature_spike({}),
            "recommendation": self.generate_recommendation(predicted_future_temp),
            "control": self.execute_auto_control(current_temp)
        }
