import numpy as np
import pandas as pd

months_heb = "חודש"
pmt_heb = "החזר חודשי"
ppmt_heb = "תשלום קרן"
ipmt_heb = "תשלום ריבית"


def generate_pd_per_maslul_bullet(cpi, madad, amount, interest, period):
    inflation = madad * len(cpi)  # 1.48953% due to Bank Leumi
    minf = (1 + inflation / 1200)
    interest_rate = interest / 1200
    periods = np.arange(period) + 1

    # IPMT
    ipmt_nominal = amount * interest_rate
    total_ipmt_nominal = ipmt_nominal * period
    ipmt_cpi = np.array([
        ipmt_nominal * minf ** n for n in range(1, period + 1)])

    # Balance
    balance_list = [amount * minf ** n for n in range(1, period + 1)]
    balance = np.array(balance_list[:-1] + [0])

    # PPMT
    last_payment_cpi = balance_list[-1]
    ppmt_cpi = np.array([0] * (period - 1) + [last_payment_cpi])

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
