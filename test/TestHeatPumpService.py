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
    return SimulatorConfiguration("EConnection", ["ee3795bd-878c-4b89-9e32-5fc4c74816ce"], "Mock-Econnection", "127.0.0.1", BROKER_TEST_PORT, "ee3795bd-878c-4b89-9e32-5fc4c74816ce", SIMULATION_DURATION_IN_SECONDS, START_DATE_TIME, "test-host", "test-port", "test-username", "test-password", "test-database-name", h.HelicsLogLevel.DEBUG, ["PVInstallation", "EConnection"])

class Test(unittest.TestCase):

    def setUp(self):
        CalculationServiceHelperFunctions.get_simulator_configuration_from_environment = simulator_environment_e_connection
        esh = EnergySystemHandler()
        esh.load_file('test.esdl')
        energy_system = esh.get_energy_system()
        self.energy_system = energy_system

    def test_send_temperatures(self):
        # Arrange
        service = CalculationServiceHeatPump()
        service.influx_connector = InfluxDBMock()

        weather_params = {}
        weather_params["solar_irradiance"] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 8.333333333333334, 16.666666666666668, 25.0, 33.333333333333336, 59.72222222222223, 86.11111111111111, 112.5, 138.88888888888889, 174.99999999999997, 211.1111111111111, 247.22222222222223, 283.3333333333333, 308.3333333333333, 333.3333333333333, 358.33333333333326, 383.3333333333333, 376.38888888888886, 369.44444444444446, 362.5, 355.55555555555554, 309.72222222222223, 263.8888888888889, 218.0555555555556, 172.22222222222223, 188.19444444444443, 204.16666666666663, 220.13888888888889]
        weather_params["air_temperature"] = [284.65, 284.1, 283.54999999999995, 283.0, 282.45, 282.575, 282.7, 282.825, 282.95, 283.075, 283.2, 283.325, 283.45, 283.29999999999995, 283.15, 283.0, 282.85, 282.9, 282.95, 283.0, 283.04999999999995, 283.17499999999995, 283.29999999999995, 283.42499999999995, 283.54999999999995, 284.29999999999995, 285.04999999999995, 285.79999999999995, 286.54999999999995, 287.17499999999995, 287.79999999999995, 288.42499999999995, 289.04999999999995, 289.17499999999995, 289.29999999999995, 289.42499999999995, 289.54999999999995, 289.54999999999995, 289.54999999999995, 289.54999999999995, 289.54999999999995, 289.65, 289.75, 289.85, 289.95, 289.95, 289.95, 289.95]
        weather_params["soil_temperature"] = [290.04999999999995, 290.0583333333333, 290.06666666666666, 290.075, 290.0833333333333, 290.09166666666664, 290.1, 290.1083333333333, 290.1166666666666, 290.125, 290.1333333333333, 290.14166666666665, 290.15, 290.1583333333333, 290.16666666666663, 290.17499999999995, 290.18333333333334, 290.19166666666666, 290.2, 290.2083333333333, 290.21666666666664, 290.225, 290.2333333333333, 290.2416666666667, 290.25, 290.24583333333334, 290.2416666666667, 290.23749999999995, 290.2333333333333, 290.22916666666663, 290.225, 290.2208333333333, 290.21666666666664, 290.2125, 290.2083333333333, 290.20416666666665, 290.2, 290.1958333333333, 290.19166666666666, 290.1875, 290.18333333333334, 290.1791666666667, 290.17499999999995, 290.1708333333333, 290.16666666666663, 290.1625, 290.1583333333333, 290.15416666666664]

        service.init_calculation_service(self.energy_system)

        # Execute
        ret_val = service.send_temperatures(weather_params, datetime(2024,1,1), TimeStepInformation(1,2), "ee3795bd-878c-4b89-9e32-5fc4c74816ce", self.energy_system)

        # Assert
        expected_dhw_temperature = 318.6502151044533
        expected_buffer_temperature = 315.93853596915767
        expected_indoor_temperature = 292.4459134830427
        expected_outdoor_temperature = 289.9804435197081
        self.assertAlmostEqual(ret_val["dhw_temperature"], expected_dhw_temperature)
        self.assertAlmostEqual(ret_val["buffer_temperature"], expected_buffer_temperature)
        self.assertAlmostEqual(ret_val["house_temperatures"][0], expected_indoor_temperature)
        self.assertAlmostEqual(ret_val["house_temperatures"][1], expected_outdoor_temperature)

    def test_update_temperatures(self):
        # Arrange
        service = CalculationServiceHeatPump()
        service.influx_connector = InfluxDBMock()
        service.init_calculation_service(self.energy_system)

        input_params = {}
        input_params["solar_irradiance"] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 8.333333333333334, 16.666666666666668, 25.0, 33.333333333333336, 59.72222222222223, 86.11111111111111, 112.5, 138.88888888888889, 174.99999999999997, 211.1111111111111, 247.22222222222223, 283.3333333333333, 308.3333333333333, 333.3333333333333, 358.33333333333326, 383.3333333333333, 376.38888888888886, 369.44444444444446, 362.5, 355.55555555555554, 309.72222222222223, 263.8888888888889, 218.0555555555556, 172.22222222222223, 188.19444444444443, 204.16666666666663, 220.13888888888889]
        input_params["air_temperature"] = [284.65, 284.1, 283.54999999999995, 283.0, 282.45, 282.575, 282.7, 282.825, 282.95, 283.075, 283.2, 283.325, 283.45, 283.29999999999995, 283.15, 283.0, 282.85, 282.9, 282.95, 283.0, 283.04999999999995, 283.17499999999995, 283.29999999999995, 283.42499999999995, 283.54999999999995, 284.29999999999995, 285.04999999999995, 285.79999999999995, 286.54999999999995, 287.17499999999995, 287.79999999999995, 288.42499999999995, 289.04999999999995, 289.17499999999995, 289.29999999999995, 289.42499999999995, 289.54999999999995, 289.54999999999995, 289.54999999999995, 289.54999999999995, 289.54999999999995, 289.65, 289.75, 289.85, 289.95, 289.95, 289.95, 289.95]
        input_params["soil_temperature"] = [290.04999999999995, 290.0583333333333, 290.06666666666666, 290.075, 290.0833333333333, 290.09166666666664, 290.1, 290.1083333333333, 290.1166666666666, 290.125, 290.1333333333333, 290.14166666666665, 290.15, 290.1583333333333, 290.16666666666663, 290.17499999999995, 290.18333333333334, 290.19166666666666, 290.2, 290.2083333333333, 290.21666666666664, 290.225, 290.2333333333333, 290.2416666666667, 290.25, 290.24583333333334, 290.2416666666667, 290.23749999999995, 290.2333333333333, 290.22916666666663, 290.225, 290.2208333333333, 290.21666666666664, 290.2125, 290.2083333333333, 290.20416666666665, 290.2, 290.1958333333333, 290.19166666666666, 290.1875, 290.18333333333334, 290.1791666666667, 290.17499999999995, 290.1708333333333, 290.16666666666663, 290.1625, 290.1583333333333, 290.15416666666664]
        input_params["heat_power_to_tank_dhw"] = 20
        input_params["heat_power_to_buffer"] = 20
        input_params["heat_power_to_dhw"] = 20
        input_params["heat_power_to_house"] = 20

        # Execute
        service.send_temperatures(input_params, datetime(2024,1,1), TimeStepInformation(1,2), "ee3795bd-878c-4b89-9e32-5fc4c74816ce", self.energy_system)
        service.update_temperatures(input_params, datetime(2024,1,1), TimeStepInformation(1,2), "ee3795bd-878c-4b89-9e32-5fc4c74816ce", self.energy_system)

        # Assert
        influxdb_outputs = service.influx_connector.data_points
        stored_dhw_tank_temperature = influxdb_outputs[0].value
        stored_buffer_temperature = influxdb_outputs[1].value
        stored_house_temperature = influxdb_outputs[2].value
        expected_dhw_temperature = 318.6502151044533
        expected_buffer_temperature = 315.93853596915767
        expected_indoor_temperature = 292.35351659016715
        self.assertAlmostEqual(stored_dhw_tank_temperature, expected_dhw_temperature)
        self.assertAlmostEqual(stored_buffer_temperature, expected_buffer_temperature)
        self.assertAlmostEqual(stored_house_temperature, expected_indoor_temperature)

if __name__ == '__main__':
    unittest.main()
