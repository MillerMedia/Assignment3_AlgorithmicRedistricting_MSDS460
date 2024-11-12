import pandas as pd
import re
from math import pi, sin, cos, asin, sqrt
from pulp import LpProblem, LpVariable, lpSum, LpMinimize, LpBinary, LpStatus, PULP_CBC_CMD
import folium

# File path
file_path = 'AdjacentCounties'

# Reading the file
with open(file_path, 'r') as file:
    data = file.read()

# Initialize an empty list to store the processed data
county_data = []
current_county = None
current_code = None

# Process each line in the file data
for line in data.strip().splitlines():
    line = line.strip()
    if not line:
        continue

    # Match for main county lines (non-indented) using regex for pattern consistency
    match_main = re.match(r'"(.+?), IN"\s+(\d+)\s+".+?"\s+(\d+)', line)
    if match_main:
        # Extract the main county details only if it is an Indiana county
        current_county = match_main.group(1)
        current_code = match_main.group(2)
    else:
        # Process indented lines for adjacent counties
        match_adjacent = re.match(r'"\s*(.+?)"\s+(\d+)', line)
        if match_adjacent and current_county and current_code:
            adjacent_county = match_adjacent.group(1)
            adjacent_code = match_adjacent.group(2)
            county_data.append([current_county, current_code, adjacent_county, adjacent_code])

# Create DataFrame with Indiana counties only
df = pd.DataFrame(county_data, columns=["County", "County_Code", "Adjacent_County", "Adjacent_County_Code"])

# Get DataFrame with Indiana counties only in the Adjacent_County column
df = df[df["Adjacent_County"].str.endswith(", IN")]
df["Adjacent_County"] = df["Adjacent_County"].str.replace(", IN", "")

adjacent = df

# Load populations
# Reading the data from the specified file 'county_data.csv'

# File path
file_path = 'county_data.csv'

# Reading the data from the file
pop_df = pd.read_csv(file_path)

# Add ' County' to end of name column
pop_df['name'] = pop_df['name'] + ' County'

pop_df.head()

# Sum of all populations divide by 9 (number of counties in Indiana)
ideal_population = pop_df['population'].sum() / 9

# Calculate the min and max based on 5% tolerance
min_population = ideal_population - (ideal_population * 0.1)
max_population = ideal_population + (ideal_population * 0.1)

# Merge to add main county data (lat, lng, population)
adjacent = pd.merge(
    adjacent,
    pop_df[['name', 'lat', 'lng', 'population']],
    left_on='County',
    right_on='name',
    how='left'
).rename(columns={'lat': 'main_lat', 'lng': 'main_lng', 'population': 'main_population'})

# Drop the extra 'name' column
adjacent = adjacent.drop(columns=['name'])

# Merge again to add adjacent county data (lat, lng, population)
adjacent = pd.merge(
    adjacent,
    pop_df[['name', 'lat', 'lng', 'population']],
    left_on='Adjacent_County',
    right_on='name',
    how='left'
).rename(columns={'lat': 'adj_lat', 'lng': 'adj_lng', 'population': 'adj_population'})

# Drop the extra 'name' column from the second merge
adjacent = adjacent.drop(columns=['name'])

def degrees_to_radians(x):
    return ((pi / 180) * x)


def lon_lat_distance_miles(lon_a, lat_a, lon_b, lat_b):
    radius_of_earth = 24872 / (2 * pi)
    c = sin((degrees_to_radians(lat_a) - \
             degrees_to_radians(lat_b)) / 2) ** 2 + \
        cos(degrees_to_radians(lat_a)) * \
        cos(degrees_to_radians(lat_b)) * \
        sin((degrees_to_radians(lon_a) - \
             degrees_to_radians(lon_b)) / 2) ** 2
    return (2 * radius_of_earth * (asin(sqrt(c))))


def lon_lat_distance_meters(lon_a, lat_a, lon_b, lat_b):
    return (lon_lat_distance_miles(lon_a, lat_a, lon_b, lat_b) * 1609.34)


adjacent['distance_miles'] = adjacent.apply(
    lambda row: lon_lat_distance_miles(row['main_lat'], row['main_lng'], row['adj_lat'], row['adj_lng']),
    axis=1
)

county_pop = adjacent[['County_Code', 'main_population']]
county_pop = county_pop.set_index('County_Code')['main_population'].to_dict()

# Initialize an empty dictionary to hold the result
adjacency_dict = {}

# Iterate over each row in the DataFrame
for _, row in adjacent.iterrows():
    # Extract main county information
    main_county = row['County_Code']

    # Calculate distance (assuming you have a function to do this)
    distance = lon_lat_distance_miles(row['main_lng'], row['main_lat'], row['adj_lng'], row['adj_lat'])

    # Structure for each adjacent county
    adjacent_info = {
        'Adjacent_County_Code': row['Adjacent_County_Code'],
        'Distance': distance
    }

    # If the main county is not yet a key in the dictionary, add it
    if main_county not in adjacency_dict:
        adjacency_dict[main_county] = []

    # Append the adjacent county info to the list for this county
    adjacency_dict[main_county].append(adjacent_info)

# Function to solve the problem with given tolerance
def solve_districting_problem_1(adjacency_dict, county_pop, target_pop, initial_tolerance=0.05, max_tolerance=0.20,
                              tolerance_step=0.01):
    # Start with the initial tolerance for population balance
    tolerance = initial_tolerance

    while tolerance <= max_tolerance:
        print(f"Trying with population tolerance: {tolerance * 100:.1f}%")

        # Define population bounds based on the current tolerance
        min_pop = target_pop * (1 - tolerance)
        max_pop = target_pop * (1 + tolerance)

        # Create the model
        prob = LpProblem("Indiana Districting", LpMinimize)

        # Number of districts
        num_districts = 9

        # Create binary variables for assigning counties to districts
        x = LpVariable.dicts("x",
                             ((i, d) for i in county_pop.keys() for d in range(1, num_districts + 1)),
                             0, 1,
                             LpBinary)

        # Auxiliary variables for compactness measure (distance minimization)
        y = LpVariable.dicts("y",
                             ((county, adj['Adjacent_County_Code'], d) for county in adjacency_dict
                              for adj in adjacency_dict[county] for d in range(1, num_districts + 1)),
                             0, 1,
                             LpBinary)

        # Objective function: minimize total distance within districts for compactness
        prob += lpSum(y[county, adj['Adjacent_County_Code'], d] * adj['Distance']
                      for county in adjacency_dict
                      for adj in adjacency_dict[county]
                      for d in range(1, num_districts + 1))

        # Constraint 1: each county must be in exactly one district
        for county in county_pop.keys():
            prob += lpSum(x[county, d] for d in range(1, num_districts + 1)) == 1

        # Constraint 2: population balance
        for d in range(1, num_districts + 1):
            district_pop = lpSum(x[county, d] * county_pop[county] for county in county_pop.keys())
            prob += district_pop >= min_pop
            prob += district_pop <= max_pop

        # Constraint 3: adjacency and auxiliary variable constraints
        for county in adjacency_dict:
            for adj in adjacency_dict[county]:
                adj_county = adj['Adjacent_County_Code']
                for d in range(1, num_districts + 1):
                    # Enforce y[(county, adj_county, d)] = x[county, d] * x[adj_county, d]
                    prob += y[(county, adj_county, d)] <= x[county, d]
                    prob += y[(county, adj_county, d)] <= x[adj_county, d]
                    prob += y[(county, adj_county, d)] >= x[county, d] + x[adj_county, d] - 1

        # Solve the problem
        solver = PULP_CBC_CMD(msg=1)
        status = prob.solve(solver)

        # Check if the solution is feasible
        if LpStatus[prob.status] == "Optimal":
            print("\nSolution Status:", LpStatus[prob.status])
            results = []

            print("\nDistrict Assignments:")
            for d in range(1, num_districts + 1):
                district_counties = []
                district_pop = 0
                for county in county_pop.keys():
                    if x[county, d].value() > 0.5:
                        district_counties.append(county)
                        district_pop += county_pop[county]

                        results.append({
                            "County": county,
                            "District": d,
                            "Population": county_pop[county]
                        })
                print(f"\nDistrict {d}:")
                print(f"Counties: {', '.join(str(c) for c in district_counties)}")
                print(f"Population: {district_pop:,} ({district_pop / target_pop * 100:.1f}% of target)")

                # Save to file
                results_df = pd.DataFrame(results)
                results_df.to_csv("district_assignments_1.csv", index=False)

            return results  # Return results if feasible solution is found
        else:
            print("Model infeasible at tolerance:", tolerance)
            tolerance += tolerance_step  # Increase tolerance and try again

    print("No feasible solution found within tolerance limits.")
    return None


# Define initial parameters for population tolerance
initial_tolerance = 0.05
max_tolerance = 0.50
tolerance_step = 0.01
num_districts = 9

# Define target population per district
total_pop = sum(county_pop.values())
target_pop = total_pop / num_districts

# Run the districting problem with varying tolerances
results = solve_districting_problem_1(adjacency_dict, county_pop, target_pop, initial_tolerance, max_tolerance,
                                    tolerance_step)

# Load the district assignment data
results_df = pd.read_csv("district_assignments_1.csv")

# Ensure consistent data types for the merge
results_df['County_Code'] = results_df['County'].astype(str)
adjacent['County_Code'] = adjacent['County_Code'].astype(str)

# Create a dictionary to map County_Code to County names
county_name_map = dict(zip(adjacent['County_Code'], adjacent['County']))

# Add the County names to results_df
results_df['County_Name'] = results_df['County_Code'].map(county_name_map)

# Merge latitude/longitude information from `adjacent` to `results_df` based on `County_Code`
results_df = results_df.merge(adjacent[['County_Code', 'main_lat', 'main_lng']], on='County_Code', how='left')

# Check for missing latitude/longitude values and handle them
missing_location = results_df[results_df[['main_lat', 'main_lng']].isna().any(axis=1)]

if not missing_location.empty:
    print("Warning: The following counties have missing location data and will be assigned default coordinates:")
    print(missing_location[['County_Name', 'District']])

    # Assign default coordinates (center of Indiana) to counties with missing lat/lng
    results_df[['main_lat', 'main_lng']] = results_df[['main_lat', 'main_lng']].fillna([40.273502, -86.126976])

# Create a map centered on Indiana
m = folium.Map(location=[40.273502, -86.126976], zoom_start=7)

# Define colors for each district (up to 9 districts)
colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue']

# Add markers for each county using different colors for each district
for _, row in results_df.iterrows():
    county_name = row['County_Name']
    district = row['District']
    lat = row['main_lat']
    lng = row['main_lng']
    color = colors[district - 1]  # Use district number to pick a color from the list

    # Add a marker for each county
    folium.Marker(
        [lat, lng],
        popup=f"{county_name} (District {district})",
        icon=folium.Icon(color=color)
    ).add_to(m)

# Save the map to an HTML file
m.save("indiana_districts_1.html")

# Function to solve the problem with given tolerance
def solve_districting_problem_2(adjacency_dict, county_pop, target_pop, initial_tolerance=0.05, max_tolerance=0.20,
                              tolerance_step=0.01):
    tolerance = initial_tolerance
    while tolerance <= max_tolerance:
        print(f"Trying with population tolerance: {tolerance * 100:.1f}%")

        # Define population bounds
        min_pop = target_pop * (1 - tolerance)
        max_pop = target_pop * (1 + tolerance)

        # Create the model
        prob = LpProblem("Indiana Districting", LpMinimize)

        # Number of districts
        num_districts = 9

        # Create binary variables for assigning counties to districts
        x = LpVariable.dicts("x",
                             ((i, d) for i in county_pop.keys() for d in range(1, num_districts + 1)),
                             0, 1,
                             LpBinary)

        # Auxiliary variables for compactness measure (distance minimization)
        y = LpVariable.dicts("y",
                             ((county, adj['Adjacent_County_Code'], d) for county in adjacency_dict
                              for adj in adjacency_dict[county] for d in range(1, num_districts + 1)),
                             0, 1,
                             LpBinary)

        # Create auxiliary variables for population deviation in each district
        deviation = LpVariable.dicts("deviation", range(1, num_districts + 1), 0)

        # Objective function: minimize total population deviation
        prob += lpSum(deviation[d] for d in range(1, num_districts + 1))

        # Constraint 1: each county must be in exactly one district
        for county in county_pop.keys():
            prob += lpSum(x[county, d] for d in range(1, num_districts + 1)) == 1

        # Constraint 2: population balance with deviation
        for d in range(1, num_districts + 1):
            district_pop = lpSum(x[county, d] * county_pop[county] for county in county_pop.keys())
            prob += district_pop - target_pop <= deviation[d]
            prob += target_pop - district_pop <= deviation[d]

        # Constraint 3: strict adjacency enforcement
        for county in adjacency_dict:
            for d in range(1, num_districts + 1):
                # A county can only be in district `d` if at least one adjacent county is also in district `d`
                prob += x[county, d] <= lpSum(x[adj['Adjacent_County_Code'], d] for adj in adjacency_dict[county])

        # Solve the problem
        solver = PULP_CBC_CMD(msg=1)
        status = prob.solve(solver)

        # Check if the solution is feasible
        if LpStatus[prob.status] == "Optimal":
            print("\nSolution Status:", LpStatus[prob.status])
            results = []

            print("\nDistrict Assignments:")
            for d in range(1, num_districts + 1):
                district_counties = []
                district_pop = 0
                for county in county_pop.keys():
                    if x[county, d].value() > 0.5:
                        district_counties.append(county)
                        district_pop += county_pop[county]

                        results.append({
                            "County": county,
                            "District": d,
                            "Population": county_pop[county]
                        })
                print(f"\nDistrict {d}:")
                print(f"Counties: {', '.join(str(c) for c in district_counties)}")
                print(f"Population: {district_pop:,} ({district_pop / target_pop * 100:.1f}% of target)")

                # Save to file
                results_df = pd.DataFrame(results)
                results_df.to_csv("district_assignments_2.csv", index=False)

            return results  # Return results if feasible solution is found
        else:
            print("Model infeasible at tolerance:", tolerance)
            tolerance += tolerance_step  # Increase tolerance and try again

    print("No feasible solution found within tolerance limits.")
    return None


# Define initial parameters for population tolerance
initial_tolerance = 0.05
max_tolerance = 0.50
tolerance_step = 0.01
num_districts = 9

# Define target population per district
total_pop = sum(county_pop.values())
target_pop = total_pop / num_districts

# Run the districting problem with varying tolerances
results = solve_districting_problem_2(adjacency_dict, county_pop, target_pop, initial_tolerance, max_tolerance,
                                    tolerance_step)

# Load the district assignment data
results_df = pd.read_csv("district_assignments.csv")

# Ensure consistent data types for the merge
results_df['County_Code'] = results_df['County'].astype(str)
adjacent['County_Code'] = adjacent['County_Code'].astype(str)

# Create a dictionary to map County_Code to County names
county_name_map = dict(zip(adjacent['County_Code'], adjacent['County']))

# Add the County names to results_df
results_df['County_Name'] = results_df['County_Code'].map(county_name_map)

# Merge latitude/longitude information from `adjacent` to `results_df` based on `County_Code`
results_df = results_df.merge(adjacent[['County_Code', 'main_lat', 'main_lng']], on='County_Code', how='left')

# Check for missing latitude/longitude values and handle them
missing_location = results_df[results_df[['main_lat', 'main_lng']].isna().any(axis=1)]

if not missing_location.empty:
    print("Warning: The following counties have missing location data and will be assigned default coordinates:")
    print(missing_location[['County_Name', 'District']])

    # Assign default coordinates (center of Indiana) to counties with missing lat/lng
    results_df[['main_lat', 'main_lng']] = results_df[['main_lat', 'main_lng']].fillna([40.273502, -86.126976])

# Create a map centered on Indiana
m = folium.Map(location=[40.273502, -86.126976], zoom_start=7)

# Define colors for each district (up to 9 districts)
colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue']

# Add markers for each county using different colors for each district
for _, row in results_df.iterrows():
    county_name = row['County_Name']
    district = row['District']
    lat = row['main_lat']
    lng = row['main_lng']
    color = colors[district - 1]  # Use district number to pick a color from the list

    # Add a marker for each county
    folium.Marker(
        [lat, lng],
        popup=f"{county_name} (District {district})",
        icon=folium.Icon(color=color)
    ).add_to(m)

# Save the map to an HTML file
m.save("indiana_districts_2.html")