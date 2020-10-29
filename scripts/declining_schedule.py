import numpy as np
import pandas as pd

months_heb = "חודש"
pmt_heb = "החזר חודשי"
ppmt_heb = "תשלום קרן"
ipmt_heb = "תשלום ריבית"


def generate_pd_per_maslul_declining(cpi, madad, amount, interest, period):
    inflation = madad * len(cpi)  # 1.48953% due to Bank Leumi
    minf = (1 + inflation/1200)
    interest_rate = interest/1200
    periods = np.arange(period) + 1
    ppmt_nominal = amount / period
    ppmt_cpi = np.array(list(
        ppmt_nominal * minf ** i for i in range(1, period + 1)))
    balance = get_balance(amount, period, ppmt_cpi, minf)

    # IPMT payments
    ipmt_cpi = get_ipmt(amount, balance, interest_rate, minf)
    ipmt_nominal = get_ipmt(amount, balance, interest_rate, 1)
    total_ipmt_nominal = np.sum(ipmt_nominal)

    pmt = ppmt_cpi + ipmt_cpi
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


def get_balance(amount, period, ppmt_cpi, minf):
    prev_balance = amount * minf
    balance = []
    for i in range(period):
        balance.append((prev_balance - ppmt_cpi[i]) * minf)
        prev_balance = (prev_balance - ppmt_cpi[i]) * minf
    return np.array(balance)


def get_ipmt(amount, balance, annual_interest_rate, minf):
    ipmt_cpi = [amount * minf * annual_interest_rate]
    for i in range(len(balance) - 1):
        ipmt_cpi.append(balance[i] * annual_interest_rate)
    return np.array(ipmt_cpi)
