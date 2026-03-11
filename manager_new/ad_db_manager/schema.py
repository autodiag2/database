from pydantic import BaseModel
from typing import List, Union

class Scope(BaseModel):
    years: Union[str, List[int]]
    ecu: List[str]
    manufacturer: Union[str, List[str]]
    model: List[str]
    engine: List[str]
    protocol: List[str]
    standard: List[str]

class Evidence(BaseModel):
    source: List[str]

class DTC(BaseModel):
    scope: Scope
    code: str
    system: str
    subsystem: str
    category: str
    definition: str
    description: str
    severity: str
    mil: str
    created: str
    updated: str
    related_code: List[str]
    detection_condition: List[str]
    causes: List[str]
    repairs: List[str]
    evidence: Evidence