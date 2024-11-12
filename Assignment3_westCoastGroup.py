import pandas as pd
import re
from math import pi, sin, cos, asin, sqrt
from pulp import LpVariable, LpProblem, LpMinimize, lpSum, LpStatus
import folium

# File path
file_path = 'AdjacentCounties'

# Reading and processing data
with open(file_path, 'r') as file:
    data = file.read()

county_data = []
current_county = None
current_code = None

for line in data.strip().splitlines():
    line = line.strip()
    if not line:
        continue

    match_main = re.match(r'"(.+?), IN"\s+(\d+)\s+".+?"\s+(\d+)', line)
    if match_main:
        current_county = match_main.group(1)
        current_code = match_main.group(2)
    else:
        match_adjacent = re.match(r'"\s*(.+?)"\s+(\d+)', line)
        if match_adjacent and current_county and current_code:
            adjacent_county = match_adjacent.group(1)
            adjacent_code = match_adjacent.group(2)
            county_data.append([current_county, current_code, adjacent_county, adjacent_code])

# Create DataFrame with Indiana counties only
df = pd.DataFrame(county_data, columns=["County", "County_Code", "Adjacent_County", "Adjacent_County_Code"])
df = df[df["Adjacent_County"].str.endswith(", IN")]
df["Adjacent_County"] = df["Adjacent_County"].str.replace(", IN", "")

# Load population data
pop_df = pd.read_csv('county_data.csv')
pop_df['name'] = pop_df['name'] + ' County'

# Calculate ideal population range
ideal_population = pop_df['population'].sum() / 9
min_population = ideal_population - (ideal_population * 0.1)
max_population = ideal_population + (ideal_population * 0.1)

# Merge main and adjacent county data
adjacent = pd.merge(df, pop_df[['name', 'lat', 'lng', 'population']], left_on='County', right_on='name', how='left')
adjacent = adjacent.drop(columns=['name']).rename(columns={'lat': 'main_lat', 'lng': 'main_lng', 'population': 'main_population'})
adjacent = pd.merge(adjacent, pop_df[['name', 'lat', 'lng', 'population']], left_on='Adjacent_County', right_on='name', how='left')
adjacent = adjacent.drop(columns=['name']).rename(columns={'lat': 'adj_lat', 'lng': 'adj_lng', 'population': 'adj_population'})

# Distance calculation functions
def degrees_to_radians(x):
    return (pi / 180) * x

def lon_lat_distance_miles(lon_a, lat_a, lon_b, lat_b):
    radius_of_earth = 24872 / (2 * pi)
    c = sin((degrees_to_radians(lat_a) - degrees_to_radians(lat_b)) / 2)**2 + \
        cos(degrees_to_radians(lat_a)) * cos(degrees_to_radians(lat_b)) * \
        sin((degrees_to_radians(lon_a) - degrees_to_radians(lon_b)) / 2)**2
    return 2 * radius_of_earth * asin(sqrt(c))

adjacent['distance_miles'] = adjacent.apply(
    lambda row: lon_lat_distance_miles(row['main_lat'], row['main_lng'], row['adj_lat'], row['adj_lng']),
    axis=1
)

# Create adjacency dictionary
county_pop = adjacent[['County_Code', 'main_population']].set_index('County_Code')['main_population'].to_dict()
adjacency_dict = {}
for _, row in adjacent.iterrows():
    main_county = row['County_Code']
    distance = lon_lat_distance_miles(row['main_lng'], row['main_lat'], row['adj_lat'], row['adj_lng'])
    adjacent_info = {'Adjacent_County_Code': row['Adjacent_County_Code'], 'Distance': distance}
    adjacency_dict.setdefault(main_county, []).append(adjacent_info)

# Define Linear Programming Problem
num_districts = 9
model = LpProblem("Indiana_Counties", LpMinimize)

# Decision variables for district assignments
district_assignments = {
    county: {d: LpVariable(f"assign_{county}_{d}", cat="Binary") for d in range(1, num_districts + 1)}
    for county in adjacency_dict.keys()
}

# Auxiliary variables for adjacency
adjacency_penalty = 1000  # High penalty for non-adjacent counties
adjacency_vars = {}
for county, adjacents in adjacency_dict.items():
    for adj in adjacents:
        for d in range(1, num_districts + 1):
            var_name = f"adjacency_{county}_{adj['Adjacent_County_Code']}_{d}"
            adjacency_vars[(county, adj['Adjacent_County_Code'], d)] = LpVariable(var_name, cat="Binary")

# Objective function - minimize distance and enforce adjacency
model += lpSum(
    adjacency_vars[(county, adj['Adjacent_County_Code'], d)] * (1 if adj['Distance'] <= 50 else adjacency_penalty)
    for county, adjacents in adjacency_dict.items()
    for adj in adjacents
    for d in range(1, num_districts + 1)
)

# Constraints
# Each county is assigned to exactly one district
for county in adjacency_dict.keys():
    model += lpSum(district_assignments[county][d] for d in range(1, num_districts + 1)) == 1

# Each district's population must fall within the specified range
for d in range(1, num_districts + 1):
    model += lpSum(county_pop[county] * district_assignments[county][d] for county in adjacency_dict.keys()) >= min_population
    model += lpSum(county_pop[county] * district_assignments[county][d] for county in adjacency_dict.keys()) <= max_population

# Adjacency constraints
for county, adjacents in adjacency_dict.items():
    for adj in adjacents:
        for d in range(1, num_districts + 1):
            adj_var = adjacency_vars[(county, adj['Adjacent_County_Code'], d)]
            # Enforce that adj_var can only be 1 if both counties are in the same district
            model += adj_var <= district_assignments[county][d]
            model += adj_var <= district_assignments[adj['Adjacent_County_Code']][d]
            model += adj_var >= district_assignments[county][d] + district_assignments[adj['Adjacent_County_Code']][d] - 1

# Solve model
model.solve()

# Collect results
results = [{'County': county, 'District': d} for county in adjacency_dict.keys() for d in range(1, num_districts + 1) if district_assignments[county][d].varValue == 1]
results_df = pd.DataFrame(results).rename(columns={"County": "County_Code"})

# Merge with county names and save
county_codes = adjacent[["County", "County_Code"]].drop_duplicates()
results_final = pd.merge(results_df, county_codes, on='County_Code')
results_final.to_csv("county_district_assignments2.csv", index=False)

#####
# Create map
#####

# Create a base map centered around Indiana
m = folium.Map(location=[40.2672, -86.1349], zoom_start=7)

# Define colors for each district
district_colors = ['blue', 'green', 'red', 'purple', 'orange', 'darkred', 'lightblue', 'lightgreen', 'pink']

# Add counties to map by district
for _, row in results_final.iterrows():
    # Get coordinates and district
    county = row['County']
    district = row['District']
    lat = adjacent.loc[adjacent['County'] == county, 'main_lat'].values[0]
    lng = adjacent.loc[adjacent['County'] == county, 'main_lng'].values[0]

    # Add a marker for each county with district-specific color
    folium.Marker(
        location=[lat, lng],
        popup=f"{county}, District {district}",
        icon=folium.Icon(color=district_colors[district - 1])
    ).add_to(m)

# Save map to HTML
m.save("indiana_counties_map.html")
