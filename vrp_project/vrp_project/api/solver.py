from __future__ import division
from __future__ import print_function
from django.conf import settings
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from api.models import Vehicle, Customer, Solution, Batch
from celery import shared_task
import requests
import json
import urllib


GOOGLE_API_URL = 'https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial'
KEY = settings.GOOGLE_API_KEY
DEPOT = "LS2+9JT"

# a function that return the addresses of and
# demands of the customers on the transportation network


def create_graph(batch):
    graph_data = {}
    graph_data['addresses'] = []
    graph_data['demands'] = []

    # add the depot's address as the first node
    graph_data['addresses'].append(DEPOT)
    graph_data['demands'].append(0)

    # get all the customers in the batch
    customers_objects = Customer.objects.filter(batch__batch_name=batch)

    # add the addresses and demands of customers
    for customer in customers_objects:
        if customer.address.zip_postcode != DEPOT:
            graph_data['addresses'].append(
                customer.address.zip_postcode.replace(' ', '+'))
            graph_data['demands'].append(customer.customer_demand)

    return graph_data


# a function to compute the distance matrix of the transportation network
def create_distance_matrix(addresses):
    # not more than 100 elements per request is accepted by Google API
    max_elements = 100
    number_addresses = len(addresses)
    max_rows = max_elements // number_addresses
    q, r = divmod(number_addresses, max_rows)
    dest_addresses = addresses
    distance_matrix = []

    for i in range(q):
        origin_addresses = addresses[i * max_rows: (i + 1) * max_rows]
        response = send_request(origin_addresses, dest_addresses)
        distance_matrix += build_distance_matrix(response)

    if r > 0:
        origin_addresses = addresses[q * max_rows: q * max_rows + r]
        response = send_request(origin_addresses, dest_addresses)
        distance_matrix += build_distance_matrix(response)

    return distance_matrix


# sending a get request to Google Matrix API
def send_request(origin_addresses, dest_addresses):
    def build_address_str(addresses):
        # Build a pipe-separated string of addresses
        address_str = ''
        for i in range(len(addresses) - 1):
            address_str += addresses[i] + '|'
        address_str += addresses[-1]
        return address_str

    request = GOOGLE_API_URL
    origin_address_str = build_address_str(origin_addresses)
    dest_address_str = build_address_str(dest_addresses)
    request = request + '&origins=' + origin_address_str + '&destinations=' + \
                        dest_address_str + '&key=' + KEY
    jsonResult = urllib.request.urlopen(request).read()
    response = json.loads(jsonResult)
    return response


# extract the distance from the JSON object returened by the API
def build_distance_matrix(response):
    distance_matrix = []
    for row in response['rows']:
        row_list = [row['elements'][j]['distance']['value']
                    for j in range(len(row['elements']))]
        distance_matrix.append(row_list)
    return distance_matrix


def create_data_model(batch_name):
    """ Prepare the data to be passed to the solver """
    data = {}
    data['depot'] = 0
    data['vehicle_capacities'] = []

    # get the vehicle which are available for service
    available_vehicles = Vehicle.objects.filter(availability=True)
    data['num_vehicles'] = available_vehicles.count()

    # get the list of capacity of each available vehicles
    for vehicle in available_vehicles:
        data['vehicle_capacities'].append(vehicle.capacity)

    # create the graph and create the distance matrix from the graph
    graph = create_graph(batch_name)
    data['demands'] = graph['demands']
    if len(graph['addresses']) < 2:
        message = "No customer found in the given batch."
    else:
        data['distance_matrix'] = create_distance_matrix(graph['addresses'])

    return data


# this function is a celery task
@shared_task
def main(batch_name, time_limit):
    """Solve the CVRP problem."""
    # Instantiate the data problem.
    data = create_data_model(batch_name)

    payload = {}

    if sum(data["vehicle_capacities"]) < sum(data["demands"]):
        message = "The vehicle capacities is less than the sum of customer demands."
        payload["message"] = message

    else:

        # Create the routing index manager.
        manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                               data['num_vehicles'], data['depot'])
        # Create Routing Model.
        routing = pywrapcp.RoutingModel(manager)

        # Create and register a transit callback.
        def distance_callback(from_index, to_index):
            """Returns the distance between the two nodes."""
            # Convert from routing variable Index to distance matrix NodeIndex.
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data['distance_matrix'][from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(
            distance_callback)

        # Define cost of each arc.
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Add Capacity constraint.
        def demand_callback(from_index):
            """Returns the demand of the node."""
            # Convert from routing variable Index to demands NodeIndex.
            from_node = manager.IndexToNode(from_index)
            return data['demands'][from_node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(
            demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            data['vehicle_capacities'],  # vehicle maximum capacities
            True,  # start cumul to zero
            'Capacity')

        # Setting first solution heuristic.
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.time_limit.seconds = time_limit
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

        # Solve the problem.
        solution = routing.SolveWithParameters(search_parameters)

        # save the solution.
        if solution:
            solution_output(data, manager, routing, solution, batch_name)


def solution_output(data, manager, routing, solution, batch_name):
    total_distance = 0
    total_load = 0
    routes = []

    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        route_distance = 0
        route_load = 0

        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_load += data['demands'][node_index]
            plan_output += ' {0} Load({1}) -> '.format(node_index, route_load)
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
        plan_output += ' {0} Load({1})\n'.format(manager.IndexToNode(index),
                                                 route_load)
        plan_output += 'Distance of the route: {}m\n'.format(route_distance)
        plan_output += 'Load of the route: {}\n'.format(route_load)
        routes.append(plan_output)
        total_distance += route_distance
        total_load += route_load

    routes_json = json.dumps(routes)

    # get the related batch object
    target_batch = Batch.objects.get(batch_name=batch_name)
    # create a solution object
    solution = Solution()
    solution.routes = routes_json
    solution.total_distance = total_distance
    solution.total_load = total_load
    solution.solver_status = routing.status()
    solution.batch = target_batch
    # save the solution
    solution.save()
