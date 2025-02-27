import csv
from dataclasses import dataclass

import matplotlib.pyplot as plt  # type: ignore
import numpy as np
import os
from scipy.stats import gmean

PERCENTILES = [5, 25, 50, 75, 95]

MODEL_OUTPUT_DIR = "../model_output"
TABLE_OUTPUT_DIR = "../tables"


@dataclass
class SummaryStats:
    mean: float
    std: float
    min: float
    percentiles: dict[int, float]
    max: float


def tidy_number(reads_required=int) -> str:
    sci_notation = f"{reads_required:.2e}"

    coefficient, exponent = sci_notation.split("e")

    is_negative = exponent.startswith("-")
    if is_negative:
        exponent = exponent[1:]

    exponent = exponent.lstrip("0")

    if is_negative:
        exponent = "⁻" + exponent

    superscript_map = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
    exponent = exponent.translate(superscript_map)

    return f"{coefficient} × 10{exponent}"


def read_data() -> dict[tuple[str, str, str, str], SummaryStats]:
    data = {}
    with open(os.path.join(MODEL_OUTPUT_DIR, "fits_summary.tsv")) as datafile:
        reader = csv.DictReader(datafile, delimiter="\t")
        for row in reader:
            virus = row["tidy_name"]
            predictor_type = row["predictor_type"]
            study = row["study"]
            location = row["location"]
            data[virus, predictor_type, study, location] = SummaryStats(
                mean=tidy_number(float(row["mean"])),
                std=tidy_number(float(row["std"])),
                min=tidy_number(float(row["min"])),
                percentiles={p: float(row[f"{p}%"]) for p in PERCENTILES},
                max=tidy_number(float(row["max"])),
            )
    return data


def create_tsv():
    data = read_data()
    viruses = set()
    for entry in data.keys():
        virus, predictor_type = entry[:2]
        viruses.add((virus, predictor_type))

    sorted_viruses = sorted(viruses, key=lambda x: (x[1], x[0]))
    study_tidy = {
        "rothman": "Rothman",
        "crits_christoph": "Crits-Christoph",
        "spurbeck": "Spurbeck",
        "brinch": "Brinch",
    }

    headers = ["Virus", "Study", "Median", "5th Percentile", "95th Percentile"]

    with open(
        os.path.join(TABLE_OUTPUT_DIR, "table_s6.tsv"),
        "w",
        newline="",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=headers, delimiter="\t")
        writer.writeheader()

        for virus, predictor_type in sorted_viruses:
            studies = ["rothman", "crits_christoph", "spurbeck"] + (
                ["brinch"] if predictor_type == "prevalence" else []
            )
            gmean_data = {
                "Median": [],
                "5th Percentile": [],
                "95th Percentile": [],
            }

            for study in studies:
                stats = data[virus, predictor_type, study, "Overall"]
                writer.writerow(
                    {
                        "Virus": virus,
                        "Study": study_tidy[study],
                        "Median": tidy_number(stats.percentiles[50]),
                        "5th Percentile": tidy_number(stats.percentiles[5]),
                        "95th Percentile": tidy_number(stats.percentiles[95]),
                    }
                )
                gmean_data["Median"].append(stats.percentiles[50])
                gmean_data["5th Percentile"].append(stats.percentiles[5])
                gmean_data["95th Percentile"].append(stats.percentiles[95])

            gmean_median = gmean(gmean_data["Median"])
            gmean_lower = gmean(gmean_data["5th Percentile"])
            gmean_upper = gmean(gmean_data["95th Percentile"])
            writer.writerow(
                {
                    "Virus": virus,
                    "Study": "Mean (geometric)",
                    "Median": tidy_number(gmean_median),
                    "5th Percentile": tidy_number(gmean_lower),
                    "95th Percentile": tidy_number(gmean_upper),
                }
            )


def start():
    create_tsv()


if __name__ == "__main__":
    start()
