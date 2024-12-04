import carla
import sys

# Add CARLA paths to Python path
sys.path.append('/home/016218293@SJSUAD/.local/lib/python3.8/site-packages/carla')
sys.path.append('/home/016218293@SJSUAD/.local/lib/python3.8/site-packages/carla/agents')


import random
import time
import os
import numpy as np
import threading
import requests
import math


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
        self._tick_thread = threading.Thread(target=self._tick_world, daemon=True)
        self._stop_tick = threading.Event()
        self._tick_thread.start()
        # Get the blueprint library
        blueprint_library = self._world.get_blueprint_library()
        self._vehicle_statuses = {}
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

    def _tick_world(self):
        """
        Background thread to keep the world ticking.
        """
        while not self._stop_tick.is_set():
            self._world.tick()
            time.sleep(0.05)  # 20 FPS (adjust the sleep time if needed)

    def stop_ticking(self):
        """
        Stop the background ticking thread.
        """
        self._stop_tick.set()
        self._tick_thread.join()

    def create_vehicle(self, vehicle_id):
        if vehicle_id in self._vehicles:
            return self._vehicles[vehicle_id]

        vehicle = self._world.spawn_actor(self._vehicle_bp, self._rand_sp)
        self._vehicles[vehicle_id] = vehicle
        self._vehicle_statuses[vehicle_id] = 'Spawned'
        return vehicle

    def set_path(self, vehicle_id, path):
        def vector_length(vector):
            return math.sqrt(vector.x**2 + vector.y**2 + vector.z**2)
        def move():
            if vehicle_id not in self._vehicles:
                raise('Vehicle not created')
            self._vehicle_statuses[vehicle_id] = 'In Transit'
            vehicle = self._vehicles[vehicle_id]
            current_location = vehicle.get_location()
            target_location = carla.Location(x=float(path[0]), y=float(path[1]), z=float(path[2]))
            direction = target_location - current_location
            direction_length = vector_length(direction)
            direction = carla.Vector3D(
                direction.x / direction_length,
                direction.y / direction_length,
                direction.z / direction_length
            )
            while direction_length > 1.0:  # Stop when close to the target
                # Update the vehicle's current location
                current_location = vehicle.get_location()
                direction = target_location - current_location
                direction_length = vector_length(direction)

                # Normalize the direction vector again
                direction = carla.Vector3D(
                    direction.x / direction_length,
                    direction.y / direction_length,
                    direction.z / direction_length
                )

                # Control the vehicle
                control = carla.VehicleControl()
                control.throttle = 0.5  # Adjust throttle as needed
                control.steer = 0.0  # Adjust steering based on direction if needed
                vehicle.apply_control(control)

                # Tick the world to advance the simulation
                self._world.tick()
                time.sleep(0.05)
            control = carla.VehicleControl(throttle=0.0, brake=1.0)
            vehicle.apply_control(control)
            self._vehicle_statuses[vehicle_id] = 'Delivered'
        move_thread = threading.Thread(target=move, daemon=True)
        move_thread.start()
        
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

    def get_vehicle_status(self, vehicle_id):
        if vehicle_id not in self._vehicles:
            return None
        return self._vehicle_statuses[vehicle_id]
    
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