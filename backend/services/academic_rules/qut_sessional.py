"""QUT sessional academic activity rates effective from December 2025."""


class QUTSessionalAcademicRules:
    SCHEME = {
        "key": "qut_sessional",
        "label": "QUT Sessional Academic Staff",
        "minimum_engagement_hours": 2,
        "repeat_window_days": 7,
        "sources": [
            {
                "label": "QUT Academic Enterprise Agreement 2022-2025",
                "url": "https://cms.qut.edu.au/__data/assets/pdf_file/0010/974026/2022-2025-QUT-Enterprise-Agreement-Academic-2022-2025.pdf",
            },
            {
                "label": "Sessional Academic Staff salary schedule",
                "url": "https://cms.qut.edu.au/__data/assets/pdf_file/0007/974023/Salary-Scales-Sessional-Academic-Staff_2025.12.13.pdf",
            },
        ],
    }

    ELIGIBILITY = {
        "standard": "Standard sessional rate",
        "relevant_phd": "Relevant doctoral qualification",
        "full_coordinator": "Full course/unit coordination duties",
    }

    # Rate codes always store the published amount directly. Composite rates
    # must not be rebuilt from a generic hourly rate.
    RATE_SCHEDULES = [
        {
            "effective_from": "2025-12-13",
            "rates": {
                "CAAAR": 55.11,
                "CAAAS": 65.86,
                "CACNK": 110.32,
                "CACNL": 82.72,
                "CACNM": 132.09,
                "CACNN": 98.90,
                "CALRA": 232.33,
                "CALRB": 310.20,
                "CALRC": 387.97,
                "CALRD": 154.73,
                "CAMAI": 110.33,
                "CAMAJ": 132.09,
                "CAMGO": 77.26,
                "CAMGP": 55.11,
                "CAMGQ": 65.86,
                "CATRE": 165.64,
                "CATRF": 110.32,
                "CATRG": 198.27,
                "CATRH": 132.09,
            },
        }
    ]

    ACTIVITIES = {
        "tutorial": {
            "label": "Tutorial",
            "payment_basis": "composite_unit",
            "quantity_label": "Tutorial delivery hours",
            "quantity_help": "Enter tutorial time delivered. The published rate already includes associated working time.",
            "course_required": True,
            "topic_required": True,
            "repeatable": True,
            "variants": {"normal": "Normal tutorial"},
            "default_variant": "normal",
            "classifications": {
                "normal:standard": {"rate_code": "CATRE", "incorporated_hours": 2, "label": "Normal tutorial"},
                "normal:higher": {"rate_code": "CATRG", "incorporated_hours": 2, "label": "Normal tutorial - PhD/coordinator"},
                "repeat:standard": {"rate_code": "CATRF", "incorporated_hours": 1, "label": "Repeat tutorial"},
                "repeat:higher": {"rate_code": "CATRH", "incorporated_hours": 1, "label": "Repeat tutorial - PhD/coordinator"},
            },
        },
        "lecture": {
            "label": "Lecture",
            "payment_basis": "composite_unit",
            "quantity_label": "Lecture delivery hours",
            "quantity_help": "Enter lecture time delivered. The published rate already includes associated working time.",
            "course_required": True,
            "topic_required": True,
            "repeatable": True,
            "variants": {
                "basic": "Basic lecture",
                "developed": "Developed lecture",
                "specialised": "Specialised lecture",
            },
            "default_variant": "basic",
            "classifications": {
                "basic:standard": {"rate_code": "CALRA", "incorporated_hours": 2, "label": "Basic lecture"},
                "developed:standard": {"rate_code": "CALRB", "incorporated_hours": 3, "label": "Developed lecture"},
                "specialised:standard": {"rate_code": "CALRC", "incorporated_hours": 4, "label": "Specialised lecture"},
                "repeat:standard": {"rate_code": "CALRD", "incorporated_hours": 1, "label": "Repeat lecture"},
            },
        },
        "clinical_health": {
            "label": "Clinical health education",
            "payment_basis": "composite_unit",
            "quantity_label": "Clinical delivery hours",
            "quantity_help": "Enter clinical education time delivered. The published rate already includes associated working time.",
            "course_required": True,
            "topic_required": False,
            "repeatable": False,
            "variants": {
                "normal_preparation": "Normal preparation",
                "little_preparation": "Little preparation",
            },
            "default_variant": "normal_preparation",
            "classifications": {
                "normal_preparation:standard": {"rate_code": "CACNK", "incorporated_hours": 1, "label": "Clinical health education - normal preparation"},
                "little_preparation:standard": {"rate_code": "CACNL", "incorporated_hours": 0.5, "label": "Clinical health education - little preparation"},
                "normal_preparation:higher": {"rate_code": "CACNM", "incorporated_hours": 1, "label": "Clinical health education - normal preparation, PhD/coordinator"},
                "little_preparation:higher": {"rate_code": "CACNN", "incorporated_hours": 0.5, "label": "Clinical health education - little preparation, PhD/coordinator"},
            },
        },
        "music_accompanying": {
            "label": "Music accompanying",
            "payment_basis": "composite_unit",
            "quantity_label": "Accompanying delivery hours",
            "quantity_help": "Enter accompanying time delivered. The published rate already includes associated working time.",
            "course_required": True,
            "topic_required": False,
            "repeatable": False,
            "variants": {"normal": "Music accompanying"},
            "default_variant": "normal",
            "classifications": {
                "normal:standard": {"rate_code": "CAMAI", "incorporated_hours": 1, "label": "Music accompanying"},
                "normal:higher": {"rate_code": "CAMAJ", "incorporated_hours": 1, "label": "Music accompanying - PhD/coordinator"},
            },
        },
        "marking": {
            "label": "Marking",
            "payment_basis": "direct_hour",
            "quantity_label": "Approved hours",
            "course_required": True,
            "topic_required": False,
            "repeatable": False,
            "requires_approval": True,
            "variants": {
                "standard": "Standard marking",
                "higher_level": "Higher-level marking",
            },
            "default_variant": "standard",
            "classifications": {
                "standard:standard": {"rate_code": "CAMGP", "incorporated_hours": 0, "label": "Standard marking"},
                "standard:higher": {"rate_code": "CAMGQ", "incorporated_hours": 0, "label": "Standard marking - PhD/coordinator"},
                "higher_level:standard": {"rate_code": "CAMGO", "incorporated_hours": 0, "label": "Higher-level marking"},
                "higher_level:higher": {"rate_code": "CAMGO", "incorporated_hours": 0, "label": "Higher-level marking"},
            },
        },
        "other_academic_activity": {
            "label": "Other required academic activity",
            "payment_basis": "direct_hour",
            "quantity_label": "Required hours",
            "course_required": False,
            "topic_required": False,
            "repeatable": False,
            "requires_approval": True,
            "variants": {
                "other": "Other required activity",
                "workshop": "Workshop",
                "practical": "Practical class",
                "non_health_clinical": "Non-health clinical session",
                "field_trip": "Student field trip",
                "performance": "Performance session",
                "simulation": "Simulation session",
                "studio": "Studio session",
                "supplementary_tuition": "Supplementary tuition",
                "supervision": "Supervision",
                "meeting": "Required meeting",
                "consultation": "Student consultation",
                "materials": "Teaching/subject materials",
            },
            "default_variant": "other",
            "classifications": {
                "other:standard": {"rate_code": "CAAAR", "incorporated_hours": 0, "label": "Other required academic activity"},
                "other:higher": {"rate_code": "CAAAS", "incorporated_hours": 0, "label": "Other required academic activity - PhD/coordinator"},
            },
            "variant_uses_default_classification": True,
        },
    }
