import numpy as np
import pandas as pd
import requests
from shapely.geometry import Polygon, Point


import map_generator


#list that will contain dataframes by J 
dataframes_by_J=[]


def get_request(url):
    response = requests.get(url)

    # Check the response status code
    if response.status_code == 200:
        # Request was successful
        return response.json()  # Extract the JSON data from the response
        # Process the data as needed
    else:
        # Request failed
        print("GET request failed with status code:", response.status_code)
        raise Exception(f"GET request failed with status code: {response.status_code}")



#Some of data is nested multiple times like :[[[[cor],[cor],[cor]]]] 
def unpack_list(L):
    if isinstance(L[0][0],list):
        return unpack_list(L[0])   
    return L


def insert_features_to_df(df, features):
    codes=[]
    names=[]
    for index, row in df.iterrows():
        latitude = row['Latitude']
        longitude = row['Longitude']
        # Flag to keep track of match
        match_found = False
        for feature in features:
            try:
                coordinates = feature['geometry']['coordinates']  # Extract the coordinates of the polygon

                polygon_coordinates = unpack_list(coordinates) #getting list in [[lat,long],[lat,long]] format
                mapped_polygon_coordinates = [tuple(sublist) for sublist in polygon_coordinates] #getting list in [(lat,long),(lat,long)] format for Polygon
                polygon = Polygon(mapped_polygon_coordinates)
                
                # Check if the coordinate is within the polygon
                if polygon.contains(Point(longitude, latitude)):
                    err=3
                    code = feature['properties'].get('code')
                    name = feature['properties'].get('nom')

                    # Append the values to the respective lists
                    codes.append(code)
                    names.append(name)

                    # Set the flag to True
                    match_found = True

                    # Break the loop once a match is found
                    break

            except Exception as e:
                print(f"Error processing feature: {e} ")

        # If no match is found, assign None or a default value to the columns
        if not match_found:
            codes.append(None)
            names.append(None)
    # Assign the new lists to the DataFrame columns
    df['domain_id']=codes
    df['region']=names
    
    return df

def generate_df_of_domains(domains_arr_obj):
    df = pd.DataFrame()  # Create an empty DataFrame

    for obj in domains_arr_obj:
        domain_id = obj['domain_id']
        phenomenon_items = obj['phenomenon_items']

        df_temp = pd.json_normalize(phenomenon_items, 'timelaps_items', ['phenomenon_id', 'phenomenon_max_color_id'])
        df_temp['domain_id'] = domain_id

        df = pd.concat([df, df_temp], ignore_index=True)

    return df

def set_binary_phenomena_columns(df):
    unique_ids = df['id'].unique()

    # Create phenomenon_n columns with 0 values
    for i in range(1, 10):
        column_name = 'phenomenon_' + str(i)
        df[column_name] = 0

    for id_value in unique_ids:
        subset = df.loc[df['id'] == id_value].copy()  # Create a copy of the subset

        # Map phenomenon_n columns based on phenomenon_id values
        for i in subset['phenomenon_id'].unique():
            df.loc[subset.index, 'phenomenon_' + str(i)] = 1

    # Drop the 'phenomenon_id' column
    df.drop('phenomenon_id', axis=1, inplace=True)

    # Drop duplicates based on all columns
    df.drop_duplicates(inplace=True, ignore_index=True)


if __name__ == '__main__':
    # Set the random seed for reproducibility
    np.random.seed(42)

    # Define the boundaries of France's latitude and longitude
    min_lat, max_lat = 41.333, 51.124
    min_lon, max_lon = -5.5, 9.662

    # Generate random latitude and longitude coordinates within the boundaries
    lats = np.random.uniform(min_lat, max_lat, 1000)
    lons = np.random.uniform(min_lon, max_lon, 1000)

    # Create a Pandas DataFrame to store the coordinates
    df = pd.DataFrame({'Latitude': lats, 'Longitude': lons})

    # Display the first few rows of the DataFrame
    print(df.head())


    # Make a GET request to a URL
    url = "https://france-geojson.gregoiredavid.fr/repo/regions.geojson"
    data=get_request(url)

    features=data.get('features')
    df_codes_regions=insert_features_to_df(df.copy(),features)
    null_counts = df_codes_regions.isnull().sum()
    print("None's values by columns")
    print(null_counts)
    df_codes_regions_no_null=df_codes_regions.dropna()
    df_codes_regions_no_null.insert(0, 'id', range(len(df_codes_regions_no_null)))

    print(df_codes_regions_no_null.head())

    # Make a GET request to a URL
    url_meta_data = "http://storage.gra.cloud.ovh.net/v1/AUTH_555bdc85997f4552914346d4550c421e/gra-vigi6-archive_public/2023/06/15/140214/CDP_CARTE_EXTERNE.json"
    meta_data=get_request(url_meta_data)

    for item in meta_data:
        print(item)

    meta_data.get("product")
    periods=meta_data.get("product").get('periods')

    for i in range(len(periods)):
        #i corresponds to J (jour)
        domains=periods[i].get("timelaps").get("domain_ids")
        merged_df = pd.merge(df_codes_regions_no_null, generate_df_of_domains(domains), on='domain_id')
        #using one-hot encoding for phenomen_id ,because we know it is between 1-9 and multiple phenomens can be at the same time in one region
        set_binary_phenomena_columns(merged_df)
        # Explanation:
        # Since we don't have any information about the risk level using the provided API,
        # we use the "phenomenon_max_color_id" field that indicates the color of this phenomenon
        # for the given day. According to the provided documentation, the values of the "phenomenon_max_color_id"
        # field correspond to the risk levels as follows:
        # • "0" : green
        # • "1" : yellow
        # • "2" : orange
        # • "3" : red
        # This approach allows us to map the color codes to the respective risk levels.
        merged_df.rename(columns={'phenomenon_max_color_id': 'risk level'}, inplace=True)
        merged_df['risk level'] = merged_df['risk level'] - 1
        dataframes_by_J.append(merged_df)

    for i in range(len(dataframes_by_J)):
        dataframe=dataframes_by_J[i]
        print(f'Data frame of J{i}')
        print(dataframe.head(),end='\n\n\n\n\n\n')
    
    #Running Tkinter
    map_generator.run_map(dataframes_by_J)
    
    
    
    