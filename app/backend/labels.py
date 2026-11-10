LABEL_NAMES = {
    "caution_and_advice": "Precauciones y consejos",
    "displaced_people_and_evacuations": "Desplazados y evacuaciones",
    "infrastructure_and_utility_damage": "Daños en infraestructura y servicios",
    "injured_or_dead_people": "Heridos o fallecidos",
    "missing_or_found_people": "Personas desaparecidas o encontradas",
    "not_humanitarian": "No humanitario",
    "other_relevant_information": "Otra información relevante",
    "requests_or_urgent_needs": "Solicitudes o necesidades urgentes",
    "rescue_volunteering_or_donation_effort": "Rescate, voluntariado o donaciones",
    "sympathy_and_support": "Solidaridad y apoyo",
}

# Response fronts used by the information center; every label belongs to exactly one.
GROUPS = [
    {"id": "personas", "name": "Personas", "color": "red",
     "labels": ["injured_or_dead_people", "missing_or_found_people", "displaced_people_and_evacuations"]},
    {"id": "necesidades", "name": "Necesidades y ayuda", "color": "orange",
     "labels": ["requests_or_urgent_needs", "rescue_volunteering_or_donation_effort"]},
    {"id": "infraestructura", "name": "Infraestructura y avisos", "color": "amber",
     "labels": ["infrastructure_and_utility_damage", "caution_and_advice"]},
    {"id": "contexto", "name": "Contexto", "color": "slate",
     "labels": ["other_relevant_information", "sympathy_and_support", "not_humanitarian"]},
]

GROUP_OF = {label: group["id"] for group in GROUPS for label in group["labels"]}
