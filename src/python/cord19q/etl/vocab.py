"""
Vocabulary module

Credit to https://www.kaggle.com/savannareid for providing keywords and analysis.
"""

class Vocab(object):
    """
    Defines vocabulary terms for studies.
    """

    # Level of Evidence vocabulary and keywords
    SYSTEMATIC_REVIEW = ["systematic review", "meta-analysis", "pooled odds ratio", "Cohen's d", "difference in means", "difference between means",
                         "d-pooled", "pooled adjusted odds ratio", "pooled or", "pooled aor", "pooled risk ratio", "pooled rr",
                         "pooled relative risk", "cochrane review", "prisma", "cohen's kappa", "databases searched"]

    RANDOMIZED_CONTROL_TRIAL = ["treatment arm", "placebo", "blind", "double-blind", "control arm", "rct", "randomized", "treatment effect",
                                "randomization method", "randomized controlled trial", "randomized clinical trial", "randomised",
                                "randomisation", "consort"]

    PSEUDO_RANDOMIZED_CONTROL_TRIAL = ["quasi-randomized", "pseudo-randomized", "non-randomized", "quasi-randomised", "pseudo-randomised",
                                       "non-randomised", "control arm", "treatment arm", "placebo", "blind", "double-blind", "treatment effect",
                                       "allocation method"]

    GENERIC_L3 = ["risk factor analysis", "risk factors", "etiology", "logistic regression", "odds ratio", "adjusted odds ratio", "aor",
                  "log odds", "incidence", "exposure status", "electronic medical records", "chart review", "medical records review"]

    RETROSPECTIVE_COHORT = ["cohort", "retrospective cohort", "retrospective chart review", "association between", "associated with",
                            "data collection instrument", "eligibility criteria", "recruitment", "potential confounders",
                            "data abstraction forms", "inter-rater reliability", "cohen's kappa"]

    GENERIC_CASE_CONTROL = ["data collection instrument", "survey instrument", "association between", "associated with", "response rate",
                            "questionnaire development", "psychometric evaluation of instrument", "eligibility criteria", "recruitment",
                            "potential confounders", "non-response bias"]

    MATCHED_CASE_CONTROL = ["cohort", "matching criteria", "number of controls per case"]

    CROSS_SECTIONAL_CASE_CONTROL = ["prevalence survey"]

    TIME_SERIES_ANALYSIS = ["survival analysis", "time-to-event analysis", "weibull", "gamma", "lognormal", "estimation", "kaplan-meier",
                            "hazard ratio", "cox proportional hazards", "etiology", "median time to event", "cohort", "censoring", "truncated",
                            "right-censored", "non-comparative study", "longitudinal", "eligibility criteria", "recruitment", "potential confounders"]

    PREVALENCE_STUDY = ["prevalence", "syndromic surveillance", "surveillance", "registry data", "frequency", "risk factors", "etiology",
                        "cross-sectional survey", "logistic regression", "odds ratio", "log odds", "adjusted odds ratio", "aor",
                        "data collection instrument", "survey instrument", "association between", "associated with", "random sample",
                        "response rate", "questionnaire development", "psychometric evaluation of instrument", "eligibility criteria",
                        "recruitment", "potential confounders"]

    COMPUTER_MODEL = ["mathematical model", "mathematical modeling", "computer model", "computer modeling", "model simulation",
                      "forecast", "forecasting"]
