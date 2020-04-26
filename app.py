import dash
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

import chart_studio.plotly as py
import plotly.graph_objects as go
import plotly.figure_factory as FF

import numpy as np
import numpy_financial as npf
import pandas as pd
import cufflinks as cf

import requests, base64
import datetime
from io import BytesIO
from collections import Counter
import random, os

PLOTLY_LOGO = "./static/—Pngtree—orange juice glass vector_3546792.png"

app = dash.Dash(external_stylesheets=[dbc.themes.YETI])
server = app.server
# try running the app with one of the Bootswatch themes e.g.
# app = dash.Dash(external_stylesheets=[dbc.themes.JOURNAL])
# app = dash.Dash(external_stylesheets=[dbc.themes.SKETCHY])
app.config.suppress_callback_exceptions = True

"""Navbar"""
# make a reuseable navitem for the different examples
nav_item = dbc.NavItem(dbc.NavLink("", href="#"))
# make a reuseable dropdown for the different examples
dropdown = dbc.DropdownMenu(
    children=[
        dbc.DropdownMenuItem("Forum Juice", href='#'),
        dbc.DropdownMenuItem("נתונים וריביות", href='https://www.boi.org.il/he/BankingSupervision/Data/Pages/Default.aspx'),
        dbc.DropdownMenuItem("מערכת נתוני אשראי", href='https://www.creditdata.org.il/'),
        # dbc.DropdownMenuItem(divider=True),
        # dbc.DropdownMenuItem("", href=''),
        # dbc.DropdownMenuItem("", href=''),
    ],
    nav=True,
    in_navbar=True,
    label="קישורים שימושים",
)

# Navbar Layout
navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=PLOTLY_LOGO, height="30px")),
                        dbc.Col(dbc.NavbarBrand("Juice", className="ml-2")),
                    ],
                    align="center",
                    no_gutters=True,
                ),
                href="#",
            ),
            dbc.NavbarToggler(id="navbar-toggler2"),
            dbc.Collapse(
                dbc.Nav(
                    [nav_item,
                     dropdown,
                     ], className="ml-auto", navbar=True
                ),
                id="navbar-collapse2",
                navbar=True,
            ),
        ]
    ),
    color="info",
    dark=True,
    className="mb-5",
)
###############################################################################
"""Apps"""
# DataFrame for all loans
mortgage_df = pd.DataFrame()

months_heb = "חודש"
pmt_heb = "החזר חודשי"
ppmt_heb = "תשלום קרן"
ipmt_heb = "תשלום ריבית"

def generate_pd_per_maslul(cpi, amount, i, per):
        inflation = 1.48953 * len(cpi)             #  1.48953 due to Bank Leumi
        minf = (1 + inflation/1200)
        interest_rate = i/1200
        mortgage_amount = amount
        n_periods = per
        periods = np.arange(n_periods) + 1
        pmt_nominal = round(npf.pmt(interest_rate, n_periods, -mortgage_amount), 2)
        ipmt_nominal = npf.ipmt(interest_rate, periods, n_periods, -mortgage_amount)
        total_ipmt_nominal = round(np.ndarray.sum(ipmt_nominal))
        #   Inflation list (CPI)
        inf = list((1 + inflation/1200) ** y for y in range(1, n_periods + 1))
        ipmt_cpi = ipmt_nominal * inf
        #   payment against loan principal.
        ppmt_nominal = npf.ppmt(interest_rate, periods, n_periods, -mortgage_amount)
        ppmt_cpi = ppmt_nominal * inf
        pmt = ppmt_cpi + ipmt_cpi
        start = mortgage_amount * minf
        balance = list()
        for i in range(len(ppmt_cpi)):
            balance.append((start-ppmt_cpi[i])*minf)
            start = (start-ppmt_cpi[i])*minf
        balance = np.array(balance)
        maslul_df = pd.DataFrame({months_heb: periods, ppmt_heb: ppmt_cpi, ipmt_heb: ipmt_cpi, pmt_heb: pmt, "יתרה": balance})
        return maslul_df, total_ipmt_nominal

# Loan Apps
maslulOne = html.Div([
    html.P('במידה והמסלול צמוד הפעל כפתור'),
    dbc.Row(
        [   dbc.Col(dbc.Checklist(options=[{"label": "צמוד למדד", "value": 1}], value=[], id="switch1", switch=True)),
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("₪", addon_type="prepend"),
                                    dbc.Input(id="amount1", placeholder="סכום ההלוואה", type="number", max=10000000, min=1000, style={'textAlign':'center'})
                                ], size="sm", className="sm"))
        ], style={'margin': 'auto', 'width': '100%'}),
    html.Br(),
    dbc.Row(
        [
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("%", addon_type="prepend"),
                                    dbc.Input(id="interest1", placeholder="ריבית שנתית", type="number", max=10, min=0, step=0.01, style={'textAlign':'center'})
                                ], size="sm", className="sm")),
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("חודשים", addon_type="prepend"),
                                    dbc.Input(id="period1", placeholder="תקופת ההלוואה", type="number", max=360, min=12, style={'textAlign':'center'})
                                ], size="sm", className="sm"))
        ], style={'margin': 'auto', 'width': '100%'}),
    html.Br(),
    dbc.Row(dbc.Input(id="inputTitle1", placeholder="שם המסלול", type="text", style={'margin': 'auto', 'width': '88%', 'textAlign':'center'})),
    html.Br(),
    dbc.Row(html.P(id='pmt1', style={'margin': 'auto', 'width': '88%', 'textAlign':"center"})),
    dbc.Row(html.P(id='total_pmt1', style={'margin': 'auto', 'width': '88%', 'textAlign':"center"})),
    html.Br(),
    dbc.Row(dcc.Graph(id='output1', style={'margin': 'auto', 'width': '100%'}))
])

maslulTwo = html.Div([
    html.P('במידה והמסלול צמוד הפעל כפתור'),
    dbc.Row(
        [   dbc.Col(dbc.Checklist(options=[{"label": "צמוד למדד", "value": 1}], value=[], id="switch2", switch=True)),
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("₪", addon_type="prepend"),
                                    dbc.Input(id="amount2", placeholder="סכום ההלוואה", type="number", max=10000000, min=1000, style={'textAlign':'center'})
                                ], size="sm", className="sm"))
        ], style={'margin': 'auto', 'width': '100%'}),
    html.Br(),
    dbc.Row(
        [
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("%", addon_type="prepend"),
                                    dbc.Input(id="interest2", placeholder="ריבית שנתית", type="number", max=10, min=0, step=0.01, style={'textAlign':'center'})
                                ], size="sm", className="sm")),
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("חודשים", addon_type="prepend"),
                                    dbc.Input(id="period2", placeholder="תקופת ההלוואה", type="number", max=360, min=12, style={'textAlign':'center'})
                                ], size="sm", className="sm"))
        ], style={'margin': 'auto', 'width': '100%'}),
    html.Br(),
    dbc.Row(dbc.Input(id="inputTitle2", placeholder="שם המסלול", type="text", style={'margin': 'auto', 'width': '88%', 'textAlign':'center'})),
    html.Br(),
    dbc.Row(html.P(id='pmt2', style={'margin': 'auto', 'width': '88%', 'textAlign':"center"})),
    dbc.Row(html.P(id='total_pmt2', style={'margin': 'auto', 'width': '88%', 'textAlign':"center"})),
    html.Br(),
    dbc.Row(dcc.Graph(id='output2', style={'margin': 'auto', 'width': '100%'}))
])

maslulThree = html.Div([
    html.P('במידה והמסלול צמוד הפעל כפתור'),
    dbc.Row(
        [   dbc.Col(dbc.Checklist(options=[{"label": "צמוד למדד", "value": 1}], value=[], id="switch3", switch=True)),
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("₪", addon_type="prepend"),
                                    dbc.Input(id="amount3", placeholder="סכום ההלוואה", type="number", max=10000000, min=1000, style={'textAlign':'center'})
                                ], size="sm", className="sm"))
        ], style={'margin': 'auto', 'width': '100%'}),
    html.Br(),
    dbc.Row(
        [
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("%", addon_type="prepend"),
                                    dbc.Input(id="interest3", placeholder="ריבית שנתית", type="number", max=10, min=0, step=0.01, style={'textAlign':'center'})
                                ], size="sm", className="sm")),
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("חודשים", addon_type="prepend"),
                                    dbc.Input(id="period3", placeholder="תקופת ההלוואה", type="number", max=360, min=12, style={'textAlign':'center'})
                                ], size="sm", className="sm"))
        ], style={'margin': 'auto', 'width': '100%'}),
    html.Br(),
    dbc.Row(dbc.Input(id="inputTitle3", placeholder="שם המסלול", type="text", style={'margin': 'auto', 'width': '88%', 'textAlign':'center'})),
    html.Br(),
    dbc.Row(html.P(id='pmt3', style={'margin': 'auto', 'width': '88%', 'textAlign':"center"})),
    dbc.Row(html.P(id='total_pmt3', style={'margin': 'auto', 'width': '88%', 'textAlign':"center"})),
    html.Br(),
    dbc.Row(dcc.Graph(id='output3', style={'margin': 'auto', 'width': '100%'}))
])

maslulFour = html.Div([
    html.P('במידה והמסלול צמוד הפעל כפתור'),
    dbc.Row(
        [   dbc.Col(dbc.Checklist(options=[{"label": "צמוד למדד", "value": 1}], value=[], id="switch4", switch=True)),
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("₪", addon_type="prepend"),
                                    dbc.Input(id="amount4", placeholder="סכום ההלוואה", type="number", max=10000000, min=1000, style={'textAlign':'center'})
                                ], size="sm", className="sm"))
        ], style={'margin': 'auto', 'width': '100%'}),
    html.Br(),
    dbc.Row(
        [
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("%", addon_type="prepend"),
                                    dbc.Input(id="interest4", placeholder="ריבית שנתית", type="number", max=10, min=0, step=0.01, style={'textAlign':'center'})
                                ], size="sm", className="sm")),
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("חודשים", addon_type="prepend"),
                                    dbc.Input(id="period4", placeholder="תקופת ההלוואה", type="number", max=360, min=12, style={'textAlign':'center'})
                                ], size="sm", className="sm"))
        ], style={'margin': 'auto', 'width': '100%'}),
    html.Br(),
    dbc.Row(dbc.Input(id="inputTitle4", placeholder="שם המסלול", type="text", style={'margin': 'auto', 'width': '88%', 'textAlign':'center'})),
    html.Br(),
    dbc.Row(html.P(id='pmt4', style={'margin': 'auto', 'width': '88%', 'textAlign':"center"})),
    dbc.Row(html.P(id='total_pmt4', style={'margin': 'auto', 'width': '88%', 'textAlign':"center"})),
    html.Br(),
    dbc.Row(dcc.Graph(id='output4', style={'margin': 'auto', 'width': '100%'}))
])

maslulFive = html.Div([
    html.P('במידה והמסלול צמוד הפעל כפתור'),
    dbc.Row(
        [   dbc.Col(dbc.Checklist(options=[{"label": "צמוד למדד", "value": 1}], value=[], id="switch5", switch=True)),
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("₪", addon_type="prepend"),
                                    dbc.Input(id="amount5", placeholder="סכום ההלוואה", type="number", max=10000000, min=1000, style={'textAlign':'center'})
                                ], size="sm", className="sm"))
        ], style={'margin': 'auto', 'width': '100%'}),
    html.Br(),
    dbc.Row(
        [
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("%", addon_type="prepend"),
                                    dbc.Input(id="interest5", placeholder="ריבית שנתית", type="number", max=10, min=0, step=0.01, style={'textAlign':'center'})
                                ], size="sm", className="sm")),
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("חודשים", addon_type="prepend"),
                                    dbc.Input(id="period5", placeholder="תקופת ההלוואה", type="number", max=360, min=12, style={'textAlign':'center'})
                                ], size="sm", className="sm"))
        ], style={'margin': 'auto', 'width': '100%'}),
    html.Br(),
    dbc.Row(dbc.Input(id="inputTitle5", placeholder="שם המסלול", type="text", style={'margin': 'auto', 'width': '88%', 'textAlign':'center'})),
    html.Br(),
    dbc.Row(html.P(id='pmt5', style={'margin': 'auto', 'width': '88%', 'textAlign':"center"})),
    dbc.Row(html.P(id='total_pmt5', style={'margin': 'auto', 'width': '88%', 'textAlign':"center"})),
    html.Br(),
    dbc.Row(dcc.Graph(id='output5', style={'margin': 'auto', 'width': '100%'}))
])

maslulSix = html.Div([
    html.P('במידה והמסלול צמוד הפעל כפתור'),
    dbc.Row(
        [   dbc.Col(dbc.Checklist(options=[{"label": "צמוד למדד", "value": 1}], value=[], id="switch6", switch=True)),
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("₪", addon_type="prepend"),
                                    dbc.Input(id="amount6", placeholder="סכום ההלוואה", type="number", max=10000000, min=1000, style={'textAlign':'center'})
                                ], size="sm", className="sm"))
        ], style={'margin': 'auto', 'width': '100%'}),
    html.Br(),
    dbc.Row(
        [
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("%", addon_type="prepend"),
                                    dbc.Input(id="interest6", placeholder="ריבית שנתית", type="number", max=10, min=0, step=0.01, style={'textAlign':'center'})
                                ], size="sm", className="sm")),
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("חודשים", addon_type="prepend"),
                                    dbc.Input(id="period6", placeholder="תקופת ההלוואה", type="number", max=360, min=12, style={'textAlign':'center'})
                                ], size="sm", className="sm"))
        ], style={'margin': 'auto', 'width': '100%'}),
    html.Br(),
    dbc.Row(dbc.Input(id="inputTitle6", placeholder="שם המסלול", type="text", style={'margin': 'auto', 'width': '88%', 'textAlign':'center'})),
    html.Br(),
    dbc.Row(html.P(id='pmt6', style={'margin': 'auto', 'width': '88%', 'textAlign':"center"})),
    dbc.Row(html.P(id='total_pmt6', style={'margin': 'auto', 'width': '88%', 'textAlign':"center"})),
    html.Br(),
    dbc.Row(dcc.Graph(id='output6', style={'margin': 'auto', 'width': '100%'}))
])

###############################################################################
"""Body Components"""
# Cards for loans
path="./static/img/"

cardmaslulOne = dbc.Card(
    [
        dbc.CardImg(src=("/static/img/" + random.choice([x for x in os.listdir(path) if os.path.isfile(os.path.join(path, x))])), top=True),
        dbc.CardBody(
            [
                html.H3(id='cardTitle1', className="card-title", style={'textAlign':"center"}),
                html.P("",
                    className="card-text",
                ),
                dbc.Button("פתח", id="openmaslul1", outline=True, color="info", size="sm"),
                dbc.Modal(
                    [
                        dbc.ModalHeader(),
                        dbc.ModalBody(maslulOne),
                        dbc.ModalFooter(dbc.Button("סגור", id="closemaslul1", outline=True, color="info", size="sm"))
                    ],
                    id="modalmaslul1",
                ),
            ]
        ),
    ],
    style={"width": "10rem"},
)

cardmaslulTwo = dbc.Card(
    [
        dbc.CardImg(src=("/static/img/" + random.choice([x for x in os.listdir(path) if os.path.isfile(os.path.join(path, x))])), top=True),
        dbc.CardBody(
            [
                html.H3(id='cardTitle2', className="card-title", style={'textAlign':"center"}),
                html.P("",
                    className="card-text",
                ),
                dbc.Button("פתח", id="openmaslul2", outline=True, color="info", size="sm"),
                dbc.Modal(
                    [
                        dbc.ModalHeader(),
                        dbc.ModalBody(maslulTwo),
                        dbc.ModalFooter(dbc.Button("סגור", id="closemaslul2", outline=True, color="info", size="sm"))
                    ],
                    id="modalmaslul2",
                ),
            ]
        ),
    ],
    style={"width": "10rem"},
)

cardmaslulThree = dbc.Card(
    [
        dbc.CardImg(src=("/static/img/" + random.choice([x for x in os.listdir(path) if os.path.isfile(os.path.join(path, x))])), top=True),
        dbc.CardBody(
            [
                html.H3(id='cardTitle3', className="card-title", style={'textAlign':"center"}),
                html.P("",
                    className="card-text",
                ),
                dbc.Button("פתח", id="openmaslul3", outline=True, color="info", size="sm"),
                dbc.Modal(
                    [
                        dbc.ModalHeader(),
                        dbc.ModalBody(maslulThree),
                        dbc.ModalFooter(dbc.Button("סגור", id="closemaslul3", outline=True, color="info", size="sm"))
                    ],
                    id="modalmaslul3",
                ),
            ]
        ),
    ],
    style={"width": "10rem"},
)

cardmaslulFour = dbc.Card(
    [
        dbc.CardImg(src=("/static/img/" + random.choice([x for x in os.listdir(path) if os.path.isfile(os.path.join(path, x))])), top=True),
        dbc.CardBody(
            [
                html.H3(id='cardTitle4', className="card-title", style={'textAlign':"center"}),
                html.P("",
                    className="card-text",
                ),
                dbc.Button("פתח", id="openmaslul4", outline=True, color="info", size="sm"),
                dbc.Modal(
                    [
                        dbc.ModalHeader(),
                        dbc.ModalBody(maslulFour),
                        dbc.ModalFooter(dbc.Button("סגור", id="closemaslul4", outline=True, color="info", size="sm"))
                    ],
                    id="modalmaslul4",
                ),
            ]
        ),
    ],
    style={"width": "10rem"},
)

cardmaslulFive = dbc.Card(
    [
        dbc.CardImg(src=("/static/img/" + random.choice([x for x in os.listdir(path) if os.path.isfile(os.path.join(path, x))])), top=True),
        dbc.CardBody(
            [
                html.H3(id='cardTitle5', className="card-title", style={'textAlign':"center"}),
                html.P("",
                    className="card-text",
                ),
                dbc.Button("פתח", id="openmaslul5", outline=True, color="info", size="sm"),
                dbc.Modal(
                    [
                        dbc.ModalHeader(),
                        dbc.ModalBody(maslulFive),
                        dbc.ModalFooter(dbc.Button("סגור", id="closemaslul5", outline=True, color="info", size="sm"))
                    ],
                    id="modalmaslul5",
                ),
            ]
        ),
    ],
    style={"width": "10rem"},
)

cardmaslulSix = dbc.Card(
    [
        dbc.CardImg(src=("/static/img/" + random.choice([x for x in os.listdir(path) if os.path.isfile(os.path.join(path, x))])), top=True),
        dbc.CardBody(
            [
                html.H3(id='cardTitle6', className="card-title", style={'textAlign':"center"}),
                html.P("",
                    className="card-text",
                ),
                dbc.Button("פתח", id="openmaslul6", outline=True, color="info", size="sm"),
                dbc.Modal(
                    [
                        dbc.ModalHeader(),
                        dbc.ModalBody(maslulSix),
                        dbc.ModalFooter(dbc.Button("סגור", id="closemaslul6", outline=True, color="info", size="sm"))
                    ],
                    id="modalmaslul6",
                ),
            ]
        ),
    ],
    style={"width": "10rem"},
)

head_card = [
    dbc.CardBody(
        [
            html.H5("?לקחת משכנתא או לתכנן", className="card-title", style={'textAlign':'center'}),
            html.Br(),
            html.P("""
בשעה טובה הגיע זמנכם לרכוש את הבית! כבר התחלתם לעשות בירורים על המשכנתא ואתם לקראת ההחלטה הכי גורלית בחייכם.
אז לפני שאתם מחליטים לסגור עם אחד הבנקים תחשבו האם ההלוואה מתאימה לצרכים שלכם:  האם גובה החזר תואם לרמת ההשתכרות או לחלופין
האם ניתן לקצר תקופת ההלוואה ולהמנע מתשלומי ריבית והצמדה מיותרים? האם הכנסותכם צפויות לעלות? האם אתם מתכוונים לסלק חלק מההלוואה בשנים הקרובות? קרן השתלמות בדרך להיפתח? וכו וכו
""", className="card-text", style={'textAlign':'right'}),
            html.P("""כשאתם באים להשוות תמהילים שונים - הריבית הנמוכה ביותר לא תמיד תצביע על ההלוואה הטובה ביותר. תסתכלו על התפלגות התשלומים העתידיים
וכמה כסף תשלמו לבנק על כל שקל שתקחו - החזר לשקל זאת אינדיקציה טובה לטיב ההלוואה.
כמו כן נסו להימנע ככל האפשר מלקיחת מסלולים צמודים למדד לתקופות ארוכות
""", className="card-text", style={'textAlign':'right'}),
            html.Hr(),
            html.P("""מצד ימין תוכלו למצוא כרטיסיות בהן ניתן להזין נתוני התמהיל ולבחון את ההלוואה ברזולוציית המסלול. בגוף העמוד יופיעו נתונים הכוללים של כל המשכנתא. במקרא התרשימים ניתן לבחור להצגה את הנתונים הרצוים, אתם יכולים לשמור את הגרפים או חלקים מהם (תשתמשו באפשרויות התרשימים)
            """, className="card-text", style={'textAlign':'right'}),
        ]
    ),
]
###############################################################################
"""Body"""
# rows
rows = html.Div(
    [
        dbc.Row(
            [
                        dbc.Col(dbc.Col(html.Img(src="/static/img/calc.png", style={'float': 'right', 'clear': 'right', 'margin-left': '19%', 'height': '50vh'}))),
                        dbc.Col(dbc.Col(dbc.Card(head_card, color="info", inverse=True)))
            ],
            style={'margin': 'auto', 'width': '90vw'}
),
        dbc.Row(
            [

                dbc.Col(dcc.Graph(id='df_total_output'), width={"size": 10, "height": "45%"}),
                dbc.Col([dbc.Row([html.Div(cardmaslulOne, style={"size": 1, "height": "45%", 'float': 'right', "margin": '2em auto'}), html.Div(cardmaslulTwo, style={"size": 1, "height": "45%", 'float': 'right', "margin": '2em auto'})])
                        ])
            ],
            style={'margin': 'auto', 'width': '80vw'}
),
        dbc.Row(
            [

                dbc.Col(dcc.Graph(id="df_sums"), width={"size": 6, "height": "20vh"}),
                dbc.Col(dbc.Table(id="df_sums_explain"), width={"size": 4, "height": "45%"}),
                dbc.Col([dbc.Row([html.Div(cardmaslulThree, style={"size": 1, "height": "45%", 'float': 'right', "margin": '2em auto'}), html.Div(cardmaslulFour, style={"size": 1, "height": "45%", 'float': 'right', "margin": '2em auto'})])
                        ])
            ],
            style={'margin': 'auto', 'width': '80vw'}
),
        dbc.Row(
            [

                dbc.Col(
                    [   dbc.Row(dbc.Container(dcc.RangeSlider(id='slider', min=0, max=360, value=[0, 8], marks={
                                                                                            0: {'label': '😄', 'style': {'color': '#77b0b1'}},
                                                                                            24: {'label': '🙂'},
                                                                                            60: {'label': '😯'},
                                                                                            120: {'label': '☹'},
                                                                                            180: {'label': '😣'},
                                                                                            240: {'label': '😰'},
                                                                                            300: {'label': '😱'},
                                                                                            360: {'label': 'שנים', 'style': {'color': '#f50'}}}))),
                html.Br(),
                dbc.Table(id='table')
                    ], width={"size": 10, "height": "45%"}),
                dbc.Col([dbc.Row([html.Div(cardmaslulFive, style={"size": 1, "height": "45%", 'float': 'right', "margin": '2em auto'}), html.Div(cardmaslulSix, style={"size": 1, "height": "45%", 'float': 'right', "margin": '2em auto'})])
                        ])
            ],
            style={'margin': 'auto', 'width': '80vw'}
),
        html.Br(),
        html.Br(),
        dbc.Alert('Proudly powered by HR', color="light")

    ]
)
###############################################################################

"""Layout"""

app.layout = html.Div(
    [navbar, rows]
)

###############################################################################
"""Apps Functions"""
# Loan callbacks

# Building data for all (loans) in one
@app.callback([ Output("df_total_output", "figure"), Output("df_sums", "figure"), Output("df_sums_explain", "children"), Output("table", "children")],
              [ Input('switch1', 'value'), Input('amount1', 'value'), Input('interest1', 'value'), Input('period1', 'value'),
                Input('switch2', 'value'), Input('amount2', 'value'), Input('interest2', 'value'), Input('period2', 'value'),
                Input('switch3', 'value'), Input('amount3', 'value'), Input('interest3', 'value'), Input('period3', 'value'),
                Input('switch4', 'value'), Input('amount4', 'value'), Input('interest4', 'value'), Input('period4', 'value'),
                Input('switch5', 'value'), Input('amount5', 'value'), Input('interest5', 'value'), Input('period5', 'value'),
                Input('switch6', 'value'), Input('amount6', 'value'), Input('interest6', 'value'), Input('period6', 'value'),
                Input('slider', 'value')
              ])
def display_value(cpi1, amount1, i1, per1, cpi2, amount2, i2, per2,
                    cpi3, amount3, i3, per3, cpi4, amount4, i4, per4,
                    cpi5, amount5, i5, per5, cpi6, amount6, i6, per6, slider_value):
    frames = []
    amount = 0
    total_ipmt_nominal = 0
    try:
        maslul1_df, total_ipmt_nominal = generate_pd_per_maslul(cpi1, amount1, i1, per1)
        frames.append(maslul1_df)
        amount += amount1
    except:
        pass

    try:
        maslul2_df, total_ipmt_nominal = generate_pd_per_maslul(cpi2, amount2, i2, per2)
        frames.append(maslul2_df)
        amount += amount2
    except:
        pass

    try:
        maslul3_df, total_ipmt_nominal = generate_pd_per_maslul(cpi3, amount3, i3, per3)
        frames.append(maslul3_df)
        amount += amount3
    except:
        pass

    try:
        maslul4_df, total_ipmt_nominal = generate_pd_per_maslul(cpi4, amount4, i4, per4)
        frames.append(maslul4_df)
        amount += amount4
    except:
        pass

    try:
        maslul5_df, total_ipmt_nominal = generate_pd_per_maslul(cpi5, amount5, i5, per5)
        frames.append(maslul5_df)
        amount += amount5
    except:
        pass

    try:
        maslul6_df, total_ipmt_nominal = generate_pd_per_maslul(cpi6, amount6, i6, per6)
        frames.append(maslul6_df)
        amount += amount6
    except:
        pass

    df_total = pd.DataFrame()
    for frame in sorted(frames, key=len, reverse=True):
        df_total = df_total.add(frame, fill_value=0)

    df_total = df_total.drop(columns=months_heb)
    df_total.insert(0, months_heb, range(1, len(df_total) + 1))
    total_ppmt = int(round(df_total[ppmt_heb].sum()))
    total_ipmt = int(round(df_total[ipmt_heb].sum()))
    total_pmt = int(round(df_total[pmt_heb].sum()))
    total_cpi = total_pmt - amount - total_ipmt_nominal
    max_pmt = round(pd.Series(df_total[pmt_heb]).max(), 2)
    # דוח יתרות
    table = dbc.Table.from_dataframe(round(df_total[slider_value[0]:slider_value[1]], 2), striped=True, bordered=True, responsive='sm', hover=True, style={'textAlign':'center'})
    # Summary table
    row1 = html.Tr([html.Td(format(amount, ',d')), html.Td("סך הלוואה")], style={"height": "20%"})
    row2 = html.Tr([html.Td(format(int(round(df_total[pmt_heb][0])), ',d')), html.Td("החזר ראשוני")])
    row3 = html.Tr([html.Td(round(total_pmt / amount, 2)), html.Td("החזר לשקל")])
    row4 = html.Tr([html.Td(format(int(total_pmt), ',d')), html.Td("סך החזרים עד סוף תקופה")])
    row5 = html.Tr([html.Td(format(int(total_ipmt_nominal), ',d')), html.Td("סך החזרי ריבית")])
    row6 = html.Tr([html.Td(format(int(total_cpi), ',d')), html.Td("סך החזרי הצמדה")])
    row7 = html.Tr([html.Td(format(int(max_pmt), ',d')), html.Td("החזר בשיא")])

    table_body = [html.Tbody([row1, row2, row7, row3, row4, row5, row6])]

    summary = dbc.Table(table_body, striped=True, bordered=True, responsive='sm', hover=True, style={'textAlign':'right'})

    '''גרף נתוני כל המשכנתא'''
    df_total.index += 1
    fig = df_total.iplot(asFigure=True)

    '''גרף סך החזרים'''
    labels = ["קרן", "ריבית", "הצמדה"]
    values = [amount, total_cpi, total_ipmt_nominal]
    fig_sums = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])

    return fig, fig_sums, summary, table


def loan_callback(i):
    @app.callback([Output("output{}".format(i), "figure"),
                Output('pmt{}'.format(i), 'children'),
                Output('total_pmt{}'.format(i), 'children')],
                [Input('switch{}'.format(i), 'value'),
                Input('amount{}'.format(i), 'value'),
                Input('interest{}'.format(i), 'value'),
                Input('period{}'.format(i), 'value')])
    def display_value(cpi, amount, i, per):
        maslul_df, total_ipmt_nominal = generate_pd_per_maslul(cpi, amount, i, per)
        df = maslul_df[[pmt_heb, ppmt_heb, ipmt_heb]]
        df.index += 1
        fig = df.iplot(asFigure=True)
        return fig, f"תשלום חודשי ראשוני:  {format(int(maslul_df[pmt_heb][0]), ',d')}" , f" החזר בסוף תקופה: {format(int(maslul_df[pmt_heb].sum()), ',d')}"

loan_callback(1)
loan_callback(2)
loan_callback(3)
loan_callback(4)
loan_callback(5)
loan_callback(6)

# Titles
@app.callback(Output("cardTitle1", "children"),
                [Input('inputTitle1', 'value')])
def name_maslul(v):
    return v


@app.callback(Output("cardTitle2", "children"),
                [Input('inputTitle2', 'value')])
def name_maslul(v):
    return v


@app.callback(Output("cardTitle3", "children"),
                [Input('inputTitle3', 'value')])
def name_maslul(v):
    return v


@app.callback(Output("cardTitle4", "children"),
                [Input('inputTitle4', 'value')])
def name_maslul(v):
    return v


@app.callback(Output("cardTitle5", "children"),
                [Input('inputTitle5', 'value')])
def name_maslul(v):
    return v


@app.callback(Output("cardTitle6", "children"),
                [Input('inputTitle6', 'value')])
def name_maslul(v):
    return v

# Callbacks for loan modals
@app.callback(
    Output("modalmaslul1", "is_open"),
    [Input("openmaslul1", "n_clicks"), Input("closemaslul1", "n_clicks")],
    [State("modalmaslul1", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(
    Output("modalmaslul2", "is_open"),
    [Input("openmaslul2", "n_clicks"), Input("closemaslul2", "n_clicks")],
    [State("modalmaslul2", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(
    Output("modalmaslul3", "is_open"),
    [Input("openmaslul3", "n_clicks"), Input("closemaslul3", "n_clicks")],
    [State("modalmaslul3", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(
    Output("modalmaslul4", "is_open"),
    [Input("openmaslul4", "n_clicks"), Input("closemaslul4", "n_clicks")],
    [State("modalmaslul4", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(
    Output("modalmaslul5", "is_open"),
    [Input("openmaslul5", "n_clicks"), Input("closemaslul5", "n_clicks")],
    [State("modalmaslul5", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(
    Output("modalmaslul6", "is_open"),
    [Input("openmaslul6", "n_clicks"), Input("closemaslul6", "n_clicks")],
    [State("modalmaslul6", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


# we use a callback to toggle the collapse on small screens
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


# the same function (toggle_navbar_collapse) is used in all three callbacks
for i in [2]:
    app.callback(
        Output(f"navbar-collapse{i}", "is_open"),
        [Input(f"navbar-toggler{i}", "n_clicks")],
        [State(f"navbar-collapse{i}", "is_open")],
    )(toggle_navbar_collapse)


if __name__ == "__main__":
    app.run_server(debug=False)