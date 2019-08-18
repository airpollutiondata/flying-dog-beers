import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from dash.dependencies import Input, Output

# Testing

# Allows for the map generation
mapbox_access_token = 'pk.eyJ1IjoiamhhbW1lcmVkMjQiLCJhIjoiY2p4eHZ2ODh0MDN1cjNtcnRrbjhkemliayJ9.kF1WMOd0RepqBUqdfXaJFw'

# Metric used for plotting
plottingParameter = '95th Percentile'

# Read in the measurements from the binary file
data = pd.read_hdf('air_pollution_data.h5', 'df')

# Table containing the limits for the EPA
#limitFile = 'EPA Limit Table.xlsx'
#Limits = pd.read_excel(limitFile)

# Make a note of the  colors used for plotting
DEFAULT_PLOTLY_COLORS=['rgb(255, 18, 18)', # red
                       'rgb(27, 30, 242)', # blue
                       'rgb(255, 127, 14)', # orange
                       'rgb(20, 97, 20)', # dark green               
                       'rgb(154, 81, 232)', # purple
                       'rgb(191, 47, 17)', # rust
                       'rgb(245, 24, 201)', # magenta
                       'rgb(26, 184, 515)', # cyan
                       'rgb(188, 189, 34)',  # yellow
                       'rgb(73, 242, 27)'] # light green

# Set up plotting markers
uniqueMarkers = ["circle", 
"diamond", # diamond
"x", 
"triangle-down", # triangle_down
"square", # square
"pentagon", 
"star", # star
"triangle-up", # triangle_up
"triangle-left", # triangle_left
"triangle-right"] # triangle_right


# Calculate the total risk found by adding up the individual risks for each parameter
# ------------------------------------------------
siteDf_PerParameter = data[['Local Site Name', 'State Name','County Name', 'City Name', 'Latitude', 'Longitude','Year', 'Parameter Name', 'Risk Level']].groupby(['Local Site Name', 'State Name','County Name', 'City Name', 'Latitude', 'Longitude', 'Year', 'Parameter Name']).max().reset_index()
siteDf_PerYear = siteDf_PerParameter[['Local Site Name', 'State Name','County Name', 'City Name', 'Latitude', 'Longitude', 'Year', 'Risk Level']].groupby(['Local Site Name', 'State Name','County Name', 'City Name', 'Latitude', 'Longitude', 'Year']).sum().reset_index()
siteDf = siteDf_PerYear[['Local Site Name', 'State Name','County Name', 'City Name', 'Latitude', 'Longitude', 'Risk Level']].groupby(['Local Site Name', 'Latitude', 'Longitude']).max().reset_index()
# Build the string to be used for hoovering on the map
siteDf['Location'] = siteDf['City Name'].str.split(pat='(', expand=True)[0] + ', ' + siteDf['State Name']
siteDf['Risk Level'] = siteDf['Risk Level'].round(decimals = 2)
siteDf['Plotting Text'] = 'Risk: ' + siteDf['Risk Level'].astype(str) + ' extra cancer cases per 100k people<br><br>' + siteDf['Local Site Name'] + '<br>' + siteDf['Location'] 
# Sort so that the highest risks are plotted last and they will end up on top
siteDf = siteDf.sort_values(by=['Risk Level'])


# --------------------------------

# TESTING FOR ADDING COLOR TO MARKERS
scl = [ [0,"rgb(30, 30, 30)"],[0.35,"rgb(90, 90, 90)"],[0.5,"rgb(128, 128, 128)"],\
    [0.6,"rgb(154, 154, 154)"],[0.7,"rgb(180, 180, 180)"],[1,"rgb(250, 250, 250)"] ]


########### Display the chart

app = dash.Dash()
server = app.server

# ************************************ APP LAYOUT ************************************
app.layout = html.Div([
        

# ----------- AIR POLLUTANT MAP -----------------
    html.Div([
        dcc.Graph(
                figure=go.Figure(
                    # Make the dark outline on the markers
                    data = [go.Scattermapbox(
                            lon = siteDf ['Longitude'],
                            lat = siteDf ['Latitude'],
                            hoverinfo = 'none',
                            mode = 'markers',
                            marker = dict( 
                                size = 7, 
                                opacity = 1,
                                color = 'rgb(0, 0, 0)',
                        ), 
                        ), 
                        
                        # Create markers whose color are scaled to the risk level
                        go.Scattermapbox(
                            lon = siteDf ['Longitude'],
                            lat = siteDf ['Latitude'],
                            text = siteDf['Plotting Text'], #siteDf ['Local Site Name'],
                            hoverinfo = 'text',
                            mode = 'markers',
                            marker = dict( 
                                size = 5, 
                                opacity = 0.8,
                                reversescale = True,
                                autocolorscale = False,
                                symbol = 'circle',
                                colorscale = scl,
                                cmin = 0, #siteDf[plottingParameter].min(),
                                color = siteDf['Risk Level'],
                                cmax = siteDf.describe(percentiles=[0.95]).loc['95%', 'Risk Level'], # Make it so the top 10% of sites have the darkest color
                                colorbar=dict(
                                    title='Cancer Risk Level'
                                    ),
                        ), 
                        )],
                layout = go.Layout(
                        title = 'Clicking on a site will pull up breakdown of risk by chemical', 
                        autosize=True,
                        hovermode='closest',
                        showlegend=False,
                        mapbox=go.layout.Mapbox(
                                accesstoken=mapbox_access_token,
                                bearing=0,
                                center=go.layout.mapbox.Center(
                                    lat=38,
                                    lon=-94
                                ),
                                pitch=0,
                                zoom=3,
                                style='light'
                        )
                        )),
            id='collection-map'
        )
    ], style={'width': '90%', 'display': 'inline-block', 'padding': '0 1'}), 
# -------------------------------------------------
        
# ----------- AIR POLLUTANT PARAMETER SCATTER PLOT -----------------
 dcc.Loading(
        children=[html.Div([
                dcc.Graph(
                        id = 'site-param-plot',
                ),
        
            ], style={'width': '90%', 'display': 'inline-block', 'padding': '0 1'}),]
    , type="circle")
# -------------------------------------------------      
    
])

# ************************************ APP CALLBACKS ************************************
@app.callback(
    Output('site-param-plot', 'figure'),
    [Input('collection-map', 'clickData')])
def update_site_param(clickData):
    
    if clickData is None:
        lon = data['Longitude'].iloc[0]
        lat = data['Latitude'].iloc[0]
    else:
        lon = clickData['points'][0]['lon']
        lat = clickData['points'][0]['lat']
    longMask = data['Longitude'] == lon
    latMask = data['Latitude'] == lat
    siteName = data[longMask & latMask]['Local Site Name'].unique()[0]
    cityName = data[longMask & latMask]['City Name'].unique()[0].split('(')[0]
    stateName = data[longMask & latMask]['State Name'].unique()[0]
    if pd.isnull(siteName):
        siteName = str(cityName) + ', ' + str(stateName)
    locationString = str(siteName) + '<br>' + str(cityName) + ', ' + str(stateName)
    
    siteData = data[longMask & latMask]
    siteData = siteData[['Parameter Name', 'Units of Measure', 'Year', 'Risk Level', 'Tumor Type']].groupby(['Parameter Name', 'Year', 'Units of Measure', 'Tumor Type']).max().reset_index()
    siteData['Plotting Text'] = siteData['Parameter Name'] + '<br>Year: ' + siteData['Year'].astype(str) + '<br>Risk: ' + siteData['Risk Level'].astype(str) + ' extra cancer cases <br> per 100k people<br><br>' + siteData['Tumor Type']

    
    # Build the array that contains the parameters sorted by risk level - this is so that the highest risk parameter will get plotted first
    OrderedByRisk = siteData[['Parameter Name', 'Risk Level']].groupby(['Parameter Name']).max()
    OrderedByRisk = OrderedByRisk.sort_values(by='Risk Level', ascending=False)
    
    # Since the colors will typically repeat, specify the markers to be used for each parameter
    nRepeats = int(len(OrderedByRisk)/len(DEFAULT_PLOTLY_COLORS))
    nRemaining = len(OrderedByRisk)%len(DEFAULT_PLOTLY_COLORS)    
    markerList = np.sort(len(DEFAULT_PLOTLY_COLORS)*uniqueMarkers[0:nRepeats] + nRemaining*[uniqueMarkers[nRepeats]])
    OrderedByRisk['Markers'] = markerList
    
    return {
            'data':[go.Scatter(
                    x = siteData[siteData['Parameter Name'] == i]['Year'],
                    y = siteData[siteData['Parameter Name'] == i]['Risk Level'],
                    text = siteData[siteData['Parameter Name'] == i]['Plotting Text'],
                    hoverinfo = 'text',
                    mode='lines+markers',
                    marker={
                        'symbol': OrderedByRisk.at[i, 'Markers'], 
                        'size': 10,
                        'opacity': 0.5,
                        'line': {'width': 0.5, 'color': 'white'}
                    },
                    name = i
                    )for i in OrderedByRisk.index
                    ],
            'layout': go.Layout(
                        title = {'text': locationString}, 
                        xaxis={
                            'title': 'Year',
                            'type': 'linear'
                        },
                        yaxis={
                            'title': 'Extra # of Cancer Cases per 100k People',
                            'type': 'linear'
                        },
                        #margin={'l': 40, 'b': 30, 't': 50, 'r': 0},
                        #height=500,
                        #width = '95%',
                        hovermode='closest',
                        showlegend=True,
               
                    )
                    
            }



if __name__ == '__main__':
    app.run_server()
