import pandas as pd
import pulp
import json

MAX_POPULATION_TOLERANCE_PERCENT = 0.1  # Maximum allowed population tolerance (10%)
TOLERANCE_STEP = 0.01  # Increment for each iteration (1%)

# Load county population data from JSON
print("Loading county population data...")
with open('county_populations.json', 'r') as file:
    population_data = json.load(file)

population_df = pd.DataFrame(population_data[1:], columns=population_data[0])

population_df['population'] = population_df['P1_001N'].astype(int)
population_df.drop(columns=['P1_001N'], inplace=True)

population_df['county'] = population_df['NAME'].str.split(',').str[0]
population_df.drop(columns=['NAME'], inplace=True)

# Parse out (part) from county names
population_df['county'] = population_df['county'].str.replace(' (part)', '')

# Remove state columns, county numbers and district numbers; we just need the populations and county names
population_df.drop(columns=['state', 'county (or part)', 'congressional district'], inplace=True)

# Combine any duplicate county rows and add populations (but don't add 'congressional district' columns)
population_df = population_df.groupby('county').sum().reset_index()

print(population_df.head())

# Get number of rows in the DataFrame
print(f"Loaded data for {len(population_df)} counties")

# Load county adjacency data
print("Loading adjacency data...")
adjacency_data = pd.read_csv('county_adjacency2023.txt', sep='|', header=0)

# Filter adjacency data for Indiana counties
print("Filtering adjacency data for Indiana...")
indiana_adjacency = adjacency_data[adjacency_data['County GEOID'].astype(str).str.startswith('18')]
print(indiana_adjacency.head())
print(f"Found {len(indiana_adjacency)} adjacency relationships")

# Create a dictionary mapping each county to its adjacent counties
print("Building adjacency dictionary...")
adjacency_dict = {}
for _, row in indiana_adjacency.iterrows():
    county1 = row['County Name']
    county2 = row['Neighbor Name']
    # Only add county1 if it's from Indiana
    if county1.endswith(', IN'):
        county1_clean = county1[:-4]  # Remove ', IN'
        if county1_clean not in adjacency_dict:
            adjacency_dict[county1_clean] = []
        if county2.endswith(', IN') and county2 != county1:
            county2_clean = county2[:-4]  # Remove ', IN'
            if county2_clean not in adjacency_dict[county1_clean]:
                adjacency_dict[county1_clean].append(county2_clean)
    # Only add county2 if it's from Indiana
    if county2.endswith(', IN'):
        county2_clean = county2[:-4]  # Remove ', IN'
        if county2_clean not in adjacency_dict:
            adjacency_dict[county2_clean] = []
        if county1.endswith(', IN') and county1 != county2:
            county1_clean = county1[:-4]  # Remove ', IN'
            if county1_clean not in adjacency_dict[county2_clean]:
                adjacency_dict[county2_clean].append(county1_clean)
print(f"Created adjacency dictionary with {len(adjacency_dict)} counties")

# Add adjacent counties to the population_df DataFrame
print("Adding adjacent counties to DataFrame...")
population_df['adjacent_counties'] = population_df['county'].map(adjacency_dict)

print(population_df.head())

# Assign Marion County to its own district
marion_county = population_df[population_df['county'] == 'Marion County']
population_df = population_df[population_df['county'] != 'Marion County']
num_counties = len(population_df)
num_districts = 8

# Calculate target population per district (excluding Marion County)
print("Calculating target populations...")
total_population = population_df['population'].sum()
target_population = total_population / num_districts
print(f"Total population (excluding Marion County): {total_population}")
print(f"Target population per district: {target_population}")

# Create binary decision variables
print("Creating decision variables...")
counties_list = population_df['county'].tolist()
x = pulp.LpVariable.dicts("x", ((i, j) for i in counties_list for j in range(num_districts)), cat='Binary')
print(f"Created variables for {len(counties_list)} counties and {num_districts} districts")

# Set up PuLP model
print("Setting up optimization model...")
model = pulp.LpProblem("Redistricting", pulp.LpMinimize)

# Add constraints
print("Adding constraints...")
# Each county must be assigned to exactly one district
print("- Adding county assignment constraints")
for i in counties_list:
    model += pulp.lpSum(x[i,j] for j in range(num_districts)) == 1

# Enforce strict adjacency constraints
print("- Adding strict adjacency constraints")
for j in range(num_districts):
    for i in counties_list:
        adjacent_counties = population_df.loc[population_df['county'] == i, 'adjacent_counties'].iloc[0]
        if adjacent_counties:
            model += pulp.lpSum(x[k, j] for k in adjacent_counties if k in counties_list) >= x[i, j], f"adjacency_constraint_{i}_{j}"

# Define objective function to minimize maximum population deviation
print("Setting up objective function...")
z = pulp.LpVariable("z", lowBound=0)

current_tolerance = 0.1
iteration = 1

while current_tolerance <= MAX_POPULATION_TOLERANCE_PERCENT:
    print(f"\nTrying population tolerance: {current_tolerance:.2f}")

    # Update population balance constraints with the current tolerance
    for j in range(num_districts):
        model += pulp.lpSum(population_df.loc[population_df['county']==i,'population'].iloc[0] * x[i,j] for i in counties_list) <= (1 + current_tolerance) * target_population, f"upper_pop_constraint_{iteration}_{j}"
        model += pulp.lpSum(population_df.loc[population_df['county']==i,'population'].iloc[0] * x[i,j] for i in counties_list) >= (1 - current_tolerance) * target_population, f"lower_pop_constraint_{iteration}_{j}"

    # Solve the model
    print("Solving optimization model...")
    
    # Setting a time limit of 60 seconds
    model.solve(pulp.PULP_CBC_CMD(timeLimit=60))

    print(f"Solution status: {pulp.LpStatus[model.status]}")

    if pulp.LpStatus[model.status] == 'Optimal':
        print(f"Found feasible solution with population tolerance: {current_tolerance:.2f}")
        break
    else:
        # Increase tolerance for the next iteration
        current_tolerance += TOLERANCE_STEP
        iteration += 1

# If no feasible solution found within the maximum tolerance
if current_tolerance > MAX_POPULATION_TOLERANCE_PERCENT:
    print("No feasible solution found within the maximum population tolerance.")
else:
    print("Target population per district: {target_population:,}")

    # Retrieve the solution and print district assignments
    print("\nDistrict assignments:")
    print(f"\nMarion County (District 1): Population {marion_county['population'].iloc[0]:,}")
    for j in range(num_districts):
        print(f"\nDistrict {j+2}:")
        district_pop = 0
        for i in counties_list:
            if x[i,j].value() == 1:
                county_pop = population_df.loc[population_df['county']==i,'population'].iloc[0]
                district_pop += county_pop
                print(f"- {i} (population: {county_pop:,})")
        print(f"Total district population: {district_pop:,}")
        print(f"Deviation from target: {abs(district_pop - target_population):,}")

# Now map the districts to the counties
import pandas as pd
import folium
from branca.colormap import linear

# Load county location data
location_data = pd.read_csv("county_location_data.csv")
location_data['name'] = location_data['name'] + " County"

# Create a dictionary to map counties to districts
county_to_district = {"Marion County": 1}
for j in range(num_districts):
    for i in counties_list:
        if x[i, j].value() == 1:
            county_to_district[i] = j + 2  # Districts are 1-indexed

# Add district assignments to the location data
location_data['district'] = location_data['name'].map(county_to_district)

# Initialize a Folium map
indiana_map = folium.Map(location=[39.826, -86.144], zoom_start=7)

# Define a colormap for the districts
district_colors = linear.Set1_08.scale(1, num_districts)

# Plot counties on the map
for _, row in location_data.iterrows():
    if not pd.isna(row['district']):  # Only plot counties with assigned districts
        folium.CircleMarker(
            location=[row['lat'], row['lng']],
            radius=5,
            color="black",
            fill=True,
            fill_color=district_colors(row['district']),
            fill_opacity=0.7,
            tooltip=f"County: {row['name']}<br>District: {row['district']}",
        ).add_to(indiana_map)
    else:
        print("Missing district for county:", row['name'])

# Add a legend
district_colors.add_to(indiana_map)

# Save the map to an HTML file
indiana_map.save("indiana_districts_map.html")
print("Map saved as indiana_districts_map.html")