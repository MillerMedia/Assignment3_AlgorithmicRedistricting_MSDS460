# %%
import pandas as pd

# %%
import pandas as pd
import re

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

# %%
adjacent = df

# %%
adjacent.head()

# %%
# Load populations
# Reading the data from the specified file 'county_data.csv'

# File path
file_path = 'county_data.csv'

# Reading the data from the file
pop_df = pd.read_csv(file_path)

# Add ' County' to end of name column
pop_df['name'] = pop_df['name'] + ' County'

pop_df.head()

# %%
# Sum of all populations divide by 9 (number of counties in Indiana)
ideal_population = pop_df['population'].sum() / 9

# Calculate the min and max based on 5% tolerance
min_population = ideal_population - (ideal_population * 0.1)
max_population = ideal_population + (ideal_population * 0.1)

ideal_population, min_population, max_population

# %%
import pandas as pd

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

# Display the updated DataFrame
adjacent.head()


# %%
from math import pi, sin, cos, asin, sqrt

def degrees_to_radians(x):
     return((pi/180)*x)
     
def lon_lat_distance_miles(lon_a,lat_a,lon_b,lat_b):
    radius_of_earth = 24872/(2*pi)
    c = sin((degrees_to_radians(lat_a) - \
    degrees_to_radians(lat_b))/2)**2 + \
    cos(degrees_to_radians(lat_a)) * \
    cos(degrees_to_radians(lat_b)) * \
    sin((degrees_to_radians(lon_a) - \
    degrees_to_radians(lon_b))/2)**2
    return(2 * radius_of_earth * (asin(sqrt(c))))    

def lon_lat_distance_meters (lon_a,lat_a,lon_b,lat_b):
    return(lon_lat_distance_miles(lon_a,lat_a,lon_b,lat_b) * 1609.34) 
    

adjacent['distance_miles'] = adjacent.apply(
    lambda row: lon_lat_distance_miles(row['main_lat'], row['main_lng'], row['adj_lat'], row['adj_lng']),
    axis=1
)

# %%
adjacent.head()

# %%
county_pop = adjacent[['County_Code', 'main_population']]
county_pop = county_pop.set_index('County_Code')['main_population'].to_dict()
county_pop

# %%
# Initialize an empty dictionary to hold the result
dict = {}

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
    if main_county not in dict:
        dict[main_county] = []
    
    # Append the adjacent county info to the list for this county
    dict[main_county].append(adjacent_info)

# Display the adjacency dictionary
dict

# %% [markdown]
# # Build Linear Programming Problem
# 
# 

# %% [markdown]
# Our objective is to maximize compactness (minimize distance between counties in the same district). Our constraints are:
# 
# • Each county must be in exactly one district.  
# • The population of each district must be within 5% of the ideal population (the mean of the total population divided by the number of districts). These are currently stored in ideal_population, min_population, max_population variables. 
# • The number of districts must be 9 (the current number of districts in Indiana).  

# %%
# Import PuLP library
from pulp import LpVariable, LpBinary, LpProblem, LpMinimize, lpSum, LpStatus

# Define the number of districts
num_districts = 9

# Initialize the model
model = LpProblem("Indiana Counties", LpMinimize)

# Create binary variables for county-district assignments
district_assignments = {
    county: {d: LpVariable(f"assign_{county}_{d}", cat="Binary") for d in range(1, num_districts + 1)}
    for county in dict.keys()}

# Objective function: minimize the total distance between counties in the same district
model += lpSum(
    district_assignments[county][d] * adj['Distance']
    for county, adjacents in dict.items()
    for adj in adjacents
    for d in range(1, num_districts + 1)
    if adj['Adjacent_County_Code'] in district_assignments
)

# Constraint: each county must be in exactly one district
for county in dict.keys():
    model += lpSum(district_assignments[county][d] for d in range(1, num_districts + 1)) == 1

# Calculate total population and ideal population per district
total_population = sum(county_pop.values())
ideal_population = total_population / num_districts
min_population = 0.7 * ideal_population
max_population = 1.3 * ideal_population

# Constraint: population of each district must be within 30% of the ideal population
for d in range(1, num_districts + 1):
    model += lpSum(
        county_pop[county] * district_assignments[county][d]
        for county in dict.keys()
    ) >= min_population
    model += lpSum(
        county_pop[county] * district_assignments[county][d]
        for county in dict.keys()
    ) <= max_population

# ADDITIONAL ADJACENCY CONSTRAINT: counties in the same district must be adjacent ** we tried this but it caused the solver to output zero rows **
#for county, adjacents in dict.items():
    #for adj in adjacents:
        #for d in range(1, num_districts + 1):
            #model += district_assignments[county][d] <= district_assignments[adj['Adjacent_County_Code']][d]

# Solve the model
model.solve()

# Initialize an empty list to store the results
results = []

# Print the results
for county in dict.keys():
    for d in range(1, num_districts + 1):
        if district_assignments[county][d].varValue == 1:
            print(f"County {county} is assigned to district {d}")
            results.append({'County': county, 'District': d})
        
# Convert the results to a DataFrame
results_df = pd.DataFrame(results)
# Display the DataFrame
print(results_df)



# %%
results_df = results_df.rename(columns = {"County": "County_Code"})
results_df

# %%
county_codes = adjacent[["County", "County_Code"]]
county_codes = county_codes.drop_duplicates()
county_codes

# %%
results_final = pd.merge(results_df, county_codes, on=['County_Code', 'County_Code'])
results_final
results_final.to_csv("county_district_assignments2.csv")


