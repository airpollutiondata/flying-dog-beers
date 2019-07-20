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



########### Set up the chart
beers=['Chesapeake Stout', 'Snake Dog IPA', 'Imperial Porter', 'Double Dog IPA']
ibu_values=[35, 60, 85, 75]
abv_values=[5.4, 7.1, 9.2, 4.3]
color1='lightblue'
color2='darkgreen'

bitterness = go.Bar(
    x=beers,
    y=ibu_values,
    name='IBU',
    marker={'color':color1}
)
alcohol = go.Bar(
    x=beers,
    y=abv_values,
    name='ABV',
    marker={'color':'red'}
)

beer_data = [bitterness, alcohol]
beer_layout = go.Layout(
    barmode='group',
    title = 'Beer Comparison'
)

beer_fig = go.Figure(data=beer_data, layout=beer_layout)

########### Display the chart

app = dash.Dash()
server = app.server

app.layout = html.Div(children=[
    html.H1('Flying Dog Beers'),
    dcc.Graph(
        id='flyingdog',
        figure=beer_fig
    ),
    html.A('Code on Github', href='https://github.com/austinlasseter/flying-dog-beers'),
    html.Br(),
    html.A('Data Source', href='https://www.flyingdog.com/beers/'),
    ]
)

if __name__ == '__main__':
    app.run_server()
