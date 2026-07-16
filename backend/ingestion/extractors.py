"""
Entity Extraction Engine
-------------------------
Rule/regex + heuristic extraction of industrial entities from raw text.
This is intentionally dependency-light (no heavyweight NER model download
required) so the platform runs fully offline, while still reliably pulling
out the structured fields the Knowledge Graph and Agents rely on:

  Equipment IDs, Pressure, Temperature, Dates, Personnel, Compliance
  references, Hazards, Regulatory codes, Failure causes, Manufacturers,
  Serial numbers, Locations/Plants.

In production this module is the natural place to swap in a fine-tuned
transformer NER model (e.g. via spaCy or HuggingFace) behind the same
`extract_entities()` interface -- nothing downstream needs to change.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict

EQUIPMENT_PATTERN = re.compile(r"\b([A-Z]{1,4}-\d{2,4}[A-Z]?)\b")
# Prefixes that match the equipment pattern shape (LETTERS-NUMBERS) but are
# actually regulation codes or document numbers, not physical equipment tags.
_NON_EQUIPMENT_PREFIXES = {"OISD", "PESO", "ISO", "SOP", "WO", "DOC", "SN"}
PRESSURE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(psi|bar|kpa|mpa)\b", re.I)
TEMP_PATTERN = re.compile(r"(-?\d+(?:\.\d+)?)\s*(°?\s?c|°?\s?f|deg\s?c|deg\s?f)\b", re.I)
DATE_PATTERN = re.compile(
    r"\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4}-\d{2}-\d{2}|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b"
)
SERIAL_PATTERN = re.compile(r"\b(?:S\/?N|Serial\s?No\.?)[:\s]*([A-Z0-9\-]{4,20})\b", re.I)
REGULATION_PATTERN = re.compile(
    r"\b(ISO\s?\d{4,5}(?::\d{4})?|OISD[-\s]?\d{1,4}|PESO[-\s]?[A-Z0-9]*|"
    r"Factory\s+Act(?:\s+\d{4})?|OSHA\s?\d{4}\.\d+)\b", re.I
)
HAZARD_KEYWORDS = [
    "flammable", "toxic", "explosion", "corrosive", "leak", "overpressure",
    "fire", "gas release", "electrical hazard", "confined space", "radiation",
    "chemical spill", "asphyxiation", "high voltage",
]
FAILURE_KEYWORDS = [
    "bearing failure", "seal leak", "corrosion", "cavitation", "overheating",
    "vibration", "misalignment", "fatigue crack", "wear", "electrical fault",
    "pump trip", "motor burnout", "valve stuck", "erosion", "fouling",
]
MANUFACTURER_PATTERN = re.compile(
    r"\b(Siemens|Honeywell|GE|Emerson|ABB|Schneider Electric|Grundfos|"
    r"Flowserve|Sulzer|KSB|Weir|Rockwell Automation)\b", re.I
)
PERSONNEL_PATTERN = re.compile(
    r"\b(?:Technician|Engineer|Inspector|Supervisor|Reported\s+by|Approved\s+by)[:\s]+([A-Z][a-z]+\s[A-Z][a-z]+)"
)
PLANT_PATTERN = re.compile(r"\b(Plant\s?[A-Z0-9]+|Unit\s?\d+|Building\s?[A-Z0-9]+)\b", re.I)


@dataclass
class ExtractedEntities:
    equipment_ids: list = field(default_factory=list)
    pressures: list = field(default_factory=list)
    temperatures: list = field(default_factory=list)
    dates: list = field(default_factory=list)
    personnel: list = field(default_factory=list)
    regulations: list = field(default_factory=list)
    hazards: list = field(default_factory=list)
    failure_causes: list = field(default_factory=list)
    manufacturers: list = field(default_factory=list)
    serial_numbers: list = field(default_factory=list)
    plants: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


def _uniq(seq):
    seen, out = set(), []
    for s in seq:
        key = s.strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(s.strip())
    return out


def extract_entities(text: str) -> ExtractedEntities:
    if not text:
        return ExtractedEntities()

    ents = ExtractedEntities()
    raw_equipment = EQUIPMENT_PATTERN.findall(text)
    ents.equipment_ids = _uniq([
        e for e in raw_equipment if e.split("-")[0].upper() not in _NON_EQUIPMENT_PREFIXES
    ])
    ents.pressures = _uniq([f"{v} {u.upper()}" for v, u in PRESSURE_PATTERN.findall(text)])
    ents.temperatures = _uniq([f"{v}°{u.strip()[-1].upper()}" for v, u in TEMP_PATTERN.findall(text)])
    ents.dates = _uniq(DATE_PATTERN.findall(text))
    ents.serial_numbers = _uniq(SERIAL_PATTERN.findall(text))
    ents.regulations = _uniq(REGULATION_PATTERN.findall(text))
    ents.manufacturers = _uniq(MANUFACTURER_PATTERN.findall(text))
    ents.personnel = _uniq(PERSONNEL_PATTERN.findall(text))
    ents.plants = _uniq(PLANT_PATTERN.findall(text))

    low = text.lower()
    ents.hazards = _uniq([h for h in HAZARD_KEYWORDS if h in low])
    ents.failure_causes = _uniq([f for f in FAILURE_KEYWORDS if f in low])

    return ents