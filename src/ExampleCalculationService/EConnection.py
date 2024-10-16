# -*- coding: utf-8 -*-
from datetime import datetime
from esdl import esdl
import helics as h
import logging
from dots_infrastructure.DataClasses import EsdlId, HelicsCalculationInformation, PublicationDescription, SubscriptionDescription, TimeStepInformation, TimeRequestType
from dots_infrastructure.HelicsFederateHelpers import HelicsSimulationExecutor
from dots_infrastructure.Logger import LOGGER
from esdl import EnergySystem
from dots_infrastructure.CalculationServiceHelperFunctions import get_vector_param_with_name

import json
import numpy as np
from ExampleCalculationService.thermalsystems import House, HeatBuffer, objectfunctions



class CalculationServiceHeatPump(HelicsSimulationExecutor):

    def __init__(self):
        super().__init__()

        subscriptions_values = [
            SubscriptionDescription(esdl_type="EnvironmentalProfiles",
                                   input_name="solar_irradiance",
                                   input_unit="Wm2",
                                   input_type=h.HelicsDataType.VECTOR),
            SubscriptionDescription(esdl_type="EnvironmentalProfiles",
                                   input_name="air_temperature",
                                   input_unit="K",
                                   input_type=h.HelicsDataType.VECTOR),
            SubscriptionDescription(esdl_type="EnvironmentalProfiles",
                                   input_name="soil_temperature",
                                   input_unit="K",
                                   input_type=h.HelicsDataType.VECTOR)
        ]

        publication_values = [
            PublicationDescription(global_flag=True,
                                   esdl_type="HeatPump",
                                   output_name="dhw_temperature",
                                   output_unit="K",
                                   data_type=h.HelicsDataType.DOUBLE),
            PublicationDescription(global_flag=True,
                                   esdl_type="HeatPump",
                                   output_name="buffer_temperature",
                                   output_unit="K",
                                   data_type=h.HelicsDataType.DOUBLE),
            PublicationDescription(global_flag=True,
                                   esdl_type="HeatPump",
                                   output_name="house_temperatures",
                                   output_unit="K",
                                   data_type=h.HelicsDataType.VECTOR)
        ]

        heatpump_period_in_seconds = 900
        self.heatpump_period_in_seconds = 900

        calculation_information = HelicsCalculationInformation(
            time_period_in_seconds=heatpump_period_in_seconds,
            offset=0, 
            uninterruptible=False, 
            wait_for_current_time_update=False, 
            terminate_on_error=True, 
            calculation_name="send_temperatures",
            inputs=subscriptions_values, 
            outputs=publication_values, 
            calculation_function=self.send_temperatures
        )
        self.add_calculation(calculation_information)

        subscriptions_values = [
            SubscriptionDescription(esdl_type="EnvironmentalProfiles",
                                   input_name="solar_irradiance",
                                   input_unit="Wm2",
                                   input_type=h.HelicsDataType.VECTOR),
            SubscriptionDescription(esdl_type="EnvironmentalProfiles",
                                   input_name="air_temperature",
                                   input_unit="K",
                                   input_type=h.HelicsDataType.VECTOR),
            SubscriptionDescription(esdl_type="EnvironmentalProfiles",
                                   input_name="soil_temperature",
                                   input_unit="K",
                                   input_type=h.HelicsDataType.VECTOR),
            SubscriptionDescription(esdl_type="EConnection",
                                    input_name="heat_power_to_tank_dhw",
                                    input_unit="W",
                                    input_type=h.HelicsDataType.DOUBLE),
            SubscriptionDescription(esdl_type="EConnection",
                                    input_name="heat_power_to_buffer",
                                    input_unit="W",
                                    input_type=h.HelicsDataType.DOUBLE),
            SubscriptionDescription(esdl_type="EConnection",
                                    input_name="heat_power_to_dhw",
                                    input_unit="W",
                                    input_type=h.HelicsDataType.DOUBLE),
            SubscriptionDescription(esdl_type="EConnection",
                                    input_name="heat_power_to_house",
                                    input_unit="W",
                                    input_type=h.HelicsDataType.DOUBLE)
        ]

        heatpump_update_period_in_seconds = 900

        calculation_information_update = HelicsCalculationInformation(heatpump_update_period_in_seconds, 0, False, False, True, "update_temperatures", subscriptions_values, [], self.update_temperatures)
        self.add_calculation(calculation_information_update)

    # def get_building_of_hp(self, esdl_id : EsdlId, energy_system: esdl.EnergySystem):
    #     for obj in energy_system.eAllContents():
    #         if hasattr(obj, "id") and obj.id == esdl_id:
    #             assert isinstance(obj.eContainer(), esdl.Building), f"Container of asset {esdl_id} is not a building"
    #             return obj.eContainer()

    def init_calculation_service(self, energy_system: esdl.EnergySystem):
        LOGGER.info("init calculation service")
        self.hp_description_dicts: dict[EsdlId, dict[str, float]] = {}
        self.hp_esdl_power: dict[EsdlId, float] = {}

        self.dhw_tanks: dict[EsdlId, HeatBuffer] = {}
        self.buffers: dict[EsdlId, HeatBuffer] = {}
        self.houses: dict[EsdlId, House] = {}

        self.inv_capacitance_matrices: dict[EsdlId, np.array] = {}
        self.conductance_matrices: dict[EsdlId, np.array] = {}
        self.forcing_matrices: dict[EsdlId, np.array] = {}
        # In other functions
        self.buffer_temperatures: dict[EsdlId, float] = {}
        self.house_temperatures: dict[EsdlId, List[float]] = {}

        for esdl_id in self.simulator_configuration.esdl_ids:
            LOGGER.info(f"Example of iterating over esdl ids: {esdl_id}")

            # Initialize heat tanks and houses
            # Get data from ESDL
            for obj in energy_system.eAllContents():
                if hasattr(obj, "id") and obj.id == esdl_id:
                    hpsystem = obj
                    if isinstance(obj.eContainer(), esdl.Building):
                        building_description = json.loads(obj.eContainer().description)
            self.hp_description_dicts[esdl_id] = json.loads(hpsystem.description)
            self.hp_esdl_power[esdl_id] = hpsystem.power

            # Set Tanks
            buffer_capacitance = self.hp_description_dicts[esdl_id]['buffer_capacitance']
            dhw_capacitance = self.hp_description_dicts[esdl_id]['dhw_capacitance']
            self.buffers[esdl_id] = HeatBuffer(buffer_capacitance)
            self.dhw_tanks[esdl_id] = HeatBuffer(dhw_capacitance)
            print('dhw_capacitance', dhw_capacitance)

            # Set Houses
            capacities = {'C_in': building_description['C_in'], 'C_out': building_description['C_out']}
            resistances = {'R_exch': building_description['R_exch'], 'R_floor': building_description['R_floor'],
                           'R_vent': building_description['R_vent'], 'R_cond': building_description['R_cond']}
            window_area = building_description['A_glass']
            self.houses[esdl_id] = House(capacities, resistances, window_area)



    def send_temperatures(self, param_dict : dict, simulation_time : datetime, time_step_number : TimeStepInformation, esdl_id : EsdlId, energy_system : EnergySystem):
        # START user calc
        LOGGER.info("calculation 'send_temperatures' started")
        # LOGGER.info(param_dict)
        LOGGER.info(get_vector_param_with_name(param_dict, "air_temperature")[0][0])
        # # Calculation(s) per ESDL object
        # temperatures_dict: dict[EsdlId, Temperatures] = {}

        predicted_solar_irradiances = get_vector_param_with_name(param_dict, "solar_irradiance")[0]
        predicted_air_temperatures = get_vector_param_with_name(param_dict, "air_temperature")[0]
        predicted_soil_temperatures = get_vector_param_with_name(param_dict, "soil_temperature")[0]

        # Check if the house and tank temperatures are properly initialized
        house = self.houses[esdl_id]
        buffer = self.buffers[esdl_id]
        dhw_tank = self.dhw_tanks[esdl_id]
        if (house.temperatures is None) or (buffer.temperature is None) or (dhw_tank.temperature is None):
            current_solar_irradiance = predicted_solar_irradiances[0]
            current_air_temperature  = predicted_air_temperatures[0]
            current_soil_temperature = predicted_soil_temperatures[0]

            hp_description_dict = self.hp_description_dicts[esdl_id]

            dhw_tank.set_initial_temperature(hp_description_dict['dhw_temp_0'])
            buffer.set_initial_temperature(hp_description_dict['buffer_temp_0'])
            house.set_initial_temperatures(hp_description_dict['house_temp_0'],
                                           self.hp_esdl_power[esdl_id],
                                           current_air_temperature,
                                           current_soil_temperature,
                                           current_solar_irradiance)

            self.dhw_tanks[esdl_id] = dhw_tank
            self.buffers[esdl_id] = buffer
            self.houses[esdl_id] = house

        house_temperatures_list = house.temperatures.tolist()
            # print(house_temperatures_list, type(house_temperatures_list[0]))

        ret_val = {}
        ret_val["dhw_temperature"]      = dhw_tank.temperature
        ret_val["buffer_temperature"]   = buffer.temperature
        ret_val["house_temperatures"]   = house_temperatures_list
        LOGGER.info(f"House temperatures: {house.temperatures}")

        print(dhw_tank.temperature, buffer.temperature, house.temperatures)
        # self.influx_connector.set_time_step_data_point(esdl_id, "EConnectionDispatch", simulation_time, ret_val["EConnectionDispatch"])
        return ret_val
    
    def update_temperatures(self, param_dict : dict, simulation_time : datetime, time_step_number : TimeStepInformation, esdl_id : EsdlId, energy_system : EnergySystem):
        # START user calc
        LOGGER.info("calculation 'update_temperatures' started")

        predicted_solar_irradiances = get_vector_param_with_name(param_dict, "solar_irradiance")[0]
        predicted_air_temperatures = get_vector_param_with_name(param_dict, "air_temperature")[0]
        predicted_soil_temperatures = get_vector_param_with_name(param_dict, "soil_temperature")[0]
        heat_to_dhw_tank = get_vector_param_with_name(param_dict, "heat_power_to_tank_dhw")[0]
        heat_to_dhw = get_vector_param_with_name(param_dict, "heat_power_to_dhw")[0]
        heat_to_buffer = get_vector_param_with_name(param_dict, "heat_power_to_buffer")[0]
        heat_to_house = get_vector_param_with_name(param_dict,"heat_power_to_house")[0]

        current_air_temperature = predicted_air_temperatures[0]
        current_soil_temperature = predicted_soil_temperatures[0]
        current_solar_irradiance = predicted_solar_irradiances[0]

        dhw_tank = self.dhw_tanks[esdl_id]
        buffer = self.buffers[esdl_id]
        house = self.houses[esdl_id]

        # hp_description_dict = self.hp_description_dicts[esdl_id]

        LOGGER.info(f"esdl id: {esdl_id}")
        LOGGER.info(f"dhw temperature before: {dhw_tank.temperature}")
        LOGGER.info(f"buffer temperature before: {buffer.temperature}")
        LOGGER.info(f"house temperatures before: {house.temperatures}")

        LOGGER.info(f"heat to dhw: {heat_to_dhw}")
        LOGGER.info(f"heat to dhw tank: {heat_to_dhw_tank}")
        LOGGER.info(f"heat to house: {heat_to_house}")
        LOGGER.info(f"heat to buffer: {heat_to_buffer}")

        # Update temperatures
        dhw_tank.update_temperature(self.heatpump_period_in_seconds,
                                    heat_to_dhw,
                                    heat_to_dhw_tank)
        buffer.update_temperature(self.heatpump_period_in_seconds,
                                  heat_to_house,
                                  heat_to_buffer)
        house.update_temperatures(self.heatpump_period_in_seconds,
                                  current_air_temperature,
                                  current_soil_temperature,
                                  current_solar_irradiance,
                                  heat_to_house)

        LOGGER.info(f"dhw temperature after: {dhw_tank.temperature}")
        LOGGER.info(f"buffer temperature after: {buffer.temperature}")
        LOGGER.info(f"house temperatures after: {house.temperatures}")

        dhw_tank_temperature = dhw_tank.temperature
        house_temperatures = house.temperatures
        buffer_temperature = buffer.temperature

        # Check whether temperatures did not surpass the limits due to some numerical error
        lower_bound_dhw_tank = self.hp_description_dicts[esdl_id]['dhw_temp_min']
        upper_bound_dhw_tank = self.hp_description_dicts[esdl_id]['dhw_temp_max']
        lower_bound_buffer = self.hp_description_dicts[esdl_id]['buffer_temp_min']
        upper_bound_buffer = self.hp_description_dicts[esdl_id]['buffer_temp_max']
        lower_bound_house = self.hp_description_dicts[esdl_id]['house_temp_min']

        # Correct errors up till error eps
        eps = 1.0e-4
        if abs(dhw_tank_temperature - lower_bound_dhw_tank) < eps:
            dhw_tank_temperature = lower_bound_dhw_tank + eps
        if abs(dhw_tank_temperature - upper_bound_dhw_tank) < eps:
            dhw_tank_temperature = upper_bound_buffer - eps
        if abs(buffer_temperature - lower_bound_buffer) < eps:
            buffer_temperature = lower_bound_buffer + eps
        if abs(buffer_temperature - upper_bound_buffer) < eps:
            buffer_temperature = upper_bound_buffer - eps
        if abs(house_temperatures[0] - lower_bound_house) < eps:
            house_temperatures[0] = lower_bound_house + eps

        # Raise errors if the values are still not within boundaries
        if (dhw_tank_temperature < lower_bound_dhw_tank) or (dhw_tank_temperature > upper_bound_dhw_tank):
            raise ValueError(f"Heat pump {esdl_id} is charged over/under its dhw capacity")
        if (buffer_temperature < lower_bound_buffer) or (buffer_temperature > upper_bound_buffer):
            raise ValueError(f"Heat pump {esdl_id} is charged over/under its buffer capacity")
        if house_temperatures[0] < lower_bound_house:
            raise ValueError(f"Heat pump {esdl_id} is charged over/under its house capacity")

        # Save as state
        dhw_tank.temperature = dhw_tank_temperature
        buffer.temperature = buffer_temperature
        house.temperatures = house_temperatures.tolist()
        self.dhw_tanks[esdl_id] = dhw_tank
        self.buffers[esdl_id] = buffer
        self.houses[esdl_id] = house

        # # Write to influx
        # time_step_nr = int(new_step.parameters_dict['time_step_nr'])
        # self.influxdb_client.set_time_step_data_point(esdl_id, 'dhw_tank_temperature',
        #                                               time_step_nr, dhw_tank_temperature)
        # self.influxdb_client.set_time_step_data_point(esdl_id, 'buffer_temperature',
        #                                               time_step_nr, buffer_temperature)
        # self.influxdb_client.set_time_step_data_point(esdl_id, 'house_temperature',
        #                                               time_step_nr, house_temperatures[0])
        # if time_step_nr == self.nr_of_time_steps:
        #     self.influxdb_client.set_summary_data_point(esdl_id, 'summary_check', 1)
        LOGGER.info("calculation 'update_temperatures' finished")

        ret_val = {}
        return ret_val

if __name__ == "__main__":

    helics_simulation_executor = CalculationServiceHeatPump()
    helics_simulation_executor.start_simulation()
    helics_simulation_executor.stop_simulation()
