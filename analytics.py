import logging
import requests

import pandas as pd

from io import StringIO
from requests.auth import HTTPBasicAuth
from scipy.stats import binom_test

logging.basicConfig(
    level=logging.INFO, format="[%(levelname)s] %(asctime)s: %(message)s"
)

### Don't forget those
ch_user = ""  # login
ch_pass = ""  # pass


sql = """
select
    gender, 
    sumIf(uniques, include = 1) as retained,
    sum(uniques) as total
from (
    select include, gender, uniqExact(userId) as uniques
    from (
        select
            userId, gender, 
            min(dt) as first_date, 
            groupUniqArray(dt) as all_dates,
            has(all_dates, first_date + 7) as include
        from default.event_data
        -- не залогиненные не нужны
        where auth = 'Logged In'
        group by userId, gender
        -- отрезаем, если у пользователи совсем свежие
        having first_date + 7 <= (select max(dt) from default.event_data)
    )
    group by include, gender
)
group by gender
with totals
"""


def get_df(q: str) -> pd.DataFrame:
    """"""
    r = requests.post(
        "https://uchi-ch.kkmagician.com",
        auth=HTTPBasicAuth(ch_user, ch_pass),
        data=(q + " format TSVWithNames").encode("utf-8"),
    )

    buf = StringIO(r.text)

    return pd.read_csv(buf, sep="\t")


def get_retention(results: dict, subset: str, raw=False, precision: int = 2) -> float:
    """"""
    raw_rr = results[subset]["retained"] / results[subset]["total"]
    if raw:
        return raw_rr
    else:
        return round(
            results[subset]["retained"] / results[subset]["total"] * 100, precision
        )


df = get_df(sql)
df["gender"] = df["gender"].fillna("all")
results = df.set_index("gender").to_dict("index")

day7_rr_all = get_retention(results, "all")
day7_rr_m = get_retention(results, "M")
day7_rr_f = get_retention(results, "F")

for rr_result in zip(
    ["all users", "men", "women"], [day7_rr_all, day7_rr_m, day7_rr_f]
):
    logging.info(f"Day 7 retention for {rr_result[0]}: {rr_result[1]}%")


# Testing
h_p_value = binom_test(
    results["M"]["retained"],
    results["M"]["total"],
    get_retention(results, "F", True),
    alternative="two-sided",
)
logging.info(f"Hypothesis p-value: {h_p_value}")

if h_p_value > 0.05:
    logging.info(f"Can't really tell if the groups are different: p-value is too high")
else:
    logging.info(f"p-value is ok, the two groups are different")
