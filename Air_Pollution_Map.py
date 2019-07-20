# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 20:18:37 2019

@author: jkelly8

Source Data:
EPA Pre-Generated Data sets - https://aqs.epa.gov/aqsweb/airdata/download_files.html#Annual![image.png](attachment:image.png)

"""
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
#import plotly.plotly as py
import numpy as np
#import glob, os   
from dash.dependencies import Input, Output
 
# ------------------------ Helper-functions ---------------------------------
def convert_to_ppm(mg_m3, MW, P = 760, R = 62.4, T = 298.16):   
    return R*T*mg_m3/(P*MW)


# ppm = R*T*mg_m3/(P*MW)
def convert_threshold_to_ppb(parameterName, Limits, limitName, unitName):
    # TODO: Add code to over-ride with measured temp, if available
    temp = 25 # degrees C
    # TODO: Add code to over-ride with measured pressure, if available
    P = 760 # mm Hg
    R = 62.4 # L torr/mol K
    T = 273.16 + temp
    
    
    # Pull out the specifics for this hazardous pollutant
    LimitRow = Limits[Limits['Parameter Name'] == parameterName]
    if len(LimitRow) == 0:
        MW = nan
    else:
        MW = LimitRow['Molecular weight']
    
    # The measurement to be converted
    mg_m3 = LimitRow[limitName]
    if 'ug' in LimitRow[unitName]:
        mg_m3 = mg_m3/1000
    ppm = convert_to_ppm(mg_m3, MW, P, R, T)
    return ppm*1000


def calculate_cancer_risk_levels(parameterName, Limits):
    LimitRow = Limits[Limits['Parameter Name'] == parameterName]
    slope = LimitRow['Cancer slope inhalation unit risk']
    MW = LimitRow['Molecular weight']
    
    # Would divide by 1000 to convert from ug/m3 to mg/m3
    # Would multiply by 1000 to convert from ppm to ppb
    # So no scaling happening in the code below
    one_in_million = convert_to_ppm(1E-6/(slope), MW)
    one_in_hundred_thous = convert_to_ppm(1E-5/(slope), MW)
    one_in_ten_thous = convert_to_ppm(1E-4/(slope), MW)
    one_in_thous = convert_to_ppm(1E-3/(slope), MW)
    
    return [(one_in_million.iloc[0], one_in_hundred_thous.iloc[0], one_in_ten_thous.iloc[0], one_in_thous.iloc[0]), 
            ('Cancer  Increases by 1 in a Million', 'Cancer Increases by 1 in 100,000', 'Cancer Increases by 1 in 10,000', 'Cancer Increases by 1 in 1,000')]

def applyrisklevel(row, Limits, plottingParameter):
    parameterName = row['Parameter Name']
    thresholds = calculate_cancer_risk_levels(parameterName, Limits)
    # Determine the # of expected cancer cases per 100k people
    return row[plottingParameter]/thresholds[0][1]
# --------------- END HELPER FUNCTOINS -----------------------



# ----------- SET UP GLOBALLY AVAILABLE DATA -----------------
folderLocation = 'C:\\Users\\Johanna\\Desktop\\Capstone\\Code\\Data'

#mapbox_access_token = 'pk.eyJ1IjoiamhhbW1lcmVkMjQiLCJhIjoiY2p4eHZ2ODh0MDN1cjNtcnRrbjhkemliayJ9.kF1WMOd0RepqBUqdfXaJFw'
mapbox_access_token = 'pk.eyJ1IjoiamhhbW1lcmVkMjQiLCJhIjoiY2p4eHZ2ODh0MDN1cjNtcnRrbjhkemliayJ9.kF1WMOd0RepqBUqdfXaJFw'

# Metric used for plotting
plottingParameter = '95th Percentile'


#all_files = glob.glob(os.path.join(folderLocation, "*.csv"))     # advisable to use os.path.join as this makes concatenation OS independent
#df_from_each_file = (pd.read_csv(f, low_memory=False) for f in all_files)
#data   = pd.concat(df_from_each_file, ignore_index=True)
# Load the data
data = pd.read_hdf(folderLocation + '\\' + 'air_pollution_data.h5', 'df')

# Table containing the limits for the EPA
limitFolder = 'C:\\Users\\Johanna\\Desktop\\Capstone\\Code'
limitFile = 'EPA Limit Table.xlsx'
Limits = pd.read_excel(limitFolder + '\\' + limitFile)



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


# ----------- Required code for Dash application-----------------
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


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
    ], style={'width': '47%', 'display': 'inline-block', 'padding': '0 1'}),      
# -------------------------------------------------
        
# ----------- AIR POLLUTANT PARAMETER SCATTER PLOT -----------------
     html.Div([
        dcc.Graph(
                id = 'site-param-plot'                
        )
    ], style={'width': '47%', 'display': 'inline-block', 'padding': '0 1'}),
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
    siteData = siteData[['Parameter Name', 'Units of Measure', 'Year', 'Risk Level']].groupby(['Parameter Name', 'Year', 'Units of Measure']).max().reset_index()
    
    # Apply cancer risk thresholds from the EPA
    # siteData['Risk Level'] = siteData.apply(lambda x:applyrisklevel(x, Limits, plottingParameter), axis=1)
    
    
    return {
            'data':[go.Scatter(
                    x = siteData[siteData['Parameter Name'] == i]['Year'],
                    y = siteData[siteData['Parameter Name'] == i]['Risk Level'],
                    text = siteData[siteData['Parameter Name'] == i]['Parameter Name'],
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
    app.run_server(debug=True)
