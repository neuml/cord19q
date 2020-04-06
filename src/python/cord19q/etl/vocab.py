"""
Vocabulary module

Credit to https://www.kaggle.com/savannareid for providing keywords and analysis.
"""

class Vocab(object):
    """
    Defines vocabulary terms for studies.
    """

    # Generic definitions
    GENERIC_CASE = ["chart review", "ehr", r"(?:electronic )?health records", r"(?:electronic )?medical records", "etiology", "exposure status",
                    "risk factor analysis", "risk factors"]

    GENERIC_COHORT = ["cohort", "followed", "loss to follow-up", "patients", "subjects"]

    GENERIC_STATS = ["adjusted odds ratio", "aor", "log odds", "logistic regression", "odds ratio"]

    # Systematic Review / Meta-Analysis
    SYSTEMATIC_REVIEW = ["cohen's d", "cochrane review", "cohen's kappa", r"database(?:s)? search(?:ed)?", "difference between means", "d-pooled",
                         "difference in means", "electronic search", "heterogeneity", "pooled relative risk", "meta-analysis",
                         "pooled adjusted odds ratio", "pooled aor", "pooled odds ratio", "pooled or", "pooled risk ratio", "pooled rr",
                         "prisma", "search criteria", "search strategy", "search string", "systematic review"]

    # Experimental Studies
    RANDOMIZED = ["blind", "consort", "control arm", "double-blind", "placebo", "randomisation", "randomised", "randomization method", "randomized",
                  "randomized clinical trial", "randomized controlled trial", "rct", "treatment arm", "treatment effect"]

    NON_RANDOMIZED = ["allocation method", "blind", "control arm", "double-blind", "non-randomised", "non-randomized", "placebo", "pseudo-randomised",
                      "pseudo-randomized", "quasi-randomised", "quasi-randomized", "treatment arm", "treatment effect"]

    # Prospective Studies
    TIME_SERIES = ["adjusted hazard ratio", "censoring", "confounding", "covariates", "cox proportional hazards", "demographics",
                   r"enroll(?:ed|ment)?", "eligibility criteria", "etiology", "gamma", "hazard ratio", "kaplan-meier", "lognormal",
                   "longitudinal", "median time to event", "non-comparative study", "potential confounders", r"recruit(?:ed|ment)?",
                   "right-censored", "survival analysis", "time-to-event analysis", r"time[-\s]series", r"time[-\s]varying", "truncated",
                   "weibull"]

    PROSPECTIVE_COHORT = ["baseline", r"prospective(?:ly)?", "prospective cohort", "relative risk", "risk ratio", "rr"]
    PROSPECTIVE_COHORT += GENERIC_COHORT + GENERIC_STATS + TIME_SERIES

    ECOLOGICAL_REGRESSION = [r"correlation(?:s)?", "per capita", "r-squared"]
    ECOLOGICAL_REGRESSION += TIME_SERIES

    # Retrospective Studies
    RETROSPECTIVE_COHORT = ["cohen's kappa", "data abstraction forms", "data collection instrument", "eligibility criteria",
                            "inter-rater reliability", "potential confounders", "retrospective", "retrospective chart review",
                            "retrospective cohort"]
    RETROSPECTIVE_COHORT += GENERIC_CASE + GENERIC_COHORT + GENERIC_STATS

    CASE_CONTROL = ["case-control", "data collection instrument", "eligibility criteria", r"match(?:ed|ing)? case", r"match(?:ed|ing)? criteria",
                    "number of controls per case", "non-response bias", "potential confounders", "psychometric evaluation of instrument",
                    "questionnaire development", "response rate", "survey instrument"]
    CASE_CONTROL += GENERIC_CASE + GENERIC_STATS

    CROSS_SECTIONAL = [r"cross[\-\s]sectional", "prevalence survey"]
    CROSS_SECTIONAL += CASE_CONTROL

    # Case Studies
    CASE_STUDY = ["case report", "case series", "etiology", "frequency", "risk factors"]

    # Model Simulations
    SIMULATION = ["bootstrap", r"computer model(?:ing)?", r"forecast(?:ing)?", r"mathematical model(?:ing)?", "model simulation",
                  "monte carlo", r"simulat(?:e|ed|ion)", "synthetic", r"synthetic data(?:set(?:s)?)?"]
    SIMULATION += GENERIC_STATS
