import numpy as np
import numpy_financial as npf
import pandas as pd


months_heb = "חודש"
pmt_heb = "החזר חודשי"
ppmt_heb = "תשלום קרן"
ipmt_heb = "תשלום ריבית"


def generate_pd_per_maslul_straight(cpi, madad, amount, interest, period):
    inflation = madad * len(cpi)  # 1.48953% due to Bank Leumi
    minf = (1 + inflation / 1200)
    interest_rate = interest / 1200
    periods = np.arange(period) + 1
    # pmt_nominal = round(npf.pmt(interest_rate, period, -amount), 2)
    ipmt_nominal = npf.ipmt(interest_rate, periods, period, -amount)
    total_ipmt_nominal = np.ndarray.sum(ipmt_nominal)

    # Inflation list (CPI)
    inf = list((1 + inflation / 1200) ** y for y in range(1, period + 1))
    ipmt_cpi = ipmt_nominal * inf

    # Payment against loan principal.
    ppmt_nominal = npf.ppmt(interest_rate, periods, period, -amount)
    ppmt_cpi = ppmt_nominal * inf
    pmt = ppmt_cpi + ipmt_cpi

    # Balance
    start = amount * minf
    balance = list()
    for i in range(len(ppmt_cpi)):
        balance.append((start-ppmt_cpi[i]) * minf)
        start = (start-ppmt_cpi[i]) * minf
    balance = np.array(balance)

    maslul_df = pd.DataFrame(
        {
            months_heb: periods,
            ppmt_heb: ppmt_cpi,
            ipmt_heb: ipmt_cpi,
            pmt_heb: pmt,
            "יתרה": balance
        }
    )
    return maslul_df, total_ipmt_nominal