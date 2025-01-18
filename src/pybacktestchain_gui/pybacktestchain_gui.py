# The code for the dashboard

from dash import Dash, dcc, html, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import polars as pl
import plotly.express as px

from pybacktestchain.data_module import FirstTwoMoments
from pybacktestchain.broker import Backtest, StopLoss
from pybacktestchain.blockchain import load_blockchain
from datetime import datetime


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
                "EqualRiskContributionStrategy",
                "FirstTwoMoments"
            ],
            multi=False,
            searchable=True,
            value= "FirstTwoMoments"
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

collapse_graphs = html.Div(
    [
        html.Br(), 
        dbc.Button(
            "Show Graphs",
            id="collapse-button-graphs",
            className="mb-3",
            color="primary",
            n_clicks=0,
            style={"margin-left": "15px"}
        ),
        dbc.Collapse(
            dbc.Card(
                dbc.CardBody(
                    children=[ 
                        html.H3("Results"),
                        dcc.Graph(id='graph-sectors'),
                        dcc.Graph(id='graph-countries'),
                        dcc.Graph(id='graph-stocks'),
                        dcc.Graph(id='graph-cash')
                        ]
                ), 
                style={"margin-left": "15px", "margin-right": "15px"}),
            id="collapse-graphs",
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
    id = 'output',
    children= [
        html.Br(),
        dash_table.DataTable(
            data=[], 
            columns=[
                {"name" : "Date", 'id': "Date"}, 
                {"name" : "Action", 'id': "Action"}, 
                {"name" : "Ticker", 'id': "Ticker"}, 
                {"name" : "Quantity", 'id': "Quantity"}, 
                {"name" : "Price", 'id': "Price"}, 
                {"name" : "Cash", 'id': "Cash"}, 
            ], 
            id='results-backtest',
            style_as_list_view = True,
            style_header={'background-color':'powderblue', 'text-align':'center'}
        )
    ],
    style={"margin-left": "15px", "margin-right": "15px"}
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


# collapse for graphs
@app.callback(
    Output("collapse-graphs", "is_open"),
    [Input("collapse-button-graphs", "n_clicks")],
    [State("collapse-graphs", "is_open")],
)
def toggle_collapse_graphs(n, is_open):
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
    
# run backtest 
@app.callback(
    Output('results-backtest',"data"),
    Output('graph-sectors', 'figure'),
    Output('graph-countries', 'figure'),
    Output('graph-stocks', 'figure'),
    Output('graph-cash', 'figure'),
    Input('backtest-button', 'n_clicks'),
    State('dropdown-stocks', 'value'),
    State('dropdown-sectors', 'value'),
    State('dropdown-countries', 'value'),
    State('dropdown-strat', 'value'),
    State('radios-stock-pick', 'value'),
    prevent_initial_call=True
)
def run_backtest(n_clicks, stocks, sectors, countries, strat, type_select):
    if type_select==1: #stocks
        selected_stocks = stocks
    elif type_select==2: #sectors
        selected_stocks = frame_universe.filter(pl.col('sector').is_in(sectors)).select('symbol').to_series().to_list()
    elif type_select==3: #countries
        selected_stocks = frame_universe.filter(pl.col('country').is_in(countries)).select('symbol').to_series().to_list()
    else:
        selected_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'INTC', 'CSCO', 'NFLX']
    
    if strat=="DrawdownControlStrategy":
        selected_strat = DrawdownControlStrategy
    elif strat=="MomentumBasedStrategy":
        selected_strat = MomentumBasedStrategy
    elif strat=="MinimumVarianceStrategy":
        selected_strat = MinimumVarianceStrategy
    elif strat=="MaximumDiversificationStrategy":
        selected_strat = MaximumDiversificationStrategy
    elif strat=="EqualRiskContributionStrategy":
        selected_strat = EqualRiskContributionStrategy
    else:
        selected_strat = FirstTwoMoments
    

    verbose = False  # Set to True to enable logging, or False to suppress it

    backtest = Backtest(
        initial_date=datetime(2019, 1, 1),
        final_date=datetime(2020, 1, 1),
        information_class=selected_strat,
        risk_model=StopLoss,
        name_blockchain='backtest',
        verbose=verbose,
    )

    backtest.broker.positions = {}

    backtest.universe = selected_stocks

    backtest.run_backtest()

    block_chain = load_blockchain('backtest')

    results = pl.DataFrame(backtest.broker.get_transaction_log())

    results_joined = results.join(frame_universe.select(pl.exclude('symbol'), pl.col('symbol').alias('Ticker')), on='Ticker')

    return (
        results.to_dicts(),
        px.pie(results_joined.select('country', 'Quantity').group_by('country').sum().to_pandas(), values = 'Quantity', names='country'),
        px.pie(results_joined.select('sector', 'Quantity').group_by('sector').sum().to_pandas(), values = 'Quantity', names='sector'), 
        px.bar(results.sort('Date').select('Ticker', 'Quantity').group_by('Ticker').sum().to_pandas().set_index('Ticker')), #stocks
        px.scatter(results.sort(by='Date').group_by('Date').last().select('Date', 'Cash').to_pandas().set_index('Date')) #cash
    )

#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------
#                                               Running GUI
#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------

app.layout = (
    navbar,
    collapse,
    button_backtest,
    collapse_graphs,
    output
)

if __name__ == '__main__':
    app.run(debug=True)

