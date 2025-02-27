#!/usr/bin/env python3

import datetime
import unittest
from collections import Counter

import mgs
import pathogens
import populations
import stats
from pathogen_properties import *


class TestPathogens(unittest.TestCase):
    def test_hsv1_imported(self):
        self.assertIn("hsv_1", pathogens.pathogens)

    def test_summarize_location(self):
        (
            us_2019,
            us_2020,
            us_2021,
            copenhagen_2022,
            copenhagen_2018,
            copenhagen_2017,
            copenhagen_2016,
            copenhagen_2015,
        ) = pathogens.pathogens["hiv"].estimate_prevalences()
        self.assertEqual(us_2019.summarize_location(), "United States")

    def test_dates(self):
        (
            us_2019,
            us_2020,
            us_2021,
            copenhagen_2022,
            copenhagen_2018,
            copenhagen_2017,
            copenhagen_2016,
            copenhagen_2015,
        ) = pathogens.pathogens["hiv"].estimate_prevalences()
        self.assertEqual(us_2019.parsed_start, datetime.date(2019, 1, 1))
        self.assertEqual(us_2019.parsed_end, datetime.date(2019, 12, 31))

    def test_properties_exist(self):
        for pathogen_name, pathogen in pathogens.pathogens.items():
            with self.subTest(pathogen=pathogen_name):
                self.assertIsInstance(pathogen.background, str)

                self.assertIsInstance(pathogen.pathogen_chars, PathogenChars)

                saw_estimate = False
                for estimate in pathogen.estimate_prevalences():
                    self.assertIsInstance(estimate, Prevalence)
                    saw_estimate = True
                for estimate in pathogen.estimate_incidences():
                    self.assertIsInstance(estimate, IncidenceRate)
                    saw_estimate = True
                if pathogen_name in ["aav5", "aav6", "hbv", "hsv_2"]:
                    # It's expected that these pathogens have no estimates; see
                    # https://docs.google.com/document/d/1IIeOFKNqAwf9NTJeVFRSl_Q9asvu9_TGc_HSrlXg8PI/edit
                    self.assertFalse(saw_estimate)
                else:
                    self.assertTrue(saw_estimate)

    def test_dates_set(self):
        for pathogen_name, pathogen in pathogens.pathogens.items():
            with self.subTest(pathogen=pathogen_name):
                for estimate in pathogen.estimate_prevalences():
                    estimate.get_dates()

    def test_by_taxids(self):
        for pathogen_name, pathogen in pathogens.pathogens.items():
            with self.subTest(pathogen=pathogen_name):
                for taxids, estimates in by_taxids(
                    pathogen.pathogen_chars, pathogen.estimate_prevalences()
                ).items():
                    self.assertNotEqual(len(taxids), 0)
                    self.assertNotEqual(len(estimates), 0)
                    for estimate in estimates:
                        if estimate.taxid:
                            self.assertEqual(
                                frozenset([estimate.taxid]), taxids
                            )
                        else:
                            self.assertEqual(
                                pathogen.pathogen_chars.taxids, taxids
                            )

    def test_duplicate_estimates(self):
        for pathogen_name, pathogen in pathogens.pathogens.items():
            with self.subTest(pathogen=pathogen_name):
                for label, predictors in [
                    (
                        "prevalence",
                        pathogen.estimate_prevalences(),
                    ),
                    (
                        "incidence",
                        pathogen.estimate_incidences(),
                    ),
                ]:
                    for taxids, estimates in by_taxids(
                        pathogen.pathogen_chars, predictors
                    ).items():
                        seen = set()
                        for estimate in estimates:
                            key = (
                                estimate.get_dates(),
                                estimate.summarize_location(),
                            )
                            if key in seen:
                                self.fail(
                                    f"Duplicate {label} estimate found for {pathogen_name}: {key}."
                                )
                            seen.add(key)


class TestMMWRWeek(unittest.TestCase):
    def test_mmwr_week(self):
        self.assertEqual(
            pathogens.pathogens["influenza"].parse_mmwr_week(2020, 1),
            # Year starts on a Wednesday, so week 1 starts in 2019.
            datetime.date(2019, 12, 29),
        )
        self.assertEqual(
            pathogens.pathogens["influenza"].parse_mmwr_week(2019, 1),
            # Year starts on a Tuesday, so week 1 starts in 2018.
            datetime.date(2018, 12, 30),
        )
        self.assertEqual(
            pathogens.pathogens["influenza"].parse_mmwr_week(2018, 1),
            # Year starts on a Monday, so week 1 starts in 2017.
            datetime.date(2017, 12, 31),
        )
        self.assertEqual(
            pathogens.pathogens["influenza"].parse_mmwr_week(2017, 1),
            # Year starts on a Sunday, so week 1 starts in 2017.
            datetime.date(2017, 1, 1),
        )
        self.assertEqual(
            pathogens.pathogens["influenza"].parse_mmwr_week(2016, 1),
            # Year starts on a Friday, so week 1 starts in 2016.
            datetime.date(2016, 1, 3),
        )
        self.assertEqual(
            pathogens.pathogens["influenza"].parse_mmwr_week(2015, 1),
            # Year starts on a Thursday, so week 1 starts in 2016.
            datetime.date(2015, 1, 4),
        )


class TestVaribles(unittest.TestCase):
    def test_date_parsing(self):
        v = Variable(date="2019")
        self.assertEqual(
            v.get_dates(),
            (datetime.date(2019, 1, 1), datetime.date(2019, 12, 31)),
        )

        v = Variable(date="2019-02")
        self.assertEqual(
            v.get_dates(),
            (datetime.date(2019, 2, 1), datetime.date(2019, 2, 28)),
        )

        v = Variable(date="2020-02")
        self.assertEqual(
            v.get_dates(),
            (datetime.date(2020, 2, 1), datetime.date(2020, 2, 29)),
        )

        v = Variable(date="2020-02-01")
        self.assertEqual(
            v.get_dates(),
            (datetime.date(2020, 2, 1), datetime.date(2020, 2, 1)),
        )

        v = Variable(start_date="2020-01", end_date="2020-02")
        self.assertEqual(
            v.get_dates(),
            (datetime.date(2020, 1, 1), datetime.date(2020, 2, 29)),
        )

        v = Variable(start_date="2020-01-07", end_date="2020-02-06")
        self.assertEqual(
            v.get_dates(),
            (datetime.date(2020, 1, 7), datetime.date(2020, 2, 6)),
        )

        v1 = Variable(date="2019")
        v2 = Variable(date="2020", date_source=v1)
        self.assertEqual(
            v2.get_dates(),
            (datetime.date(2019, 1, 1), datetime.date(2019, 12, 31)),
        )

        with self.assertRaises(Exception):
            Variable(start_date="2020-01-07")

        with self.assertRaises(Exception):
            Variable(end_date="2020-01-07")

        with self.assertRaises(Exception):
            Variable(start_date="2020-01-07", date="2020")

        with self.assertRaises(Exception):
            Variable(end_date="2020-01-07", date="2020")

        with self.assertRaises(Exception):
            Variable(start_date="2020-01-07", end_date="2020-01-06")

        with self.assertRaises(Exception):
            Variable(date="2020-1")

        with self.assertRaises(Exception):
            Variable(date="2020/1/1")

        with self.assertRaises(Exception):
            Variable(date="2020/01/01")

        v = Variable(date="2020")
        with self.assertRaises(AssertionError):
            v.get_date()  # asserts start==end

        v = Variable()
        self.assertIsNone(v.parsed_start)
        self.assertIsNone(v.parsed_end)
        with self.assertRaises(AssertionError):
            v.get_dates()  # asserts dates are set

    def test_locations(self):
        v1 = Variable(
            country="United States", state="Ohio", county="Franklin County"
        )
        self.assertEqual(
            ("United States", "Ohio", "Franklin County"), v1.get_location()
        )

        v2 = Variable(
            country="United States",
            state="California",
            county="Alameda County",
        )

        # Conflicting locations with no resolution specified.
        with self.assertRaises(ValueError):
            Variable(inputs=[v1, v2])

        v3 = Variable(inputs=[v1, v2], location_source=v1)
        self.assertEqual(
            ("United States", "Ohio", "Franklin County"), v3.get_location()
        )


class TestMGS(unittest.TestCase):
    repo = mgs.GitHubRepo(**mgs.MGS_REPO_DEFAULTS)

    def test_load_bioprojects(self):
        bps = mgs.load_bioprojects(self.repo)
        for study, study_bps in mgs.target_bioprojects.items():
            with self.subTest(study=study):
                for bp in study_bps:
                    self.assertIn(bp, bps)

    def test_load_sample_attributes(self):
        samples = mgs.load_sample_attributes(self.repo)
        s1 = mgs.Sample("SRR14530726")  # Randomly picked Rothman sample
        s2 = mgs.Sample("SRR23083716")  # Randomly picked Spurbeck sample
        self.assertIn(s1, samples)
        self.assertIn(s2, samples)
        attrs = samples[s1]
        self.assertEqual(attrs.country, "United States")
        self.assertEqual(attrs.state, "California")
        self.assertEqual(attrs.county, "San Diego County")
        self.assertEqual(attrs.date, datetime.date(2020, 8, 27))
        self.assertEqual(attrs.enrichment, mgs.Enrichment.VIRAL)
        self.assertIsNone(attrs.method)
        self.assertEqual(samples[s2].method, "IJ")

    def test_load_sample_counts(self):
        sample_counts = mgs.load_sample_counts(self.repo)
        for p in ["sars_cov_2", "hiv"]:
            with self.subTest(pathogen=p):
                for taxid in pathogens.pathogens[p].pathogen_chars.taxids:
                    self.assertIn(taxid, sample_counts)

class TestWeightedAverageByPopulation(unittest.TestCase):
    def test_weightedAverageByPopulation(self):
        prevalences = [
            Prevalence(
                infections_per_100k=i,
                date="2000-01-0%s" % i,
                active=Active.ACTIVE,
            )
            for i in range(1, 5)
        ]
        populations = [
            Population(
                people=100_000 * i,
                date="2000-01-0%s" % i,
            )
            for i in range(1, 5)
        ]
        self.assertAlmostEqual(
            (1 * 100_000 + 2 * 200_000 + 3 * 300_000 + 4 * 400_000)
            / (100_000 * (1 + 2 + 3 + 4)),
            Prevalence.weightedAverageByPopulation(
                *zip(prevalences, populations)
            ).infections_per_100k,
        )


class TestMGSData(unittest.TestCase):
    mgs_data = mgs.MGSData.from_repo()
    (bioproject,) = mgs.target_bioprojects["rothman"]
    sample = mgs.Sample("SRR14530726")  # Random Rothman sample
    taxids = pathogens.pathogens["norovirus"].pathogen_chars.taxids

    def test_from_repo(self):
        self.assertIsInstance(mgs.MGSData.from_repo(), mgs.MGSData)

    def test_sample_attributes(self):
        samples = self.mgs_data.sample_attributes(self.bioproject)
        self.assertIn(self.sample, samples)
        self.assertIsInstance(samples[self.sample], mgs.SampleAttributes)

    def test_total_reads(self):
        reads = self.mgs_data.total_reads(self.bioproject)
        self.assertIn(self.sample, reads)
        self.assertIsInstance(reads[self.sample], int)

    def test_viral_reads(self):
        reads = self.mgs_data.viral_reads(self.bioproject, self.taxids)
        self.assertIn(self.sample, reads)
        self.assertIsInstance(reads[self.sample], int)


class TestPopulations(unittest.TestCase):
    def test_county_state(self):
        self.assertEqual(
            populations.us_population(
                county="Bristol County", state="Rhode Island", year=2020
            ),
            Population(
                people=50_774,
                date="2020-07-01",
                source="https://www.census.gov/data/tables/time-series/demo/popest/2020s-counties-total.html",
                country="United States",
                state="Rhode Island",
                county="Bristol County",
            ),
        )

        self.assertEqual(
            populations.us_population(
                county="Bristol County", state="Rhode Island", year=2020
            ).people,
            50_774,
        )
        self.assertEqual(
            populations.us_population(
                county="Bristol County", state="Rhode Island", year=2021
            ).people,
            50_800,
        )
        self.assertEqual(
            populations.us_population(
                county="Bristol County", state="Rhode Island", year=2022
            ).people,
            50_360,
        )

        self.assertEqual(
            populations.us_population(
                county="Southeastern Connecticut Planning Region",
                state="Connecticut",
                year=2022,
            ).people,
            280_403,
        )

    def test_state(self):
        self.assertEqual(
            populations.us_population(state="California", year=2022),
            Population(
                # From https://www.census.gov/quickfacts/CA
                people=39_029_342,
                date="2022-07-01",
                source="https://www.census.gov/data/tables/time-series/demo/popest/2020s-counties-total.html",
                country="United States",
                state="California",
            ),
        )

    def test_country(self):
        self.assertEqual(
            populations.us_population(year=2022),
            Population(
                # https://www.census.gov/quickfacts/USA
                people=333_287_557,
                date="2022-07-01",
                source="https://www.census.gov/data/tables/time-series/demo/popest/2020s-counties-total.html",
                country="United States",
            ),
        )


class TestStats(unittest.TestCase):
    attrs = mgs.SampleAttributes(
        country="United States",
        state="Pennsylvania",
        county="Allegheny County",
        date=datetime.date.fromisoformat("2019-05-14"),
        reads=100,
        location="Loc",
        enrichment=mgs.Enrichment.VIRAL,
    )

    def test_match_quality(self):
        v1 = Variable(country="United States", date="2019")
        self.assertEqual(stats.match_quality(self.attrs, v1), 0)
        v2 = Variable(country="United States", date="2019-05-14")
        self.assertEqual(stats.match_quality(self.attrs, v2), 0)
        v3 = Variable(country="United States", date="2019-05-15")
        # One day off, so -1.
        self.assertEqual(stats.match_quality(self.attrs, v3), -1)
        v4 = Variable(
            country="United States",
            start_date="2019-05-01",
            end_date="2019-06-02",
        )
        self.assertEqual(stats.match_quality(self.attrs, v4), 0)
        v5 = Variable(
            country="United States",
            state="Pennsylvania",
            county="Allegheny County",
            date="2019",
        )
        # Higher score for state and county match.
        self.assertEqual(stats.match_quality(self.attrs, v5), 30)
        v6 = Variable(
            country="United States",
            state="Pennsylvania",
            county="Beaver County",
            date="2019",
        )
        self.assertIsNone(stats.match_quality(self.attrs, v6))
        v7 = Variable(
            country="United States",
            state="Ohio",
            county="Lake County",
            date="2019",
        )
        self.assertIsNone(stats.match_quality(self.attrs, v7))

    def test_lookup_variables(self):
        v1 = Variable(country="United States", date="2019")
        v2 = Variable(country="United States", date="2019-05-14")
        v3 = Variable(country="United States", date="2019-05-15")
        v4 = Variable(country="United States", date="2019-05-16")
        v5 = Variable(country="United States", date="2019-05-31")
        v6 = Variable(
            country="United States", state="Pennsylvania", date="2019"
        )
        v7 = Variable(
            country="United States",
            state="Pennsylvania",
            county="Allegheny County",
            date="2019",
        )

        self.assertEqual(stats.lookup_variables(self.attrs, [v1, v3]), [v1])
        # Prefer v2 to v3 because it's an exact match.
        self.assertEqual(stats.lookup_variables(self.attrs, [v2, v3]), [v2])
        self.assertEqual(stats.lookup_variables(self.attrs, [v3, v1]), [v1])
        self.assertEqual(
            stats.lookup_variables(self.attrs, [v1, v2]), [v1, v2]
        )
        # Accept v3 because it's pretty close (one day off).
        self.assertEqual(stats.lookup_variables(self.attrs, [v3]), [v3])
        # Prefer v3 over v4 because it's closer.
        self.assertEqual(stats.lookup_variables(self.attrs, [v3, v4]), [v3])
        # Don't accept v5 because it's too far off.
        self.assertEqual(stats.lookup_variables(self.attrs, [v5]), [])

        # Prefer state match over general country
        self.assertEqual(stats.lookup_variables(self.attrs, [v1, v6]), [v6])

        # Prefer county match over state
        self.assertEqual(stats.lookup_variables(self.attrs, [v6, v7]), [v7])

    def test_build_model(self):
        mgs_data = mgs.MGSData.from_repo()
        for (
            pathogen_name,
            tidy_name,
            predictor_type,
            taxids,
            predictors,
        ) in pathogens.predictors_by_taxid():
            for study, bioprojects in mgs.target_bioprojects.items():
                with self.subTest(
                    pathogen=pathogen_name,
                    taxids=taxids,
                    predictor=predictor_type,
                    study=study,
                ):
                    enrichment = (
                        None if study == "brinch" else mgs.Enrichment.VIRAL
                    )
                    model = stats.build_model(
                        mgs_data,
                        bioprojects,
                        predictors,
                        taxids,
                        random_seed=1,
                        enrichment=enrichment,
                    )
                    # No matching data
                    if model is None:
                        continue
                    all_sample_attributes = {}
                    for bioproject in bioprojects:
                        all_sample_attributes.update(
                            mgs_data.sample_attributes(
                                bioproject,
                                enrichment=enrichment,
                            )
                        )
                    self.assertEqual(
                        len(model.data), len(all_sample_attributes)
                    )

    def test_fit_model(self):
        mgs_data = mgs.MGSData.from_repo()
        pathogen = pathogens.pathogens["sars_cov_2"]
        bioprojects = mgs.target_bioprojects["rothman"]
        taxids, predictors = next(
            iter(
                by_taxids(
                    pathogen.pathogen_chars,
                    pathogen.estimate_incidences(),
                ).items()
            )
        )
        model = stats.build_model(
            mgs_data,
            bioprojects,
            predictors,
            taxids,
            random_seed=1,
            enrichment=mgs.Enrichment.VIRAL,
        )
        assert model is not None
        self.assertIsNone(model.fit)
        self.assertIsNone(model.output_df)
        with self.assertRaises(ValueError):
            model.get_output_by_sample()
        with self.assertRaises(ValueError):
            model.get_coefficients()
        model.fit_model(num_chains=1, num_samples=1)
        self.assertIsNotNone(model.fit)
        self.assertIsNotNone(model.output_df)
        model.get_output_by_sample()
        model.get_coefficients()


class TestPathogensMatchStudies(unittest.TestCase):
    def test_pathogens_match_studies(self):
        # Every pathogen should have at least one estimate for every sample
        # in the projects we're working with.
        mgs_data = mgs.MGSData.from_repo()
        for (
            pathogen_name,
            tidy_name,
            predictor_type,
            taxids,
            predictors,
        ) in pathogens.predictors_by_taxid():
            for study, bioprojects in mgs.target_bioprojects.items():
                for bioproject in bioprojects:
                    with self.subTest(
                        pathogen=pathogen_name,
                        taxids=taxids,
                        predictor=predictor_type,
                        study=study,
                        bioproject=bioproject,
                    ):
                        enrichment = (
                            None if study == "brinch" else mgs.Enrichment.VIRAL
                        )
                        chosen_predictors = {
                            sample: stats.lookup_variables(attrs, predictors)
                            for sample, attrs in mgs_data.sample_attributes(
                                bioproject, enrichment=enrichment
                            ).items()
                        }
                        # It's ok to have no data at all.
                        # We just can't handle partial data at the moment.
                        if all(ps == [] for ps in chosen_predictors.values()):
                            continue
                        for sample, preds in chosen_predictors.items():
                            with self.subTest(sample=sample):
                                self.assertNotEqual(preds, [])
                                for predictor in preds:
                                    with self.subTest(predictor=predictor):
                                        self.assertGreater(
                                            predictor.get_data(), 0
                                        )


if __name__ == "__main__":
    unittest.main()
