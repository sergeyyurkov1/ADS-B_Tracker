import json
import os

import dash_bootstrap_components as dbc
import dash_leaflet as dl
import dash_leaflet.express as dlx
import requests
from dash import Input, Output, callback, callback_context, dcc, html
from dash_extensions.javascript import assign
from dotenv import load_dotenv

load_dotenv()

appid = os.environ["OW_API_KEY"]

TITLE = "ADS-B Tracker"


def get_states(bounds: list) -> list:
    bounds_ = eval(json.dumps(bounds))

    lamin = bounds_[0][0]
    lomin = bounds_[0][1]
    lamax = bounds_[1][0]
    lomax = bounds_[1][1]

    url = f"https://opensky-network.org/api/states/all?lamin={lamin}&lomin={lomin}&lamax={lamax}&lomax={lomax}"

    response = requests.get(url)

    print(response.status_code, response.headers)

    if response.status_code in (429, 503):
        with open("states.json", "r") as f:
            states = json.load(f)
    else:
        states = response.json()["states"]

    # with open("states.json", "w") as f:
    #     json.dump(states, f, indent=4)

    features = []
    try:
        for i in states:
            features.append(
                {
                    "lon": i[5],
                    "lat": i[6],
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
                }
            )
    except:
        pass

    return features[:200]


def get_aircraft_data(id: str) -> dict:
    import os

    API_KEY = os.environ["API_KEY"]

    url = f"https://sy-apis.onrender.com/aircraft-data/v1/flight/{id}"
    url = url.replace(" ", "%20")

    response = requests.get(url, headers={"Authorization": API_KEY})

    if response.status_code != 200:
        return False

    data = response.json()

    return data


# Dash-Leaflet JavaScript functions
point_to_layer = assign(
    """
    function(feature, latlng, context) {
        const marker_ = L.icon({
            iconUrl: 'assets/4.png',
        });
        const true_track = feature.properties.true_track;
        
        return L.marker(latlng, { icon: marker_, rotationAngle: true_track });
    }
"""
)
cluster_to_layer = assign(
    """
    function(feature, latlng, context) {
        const point_count = feature.properties.point_count;
        const size =
            point_count <= 5 ? 'small' :
            point_count > 5 && point_count <= 10 ? 'medium' : 'large';
        const icon = L.divIcon({
            html: `<div><span>${ feature.properties.point_count_abbreviated }</span></div>`,
            className: `marker-cluster marker-cluster-${ size }`,
            iconSize: L.point(40, 40)
        });

        return L.marker(latlng, { icon });
    }
"""
)


def generate_key():
    import uuid

    return str(uuid.uuid4())


url = "https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png"

attribution = 'Tiles from <a href="https://stadiamaps.com">Stadia Maps</a> | Data from <a href="https://openskynetwork.github.io/opensky-api/rest.html">OpenSky</a>, <a href="https://openweathermap.org/api/weathermaps">OpenWeather</a>, <a href="https://flightaware.com">FlightAware</a>'

layout = [
    dl.Map(
        children=[
            # dl.LocateControl(options={"locateOptions": {"enableHighAccuracy": False}}),
            dl.TileLayer(url=url, maxZoom=25, attribution=attribution),
            dl.GeoJSON(
                id="data",
                options=dict(pointToLayer=point_to_layer),
                cluster=True,
                zoomToBoundsOnClick=True,
                clusterToLayer=cluster_to_layer,
            ),
            dl.WMSTileLayer(
                url="https://tile.openweathermap.org/map/{layers}/{z}/{x}/{y}.png?appid="
                + appid,
                layers="None",  # precipitation_new
                format="image/png",
                transparent=True,
                updateInterval=10_000,
                extraProps={"key": generate_key()},
                id="layer1",
            ),
        ],
        center=(31, 121),
        zoom=5,
        preferCanvas=True,
        style={
            "width": "100%",
            # "height": "calc(100vh - 53px)",
            "height": "calc(var(--app-height) - var(--nav-height))",
        },
        id="map",
    ),
    dcc.Loading(
        html.Div(id="loading"),
        type="default",
        fullscreen=True,
        style={
            "z-index": "1000",
            "background-color": "rgba(0, 0, 0, 0.5)",
            "top": "calc(100% - var(--app-height))",
            "height": "var(--app-height)",
        },  # important
    ),
    dcc.Interval(
        id="interval",
        interval=300 * 1000,  # in milliseconds
        n_intervals=0,
    ),
    dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle("About"),
                close_button=True,
            ),
            dbc.ModalBody(
                dcc.Markdown(
                    """
                    **Automatic Dependent Surveillance Broadcast (ADS-B)** is a system by which an aircraft transmits it's flight data to be received by ground equipment and other aircraft in the area for better situational awareness and air traffic control in lieu of a traditional radar.

                    This project uses information from publicly available databases maintained by aviation enthusiasts around the world; coverage is partial as some areas either have restricted access to the data or don't have the necessary equipment to make such logging possible.
                    """
                ),
                style={
                    "font-family": "monospace, sans-serif",
                    "whiteSpace": "pre-wrap",
                },
            ),
        ],
        is_open=False,
        centered=True,
        id="info_modal",
    ),
    dbc.ButtonGroup(
        [
            dbc.Button("", className="me-1", id="info_button"),
            dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem(
                        "Precipitation", id="precipitation", n_clicks=0
                    ),
                    dbc.DropdownMenuItem("Wind speed", id="wind_speed", n_clicks=0),
                    dbc.DropdownMenuItem("Clouds", id="clouds", n_clicks=0),
                    dbc.DropdownMenuItem("None", id="none", n_clicks=0),
                ],
                label="Weather overlay",
                align_end=True,
                color="light",
                toggle_style={
                    "background": "transparent",
                    "color": "white",
                    "border": "none",
                },
            ),
        ],
        id="ddm",
    ),
]


@callback(
    Output("info_modal", "is_open"),
    Input("info_button", "n_clicks"),
)
def show_info(n):
    changed_id = [p["prop_id"] for p in callback_context.triggered][0]
    if "info_button" in changed_id:
        return True


@callback(
    Output("layer1", "layers"),
    Output("layer1", "extraProps"),
    Output("precipitation", "active"),
    Output("wind_speed", "active"),
    Output("clouds", "active"),
    Output("none", "active"),
    Input("precipitation", "n_clicks"),
    Input("wind_speed", "n_clicks"),
    Input("clouds", "n_clicks"),
    Input("none", "n_clicks"),
)
def set_overlay(n1, n2, n3, n4):
    changed_id = [p["prop_id"] for p in callback_context.triggered][0]
    if "precipitation" in changed_id:
        return "precipitation_new", {"key": generate_key()}, True, False, False, False
    elif "wind_speed" in changed_id:
        return "wind_new", {"key": generate_key()}, False, True, False, False
    elif "clouds" in changed_id:
        return "clouds_new", {"key": generate_key()}, False, False, True, False
    else:
        return "none", {"key": generate_key()}, False, False, False, True


@callback(
    Output("loading", "children"),
    Input("data", "click_feature"),  # alt: hover_feature
)
def update_tooltip(feature):
    if feature is None:
        return ""  # doesn't open the modal, fails silently

    callsign = feature["properties"]["callsign"]
    if callsign == "":
        callsign_element = "Callsign unknown"
    else:
        callsign_element = html.A(
            callsign,
            href=f"https://flightaware.com/live/flight/{callsign}",
            target="_blank",
        )

    true_track = feature["properties"]["true_track"]
    if not (isinstance(true_track, int) or isinstance(true_track, float)):
        true_track = "----"
    else:
        true_track = f"{round(true_track)}°"

    on_ground = feature["properties"]["on_ground"]
    if not isinstance(on_ground, bool):
        in_flight = "----"
    elif on_ground == True:
        in_flight = "No"
    else:
        in_flight = "Yes"

    velocity = feature["properties"]["velocity"]
    if not (isinstance(velocity, int) or isinstance(velocity, float)):
        velocity = "----"
    else:
        velocity = f"{round(velocity * 3.6):,} km/h"

    vertical_rate = feature["properties"]["vertical_rate"]
    if not (isinstance(vertical_rate, int) or isinstance(vertical_rate, float)):
        vertical_rate = "----"
    else:
        vertical_rate = f"{round(vertical_rate)} m/s"

    geo_altitude = feature["properties"]["geo_altitude"]
    if not (isinstance(geo_altitude, int) or isinstance(geo_altitude, float)):
        geo_altitude = "----"
    else:
        geo_altitude = f"{round(geo_altitude):,} meters"

    squawk = feature["properties"]["squawk"]
    if squawk == None:
        squawk = "----"

    aircraft_data = get_aircraft_data(callsign)
    if aircraft_data == False:
        airline = ""
        aircraft_type = ""
        image_url_1 = "assets/3.png"
    else:
        airline = aircraft_data["airline"]
        aircraft_type = aircraft_data["aircraft_type"]

        if len(aircraft_data["image_urls"]) == 0:
            image_url_1 = "assets/3.png"
        else:
            import random

            image_url_1 = random.choice(aircraft_data["image_urls"])

    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle(callsign_element),
                close_button=True,
            ),
            dbc.ModalBody(
                [
                    dbc.Row(
                        html.P(
                            f"{airline} {aircraft_type}".upper(),
                            style={"text-align": "center", "font-weight": "bold"},
                        ),
                        justify="center",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                html.Div(
                                    [
                                        html.P(f"In flight: {in_flight}".upper()),
                                        html.P(f"Altitude: {geo_altitude}".upper()),
                                        html.P(f"Heading: {true_track}".upper()),
                                        html.P(f"Speed: {velocity}".upper()),
                                        html.P(
                                            f"Vertical speed: {vertical_rate}".upper()
                                        ),
                                        html.P(f"Squawk code: {squawk}".upper()),
                                    ],
                                ),
                            ),
                            dbc.Col(
                                [
                                    dbc.Row(
                                        html.Img(src=image_url_1),
                                        justify="center",
                                        align="center",
                                    ),
                                ],
                                id="aircraft-image",
                            ),
                        ],
                    ),
                ],
                style={"font-family": "monospace, sans-serif"},
            ),
        ],
        is_open=True,
        centered=True,
    )


@callback(
    Output("data", "data"),
    Input("map", "bounds"),
    Input("interval", "n_intervals"),
)
def log_bounds(bounds, n_intervals):
    states = get_states(bounds)
    geojson = dlx.dicts_to_geojson([{**state} for state in states])
    return geojson
