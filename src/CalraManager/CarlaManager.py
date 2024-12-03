import carla
import random
import time
import os
import cv2
import numpy as np


class CarlaManager:
    def __init__(self, addr='localhost', port=2000):
        self._client = carla.Client(addr, port)
        self._client.set_timeout(10.0)

        with open('./map.xodr', 'r') as f:
            xodr_data = f.read()
            self._world = self._client.generate_opendrive_world(xodr_data)

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
        self._vehicles[vehicle_id] = vehicle
        return vehicle

    def set_path(self, vehicle_id, path):
        vehicle = self._vehicles[vehicle_id]
        vehicle.set_autopilot(True, self._traffic_manager.get_port())
        self._traffic_manager.set_path(vehicle, self.create_locations(path))

    def get_vehicle_location(self, vehicle_id):
        if vehicle_id not in self._vehicles:
            return None
        loc = self._vehicles[vehicle_id].get_location()
        return loc.x, loc.y, loc.z

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