from dash import Dash
from layout.layout import layout
from database import session
from models import Station

app = Dash(__name__)
app.layout = layout

if __name__ == '__main__':
    app.run(debug=True)
