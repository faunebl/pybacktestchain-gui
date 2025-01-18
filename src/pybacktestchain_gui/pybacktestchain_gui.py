# The code for the dashboard

from dash import Dash, dcc, html, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import polars as pl
# import plotly.express as px

from utils import get_tickers
from strategies import DrawdownControlStrategy,MomentumBasedStrategy,MinimumVarianceStrategy,MaximumDiversificationStrategy,EqualRiskContributionStrategy


#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------
#                                           Importing Data
#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------

frame_universe = get_tickers()
list_universe = frame_universe.select('symbol').to_series().to_list()

#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------
#                                           Layout for GUI
#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------

app = Dash(name="Backtest GUI", external_stylesheets= [dbc.themes.FLATLY]) 

# NavBar : to navigate the gui  

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Page 1", href="#")),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("More pages", header=True),
                dbc.DropdownMenuItem("Page 2", href="#"),
                dbc.DropdownMenuItem("Page 3", href="#"),
            ],
            nav=True,
            in_navbar=True,
            label="More",
        ),
    ],
    brand="Backtesting Strategies",
    brand_href="#",
    color="primary",
    dark=True,
)

dropdown_stocks = dbc.Row(html.Div(
    [
        dbc.Label("Manually Pick Stocks", html_for="dropdown"),
        dcc.Dropdown(
            id="dropdown-stocks",
            options=list_universe,
            multi=True,
            searchable=True
        ),
    ],
    className="mb-3",
), className="mb-3")

dropdown_countries = dbc.Row(html.Div(
    [
        dbc.Label("Manually Pick Countries", html_for="dropdown"),
        dcc.Dropdown(
            id="dropdown-countries",
            options=frame_universe.filter(~pl.col('country').eq("")).select('country').unique().to_series().to_list(),
            multi=True,
            searchable=True
        ),
    ],
    className="mb-3",
), className="mb-3")

dropdown_sectors = dbc.Row(html.Div(
    [
        dbc.Label("Manually Pick Sectors", html_for="dropdown"),
        dcc.Dropdown(
            id="dropdown-sectors",
            options=frame_universe.filter(~pl.col('country').eq("")).select('sector').drop_nulls().unique().to_series().to_list(),
            multi=True,
            searchable=True
        ),
    ],
    className="mb-3",
), className="mb-3")

dropdown_strats = dbc.Row(html.Div(
    [
        dbc.Label("Select Strategy", html_for="dropdown"),
        dcc.Dropdown(
            id="dropdown-strat",
            options=[
                "DrawdownControlStrategy",
                "MomentumBasedStrategy",
                "MinimumVarianceStrategy",
                "MaximumDiversificationStrategy",
                "EqualRiskContributionStrategy"
            ],
            multi=False,
            searchable=True
        ),
    ],
    className="mb-3",
), className="mb-3")

radios_input = dbc.Row(
    [
        dbc.Label("Select tickers to include in the portfolio", html_for="radios-stock-pick", width=2),
        dbc.Col(
            dbc.RadioItems(
                id="radios-stock-pick",
                options=[
                    {"label": "Select Stocks", "value": 1},
                    {"label": "Select Sectors", "value": 2},
                    {"label": "Select Countries", "value": 3},
                    {"label": "Select Defaults", "value": 4},
                ],
            ),
            width=10,
        ),
    ],
    className="mb-3",
)

form = dbc.Form([radios_input, dropdown_stocks, dropdown_sectors, dropdown_countries, dropdown_strats])


collapse = html.Div(
    [
        html.Br(), 
        dbc.Button(
            "Change Backtest Parameters",
            id="collapse-button",
            className="mb-3",
            color="primary",
            n_clicks=0,
            style={"margin-left": "15px"}
        ),
        dbc.Collapse(
            dbc.Card(dbc.CardBody(children=[ html.H3("Parameters for Backtest"), form]), style={"margin-left": "15px", "margin-right": "15px"}),
            id="collapse",
            is_open=False,
        ),
    ]
)

# button to run backtest 
button_backtest = html.Div(
    [
        html.Br(), 
        dbc.Button(
            "Run Backtest",
            id="backtest-button",
            className="mb-3",
            color="danger",
            n_clicks=0,
            style={"margin-left": "15px"}
        ) 
    ]
)

output = html.Div(
    [
        html.Br(),
        html.H5('Results Not computed')
    ]
)

#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------
#                                           Callbacks for GUI
#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------

# collapse for filters/params
@app.callback(
    Output("collapse", "is_open"),
    [Input("collapse-button", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

# select which type of stock pick
@app.callback(
    Output("dropdown-stocks", "disabled"),
    Output("dropdown-sectors", "disabled"),
    Output("dropdown-countries", "disabled"),
    [Input("radios-stock-pick", "value")],
)
def get_type_stock_pick(value):
    if value==1:
        return (False, True, True)
    elif value==2:
        return (True, False, True)
    elif value==3:
        return (True, True, False)
    else:
        return (True, True, True)

#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------
#                                               Running GUI
#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------

app.layout = (
    navbar,
    collapse,
    button_backtest,
    output
)

if __name__ == '__main__':
    app.run(debug=True)

