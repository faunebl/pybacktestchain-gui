# The code for the dashboard

from dash import dcc, html, dash_table, Dash
import plotly.express as px

app = Dash(name="Backtest GUI")



if __name__ == '__main__':
    app.run(debug=True)

