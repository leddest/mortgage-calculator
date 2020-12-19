import os
import random

import cufflinks as cf
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import dash_html_components as html
from flask import Flask
import numpy as np
import numpy_financial as npf
import pandas as pd
from plotly.graph_objs.bar import Marker
import plotly.graph_objects as go

from scripts.declining_schedule import generate_pd_per_maslul_declining
from scripts.straight_schedule import generate_pd_per_maslul_straight
from scripts.bullet_schedule import generate_pd_per_maslul_bullet


server = Flask(__name__)

app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[dbc.themes.JOURNAL],
)

app.config.suppress_callback_exceptions = True
app.title = 'Mortgage Dashboard'

PLOTLY_LOGO = "./static/undraw_at_home_octe.svg"
# try running the app with one of the Bootswatch themes e.g.
# app = dash.Dash(external_stylesheets=[dbc.themes.JOURNAL])
# app = dash.Dash(external_stylesheets=[dbc.themes.SKETCHY])

"""Navbar"""
# make a reuseable navitem for the different examples
nav_item = dbc.NavItem(dbc.NavLink("", href="#"))
# make a reuseable dropdown for the different examples
dropdown = dbc.DropdownMenu(
    children=[
        dbc.DropdownMenuItem(
            "פורום משכנתאות",
            href='https://www.facebook.com/groups/mashkanta1/',
            style={"text-align": "right"}),
        dbc.DropdownMenuItem(
            "נתונים וריביות",
            href='https://www.boi.org.il/he/BankingSupervision/Data/Pages/Default.aspx',
            style={"text-align": "right"}),
        dbc.DropdownMenuItem(
            "מערכת נתוני אשראי",
            href='https://www.creditdata.org.il/',
            style={"text-align": "right"}),
        # dbc.DropdownMenuItem(divider=True),
        # dbc.DropdownMenuItem("", href=''),
        # dbc.DropdownMenuItem("", href=''),
    ],
    nav=True,
    in_navbar=True,
    label="קישורים שימושים"
)

# Navbar Layout
navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(
                            html.Img(src=PLOTLY_LOGO, height="30px")),
                        dbc.Col(
                            dbc.NavbarBrand(
                                "Mortgage Dashboard", className="ml-2")),
                    ],
                    align="center",
                    no_gutters=True,
                ),
                href="#",
            ),
            dbc.NavbarToggler(id="navbar-toggler2"),
            dbc.Collapse(
                dbc.Nav(
                    [
                        nav_item,
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


# Loan Apps
def gen_maslul(index):
    return html.Div([
        dbc.Row(
            dbc.Input(
                id=f"inputTitle{index}",
                placeholder="שם המסלול",
                type="text", maxLength="15",
                style={
                    'margin': 'auto', 'width': '88%', 'textAlign': 'center'})),
        html.Br(),
        dbc.Row(
        [
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("₪", addon_type="prepend"),
                                    dbc.Input(id=f"amount{index}", placeholder="סכום", type="number", max=10000000, min=1000, style={'textAlign':'center'})
                                ], size="sm", className="sm")),
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("%", addon_type="prepend"),
                                    dbc.Input(id=f"interest{index}", placeholder="ריבית", type="number", max=10, min=0, step=0.01, style={'textAlign':'center'})
                                ], size="sm", className="sm")),
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("חודשים", addon_type="prepend"),
                                    dbc.Input(id=f"period{index}", placeholder="תקופה", type="number", max=420, min=1, style={'textAlign':'center'})
                                ], size="sm", className="sm")),
        ], style={'margin': 'auto', 'width': '100%'}),
        html.Br(),
        html.Hr(),

        dbc.Row(
        [
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("%", addon_type="prepend"),
                                    dbc.Input(id=f"madad{index}", placeholder="מדד שנתי", type="number", value=1.48953, max=10, min=-2, step=0.00001, style={'textAlign':'center'}),
                                    dbc.InputGroupAddon("מדד שנתי משוער", addon_type="append"),
                                ], size="sm", className="sm", style={'margin': 'auto', 'width': '122%', 'textAlign':'left'},)),
            dbc.Col(dbc.Checklist(
                id=f"switch{index}", options=[{"label": "מסלול צמוד", "value": 1}], value=[1], switch=True, style={'margin': 'auto', 'width': '100%', 'textAlign':'right'}
            )),
        ], style={'margin': 'auto', 'width': '100%'}),
        html.Br(),

        dbc.Row(
        [
            dbc.Col(dbc.RadioItems(
                    options=[
                        {"label": "בוליט", "value": 'bullet'},
                        {"label": "קרן שווה", "value": 'declining'},
                        {"label": "שפיצר", "value": 'straight'},
                    ],
                    value='straight',
                    id=f"schedule{index}",
                    inline=True,
                    style={
                        'margin': 'auto',
                        'width': '140%',
                        'textAlign':'left'},
                    )
            ),
            dbc.Col(
                html.P(
                    'שיטת החזר (לוח)',
                    style={
                        'margin': 'auto',
                        'width': '100%',
                        'textAlign': 'right'})),
        ], style={'margin': 'auto', 'width': '100%'}),
        html.Hr(),

        dbc.Row(
            html.P(
                id=f'pmt{index}',
                style={
                    'margin': 'auto',
                    'width': '88%',
                    'textAlign': "center"})),
        dbc.Row(
            html.P(
                id=f'total_pmt{index}',
                style={
                    'margin': 'auto',
                    'width': '88%',
                    'textAlign': "center"})),
        dbc.Row(
            dcc.Graph(
                id=f'output{index}',
                style={
                    'margin': 'auto',
                    'width': '100%'}))
])


maslulOne = html.Div([
    dbc.Row(dbc.Input(id="inputTitle1", placeholder="שם המסלול", type="text", value="קבוע צמוד", maxLength="15", style={'margin': 'auto', 'width': '88%', 'textAlign': 'center'})),
    html.Br(),

    dbc.Row(
        [
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("₪", addon_type="prepend"),
                                    dbc.Input(id="amount1", placeholder="סכום", type="number", value=100000, max=10000000, min=1000, style={'textAlign':'center'})
                                ], size="sm", className="sm")),
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("%", addon_type="prepend"),
                                    dbc.Input(id="interest1", placeholder="ריבית", type="number", value=3, max=10, min=0, step=0.01, style={'textAlign':'center'})
                                ], size="sm", className="sm")),
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("חודשים", addon_type="prepend"),
                                    dbc.Input(id="period1", placeholder="תקופה", type="number", value=240, max=420, min=1, style={'textAlign':'center'})
                                ], size="sm", className="sm")),
        ], style={'margin': 'auto', 'width': '100%'}),
    html.Br(),
    html.Hr(),

    dbc.Row(
        [
            dbc.Col(dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("%", addon_type="prepend"),
                                    dbc.Input(id="madad1", placeholder="מדד שנתי", type="number", value=1.48953, max=10, min=-2, step=0.00001, style={'textAlign':'center'}),
                                    dbc.InputGroupAddon("מדד שנתי משוער", addon_type="append"),
                                ], size="sm", className="sm", style={'margin': 'auto', 'width': '122%', 'textAlign':'left'},)),
            dbc.Col(dbc.Checklist(
                id="switch1", options=[{"label": "מסלול צמוד", "value": 1}], value=[1], switch=True, style={'margin': 'auto', 'width': '100%', 'textAlign':'right'}
            )),
        ], style={'margin': 'auto', 'width': '100%'}),
    html.Br(),
    
    dbc.Row(
        [
            dbc.Col(dbc.RadioItems(
                    options=[
                        {"label": "בוליט", "value": 'bullet'},
                        {"label": "קרן שווה", "value": 'declining'},
                        {"label": "שפיצר", "value": 'straight'},
                    ],
                    value='straight',
                    id="schedule1",
                    inline=True,
                    style={'margin': 'auto', 'width': '140%', 'textAlign':'left'},
                    )
            ),
            dbc.Col(html.P('שיטת החזר (לוח)', style={'margin': 'auto', 'width': '100%', 'textAlign':'right'})),
        ], style={'margin': 'auto', 'width': '100%'}),
    html.Hr(),

    dbc.Row(html.P(id='pmt1', style={'margin': 'auto', 'width': '88%', 'textAlign':"center"})),
    dbc.Row(html.P(id='total_pmt1', style={'margin': 'auto', 'width': '88%', 'textAlign':"center"})),  
    dbc.Row(dcc.Graph(id='output1', style={'margin': 'auto', 'width': '100%'}))
])

maslulTwo = gen_maslul(2)
maslulThree = gen_maslul(3)
maslulFour = gen_maslul(4)
maslulFive = gen_maslul(5)
maslulSix = gen_maslul(6)


###############################################################################
"""Body Components"""

# Cards for loans
def gen_card_for_loan(index, maslul):
    path = "./static/img/"
    return dbc.Card(
    [
        dbc.CardImg(src=("/static/img/" + random.choice([x for x in os.listdir(path) if os.path.isfile(
            os.path.join(path, x))])), top=True, style={"height": "6rem", "width": "100%", "object-fit": "cover"}),
        dbc.CardBody(
            [
                dbc.Button(f"הזן מסלול {index}", id=f"openmaslul{index}",
                           outline=True, color="link", size="sm"),
                html.Hr(),
                html.H6(
                    id=f'cardTitle{index}', className="card-title text-primary", style={'textAlign': "right"}),
                html.H6(
                    id=f'cardSum{index}', className="card-title text-primary", style={'textAlign': "right"}),
                html.H6(
                    id=f'cardPeriod{index}', className="card-title text-primary", style={'textAlign': "right"}),
                html.H6(
                    id=f'cardInterest{index}', className="card-title text-primary", style={'textAlign': "right"}),
                dbc.Modal(
                    [
                        dbc.ModalHeader(),
                        dbc.ModalBody(maslul),
                        dbc.ModalFooter(dbc.Button("סגור", id=f"closemaslul{index}", outline=True, color="info", size="sm"))
                    ],
                    id=f"modalmaslul{index}",
                ),
            ]
        ),
    ],
        style={"width": "8rem", "height": "20rem", 'border': 'none'},
)


cardmaslulOne = gen_card_for_loan(1, maslulOne)
cardmaslulTwo = gen_card_for_loan(2, maslulTwo)
cardmaslulThree = gen_card_for_loan(3, maslulThree)
cardmaslulFour = gen_card_for_loan(4, maslulFour)
cardmaslulFive = gen_card_for_loan(5, maslulFive)
cardmaslulSix = gen_card_for_loan(6, maslulSix)

head_card = [
    dbc.CardBody(
        [
            html.H4("מחשבון משכנתא מתקדם", className="card-title", style={'textAlign':'center'}),
            html.Br(),
            html.P("""
            לפניכם כלי משוכלל לבניית דשבורד עוצמתי
            המאפשר לקבל את כל המידע על המשכנתא
            הן ברזולוציית המסלול והן ברמת התמהיל
            """, className="card-text", style={'textAlign':'right'}),
            html.P("""
            ויזואליזציה גרפית מתמקדת בייצוג נתונים מופשטים
            באופן אינטראקטיבי כדי לשפר את עיבוד המידע האנושי של המשתמש בנתונים
            """, className="card-text", style={'textAlign':'right'}),
            dbc.CardLink("Information visualization, wiki", href="https://en.wikipedia.org/wiki/Information_visualization")

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
                dbc.Col(dbc.Col(html.Img(src="/static/img/main.svg", style={'float': 'right', 'clear': 'right', 'margin-left':'15px', 'height': '40vh'}))),
                dbc.Col(
                    dbc.Col(dbc.Card(head_card, color="light", style={'border': 'none'}, className="bg-secondary")))
            ],
            style={'margin': 'auto', 'width': '80vw'}
),
        dbc.Row(html.Br()
),

        dbc.Row(html.Br()
),
        dbc.Row(
            [
                dbc.Col(
                            [
                                dbc.Row(
                                            [
                                                html.Div(cardmaslulSix, style={"size": 1, "height": "75%", 'float': 'right', "margin": '2em auto'}),
                                                html.Div(cardmaslulFive, style={"size": 1, "height": "75%", 'float': 'right', "margin": '2em auto'}),
                                                html.Div(cardmaslulFour, style={"size": 1, "height": "75%", 'float': 'right', "margin": '2em auto'}),
                                                html.Div(cardmaslulThree, style={"size": 1, "height": "75%", 'float': 'right', "margin": '2em auto'}),
                                                html.Div(cardmaslulTwo, style={"size": 1, "height": "75%", 'float': 'right', "margin": '2em auto'}),
                                                html.Div(cardmaslulOne, style={"size": 1, "height": "75%", 'float': 'right', "margin": '2em auto'}),
                                            ]
                                        )
                            ]
                        ),
            ],
            style={'margin': 'auto', 'width': '80vw'}
),
        dbc.Row(html.Br()
),
        dbc.Row(
            [

                dbc.Col(dcc.Graph(id='df_total_output'), width={"size": 8, "height": "20vh"}),
                dbc.Col(dbc.Table(id="df_sums_explain"), width={"size": 4, "height": "10vh" }),

            ],
            style={'margin': 'auto', 'width': '80vw'}
),
        dbc.Row(html.Br()
),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="df_payments"), width={"size": 7, "height": "20vh"}),
                dbc.Col(dcc.Graph(id="df_sums"), width={"size": 5, "height": "20vh"}),


            ],
            style={'margin': 'auto', 'width': '80vw'}
),
        dbc.Row(html.Br()
),
        dbc.Row(
            [

                dbc.Col(
                    [   dbc.Row(dbc.Container(dcc.RangeSlider(id='slider', min=0, max=360, value=[0, 8], marks={
                                                                                            0: {'label': '😄', 'style': {'color': '#77b0b1'}},
                                                                                            24: {'label': '24'},
                                                                                            60: {'label': '😯'},
                                                                                            120: {'label': '120'},
                                                                                            180: {'label': '😰'},
                                                                                            240: {'label': '240'},
                                                                                            300: {'label': '😱'},
                                                                                            360: {'label': '360', 'style': {'color': '#f50'}}}))),
                html.Br(),
                dbc.Table(id='table')
                    ], width={"size": 12, "height": "45%"}),

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
months_heb = "חודש"
pmt_heb = "החזר חודשי"
ppmt_heb = "תשלום קרן"
ipmt_heb = "תשלום ריבית"


def generate_pd_per_maslul(schedule, cpi, madad, amount, i, period):
    if schedule == 'straight':
        return generate_pd_per_maslul_straight(cpi, madad, amount, i, period)
    elif schedule == 'declining':
        return generate_pd_per_maslul_declining(cpi, madad, amount, i, period)
    return generate_pd_per_maslul_bullet(cpi, madad, amount, i, period)


# Building data for all (loans) in one. Brutallity callback.
@app.callback([ Output("df_total_output", "figure"), Output("df_sums", "figure"), Output("df_payments",
                "figure"), Output("df_sums_explain", "children"), Output("table", "children")
                ],
              [ Input('schedule1', 'value'), Input('switch1', 'value'), Input('madad1', 'value'),
                Input('amount1', 'value'), Input('interest1', 'value'), Input('period1', 'value'),
                Input('schedule2', 'value'), Input('switch2', 'value'), Input('madad2', 'value'),
                Input('amount2', 'value'), Input('interest2', 'value'), Input('period2', 'value'),
                Input('schedule3', 'value'), Input('switch3', 'value'), Input('madad3', 'value'),
                Input('amount3', 'value'), Input('interest3', 'value'), Input('period3', 'value'),
                Input('schedule4', 'value'), Input('switch4', 'value'), Input('madad4', 'value'),
                Input('amount4', 'value'), Input('interest4', 'value'), Input('period4', 'value'),
                Input('schedule5', 'value'), Input('switch5', 'value'), Input('madad5', 'value'),
                Input('amount5', 'value'), Input('interest5', 'value'), Input('period5', 'value'),
                Input('schedule6', 'value'), Input('switch6', 'value'), Input('madad6', 'value'),
                Input('amount6', 'value'), Input('interest6', 'value'), Input('period6', 'value'),
                Input('slider', 'value')
              ])
def display_value(schedule1, cpi1, inf1, amount1, i1, per1, schedule2,  cpi2, inf2, amount2, i2, per2,
                    schedule3, cpi3, inf3, amount3, i3, per3, schedule4,  cpi4, inf4, amount4, i4, per4,
                    schedule5, cpi5, inf5, amount5, i5, per5, schedule6,  cpi6, inf6, amount6, i6, per6, slider_value):
    frames = []
    amount = 0
    total_ipmt_nominal = 0

    try:
        maslul1_df, total_ipmt_nominal1 = generate_pd_per_maslul(schedule1, cpi1, inf1, amount1, i1, per1)
        frames.append(maslul1_df)
        total_ipmt_nominal += total_ipmt_nominal1
        amount += amount1
    except Exception:
        pass

    try:
        maslul2_df, total_ipmt_nominal2 = generate_pd_per_maslul(schedule2, cpi2, inf2, amount2, i2, per2)
        frames.append(maslul2_df)
        total_ipmt_nominal += total_ipmt_nominal2
        amount += amount2
    except Exception:
        pass

    try:
        maslul3_df, total_ipmt_nominal3 = generate_pd_per_maslul(schedule3, cpi3, inf3, amount3, i3, per3)
        frames.append(maslul3_df)
        total_ipmt_nominal += total_ipmt_nominal3
        amount += amount3
    except Exception:
        pass

    try:
        maslul4_df, total_ipmt_nominal4 = generate_pd_per_maslul(schedule4, cpi4, inf4, amount4, i4, per4)
        frames.append(maslul4_df)
        total_ipmt_nominal += total_ipmt_nominal4
        amount += amount4
    except Exception:
        pass

    try:
        maslul5_df, total_ipmt_nominal5 = generate_pd_per_maslul(schedule5, cpi5, inf5, amount5, i5, per5)
        frames.append(maslul5_df)
        total_ipmt_nominal += total_ipmt_nominal5
        amount += amount5
    except Exception:
        pass

    try:
        maslul6_df, total_ipmt_nominal6 = generate_pd_per_maslul(schedule6, cpi6, inf6, amount6, i6, per6)
        frames.append(maslul6_df)
        total_ipmt_nominal += total_ipmt_nominal6
        amount += amount6
    except Exception:
        pass

    df_total = pd.DataFrame()
    for frame in sorted(frames, key=len, reverse=True):
        df_total = df_total.add(frame, fill_value=0)

    df_total = df_total.drop(columns=months_heb)
    df_total.insert(0, months_heb, range(1, len(df_total) + 1))
    total_ppmt = df_total[ppmt_heb].sum()
    total_ipmt = df_total[ipmt_heb].sum()
    total_pmt = df_total[pmt_heb].sum()
    total_cpi = total_pmt - amount - total_ipmt_nominal
    if total_cpi <= 2:
        total_cpi = 0
    max_pmt = pd.Series(df_total[pmt_heb]).max()

    # דוח יתרות
    df_reversed = df_total[df_total.columns[::-1]]
    table = dbc.Table.from_dataframe(round(df_reversed[slider_value[0]:slider_value[1]], 2), striped=True, bordered=True, responsive='sm', hover=True, style={'textAlign':'center'})
    # Summary table

    row1 = html.Tr([html.Td(f'{round(amount, 1):,}'), html.Td("סך הלוואה")], style={"height": "20%"})
    row2 = html.Tr([html.Td(f'{round(df_total[pmt_heb][0], 1):,}'), html.Td("החזר ראשוני")])
    row3 = html.Tr([html.Td(f'{round(total_pmt / amount, 2):,}'), html.Td("החזר לשקל")])
    row4 = html.Tr([html.Td(f'{round(total_pmt, 1):,}'), html.Td("סך החזרים עד סוף תקופה")])
    row5 = html.Tr([html.Td(f'{round(total_ipmt_nominal, 1):,}'), html.Td("סך החזרי ריבית")])
    row6 = html.Tr([html.Td(f'{round(total_cpi, 1):,}'), html.Td("סך החזרי הצמדה")])
    row7 = html.Tr([html.Td(f'{round(max_pmt, 1):,}'), html.Td("החזר בשיא")])

    table_body = [html.Tbody([row1, row2, row7, row3, row4, row5, row6])]

    summary = dbc.Table(table_body, striped=True, bordered=True, responsive='sm', hover=True, style={'textAlign':'right'})

    '''גרף נתוני כל המשכנתא'''
    df_total.index += 1
    fig = df_total.iplot(asFigure=True)
    fig.update_layout(
        title_text='תצוגה גרפית של לוח סילוקין',
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend_bgcolor='rgba(0,0,0,0)'
    )

    '''גרף סך החזרים'''
    labels = ["קרן", "ריבית", "הצמדה"]
    values = [amount, round(total_ipmt_nominal), round(total_cpi)]
    fig_sums = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.2)])
    fig_sums.update_layout(
        title_text='התפלגות סך ההחזרים עד סוף תקופת המשכנתא',
        title_x=0.5,
    )

    '''גרך תשלומים חודשיים לפי ריבית - הצמדה'''
    fig_payments = go.Figure(data=[
        go.Bar(
            name='תשלום ריבית',
            x=df_total["חודש"],
            y=df_total['תשלום ריבית'].round(
                decimals=2), marker=Marker(color='rgb(90, 202, 138)')),
        go.Bar(
            name='תשלום קרן', x=df_total["חודש"],
            y=df_total['תשלום קרן'].round(
                decimals=2), marker=Marker(color='rgb(250, 131, 210)'))
    ])
    fig_payments.update_layout(
        barmode='stack',
        title_text='החזר חודשי בחלוקה לקרן וריבית',
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig, fig_sums, fig_payments, summary, table


def loan_callback(i):
    @app.callback(
        [
            Output("output{}".format(i), "figure"),
            Output('pmt{}'.format(i), 'children'),
            Output('total_pmt{}'.format(i), 'children')],
        [
            Input('schedule{}'.format(i), 'value'),
            Input('switch{}'.format(i), 'value'),
            Input('madad{}'.format(i), 'value'),
            Input('amount{}'.format(i), 'value'),
            Input('interest{}'.format(i), 'value'),
            Input('period{}'.format(i), 'value')])
    def display_value(schedule, cpi, madad, amount, i, period):
        if (period and i and amount):
            maslul_df, total_ipmt_nominal = generate_pd_per_maslul(
                schedule, cpi, madad, amount, i, period)
            df = maslul_df[[pmt_heb, ppmt_heb, ipmt_heb]]
            df.index += 1
            fig = df.iplot(asFigure=True)
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                legend_bgcolor='rgba(0,0,0,0)'
            )
            return (
                fig,
                f"תשלום חודשי ראשוני:  {round(maslul_df[pmt_heb][0], 2):,}",
                f" החזר בסוף תקופה: {round(maslul_df[pmt_heb].sum(), 1):,}")
        fig = go.Figure(data=[go.Scatter(x=[], y=[])])
        return fig, None, None


# Render loan description
def card_callback(i):
    @app.callback(Output(f"cardTitle{i}", "children"),
                  [Input(f'inputTitle{i}', 'value')])
    def render_title(t):
        if t:
            return t

    @app.callback(Output(f"cardSum{i}", "children"),
                  [Input(f'amount{i}', 'value')])
    def render_amount(a):
        if a:
            return a

    @app.callback(Output(f"cardInterest{i}", "children"),
                  [Input(f'interest{i}', 'value')])
    def render_interest(interest):
        if interest:
            return f'{interest} %'

    @app.callback(Output(f"cardPeriod{i}", "children"),
                  [Input(f'period{i}', 'value')])
    def render_period(p):
        return p


# Callbacks for loan modals
def modal_callback(i):
    @app.callback(
        Output(f"modalmaslul{i}", "is_open"),
        [Input(f"openmaslul{i}", "n_clicks"),
         Input(f"closemaslul{i}", "n_clicks")],
        [State(f"modalmaslul{i}", "is_open")],
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


# render callbacks
for i in range(1, 7):
    loan_callback(i)
    card_callback(i)
    modal_callback(i)


# the same function (toggle_navbar_collapse) is used in all three callbacks
for i in [2]:
    app.callback(
        Output(f"navbar-collapse{i}", "is_open"),
        [Input(f"navbar-toggler{i}", "n_clicks")],
        [State(f"navbar-collapse{i}", "is_open")],
    )(toggle_navbar_collapse)


if __name__ == "__main__":
    app.run_server(debug=False)
