#!/usr/bin/env python3
from pathlib import Path

import pandas as pd

import stats
from mgs import Enrichment, MGSData, target_bioprojects
from pathogens import predictors_by_taxid


def summarize_output(coeffs: pd.DataFrame) -> pd.DataFrame:
    return coeffs.groupby(
        [
            "pathogen",
            "tidy_name",
            "taxids",
            "predictor_type",
            "study",
            "location",
        ]
    ).ra_at_1in100.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])


def start(num_samples: int, plot: bool) -> None:
    branch = "simon-p2ra-manuscript"
    print("Using mgs-pipeline branch simon-p2ra-manuscript")
    figdir = Path("panel_fig")
    if plot:
        figdir.mkdir(exist_ok=True)
    mgs_data = MGSData.from_repo(ref=branch)
    input_data = []
    output_data = []
    for (
        pathogen_name,
        tidy_name,
        predictor_type,
        taxids,
        predictors,
    ) in predictors_by_taxid():
        taxids_str = "_".join(str(t) for t in taxids)
        for study, bioprojects in target_bioprojects.items():
            if study in ["brinch", "spurbeck"]: 
                print(f"Skipping {study} for {pathogen_name}")
                continue
            enrichment = Enrichment.PANEL
            model = stats.build_model(
                mgs_data,
                bioprojects,
                predictors,
                taxids,
                random_seed=sum(taxids),
                enrichment=enrichment,
            )
            if model is None:
                continue
            model.fit_model(num_samples=num_samples)
            if plot:
                taxid_str = "-".join(str(tid) for tid in taxids)
                model.plot_figures(
                    path=figdir,
                    prefix=f"{pathogen_name}-{taxid_str}-{predictor_type}-{study}",
                )
            metadata = dict(
                pathogen=pathogen_name,
                tidy_name=tidy_name,
                taxids=taxids_str,
                predictor_type=predictor_type,
                study=study,
            )
            input_data.append(model.input_df.assign(**metadata))
            output_data.append(model.get_coefficients().assign(**metadata))
    input = pd.concat(input_data)
    input.to_csv("panel_input.tsv", sep="\t", index=False)
    coeffs = pd.concat(output_data)
    coeffs.to_csv("panel_fits.tsv", sep="\t", index=False)
    summary = summarize_output(coeffs)
    summary.to_csv("panel_fits_summary.tsv", sep="\t")


if __name__ == "__main__":
    # TODO: Command line arguments
    start(num_samples=1000, plot=True)
