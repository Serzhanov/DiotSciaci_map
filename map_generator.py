import tkinter as tk
import webbrowser
import folium


color_mapping={
    1:"lightgreen",#green in original doc
    2:"darkgreen",#yelllow in original doc
    3:"orange",
    4:"red"
}

phenomenon_mapping={
    1: "wind", 
    2: "rain", 
    3: "thunderstorms", 
    4: "floods", 
    5: "snow or ice",
    6: "heatwave", 
    7: "cold wave", 
    8: "avalanches", 
    9: "storm surges",
}

risk_level_mapping={
    0:"green",
    1:"yellow",
    2:"orange",
    3:"red"
}

def open_map(df,indexJ):
    # Create a folium map centered on Hauts-de-France
    # Create a folium map centered on Hauts-de-France
    map_center = [50.641444, 2.716302]
    m = folium.Map(location=map_center, zoom_start=10)

    # Iterate over the rows of the data frame
    for index, row in df.iterrows():
        # Get the latitude, longitude, and color_id
        lat = row['Latitude']
        lon = row['Longitude']
        color_id = row['color_id']
        risk_level = row['risk level']

        # Get the marker color based on the color_id
        marker_color = color_mapping.get(color_id, 'gray')  # Use gray if color_id mapping not found
        # Create a marker with the corresponding color
        marker = folium.Marker(location=[lat, lon], icon=folium.Icon(color=marker_color))

        # Create a popup with additional information
        popup_text = f'Risk Level: {risk_level_mapping.get(risk_level)}'
        for i in range(1, 10):
            isPhenomenon=row[f'phenomenon_{i}']
            if isPhenomenon==1:
                phenomenon = phenomenon_mapping.get(i)
            else:
                phenomenon = "None"
            popup_text += f'<br>Phenomenon {i}: {phenomenon}'

        popup = folium.Popup(popup_text, max_width=250)

        # Add the popup to the marker
        marker.add_child(popup)

        # Add the marker to the map
        marker.add_to(m)

    filename='map'+str(indexJ)+'.html'

    m.save(filename)

    # Open the HTML file in a web browser
    webbrowser.open(filename)

def run_map(dataframes_by_J):
    # Create a Tkinter window
    for i in range(len(dataframes_by_J)):
        open_map(dataframes_by_J[i],i)

