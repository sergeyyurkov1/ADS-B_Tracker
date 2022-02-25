import dash_leaflet as dl
import dash_leaflet.express as dlx
import json
from dash import html, Input, Output, Dash, dcc
import requests
from pprint import pprint
from dash_extensions.javascript import assign
import dash_bootstrap_components as dbc
import pandas as pd

def get_states(bounds: list) -> list:
    bounds_ = eval(json.dumps(bounds))
    
    lamin = bounds_[0][0]
    lomin = bounds_[0][1]
    lamax = bounds_[1][0]
    lomax = bounds_[1][1]
 
    url = f"https://opensky-network.org/api/states/all?lamin={lamin}&lomin={lomin}&lamax={lamax}&lomax={lomax}"

    response = requests.get(url)

    states = response.json()["states"]

    features = []

    try:
        for i in states:
            features.append({
                "lon": i[5],
                "lat":  i[6],
                "true_track": i[10],
                "icao24": i[0],
                "callsign": i[1][:-2],
                "origin_country": i[2],
                "time_position": i[3],
                "last_contact": i[4],
                "baro_altitude": i[7],
                "on_ground": i[8],
                "velocity": i[9],
                "vertical_rate": i[11],
                "sensors": i[12],
                "geo_altitude": i[13],
                "squawk": i[14],
                "spi": i[15],
                "position_source": i[16],
            })
    except:
        pass

    return features[:200]

def get_flight_status(icao24: str) -> tuple:
    df = pd.read_csv("aircraftDatabase.csv", index_col="icao24")

    try:
        operator = df.loc[icao24, "operator"]
        manufacturername = df.loc[icao24, "manufacturername"]
        model = df.loc[icao24, "model"]
    except KeyError:
        operator, manufacturername, model = "", "", ""

    return operator, manufacturername, model

def get_image_url(aircraft_model: str) -> str:
    from bs4 import BeautifulSoup
    
    url = f"https://flightaware.com/photos/description/{aircraft_model}"
    url = url.replace(" ", "%20")

    response = requests.get(url)

    html = response.text
    soup = BeautifulSoup(html, features="lxml")

    image_url = soup.find("img", {"class": "thumbnail_nav"})["src"]

    return image_url


# JavaScript
point_to_layer = assign("""
    function(feature, latlng, context) {
        var marker_ = L.icon({
            iconUrl: "assets/airplane-4-32.png",
        });
        var true_track = feature.properties.true_track;
        return L.marker(latlng, { icon: marker_, rotationAngle: true_track });
    }
""")

cluster_to_layer = assign("""
    function(feature, latlng, context) {
        const count = feature.properties.point_count;
        const size =
            count <= 5 ? 'small' :
            count > 5 && count < 10 ? 'medium' : 'large';
        const icon = L.divIcon({
            html: `<div><span>${ feature.properties.point_count_abbreviated }</span></div>`,
            className: `marker-cluster marker-cluster-${ size }`,
            iconSize: L.point(40, 40)
        });

        return L.marker(latlng, { icon });
    }
""")


app = Dash(
    external_stylesheets=["https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css", dbc.themes.BOOTSTRAP],
    prevent_initial_callbacks=True,
    meta_tags=[{'name': 'viewport',
        'content': 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no'
    }]
)

PLOTLY_LOGO = "https://openskynetwork.github.io/opensky-api/_static/radar_small.png"

url = 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png'
attribution = '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a>'

app.layout = html.Div(
    [
        dbc.Navbar(
            dbc.Container(
                [
                    html.A(
                        dbc.Row(
                            [
                                dbc.Col(html.Img(src=PLOTLY_LOGO, height="30px")),
                                dbc.Col(dbc.NavbarBrand("ADS-B Tracker", className="ms-2")),
                            ],
                            align="center",
                            className="g-0",
                        ),
                        href="#",
                        style={"textDecoration": "none"},
                    ),
                ]
            ),
            color="dark",
            dark=True,
        ),
        dl.Map(
            children=[
                dl.LocateControl(options={'locateOptions': {'enableHighAccuracy': False}}),
                dl.TileLayer(url=url, maxZoom=20, attribution=attribution),
                dl.GeoJSON(id="data",
                    options=dict(pointToLayer=point_to_layer),
                    cluster=True,
                    zoomToBoundsOnClick=True,
                    clusterToLayer=cluster_to_layer,
                    # children=[dl.Tooltip(id="tooltip")]
                ),
            ],
            center=(31, 121), zoom=5,
            preferCanvas=True,
            style={"width": "100%", "height": "100vh"},
            id="map",
        ), # 100vw, 100vh, 500px
        dcc.Interval(
            id="interval-component",
            interval=10*1000, # in milliseconds
            n_intervals=0
        ),
        dbc.Modal(
            id="modal-centered",
            centered=True,
            is_open=False,
        ),
    ]
)

@app.callback(
    Output("modal-centered", "children"),
    Output("modal-centered", "is_open"),
    [Input("data", "click_feature")], # hover_feature
)
def update_tooltip(feature):
    if feature is None:
        return ("", False)

    callsign = feature["properties"]["callsign"]

    true_track = feature["properties"]["true_track"]
    if not (isinstance(true_track, int) or isinstance(true_track, float)):
        true_track = "----"
    on_ground = feature["properties"]["on_ground"]
    if not isinstance(on_ground, bool):
        on_ground = "----"
    velocity = feature["properties"]["velocity"]
    if not (isinstance(velocity, int) or isinstance(velocity, float)):
        velocity = "----"
    vertical_rate = feature["properties"]["vertical_rate"]
    if not (isinstance(vertical_rate, int) or isinstance(vertical_rate, float)):
        vertical_rate = "----"
    geo_altitude = feature["properties"]["geo_altitude"]
    if not (isinstance(geo_altitude, int) or isinstance(geo_altitude, float)):
        geo_altitude = "----"
    squawk = feature["properties"]["squawk"]
    if squawk == None:
        squawk = "----" 
    
    return ([
        dbc.ModalHeader(
            dbc.ModalTitle(
                html.A(callsign, href=f"https://flightaware.com/live/flight/{callsign}", target="_blank"),
            ),
            close_button=True,
        ),
        dbc.ModalBody(
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.P(f"Heading: {true_track}°"),
                                html.P(f"Grounded: {on_ground}"),
                                html.P(f"Speed: {velocity} m/s"),
                                html.P(f"Vertical speed: {vertical_rate} m/s"),
                                html.P(f"Altitude: {geo_altitude} meters"),
                                html.P(f"Squawk code: {squawk}"),
                            ],
                            style={"whiteSpace": "pre-wrap", 'font-family': 'Courier, sans-serif'}
                        ),
                    ),
                    dbc.Col(
                        [
                            dbc.Row( (html.Img(src="https://via.placeholder.com/500x500?text=Image+coming+soon")) ), # height="200px"
                        ]
                    ),
                ], # className="g-0",
            ),
        )
    ], True)

@app.callback(
    Output("data", "data"),
    Input("map", "bounds"),
    Input("interval-component", "n_intervals"),
)
def log_bounds(bounds, n_intervals):
    states = get_states(bounds)
    geojson = dlx.dicts_to_geojson([{**state} for state in states]) # , **dict(tooltip = state["callsign"])
    return geojson

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", debug=True)