# Indiana Congressional District Optimization

## Overview
This project attempts to optimize Indiana's congressional districts using linear programming while maintaining county boundaries intact. The goal was to create nine balanced districts while keeping counties whole and ensuring district contiguity.

## Data Sources
- Population data: Census 2020 API (Indiana congressional district data). Direct link to Indiana district data can be found [here](https://api.census.gov/data/2020/dec/pl?get=NAME,P1_001N&for=county%20(or%20part):*&in=state:18%20congressional%20district:01,02,03,04,05,06,07,08,09)
- County adjacency data: U.S. Census Bureau (county_adjacency2023.txt)
- County location data: county_location_data.csv for visualization

## Implementation
The solution uses Python with the following key libraries:
- PuLP for linear programming optimization
- Pandas for data preprocessing
- Folium for visualization
- Networkx for graph operations

### Key Features
- Population balance constraints (10% tolerance)
- County adjacency requirements
- Marion County pre-assigned to its own district
- Interactive map visualization

### Scripts
1. `main.py`: Primary implementation with basic adjacency constraints
2. `unresolved_districts.py`: Alternative implementation with stricter contiguity requirements

## Results
The implementation found a mathematical solution but with important limitations:
- Achieved population balance within 8.4% deviation
- All counties assigned to districts
- Districts maintain local adjacency but not full contiguity
- Second implementation with stricter contiguity failed to converge

## Key Findings
1. Current county boundaries make it mathematically impossible to create:
   - Contiguous districts
   - Equal populations
   - Whole counties
   All three simultaneously

2. Real-world districting requires either:
   - Splitting counties (current approach)
   - Accepting non-contiguous districts
   - Allowing large population deviations
   - Redrawing county boundaries

## Requirements
- Python 3.x
- PuLP
- Pandas
- Folium
- Networkx
- Branca

## Usage
1. Clone the repository
2. Install requirements: `pip install -r requirements.txt`
3. Place data files in project directory:
   - county_populations.json
   - county_adjacency2023.txt
   - county_location_data.csv
4. Run: `python main.py`

## Output
- District assignments with populations
- Interactive map (indiana_districts_map.html)
- Population deviation statistics

## Authors
- Hannah Graham
- Matt Miller
- Morgan McCoy
- Aishanee Wijeratna

## License
MIT License