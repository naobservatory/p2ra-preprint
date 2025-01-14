import dataclasses

from pathogen_properties import *

background = """BK virus is a common virus which has minimal impact in
immunocompetent humans"""

pathogen_chars = PathogenChars(
    na_type=NAType.DNA,
    enveloped=Enveloped.NON_ENVELOPED,
    taxid=TaxID(1891762),
    selection=SelectionRound.ROUND_2,
)


ch_2009_seroprevalence = Prevalence(
    infections_per_100k=0.82 * 100_000,
    # "Prevalence of BKV [...]antibodies [...] among healthy blood donors was
    # 82% (328 of 400)[...]"
    number_of_participants=400,
    # Note that this study also provides numbers on urinary shedding:
    # "BKV was detected in urine samples from 28 (7%) of 400"
    # Given that BK Virus stays latent after infection, seroprevalence likely
    # tracks prevalence more closely than urinary shedding.
    country="Switzerland",
    date="2009",
    active=Active.LATENT,
    source="https://academic.oup.com/jid/article/199/6/837/2192120?login=false#90076999:~:text=Prevalence%20of%20BKV%20and%20JCV%20antibodies%2C%20DNAemia%2C%20and%20DNAuriaBKV%20IgG%20seroprevalence%20among%20healthy%20blood%20donors%20was%2082%25%20(328%20of%20400)%2C%20significantly%20higher%20than%20the%20corresponding%20JCV%20IgG%20seroprevalence%20of%2058%25%20(231%20of%20400)",
)


uk_1991_seroprevalence = Prevalence(
    infections_per_100k=0.81 * 100_000,
    # "A comparative age seroprevalence study was undertaken on 2,435 residual
    # sera from 1991 by haemagglutination inhibition (HI) for BKV and JCV, and
    # virus neutralisation for SV40. The overall rates of seropositivity for
    # BKV and JCV were 81% and 35%"
    number_of_participants=2435,
    # Age breakdown is available in the study, page 3, table 1.
    country="United Kingdom",
    date="1991",
    # Sera are from 1991, the study is from 2003
    active=Active.LATENT,
    source="https://onlinelibrary.wiley.com/doi/10.1002/jmv.10450#:~:text=A%20comparative%20age%20seroprevalence%20study%20was%20undertaken%20on%202%2C435%20residual%20sera%20from%201991%20by%20haemagglutination%20inhibition%20(HI)%20for%20BKV%20and%20JCV%2C%20and%20virus%20neutralisation%20for%20SV40.%20The%20overall%20rates%20of%20seropositivity%20for%20BKV%20and%20JCV%20were%2081%25%20and%2035%25",
    # Methods are paywalled. Sera were "collected during 1991 by seven
    # laboratories distributed throughout England and Wales were available, as
    # part of the PHLS Serological Surveillance Programme from individuals
    # aged 1–69 years."
)


us_2007_seroprevalence = Prevalence(
    infections_per_100k=0.82 * 100_000,
    # "We found the seroprevalence (+/− 1%) in healthy adult blood donors
    # (1501) was [...] BCV (82%)[...]"
    # Note that these were blood donors, and thus aren't representative of the
    # general population.
    number_of_participants=1501,
    # Plasma samples from healthy adult blood donors were obtained (May and June, 2007) from Bonfils Blood Center (Denver), and pediatric plasma samples were obtained from The Children's Hospital (Denver)
    country="United States",
    date="2007",
    # Study is from 2009, sera are from 2007
    active=Active.LATENT,
    source="https://journals.plos.org/plospathogens/article?id=10.1371/journal.ppat.1000363#:~:text=We%20found%20the%20seroprevalence%20(%2B/%E2%88%92%201%25)%20in%20healthy%20adult%20blood%20donors%20(1501)%20was%20SV40%20(9%25)%2C%20BKV%20(82%25)%2C%20JCV%20(39%25)%2C%20LPV",
    # A tabular breakdown can be found here: "https://journals.plos.org/plospathogens/article?id=10.1371/journal.ppat.1000363#:~:text=original%20image-,Table%201.,-Seroprevalence%20of%20polyomaviruses"
)


def estimate_prevalences() -> list[Prevalence]:
    # BK Virus has no clinical relevance for most individuals, and is not
    # targeted by treatments or vaccines. We can thus extrapolate 2007 data to
    # 2019-2021.

    us_2020 = dataclasses.replace(
        us_2007_seroprevalence, date_source=Variable(date="2020")
    )
    us_2021 = dataclasses.replace(
        us_2007_seroprevalence, date_source=Variable(date="2021")
    )
    # Due to a lack of polyomavirus prevalence data for Denmark, we
    # extrapolate Swiss data from 2009 to Denmark, 2015-2018.
    # Originally we intended to use the same Dutch study as used in mcv.py:
    # https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0206273#pone.0206273.ref024:~:text=Table%202.%20Seropositivity%20numbers%20and%20seroprevalence."
    # Table 2, row 1, column 1.
    # But looking into the methods paper underlying the used immunoassay, we
    # found evidence for crossreactivity between JC Virus and BK Virus,
    # potentially leading to seroprevalence measurements that are
    # overestimates. https://journals.asm.org/doi/full/10.1128/jcm.01566-17#:~:text=Preincubation%20with%20JCPyV,S6B1%20and%20B3).
    dk_2015 = dataclasses.replace(
        ch_2009_seroprevalence,
        date_source=Variable(date="2015"),
        location_source=Variable(country="Denmark"),
    )
    dk_2016 = dataclasses.replace(
        ch_2009_seroprevalence,
        date_source=Variable(date="2016"),
        location_source=Variable(country="Denmark"),
    )
    dk_2017 = dataclasses.replace(
        ch_2009_seroprevalence,
        date_source=Variable(date="2017"),
        location_source=Variable(country="Denmark"),
    )
    dk_2018 = dataclasses.replace(
        ch_2009_seroprevalence,
        date_source=Variable(date="2018"),
        location_source=Variable(country="Denmark"),
    )
    # Not included due to being a Group 2 virus (i.e., a virus we picked once
    # we saw it was high relative abundance in sequencing data. This post-hoc
    # selection is hard to explain and doesn't add much to the results due to
    # the connnected selection bias.)
    return []


def estimate_incidences():
    return []
