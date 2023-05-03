from collections import defaultdict

import numpy as np

from pathogen_properties import *

background = """Norovirus is a GI infection, mostly spread through personal
contact."""


pathogen_chars = PathogenChars(
    na_type=NAType.RNA,
    enveloped=Enveloped.NON_ENVELOPED,
    taxid=TaxID(142786),
)

# We're using Scallan 2011
# (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3375761/) which:
#
#  1. Estimates the annual number of foodborne Norovirus cases
#  2. Estimates the fractionof Norovirus cases that are foodborne
#
# This gives us enough information to estimate the annual number of Norovirus
# cases.
#
# This is the source for the CDC's estimate:
# https://wwwnc.cdc.gov/eid/article/19/8/pdfs/13-0465.pdf cites this paper as
# their source for 21M annual cases in the US.
#
# Note that this is "2006" as in "relative to the 2006 population" not as in
# "number of cases in 2006".  They're using several years worth of data
# ("mostly from 2000–2008") to make their estimates.

us_national_foodborne_cases_2006 = IncidenceAbsolute(
    annual_infections=5_461_731,
    confidence_interval=(3_227_078, 8_309_480),
    coverage_probability=0.9,  # credible interval
    country="United States",
    tag="us-2006",
    date="2006",
    # "Domestically acquired foodborne, mean (90% credible interval)
    # ... 5,461,731 (3,227,078–8,309,480)"
    source="https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3375761/#:~:text=5%2C461%2C731%20(3%2C227%2C078%E2%80%938%2C309%2C480)",
)

us_total_relative_to_foodborne_2006 = Scalar(
    scalar=1 / 0.26,
    country="United States",
    date="2006",
    # "Foodborne % ... 26"
    source="https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3375761/#:~:text=%3C1-,26,-5%2C461%2C731%20(3%2C227%2C078%E2%80%938%2C309%2C480",
)

us_population_2006 = Population(
    people=299_000_000,
    country="United States",
    date="2006",
    tag="us-2006",
    # "all estimates were based on the US population in 2006 (299 million
    # persons)"
    source="https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3375761/#:~:text=population%20in%202006%20(-,299%20million%20persons,-).%20Estimates%20were%20derived",
)

shedding_duration = SheddingDuration(
    days=2,
    confidence_interval=(1, 3),
    # "Norovirus infection symptoms usually last 1 to 3 days"
    source="https://www.mayoclinic.org/diseases-conditions/norovirus/symptoms-causes/syc-20355296#:~:text=Norovirus%20infection%20symptoms%20usually%20last%201%20to%203%20days",
)


monthwise_count = dict[tuple[int, int], float]  # [year, month] -> float


def to_daily_counts(outbreaks_per_month: monthwise_count) -> monthwise_count:
    outbreaks_per_day: monthwise_count = {}
    for year, month in outbreaks_per_month:
        outbreaks_per_day[year, month] = outbreaks_per_month[
            year, month
        ] / days_in_month(year, month)
    return outbreaks_per_day


def load_nors_outbreaks() -> monthwise_count:
    us_outbreaks: monthwise_count = defaultdict(float)  # date -> count

    # Downloaded on 2023-04-28 from https://wwwn.cdc.gov/norsdashboard/
    # Click "Download all NORS Dashboard data (Excel)."
    # Exported from Google Sheets as CSV.
    #
    # Data runs through the end of 2021.
    with open(prevalence_data_filename("cdc-nors-outbreak-data.tsv")) as inf:
        cols = None
        for line in inf:
            row = line.strip().split("\t")
            if not cols:
                cols = row
                continue

            year = int(row[cols.index("Year")])
            month = int(row[cols.index("Month")])
            state = row[cols.index("State")]
            etiology = row[cols.index("Etiology")]
            # It distinguishes between GI and GII Norovirus.  I'm currently
            # discarding this, but it could potentially be useful?
            genotype = row[cols.index("Serotype or Genotype")]
            if "Norovirus" not in etiology:
                # It's the National Outbreak Reporting System, not the
                # Norovirus Outbreak Reporting System.
                #
                # The non-Norovirus ones are almost all bacteria or parasites,
                # though, not much useful to us.
                continue

            date = year, month

            us_outbreaks[date] += 1

    return us_outbreaks


def determine_average_daily_outbreaks(us_outbreaks: monthwise_count) -> float:
    total_us_outbreaks = 0.0
    days_considered = 0
    for year in range(HISTORY_START, HISTORY_END + 1):
        for month in range(1, 13):
            total_us_outbreaks += us_outbreaks[year, month]
            days_considered += days_in_month(year, month)
    return total_us_outbreaks / days_considered


# When estimating the historical pattern, use 2012 through 2019.  This is:
#  * Recent enough to have good data
#  * Long enough to reduce noise
#  * Pre-covid
HISTORY_START = 2012
HISTORY_END = 2019


def estimate_prevalences():
    prevalences = []

    us_outbreaks = load_nors_outbreaks()
    pre_covid_us_average_daily_outbreaks = determine_average_daily_outbreaks(
        us_outbreaks
    )

    pre_covid_national_prevalence = (
        us_national_foodborne_cases_2006.to_rate(
            us_population_2006
        ).to_prevalence(shedding_duration)
        * us_total_relative_to_foodborne_2006
    )

    us_daily_outbreaks = to_daily_counts(us_outbreaks)

    for year in range(HISTORY_START, HISTORY_END + 1):
        for month in range(1, 13):
            target_date = f"{year}-{month:02d}"

            prevalences.append(
                (
                    pre_covid_national_prevalence
                    * (
                        Scalar(
                            scalar=us_daily_outbreaks[year, month]
                            / pre_covid_us_average_daily_outbreaks,
                            country="United States",
                            date=target_date,
                            source="https://wwwn.cdc.gov/norsdashboard/",
                        )
                    )
                ).target(country="United States", date=target_date)
            )

    return prevalences
