"""
Sélecteurs CSS/XPath pour l'extraction des données d'essais cliniques.
Ce fichier contient tous les sélecteurs utilisés pour extraire les données
des différentes sections du document HTML.
"""

# Sélecteurs pour l'en-tête
HEADER_SELECTORS = {
    "title": "p.bolder:-soup-contains('Title:') + p",
    "euct_number": "p.bolder:-soup-contains('EUCT number:') + p",
    "protocol_code": "p.bolder:-soup-contains('Protocol code:') + p",
}

# Sélecteurs pour la section Summary
SUMMARY_SELECTORS = {
    "section": "div#summary",
    "trial_information": {
        "section": "div#trial_information",
        "medical_condition": "p.bolder:-soup-contains('Medical condition') + p",
        "trial_phase": "p.bolder:-soup-contains('Trial Phase:') + p",
        "transition_trial": "p.bolder:-soup-contains('Transition Trial:') + p",
        "sponsor": "p.bolder:-soup-contains('Sponsor:') + p",
        "participants_type": "p.bolder:-soup-contains('Participants type:') + p",
        "age_range": "p.bolder:-soup-contains('Age range:') + p",
        "locations": "p.bolder:-soup-contains('Locations:') + p",
        "main_objective": "p.bolder:-soup-contains('Main objective') + p",
    },
    "overall_trial_status": {
        "section": "div#overall_trial_status",
        "status": "p.bolder:-soup-contains('Overall trial status:') + p",
        "start_date": "p.bolder:-soup-contains('Start of Trial:') + p",
        "end_date": "p.bolder:-soup-contains('End of trial:') + p",
        "global_end_date": "p.bolder:-soup-contains('Global end of trial:') + p",
        "application_trial_status": "p.bolder:-soup-contains('Application Trial Status:') + table",
    },
    "trial_notifications": {
        "section": "div#trial_notifications",
        "countries": "div#trial_notifications h3",
        "start_trial": "p.bolder:-soup-contains('Start of trial:') + p",
        "restart_trial": "p.bolder:-soup-contains('Restart trial:') + p",
        "end_trial": "p.bolder:-soup-contains('End of trial:') + p",
        "early_termination": "p.bolder:-soup-contains('Early termination:') + p",
        "termination_reason": "p.bolder:-soup-contains('Reason for early termination:') + p",
    },
    "recruitment_notifications": {
        "section": "div#recruitment_notifications",
        "countries": "div#recruitment_notifications h3",
        "start_recruitment": "p.bolder:-soup-contains('Start of recruitment:') + p",
        "restart_recruitment": "p.bolder:-soup-contains('Restart of recruitment:') + p",
        "end_recruitment": "p.bolder:-soup-contains('End of recruitment:') + p",
    },
    "trial_duration": {
        "section": "div#trial_duration",
        "estimated_recruitment_start": "p.bolder:-soup-contains('Estimated recruitment start date') + p",
        "estimated_end_date": "p.bolder:-soup-contains('Estimated end of trial date') + p",
        "estimated_global_end_date": "p.bolder:-soup-contains('Estimated global end date') + p",
    },
    "applications": {
        "section": "div#applications",
        "applications": "div#applications h3",
        "application_type": "p.bolder:-soup-contains('Application type:') + p",
        "submission_date": "p.bolder:-soup-contains('Submission date:') + p",
        "assessment_part1": {
            "section": "h4:-soup-contains('Assessment Part I')",
            "reference_member_state": "p.bolder:-soup-contains('Reference Member State:') + p",
            "conclusion": "p.bolder:-soup-contains('Final conclusion:') + p",
            "reporting_date": "p.bolder:-soup-contains('Conclusion reporting date:') + p",
        },
        "assessment_part2": {
            "section": "h4:-soup-contains('Assessment Part II')",
            "table": "h4:-soup-contains('Assessment Part II') + table",
        },
        "decision": {
            "section": "h4:-soup-contains('Decision')",
            "table": "h4:-soup-contains('Decision') + table",
        },
    },
}

# Sélecteurs pour la section Trial Information
TRIAL_INFO_SELECTORS = {
    "section": "div#full_trial_info",
    "trial_details": {
        "section": "div#trial_details",
        "trial_identifiers": {
            "section": "h3:-soup-contains('Trial identifiers')",
            "eu_trial_number": "p.bolder:-soup-contains('EU trial number:') + p",
            "full_title": "p.bolder:-soup-contains('Full title') + p",
            "public_title": "p.bolder:-soup-contains('Public title') + p",
            "protocol_code": "p.bolder:-soup-contains('Protocol code:') + p",
        },
        "trial_information": {
            "section": "h3:-soup-contains('Trial Information')",
            "trial_phase": "p.bolder:-soup-contains('Trial phase:') + p",
            "medical_condition": "p.bolder:-soup-contains('Medical condition') + p",
            "therapeutic_area": "p.bolder:-soup-contains('Therapeutic area:') + p",
            "main_objective": "p.bolder:-soup-contains('Main objective') + p",
        },
        "inclusion_criteria": {
            "section": "h4:-soup-contains('Principal inclusion criteria')",
            "table": "h4:-soup-contains('Principal inclusion criteria') + table",
        },
        "exclusion_criteria": {
            "section": "h4:-soup-contains('Principal exclusion criteria')",
            "table": "h4:-soup-contains('Principal exclusion criteria') + table",
        },
        "primary_endpoints": {
            "section": "h4:-soup-contains('Primary end points')",
            "table": "h4:-soup-contains('Primary end points') + table",
        },
        "secondary_endpoints": {
            "section": "h4:-soup-contains('Secondary end points')",
            "table": "h4:-soup-contains('Secondary end points') + table",
        },
    },
    "products": {
        "section": "div#products",
        "product_sections": "div#products > h3",
        "product_details": {
            "name": "p.bolder:-soup-contains('Medicinal product name:') + p",
            "id": "p.bolder:-soup-contains('EU medicinal product number') + p",
            "form": "p.bolder:-soup-contains('Pharmaceutical form:') + p",
            "role": "p.bolder:-soup-contains('Medicinal product role in trial:') + p",
        },
        "product_characteristics": {
            "characteristics": "p.bolder:-soup-contains('Medicinal product characteristics:') + p",
        },
        "dosage": {
            "route": "p.bolder:-soup-contains('Route of administration:') + p",
            "duration": "p.bolder:-soup-contains('Maximum duration of treatment:') + p",
            "daily_dose": "p.bolder:-soup-contains('Maximum daily dose allowed:') + p",
            "total_dose": "p.bolder:-soup-contains('Maximum total dose allowed:') + p",
        },
        "active_substance": {
            "name": "p.bolder:-soup-contains('Active Substance name:') + p",
            "code": "p.bolder:-soup-contains('EU Active Substance Code:') + p",
        },
    },
}

# Sélecteurs pour la section Trial Results
TRIAL_RESULTS_SELECTORS = {
    "section": "div#trial_results",
    "summaries": "h2#results_summary",
    "layperson_summaries": "h2#layperson_results_summary",
    "clinical_study_reports": "h2#clinical_study_reports",
}

# Sélecteurs pour la section Locations and Contact
LOCATIONS_SELECTORS = {
    "section": "div#locations",
    "countries": "div#locations > div > h3",
    "planned_subjects": "p.bolder:-soup-contains('Planned number of subjects:') + p",
    "sites": {
        "section": "h4",
        "oms_id": "p.bolder:-soup-contains('OMS ID:') + p",
        "department": "p.bolder:-soup-contains('Department name:') + p",
        "location": "p.bolder:-soup-contains('Site location:') + p",
        "address": "p.bolder:-soup-contains('Site street address:') + p",
        "city": "p.bolder:-soup-contains('Site city:') + p",
        "post_code": "p.bolder:-soup-contains('Site post code:') + p",
        "country": "p.bolder:-soup-contains('Site country:') + p",
        "contact_first_name": "p.bolder:-soup-contains('First name:') + p",
        "contact_last_name": "p.bolder:-soup-contains('Last name:') + p",
        "contact_title": "p.bolder:-soup-contains('Title:') + p",
        "contact_phone": "p.bolder:-soup-contains('Telephone number:') + p",
        "contact_email": "p.bolder:-soup-contains('Email:') + p",
    },
    "sponsors": {
        "section": "h2#sponsors",
        "sponsor_details": {
            "id": "p.bolder:-soup-contains('ID:') + p",
            "name": "p.bolder:-soup-contains('Name of sponsor organisation:') + p",
            "address": "p.bolder:-soup-contains('Address:') + p",
            "city": "p.bolder:-soup-contains('Town/City:') + p",
            "post_code": "p.bolder:-soup-contains('Post code:') + p",
            "country": "p.bolder:-soup-contains('Country:') + p",
            "phone": "p.bolder:-soup-contains('Phone:') + p",
            "email": "p.bolder:-soup-contains('Email address:') + p",
        },
        "scientific_contact": {
            "name": "h4:-soup-contains('Scientific contact point') + p.bolder:-soup-contains('Name of organisation:') + p",
            "contact_name": "h4:-soup-contains('Scientific contact point') + p.bolder:-soup-contains('Functional contact point name:') + p",
            "phone": "h4:-soup-contains('Scientific contact point') + p.bolder:-soup-contains('Phone:') + p",
            "email": "h4:-soup-contains('Scientific contact point') + p.bolder:-soup-contains('Email address:') + p",
        },
        "public_contact": {
            "name": "h4:-soup-contains('Public contact point') + p.bolder:-soup-contains('Name of organisation:') + p",
            "contact_name": "h4:-soup-contains('Public contact point') + p.bolder:-soup-contains('Functional contact point name:') + p",
            "phone": "h4:-soup-contains('Public contact point') + p.bolder:-soup-contains('Phone:') + p",
            "email": "h4:-soup-contains('Public contact point') + p.bolder:-soup-contains('Email address:') + p",
        },
    },
}