import pandas as pd
import pulp
import json
import networkx as nx
import folium
from branca.colormap import linear

MAX_POPULATION_TOLERANCE_PERCENT = 0.6  # Maximum allowed population tolerance
TOLERANCE_STEP = 0.01  # Increment for each iteration

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

# Remove state columns, county numbers and district numbers
population_df.drop(columns=['state', 'county (or part)', 'congressional district'], inplace=True)

# Combine any duplicate county rows and add populations
population_df = population_df.groupby('county').sum().reset_index()

print(population_df.head())
print(f"Loaded data for {len(population_df)} counties")

# Load county adjacency data
print("Loading adjacency data...")
adjacency_data = pd.read_csv('county_adjacency2023.txt', sep='|', header=0)

# Filter adjacency data for Indiana counties
print("Filtering adjacency data for Indiana...")
indiana_adjacency = adjacency_data[adjacency_data['County GEOID'].astype(str).str.startswith('18')]
print(indiana_adjacency.head())
print(f"Found {len(indiana_adjacency)} adjacency relationships")

# Create adjacency dictionary
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

# Add adjacent counties to the DataFrame
population_df['adjacent_counties'] = population_df['county'].map(adjacency_dict)

def check_district_contiguity(assignments, district_num, adjacency_dict):
    """
    Check if a district is contiguous using networkx
    """
    # Get counties in this district
    district_counties = [county for county, dist in assignments.items() if dist == district_num]
    if not district_counties:
        return True
        
    # Create a graph of just this district's counties
    G = nx.Graph()
    for county in district_counties:
        G.add_node(county)
        for adj_county in adjacency_dict.get(county, []):
            if adj_county in district_counties:
                G.add_edge(county, adj_county)
                
    # Check if the graph is connected
    return nx.is_connected(G) if len(G.nodes) > 0 else True

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

# Set up optimization model
print("Setting up optimization model...")
model = pulp.LpProblem("Redistricting", pulp.LpMinimize)

# Basic constraints (one district per county)
print("Adding basic constraints...")
for i in counties_list:
    model += pulp.lpSum(x[i,j] for j in range(num_districts)) == 1

# Contiguity constraints using "seed and grow" approach
print("Adding contiguity constraints...")
for j in range(num_districts):
    # Add variables to track which county is the "seed" for this district
    y = pulp.LpVariable.dicts(f"seed_{j}", counties_list, cat='Binary')
    
    # Exactly one seed county per district
    model += pulp.lpSum(y[i] for i in counties_list) == 1
    
    # Seed county must be in its district
    for i in counties_list:
        model += y[i] <= x[i,j]
    
    # Every non-seed county in the district must be adjacent to at least
    # one other county in the same district
    for i in counties_list:
        adjacent_counties = adjacency_dict.get(i, [])
        if adjacent_counties:
            model += pulp.lpSum(x[k,j] for k in adjacent_counties if k in counties_list) >= x[i,j] - y[i]

# Iterative solving with increasing population tolerance
current_tolerance = 0.3
iteration = 1

while current_tolerance <= MAX_POPULATION_TOLERANCE_PERCENT:
    print(f"\nTrying population tolerance: {current_tolerance:.2f}")
    
    # Update population balance constraints
    for j in range(num_districts):
        model += pulp.lpSum(population_df.loc[population_df['county']==i,'population'].iloc[0] * x[i,j] 
                          for i in counties_list) <= (1 + current_tolerance) * target_population
        model += pulp.lpSum(population_df.loc[population_df['county']==i,'population'].iloc[0] * x[i,j] 
                          for i in counties_list) >= (1 - current_tolerance) * target_population
    
    # Solve with increased time limit
    status = model.solve(pulp.PULP_CBC_CMD(timeLimit=300))
    
    if status == pulp.LpStatusOptimal:
        # Verify contiguity of the solution
        assignments = {i: next(j for j in range(num_districts) if x[i,j].value() > 0.5)
                      for i in counties_list}
        
        all_contiguous = all(check_district_contiguity(assignments, j, adjacency_dict)
                            for j in range(num_districts))
        
        if all_contiguous:
            print(f"Found feasible solution with population tolerance: {current_tolerance:.2f}")
            break
        else:
            print("Solution found but districts not contiguous, increasing tolerance")
            current_tolerance += TOLERANCE_STEP
    else:
        print(f"No solution found with tolerance {current_tolerance:.2f}")
        current_tolerance += TOLERANCE_STEP
    
    iteration += 1

# Print results if solution found
if current_tolerance <= MAX_POPULATION_TOLERANCE_PERCENT:
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
else:
    print("No feasible solution found within the maximum population tolerance.")

# Visualization
print("\nCreating visualization...")
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

# Initialize the map
indiana_map = folium.Map(location=[39.826, -86.144], zoom_start=7)

# Define a colormap for the districts
district_colors = linear.Set1_08.scale(1, num_districts)

# Plot counties on the map
for _, row in location_data.iterrows():
    if not pd.isna(row['district']):
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

# Add legend
district_colors.add_to(indiana_map)

# Save the map
indiana_map.save("indiana_districts_map.html")
print("Map saved as indiana_districts_map.html")