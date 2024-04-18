import dash
from dash import dcc, html, Input, Output
import json
import pandas as pd
import plotly.express as px
from urllib.request import urlopen

# Load country geometry data
with urlopen('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json') as response:
    countries = json.load(response)

# Read the data
df = pd.read_csv("area_percentage_by_country_each_species_final.csv")

# Initialize the Dash app
app = dash.Dash(__name__)

#From Dash tools
server = app.server

# Create choropleth map figure
def create_figure(species, threshold):
    filtered_df = df[df['species'] == species].drop(columns=['species', 'group', 'lcat'])

    # Calculate total endemicity for the selected species
    total_endemicity = filtered_df.sum(axis=1)

    # Calculate the percentage contribution of each country to the total endemicity
    percentage_df = filtered_df.div(total_endemicity, axis=0) * 100

    # Reset index for proper merging
    percentage_df.reset_index(inplace=True)

    # Melt the dataframe to long format
    percentage_df = percentage_df.melt(id_vars=['index'], var_name='Country', value_name='Percentage')

    # Filter countries based on the threshold
    filtered_countries = percentage_df[percentage_df['Percentage'] <= threshold]

    # Merge the filtered countries with the original filtered dataframe
    filtered_df = filtered_df.merge(filtered_countries[['index']], left_index=True, right_on='index')

    # Melt the dataframe to long format
    filtered_df = filtered_df.melt(id_vars=['index'], var_name='Country', value_name='Endemicity')

    fig = px.choropleth(filtered_df,
                        geojson=countries,
                        locations='Country',
                        locationmode='country names',
                        color='Endemicity',
                        hover_name='Country',
                        color_continuous_scale=px.colors.sequential.Plasma,
                        range_color=(0, 100),
                        labels={'Endemicity': 'Endemicity by %'},
                        )

    # Customize popup labels
    fig.update_traces(hovertemplate='<b>%{location}</b><br>Endemicity: %{z:.2f}%')
    
    # Customize layout to match the desired styling
    fig.update_geos(showcountries=True, countrycolor="black")  # Show country boundaries
    fig.update_layout(geo=dict(showframe=False, showcoastlines=False, projection_type='equirectangular'))

    return fig

# Define layout of the Dash app
app.layout = html.Div([
    html.H1("Biodiversity: Endemicity by Country"),
    
    # Dropdown for selecting species
    dcc.Dropdown(
        id='species-dropdown',
        options=[{'label': species, 'value': species} for species in df['species'].unique()],
        value=df['species'].iloc[0],
        style={'width': '50%'}  # Adjust dropdown size horizontally
    ),

    # Graph for displaying world map
    dcc.Graph(id='world-map', style={'height': '780px'}),

    # Label for selected threshold percentage
    html.Div(id='threshold-label')
])


# Define callback to update the world map based on dropdown value
@app.callback(
    Output('world-map', 'figure'),
    [Input('species-dropdown', 'value')]
)
def update_map_by_species(species):
    return create_figure(species, threshold=50)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
