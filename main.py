from upgrade import upgrade_data  # Ensure this module contains your upgrade data
#not 100% done with the data/upgrades.py but the main.py is done 
class UpgradableItem:
    def __init__(self, name, category, upgrades, unlock_info):
        self.name = name
        self.category = category
        self.upgrades = upgrades
        self.unlock_info = unlock_info
        self.is_wall = name.lower() == 'wall'  # Flag to identify walls

    def get_quantity_at_th_level(self, th_level):
        """
        Determines the quantity of the item available at the given Town Hall level.
        """
        quantity = 0
        for info in self.unlock_info:
            if info['townhall_level'] <= th_level:
                quantity = info['quantity']
            else:
                break
        return quantity

    def get_max_level(self, th_level):
        """
        Determines the maximum upgrade level available for the item based on the Town Hall level.
        """
        max_level = 0
        for upgrade in self.upgrades:
            if upgrade['required_townhall_level'] <= th_level:
                if upgrade['level'] > max_level:
                    max_level = upgrade['level']
        return max_level


class TownHall:
    def __init__(self, level, builders, humanity_factor=1.0):
        """
        Initializes the TownHall with its level, number of builders, and humanity factor.
        - humanity_factor: A multiplier to simulate downtime. For example, 1.2 adds a 20% downtime.
        """
        self.level = level
        self.builders = builders
        self.upgradable_items = []
        self.humanity_factor = humanity_factor

    def add_item(self, item):
        """
        Adds an UpgradableItem to the Town Hall's list of upgradable items.
        """
        self.upgradable_items.append(item)

    def calculate_total_cost_and_time(self):
        """
        Calculates the total cost and time required to fully upgrade the Town Hall.
        Separates upgrades into parallel (buildings and heroes) and serial (troops and spells).
        Walls are handled separately as instant upgrades.
        """
        total_cost = {'gold': 0, 'elixir': 0, 'dark_elixir': 0, 'gold_or_elixir': 0}
        parallel_upgrades = []
        serial_upgrades = []
        wall_total_cost = 0  # To accumulate wall costs

        # Define categories that should be upgraded serially
        serial_categories = ['troops', 'spells']

        for item in self.upgradable_items:
            quantity = item.get_quantity_at_th_level(self.level)
            if quantity == 0:
                continue  # Item not available at this Town Hall level

            max_level = item.get_max_level(self.level)

            for upgrade in item.upgrades:
                if upgrade['level'] > max_level or upgrade['required_townhall_level'] > self.level:
                    continue  # Upgrade not available at current Town Hall level

                resource_type = upgrade.get('resource_type', 'gold')
                cost = upgrade['cost'] * quantity
                time = upgrade['time']

                if item.is_wall:
                    # Accumulate wall costs without adding to parallel_upgrades
                    wall_total_cost += cost
                    print(f"Wall Upgrade Processed: {{'cost': {cost}, 'level': {upgrade['level']}}}")
                    continue  # Skip adding to parallel or serial upgrades

                # Accumulate costs based on resource type
                if resource_type == 'gold_or_elixir':
                    total_cost['gold_or_elixir'] += cost
                else:
                    total_cost[resource_type] += cost

                # Create individual upgrade entries based on quantity
                for _ in range(quantity):
                    upgrade_entry = {'time': time, 'item': item.name, 'level': upgrade['level']}
                    if item.category in serial_categories:
                        serial_upgrades.append(upgrade_entry)
                        print(f"Serial Upgrade Added: {upgrade_entry}")
                    else:
                        parallel_upgrades.append(upgrade_entry)
                        print(f"Parallel Upgrade Added: {upgrade_entry}")

        # Add wall costs to total_cost
        total_cost['elixir'] += wall_total_cost  # Assuming walls use elixir

        # Calculate total parallel build time using builders
        parallel_build_time = self.calculate_total_build_time(parallel_upgrades)
        print(f"Total Parallel Build Time: {parallel_build_time} seconds")

        # Calculate total serial build time (one at a time)
        serial_build_time = sum(upgrade['time'] for upgrade in serial_upgrades)
        print(f"Total Serial Build Time: {serial_build_time} seconds")

        # The raw total build time is the maximum of parallel and serial build times
        raw_total_time = max(parallel_build_time, serial_build_time)
        print(f"Raw Total Build Time (without humanity factor): {raw_total_time} seconds")

        # Adjust the total build time by the humanity factor to account for downtime
        adjusted_total_time = raw_total_time * self.humanity_factor
        print(f"Adjusted Total Build Time (including humanity factor): {adjusted_total_time} seconds")

        return total_cost, adjusted_total_time

    def calculate_total_build_time(self, all_upgrades):
        """
        Calculates the total build time for parallel upgrades using the available builders.
        Utilizes a greedy algorithm to assign upgrades to the earliest available builder.
        """
        if not all_upgrades:
            return 0

        # Sort upgrades by time in descending order for better load balancing
        all_upgrades.sort(key=lambda x: x['time'], reverse=True)

        # Initialize builder availability times
        builder_times = [0] * self.builders

        for upgrade in all_upgrades:
            # Assign the upgrade to the builder that becomes available the earliest
            next_available_builder = builder_times.index(min(builder_times))
            builder_times[next_available_builder] += upgrade['time']
            print(f"Assigned {upgrade['item']} Level {upgrade['level']} (Time: {upgrade['time']}s) to Builder {next_available_builder + 1}")

        # The total build time is the maximum time among all builders
        total_build_time = max(builder_times)
        return total_build_time


def format_time(seconds):
    """
    Formats time from seconds to a more readable string (days, hours, minutes).
    """
    days = seconds // (24 * 3600)
    hours = (seconds % (24 * 3600)) // 3600
    minutes = (seconds % 3600) // 60
    return f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes"


if __name__ == "__main__":
    try:
        # Prompt user for Town Hall level
        town_hall_level = int(input("Enter your Town Hall level: "))

        # Prompt user for the number of builders
        builders = int(input("Enter the number of builders you have: "))

        # Prompt user for humanity factor
        print("\nTo account for downtime, you can specify a humanity factor.")
        print("A value greater than 1 increases the total build time (e.g., 1.2 adds a 20% downtime).")
        print("A value of 1 means no additional downtime.")
        humanity_input = input("Enter humanity factor (default is 1.2): ")
        if humanity_input.strip() == "":
            humanity_factor = 1.2  # Default 20% downtime
        else:
            humanity_factor = float(humanity_input)
            if humanity_factor < 1.0:
                print("Humanity factor cannot be less than 1.0. Setting to default 1.2.")
                humanity_factor = 1.2

        th = TownHall(level=town_hall_level, builders=builders, humanity_factor=humanity_factor)

        # Iterate over the upgrade_data to create UpgradableItem instances
        for category, items in upgrade_data.items():
            for item_name, item_data in items.items():
                if not isinstance(item_data, dict):
                    print(f"Error: '{item_name}' data is not in the correct format. Skipping.")
                    continue
                unlock_info = item_data.get('unlock_info', [])
                upgrades = item_data.get('upgrades', [])
                if not upgrades:
                    continue  # Skip items without upgrades
                item = UpgradableItem(name=item_name, category=category, upgrades=upgrades, unlock_info=unlock_info)
                th.add_item(item)

        # Calculate total cost and time
        total_cost, total_time = th.calculate_total_cost_and_time()

        # Output the results
        print(f"\nTotal Cost to max Town Hall {th.level}:")
        for resource_type, cost in total_cost.items():
            if cost > 0:
                if resource_type == 'gold_or_elixir':
                    print(f"  {cost} gold or elixir (your choice for walls)")
                else:
                    print(f"  {cost} {resource_type}")
        print(f"Raw Total Time (without humanity factor): {format_time(int(th.calculate_total_cost_and_time()[1] / th.humanity_factor))}")
        print(f"Adjusted Total Time to max Town Hall {th.level} with {th.builders} builders: {format_time(total_time)}")
    except ValueError:
        print("Invalid input. Please enter numeric values for Town Hall level, number of builders, and humanity factor.")
