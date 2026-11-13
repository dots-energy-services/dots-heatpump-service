from datetime import datetime
import unittest
from heatpumpservice.heatpump_service import CalculationServiceHeatPump
from dots_infrastructure.DataClasses import SimulatorConfiguration, TimeStepInformation
from dots_infrastructure.test_infra.InfluxDBMock import InfluxDBMock
import helics as h
from esdl.esdl_handler import EnergySystemHandler

from dots_infrastructure import CalculationServiceHelperFunctions

BROKER_TEST_PORT = 23404
START_DATE_TIME = datetime(2024, 1, 1, 0, 0, 0)
SIMULATION_DURATION_IN_SECONDS = 960

def simulator_environment_e_connection():
    # return SimulatorConfiguration("EConnection", ["ee3795bd-878c-4b89-9e32-5fc4c74816ce"], "Mock-Econnection", "127.0.0.1", BROKER_TEST_PORT, "ee3795bd-878c-4b89-9e32-5fc4c74816ce", SIMULATION_DURATION_IN_SECONDS, START_DATE_TIME, "test-host", "test-port", "test-username", "test-password", "test-database-name", h.HelicsLogLevel.DEBUG, ["PVInstallation", "EConnection"])
    return SimulatorConfiguration("EConnection", ["313da8ce-4c9e-4d87-a877-3bdc13295a32"], "Mock-Econnection",
                                  "127.0.0.1", BROKER_TEST_PORT, "313da8ce-4c9e-4d87-a877-3bdc13295a32",
                                  SIMULATION_DURATION_IN_SECONDS, START_DATE_TIME, "test-host", "test-port",
                                  "test-username", "test-password", "test-database-name", h.HelicsLogLevel.DEBUG,
                                  ["PVInstallation", "EConnection"])


class Test(unittest.TestCase):

    def setUp(self):
        CalculationServiceHelperFunctions.get_simulator_configuration_from_environment = simulator_environment_e_connection
        esh = EnergySystemHandler()
        esh.load_file('test/test.esdl')
        energy_system = esh.get_energy_system()
        self.energy_system = energy_system

    def test_send_temperatures(self):
        # Arrange
        service = CalculationServiceHeatPump()
        service.influx_connector = InfluxDBMock()

        weather_params = {}
        weather_params["solar_irradiance"] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 8.333333333333334, 16.666666666666668, 25.0, 33.333333333333336, 59.72222222222223, 86.11111111111111, 112.5, 138.88888888888889, 174.99999999999997, 211.1111111111111, 247.22222222222223, 283.3333333333333, 308.3333333333333, 333.3333333333333, 358.33333333333326, 383.3333333333333, 376.38888888888886, 369.44444444444446, 362.5, 355.55555555555554, 309.72222222222223, 263.8888888888889, 218.0555555555556, 172.22222222222223, 188.19444444444443, 204.16666666666663, 220.13888888888889]
        weather_params["air_temperature"] = [11.50, 10.95, 10.40, 9.85, 9.30, 9.425, 9.55, 9.675, 9.80, 9.925, 10.05, 10.175, 10.30, 10.15, 10.00, 9.85, 9.70, 9.75, 9.80, 9.85, 9.90, 10.025, 10.15, 10.275, 10.40, 11.15, 11.90, 12.65, 13.40, 14.025, 14.65, 15.275, 15.90, 16.025, 16.15, 16.275, 16.40, 16.40, 16.40, 16.40, 16.40, 16.50, 16.60, 16.70, 16.80, 16.80, 16.80, 16.80]
        weather_params["soil_temperature"] = [16.90, 16.9083333333, 16.9166666667, 16.925, 16.9333333333, 16.9416666667, 16.95, 16.9583333333, 16.9666666667, 16.975, 16.9833333333, 16.9916666667, 17.00, 17.0083333333, 17.0166666667, 17.025, 17.0333333333, 17.0416666667, 17.05, 17.0583333333, 17.0666666667, 17.075, 17.0833333333, 17.0916666667, 17.10, 17.0958333333, 17.0916666667, 17.0875, 17.0833333333, 17.0791666667, 17.075, 17.0708333333, 17.0666666667, 17.0625, 17.0583333333, 17.0541666667, 17.05, 17.0458333333, 17.0416666667, 17.0375, 17.0333333333, 17.0291666667, 17.025, 17.0208333333, 17.0166666667, 17.0125, 17.0083333333, 17.0041666667]
        service.init_calculation_service(self.energy_system)

        # Execute
        ret_val = service.send_temperatures(weather_params, datetime(2024,1,1), TimeStepInformation(1,2), "313da8ce-4c9e-4d87-a877-3bdc13295a32", self.energy_system)

        # Assert
        expected_dhw_temperature = 318.6502151044533
        expected_buffer_temperature = 315.93853596915767
        expected_indoor_temperature = 292.4459134830427
        expected_outdoor_temperature = 289.9804435197081
        # self.assertAlmostEqual(ret_val["dhw_temperature"], expected_dhw_temperature)
        # self.assertAlmostEqual(ret_val["buffer_temperature"], expected_buffer_temperature)
        # self.assertAlmostEqual(ret_val["house_temperatures"][0], expected_indoor_temperature)
        # self.assertAlmostEqual(ret_val["house_temperatures"][1], expected_outdoor_temperature)

    def test_update_temperatures(self):
        # Arrange
        service = CalculationServiceHeatPump()
        service.influx_connector = InfluxDBMock()
        service.init_calculation_service(self.energy_system)

        input_params = {}
        input_params["solar_irradiance"] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 8.333333333333334, 16.666666666666668, 25.0, 33.333333333333336, 59.72222222222223, 86.11111111111111, 112.5, 138.88888888888889, 174.99999999999997, 211.1111111111111, 247.22222222222223, 283.3333333333333, 308.3333333333333, 333.3333333333333, 358.33333333333326, 383.3333333333333, 376.38888888888886, 369.44444444444446, 362.5, 355.55555555555554, 309.72222222222223, 263.8888888888889, 218.0555555555556, 172.22222222222223, 188.19444444444443, 204.16666666666663, 220.13888888888889]
        input_params["air_temperature"] = [11.50, 10.95, 10.40, 9.85, 9.30, 9.425, 9.55, 9.675, 9.80, 9.925, 10.05, 10.175, 10.30, 10.15, 10.00, 9.85, 9.70, 9.75, 9.80, 9.85, 9.90, 10.025, 10.15, 10.275, 10.40, 11.15, 11.90, 12.65, 13.40, 14.025, 14.65, 15.275, 15.90, 16.025, 16.15, 16.275, 16.40, 16.40, 16.40, 16.40, 16.40, 16.50, 16.60, 16.70, 16.80, 16.80, 16.80, 16.80]
        input_params["soil_temperature"] = [16.90, 16.9083333333, 16.9166666667, 16.925, 16.9333333333, 16.9416666667, 16.95, 16.9583333333, 16.9666666667, 16.975, 16.9833333333, 16.9916666667, 17.00, 17.0083333333, 17.0166666667, 17.025, 17.0333333333, 17.0416666667, 17.05, 17.0583333333, 17.0666666667, 17.075, 17.0833333333, 17.0916666667, 17.10, 17.0958333333, 17.0916666667, 17.0875, 17.0833333333,  17.0791666667, 17.075, 17.0708333333, 17.0666666667, 17.0625, 17.0583333333, 17.0541666667, 17.05, 17.0458333333, 17.0416666667, 17.0375, 17.0333333333, 17.0291666667, 17.025, 17.0208333333, 17.0166666667, 17.0125, 17.0083333333, 17.0041666667]
        input_params["heat_power_to_tank_dhw"] = 20
        input_params["heat_power_to_buffer"] = 20
        input_params["heat_power_to_dhw"] = 20
        input_params["heat_power_to_house"] = 1075.0408698247047

        # Execute
        service.send_temperatures(input_params, datetime(2024,1,1), TimeStepInformation(1,2), "313da8ce-4c9e-4d87-a877-3bdc13295a32", self.energy_system)
        service.update_temperatures(input_params, datetime(2024,1,1), TimeStepInformation(1,2), "313da8ce-4c9e-4d87-a877-3bdc13295a32", self.energy_system)

        # Assert
        influxdb_outputs = service.influx_connector.data_points
        stored_dhw_tank_temperature = influxdb_outputs[0].value
        stored_buffer_temperature = influxdb_outputs[1].value
        stored_house_temperature = influxdb_outputs[2].value
        expected_dhw_temperature = 318.6502151044533
        expected_buffer_temperature = 315.93853596915767
        expected_indoor_temperature = 292.35351659016715
        # self.assertAlmostEqual(stored_dhw_tank_temperature, expected_dhw_temperature)
        # self.assertAlmostEqual(stored_buffer_temperature, expected_buffer_temperature)
        # self.assertAlmostEqual(stored_house_temperature, expected_indoor_temperature)

if __name__ == '__main__':
    unittest.main()
