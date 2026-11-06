"""Mapeo único de las etiquetas de CrisisBench a las de HumAID.

HumAID es la referencia: sus etiquetas son las clases del proyecto. El mapeo solo se usa
para el test externo de Chile 2014 (CrisisBench no entra al entrenamiento). Las etiquetas
sin equivalente claro se descartan y se reportan, no se fuerzan a una clase.
"""

CRISISBENCH_TO_HUMAID = {
    "requests_or_needs": "requests_or_urgent_needs",
    "not_humanitarian": "not_humanitarian",
    "displaced_and_evacuations": "displaced_people_and_evacuations",
    "other_relevant_information": "other_relevant_information",
    "infrastructure_and_utilities_damage": "infrastructure_and_utility_damage",
    "caution_and_advice": "caution_and_advice",
    "sympathy_and_support": "sympathy_and_support",
    "donation_and_volunteering": "rescue_volunteering_or_donation_effort",
    "injured_or_dead_people": "injured_or_dead_people",
    "missing_and_found_people": "missing_or_found_people",
    # Sin equivalente directo en HumAID: se descartan del test de Chile.
    "affected_individual": None,
    "disease_related": None,
    "response_efforts": None,
    "personal_update": None,
    "physical_landslide": None,
    "terrorism_related": None,
}
