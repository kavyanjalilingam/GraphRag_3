from dataclasses import dataclass, asdict
from typing import Optional

# Vertex Models

@dataclass
class Company:
    ticker: str
    name: str

@dataclass
class Filing:
    accession: str
    ticker: str
    form: str
    filing_date: str
    event_date: Optional[str] = None

@dataclass
class MetricDefinition:
    name: str

@dataclass
class MetricObservation:
    id: str  # ticker|metric|period|units|scope
    ticker: str
    accession: str
    period: str
    value: float
    unit: str
    scope: str
    raw_label: str

@dataclass
class CorporateEvent:
    id: str  # ticker|eventType|date|accession
    ticker: str
    event_type: str
    date: str
    accession: str
    description: str

@dataclass
class AuditFirm:
    name: str

@dataclass
class Person:
    id: str  # company|name
    ticker: str
    name: str

@dataclass
class RoleAssignment:
    id: str  # company|name|role
    person_id: str
    company_id: str
    role: str

@dataclass
class SourceSpan:
    id: str  # accession|span
    accession: str
    span: str

# Edge Models

@dataclass
class FiledEdge:
    company_id: str
    filing_id: str

@dataclass
class ReportsEdge:
    filing_id: str
    observation_id: str
    source_spans: str  # comma separated
    confidence: str

@dataclass
class OfMetricEdge:
    observation_id: str
    definition_id: str

@dataclass
class DisclosesEdge:
    filing_id: str
    event_id: str
    source_spans: str
    confidence: str

@dataclass
class AuditedByEdge:
    company_id: str
    firm_id: str
    filing_accession: str
    source_spans: str
    confidence: str

@dataclass
class RoleHeldEdge:
    person_id: str
    role_id: str
    filing_accession: str
    source_spans: str
    confidence: str

@dataclass
class HasEvidenceEdge:
    source_id: str
    target_id: str  # observation_id, event_id, role_id, etc.
    span_id: str

@dataclass
class HasSpanEdge:
    filing_id: str
    span_id: str
