from threading import Thread

import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, callback, dcc, html  # callback_context

import adsb_tracker

LOGO = "assets/0.png"

app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css",
        dbc.icons.BOOTSTRAP,
    ],
    update_title=None,
    # title="Yurkov Sergey",
    # prevent_initial_callbacks=True,
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no",
        }
    ],
    suppress_callback_exceptions=True,
)

server = app.server

navbar = (
    dbc.Navbar(
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=LOGO, height="35px")),
                        dbc.Col(
                            dbc.NavbarBrand(
                                "",
                                className="ms-2",
                                id="nvb",
                            )
                        ),
                    ],
                    align="center",
                    className="g-0",
                ),
            ]
        ),
        color="dark",
        dark=True,
        className="fixed-top",
        style={
            "height": "53px",
            "border-bottom": "1px solid #0d6efd",
        },
        id="navbar",
    ),
)

content = html.Div(
    style={
        "margin-top": "var(--nav-height)",
    },
    id="content",
)

app.layout = html.Div([dcc.Location(id="url"), *navbar, content], id="layout")


def ping(hosts):
    # import platform
    # import subprocess

    import requests

    for host in hosts:
        # param = "-n" if platform.system().lower() == "windows" else "-c"
        # command = ["ping", param, "1", host]
        # subprocess.call(command)

        try:
            requests.get(host, verify=False, timeout=1)
            # print(r.status_code)
        except requests.exceptions.ReadTimeout:
            print(f"{host} timed out!")

    print("Ping finished!")


def run_once(func):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return func(*args, **kwargs)

    wrapper.has_run = False
    return wrapper


@callback(
    Output("content", "children"),
    Output("nvb", "children"),
    Input("url", "pathname"),
)
def render_page_content(pathname):
    ping_worker()

    return (
        adsb_tracker.layout,
        adsb_tracker.TITLE,
    )


@run_once
def ping_worker():
    hosts = [
        "https://sy-apis.onrender.com/",
    ]
    thread = Thread(target=ping, args=(hosts,))
    thread.start()


if __name__ == "__main__":
    app.run_server(debug=True)  # host="0.0.0.0"
