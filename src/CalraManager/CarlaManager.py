import carla
from carla.agents.navigation.behavior_agent import BehaviorAgent
import random
import time
import os
import cv2
import numpy as np
import threading


class CarlaManager:
    def __init__(self, addr='localhost', port=2000):
        self._client = carla.Client(addr, port)
        self._client.set_timeout(10.0)

        with open('./map.xodr', 'r') as f:
            xodr_data = f.read()
            self._world = self._client.generate_opendrive_world(xodr_data)
        settings = self._world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = 0.05  # 20 ticks per second
        self._world.apply_settings(settings)
        # Get the blueprint library
        blueprint_library = self._world.get_blueprint_library()

        # Choose a random vehicle blueprint
        self._vehicle_bp = random.choice(blueprint_library.filter('vehicle.*'))

        # Get a random valid spawn point
        self._spawn_points = self._world.get_map().get_spawn_points()
        self._rand_sp = random.choice(self._spawn_points)
        if not self._spawn_points:
            print("No valid spawn points found!")
            exit(1)
        self._vehicles = {}
        self._traffic_manager = self._client.get_trafficmanager()

    def create_vehicle(self, vehicle_id):
        if vehicle_id in self._vehicles:
            return self._vehicles[vehicle_id]

        vehicle = self._world.spawn_actor(self._vehicle_bp, self._rand_sp)
        agent = BehaviorAgent(vehicle)
        self._vehicles[vehicle_id] = (vehicle, agent)
        return vehicle

    def set_path(self, vehicle_id, path):
        vehicle, agent = self._vehicles[vehicle_id]
        locations = self.create_locations(path)
        self.navigate_vehicle_with_agent(vehicle, agent, locations)

    def navigate_vehicle_with_agent(self, vehicle, agent, destinations):
        """
        Automates vehicle navigation using a BehaviorAgent in a threaded and synchronous manner.

        Args:
            vehicle (carla.Vehicle): The CARLA vehicle object to control.
            agent (BehaviorAgent): The BehaviorAgent to control the vehicle.
            destinations (list of carla.Location): List of destination locations.
        """
        # Ensure synchronous mode
        settings = self._world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = 0.05  # Optional: Set time step to 20 FPS
        self._world.apply_settings(settings)

        def agent_navigation():
            """Threaded navigation logic for the agent."""
            for destination in destinations:
                # Get the waypoint for the destination
                destination_waypoint = self._world.get_map().get_waypoint(destination)
                agent.set_destination(destination_waypoint.transform.location)
                print(f"Navigating to: {destination}")

                while not agent.done():
                    control = agent.run_step()
                    vehicle.apply_control(control)

                print(f"Reached destination: {destination}")

            # Stop the vehicle after all destinations
            print("All destinations reached.")
            vehicle.apply_control(carla.VehicleControl(throttle=0.0, brake=1.0))

        # Start navigation in a separate thread
        agent_thread = threading.Thread(target=agent_navigation)
        agent_thread.start()

        try:
            # Main thread handles simulation ticks
            while agent_thread.is_alive():
                self._world.tick()  # Advance simulation
        except KeyboardInterrupt:
            print("Simulation interrupted.")
        finally:
            # Restore default settings after simulation
            settings.synchronous_mode = False
            self._world.apply_settings(settings)



    def get_vehicle_location(self, vehicle_id):
        if vehicle_id not in self._vehicles:
            return None
        loc = self._vehicles[vehicle_id].get_location()
        return loc.x, loc.y, loc.z
    
    def get_vehicle_telemetry(self, vehicle_id):
        if vehicle_id not in self._vehicles:
            return None
        loc = self._vehicles[vehicle_id].get_location()
        speed = self._vehicles[vehicle_id].get_velocity()
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        return loc.x, loc.y, loc.z, speed, timestamp

    @staticmethod
    def create_locations(path):
        res = []
        for loc in path:
            x, y, z = loc
            location = carla.Location(x=x, y=y, z=z)
            res.append(location)
        return res

    def get_all_locations(self):
        res = []
        for sp in self._spawn_points:
            loc = sp.location
            res.append((loc.x, loc.y, loc.z))
        return res

    def destroy_truck(self, vehicle_id):
        vehicle = self._vehicles.pop(vehicle_id)
        vehicle.destroy()

    def destroy_all_vehicles(self):
        for vehicle in self._vehicles.values():
            vehicle.destroy()
        self._vehicles.clear()