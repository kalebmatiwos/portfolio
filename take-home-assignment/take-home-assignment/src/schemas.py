"""
Pydantic schemas for the two GFW datasets this pipeline ingests.

Field names and nesting here are taken directly from the example
responses in GFW's own quick-start docs (Vessels search and Events),
not guessed. `extra="ignore"` on every model is deliberate: GFW can
add fields to their response without notice, and we don't want an
ingestion run to fail just because a new field showed up -- unknown
fields are dropped, not rejected. Missing REQUIRED fields is a
different story and does fail validation, on purpose.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class _Lenient(BaseModel):
    model_config = ConfigDict(extra="ignore")


# --- Vessels (search) ------------------------------------------------------


class SelfReportedInfo(_Lenient):
    id: str  # the internal vessel id the Events API expects
    ssvid: Optional[str] = None  # MMSI
    shipname: Optional[str] = None
    flag: Optional[str] = None
    callsign: Optional[str] = None
    imo: Optional[str] = None
    transmissionDateFrom: Optional[datetime] = None
    transmissionDateTo: Optional[datetime] = None


class RegistryInfo(_Lenient):
    id: Optional[str] = None
    ssvid: Optional[str] = None
    flag: Optional[str] = None
    shipname: Optional[str] = None
    callsign: Optional[str] = None
    imo: Optional[str] = None
    geartype: Optional[list[str]] = None
    lengthM: Optional[float] = None
    tonnageGt: Optional[float] = None


class VesselSearchEntry(_Lenient):
    dataset: Optional[str] = None
    registryInfo: list[RegistryInfo] = []
    # Required: a search result with no self-reported identity at all isn't
    # usable downstream -- there'd be no id to join events against.
    selfReportedInfo: list[SelfReportedInfo]


class VesselSearchResponse(_Lenient):
    limit: Optional[int] = None
    total: Optional[int] = None
    entries: list[VesselSearchEntry] = []


# --- Events ------------------------------------------------------------------


class EventPosition(_Lenient):
    lat: float
    lon: float


class EventRegions(_Lenient):
    mpa: list[str] = []
    eez: list[str] = []
    rfmo: list[str] = []
    fao: list[str] = []


class EventDistances(_Lenient):
    startDistanceFromShoreKm: Optional[float] = None
    endDistanceFromShoreKm: Optional[float] = None
    startDistanceFromPortKm: Optional[float] = None
    endDistanceFromPortKm: Optional[float] = None


class VesselAuthorization(_Lenient):
    rfmo: Optional[str] = None
    # The real API returns this as the string "false"/"true", not a JSON
    # boolean -- confirmed from a real sample, not assumed. Modeled as a
    # string on purpose rather than coercing it, since a silent bool
    # coercion here would hide that quirk instead of surfacing it.
    hasPubliclyListedAuthorization: Optional[str] = None


class EventVesselRef(_Lenient):
    id: str
    name: Optional[str] = None
    ssvid: Optional[str] = None
    # A compliance/risk signal, not incidental data -- whether the vessel
    # holds a publicly listed fishing authorization for the RFMO(s) it
    # operated under during this event. Present and non-empty in every
    # record checked in the real sample.
    publicAuthorizations: list[VesselAuthorization] = []


class FishingDetail(_Lenient):
    totalDistanceKm: Optional[float] = None
    averageSpeedKnots: Optional[float] = None
    averageDurationHours: Optional[float] = None
    potentialRisk: Optional[bool] = None
    # e.g. "not_matching_relevant_public_authorization" -- the same
    # authorization signal as EventVesselRef.publicAuthorizations, but
    # GFW's own derived summary of it rather than the raw listing.
    vesselPublicAuthorizationStatus: Optional[str] = None


class EventEntry(_Lenient):
    id: str
    type: str
    start: datetime
    end: datetime
    position: EventPosition
    regions: EventRegions = EventRegions()
    vessel: EventVesselRef
    distances: Optional[EventDistances] = None
    # Only populated for type == "fishing"; other event types (encounter,
    # loitering, port_visit) carry a different nested key instead, which
    # this pipeline doesn't model since we're only pulling the fishing
    # events dataset -- see README for how encounters/loitering would extend this.
    fishing: Optional[FishingDetail] = None
    # [minLon, minLat, maxLon, maxLat] by the numeric pattern in a real
    # sample, but GFW's docs don't explicitly confirm that ordering, so
    # this is kept as a plain array rather than decomposed into named
    # min/max lon/lat fields that would assert semantics not actually
    # confirmed. Present in every record checked.
    boundingBox: Optional[list[float]] = None


class EventsResponse(_Lenient):
    total: Optional[int] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    nextOffset: Optional[int] = None
    entries: list[EventEntry] = []
