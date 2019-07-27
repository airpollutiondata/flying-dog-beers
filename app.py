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
limitFile = 'EPA Limit Table.xlsx'
Limits = pd.read_excel(limitFile)


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
                        title = 'EPA Measured Air Pollution Converted to Cancer Risk<br> Click on a site to see measurements', 
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
     html.Div([
        dcc.Graph(
                id = 'site-param-plot'                
        )
    ], style={'width': '90%', 'display': 'inline-block', 'padding': '0 1'}),
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
    #locationString = str(siteName) + ': ' + str(cityName) + ', ' + str(stateName)
    locationString = str(siteName) + '<br>' + str(cityName) + ', ' + str(stateName)
    
    #siteName = 'Zion NP - Dalton\'s Wash'
    siteData = data[longMask & latMask]
    siteData = siteData[['Parameter Name', 'Units of Measure', 'Year', 'Risk Level', 'Tumor Type']].groupby(['Parameter Name', 'Year', 'Units of Measure', 'Tumor Type']).max().reset_index()
    siteData['Plotting Text'] = siteData['Parameter Name'] + '<br>Year: ' + siteData['Year'].astype(str) + '<br>Risk: ' + siteData['Risk Level'].astype(str) + ' extra cancer cases <br> per 100k people<br><br>' + siteData['Tumor Type']

    # Apply cancer risk thresholds from the EPA
    # siteData['Risk Level'] = siteData.apply(lambda x:applyrisklevel(x, Limits, plottingParameter), axis=1)
    
    
    return {
            'data':[go.Scatter(
                    x = siteData[siteData['Parameter Name'] == i]['Year'],
                    y = siteData[siteData['Parameter Name'] == i]['Risk Level'],
                    text = siteData[siteData['Parameter Name'] == i]['Plotting Text'],
                    hoverinfo = 'text',
                    mode='lines+markers',
                    marker={
                        'size': 10,
                        'opacity': 0.5,
                        'line': {'width': 0.5, 'color': 'white'}
                    },
                    name = i
                    )for i in np.sort(siteData['Parameter Name'].unique())
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
