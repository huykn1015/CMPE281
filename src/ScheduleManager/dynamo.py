from ScheduleManager import ScheduleManager


if __name__ == "__main__":
    # Initialize ScheduleManager
    schedule_manager = ScheduleManager()

    # Create some schedules for testing
    schedule_manager.create_schedule("123", ["Stop A", "Stop B", "Stop C"])
    schedule_manager.create_schedule("456", ["Stop D", "Stop E"])

    # Retrieve and print all schedules
    all_schedules = schedule_manager.get_all_schedules()

    print("All Schedules:")
    for schedule in all_schedules:
        print(f"Truck ID: {schedule['truck_id']} -> Stops: {schedule['stops']}")