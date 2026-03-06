> ⚠️ **Archived** — This document was written during initial development and
> references the Gemini API or earlier MVP assumptions. The system now uses OpenAI.
> Use the root `README.md` for setup and `doc/README.md` for document status.

# Service Architecture

This document defines the core service architecture for urbanIQ Berlin geodata aggregation system.

## Architecture Overview

The system follows a service-oriented architecture with four core services that orchestrate geodata acquisition, processing, and metadata generation.

**MVP Implementation Scope**: Initial version focuses on three core datasets: district boundaries, buildings from Berlin Geoportal, and public transport stops from OpenStreetMap. The AI service directly identifies and returns these specific datasets rather than using categorical mapping.

## 1. NLP Service (Gemini Integration)

**Purpose**: Parse natural language user requests to extract Berlin districts and data categories.

**Technology Stack**:

- LangChain Google GenAI integration
- Google Gemini 1.5 Pro model
- Temperature: 0.1 (deterministic parsing)

**Key Methods**:

### parse_user_request(text: str) → Dict[str, any]

Extracts structured information from natural language input and identifies relevant datasets.

**Input**: "Pankow Gebäude und ÖPNV-Haltestellen für Mobilitätsanalyse"
**Output**:

```json
{
  "bezirk": "Pankow",
  "datasets": ["gebaeude", "oepnv_haltestellen"],
  "confidence": 0.95
}
```

**Available Berlin Districts**:

- Mitte, Pankow, Charlottenburg-Wilmersdorf
- Spandau, Steglitz-Zehlendorf, Tempelhof-Schöneberg
- Neukölln, Treptow-Köpenick, Marzahn-Hellersdorf
- Lichtenberg, Reinickendorf, Friedrichshain-Kreuzberg

**Available Datasets (MVP)**:

- **gebaeude**: Building footprints and data (Berlin Geoportal)
- **oepnv_haltestellen**: Public transport stops (OpenStreetMap)

**Note**: District boundaries (`bezirksgrenzen`) are automatically retrieved for every request to enable spatial filtering and are not explicitly requested by users.

**Error Handling**:

- Confidence threshold: 0.7
- Fallback for ambiguous requests
- Suggestion generation for unclear input

## 2. Data Service (Connector Orchestration)

**Purpose**: Coordinate geodata acquisition from multiple external sources.

**Key Methods**:

### fetch_datasets_for_request(bezirk: str, datasets: List[str]) → List[Dict]

Orchestrates parallel data acquisition with automatic district boundary retrieval.

**Process Flow**:

1. **Always**: Load district boundary for the specified bezirk (spatial filtering)
2. Map requested datasets to data source endpoints
3. Execute parallel connector requests (Geoportal WFS + OSM Overpass)
4. Filter successful results and handle errors
5. Calculate runtime statistics

**Dataset Mapping (MVP)**:

- `bezirksgrenzen` → **Always retrieved**: `https://gdi.berlin.de/services/wfs/alkis_bezirke`
- `gebaeude` → `https://gdi.berlin.de/services/wfs/alkis_gebaeude`
- `oepnv_haltestellen` → `https://overpass-api.de/api/interpreter`

**Output Structure**:

```python
# Always included: District boundary
{
    "dataset_id": "bezirksgrenzen_pankow",
    "dataset_type": "bezirksgrenzen",
    "source": "geoportal",
    "geodata": GeoDataFrame,  # 1 district polygon
    "predefined_metadata": {
        "name": "Bezirksgrenzen Berlin",
        "description": "Administrative district boundaries",
        "license": "CC BY 3.0 DE",
        "update_frequency": "monthly"
    },
    "runtime_stats": {
        "feature_count": 1,
        "spatial_extent": [13.0, 52.3, 13.8, 52.7],
        "coverage_percentage": 100.0,
        "data_quality_score": 0.95
    }
},

# Requested datasets (example: buildings)
{
    "dataset_id": "gebaeude_pankow",
    "dataset_type": "gebaeude",
    "source": "geoportal",
    "geodata": GeoDataFrame,  # Buildings clipped to district
    "predefined_metadata": {
        "name": "Gebäudedaten Berlin",
        "description": "Building footprints and usage data",
        "license": "CC BY 3.0 DE",
        "update_frequency": "quarterly"
    },
    "runtime_stats": {
        "feature_count": 25000,
        "spatial_extent": [13.0, 52.3, 13.8, 52.7],
        "coverage_percentage": 95.0,
        "data_quality_score": 0.85
    }
}
```

**Error Resilience**:

- Timeout handling per connector
- Partial success scenarios
- Quality score calculation
- Coverage assessment

## 3. Processing Service (Data Harmonization)

**Purpose**: Standardize and combine geodata from multiple sources.

**Target CRS**: ETRS89/UTM33N (EPSG:25833) - Standard for Berlin

**Key Methods**:

### harmonize_datasets(datasets: List[Dict], target_boundary: GeoDataFrame) → GeoDataFrame

Harmonizes multiple geodatasets into unified format.

**Processing Steps**:

1. **CRS Standardization**: Transform all datasets to EPSG:25833
2. **Spatial Clipping**: Clip to target district boundary
3. **Schema Standardization**: Apply common attribute schema
4. **Data Combination**: Merge all datasets into single GeoDataFrame

**Standard Schema**:

```python
{
    "feature_id": "unique_identifier",
    "dataset_type": "bezirksgrenzen|gebaeude|oepnv_haltestellen",
    "source_system": "geoportal|osm",
    "bezirk": "target_district_name",  # Always included for spatial context
    "geometry": "standardized_geometry_column",
    # Dataset-specific attributes preserved
    "original_attributes": "dict_with_source_specific_fields"
}
```

**MVP Dataset Attributes**:

- **Bezirksgrenzen** (always included): `bezirk_name`, `bezirk_schluessel`, `flaeche_ha`
- **Gebäude** (on request): `nutzung`, `geschosse`, `baujahr`, `flaeche_m2`
- **ÖPNV-Haltestellen** (on request): `name`, `operator`, `transport_mode`, `line_refs`

**Quality Assurance**:

- Geometry validation
- Attribute completeness checks
- Spatial relationship verification
- Empty geometry handling

## 4. LLM Metadata Service

**Purpose**: Generate professional metadata reports using Gemini analysis.

**Key Methods**:

### create_metadata_report(datasets: List[Dict], bezirk: str, request_info: Dict) → str

Creates comprehensive metadata reports for geodata packages.

**Report Structure**:

```markdown
# Geodaten-Metadatenreport: [Bezirk]

## Übersicht

- Erstellungsdatum, Bezirk, Anzahl Datensätze
- Koordinatensystem: ETRS89/UTM Zone 33N
- Verfügbare Datenlayer: Bezirksgrenzen, Gebäude, ÖPNV-Haltestellen

## Enthaltene Datensätze

### Bezirksgrenzen (Berlin Geoportal) - Immer enthalten

- Beschreibung: Administrative Bezirksgrenzen für räumliche Filterung
- Features: 1 Polygon pro angefragtem Bezirk
- Aktualität: Monatlich aktualisiert
- Qualität: Sehr hoch (0.95)
- Verwendung: Automatisch abgerufen für jeden Request

### Gebäudedaten (Berlin Geoportal) - Auf Anfrage

- Beschreibung: Gebäudegrundrisse mit Nutzungsinformationen
- Features: ~25.000 Gebäude pro Bezirk (räumlich gefiltert)
- Aktualität: Quartalsweise aktualisiert
- Qualität: Hoch (0.85)

### ÖPNV-Haltestellen (OpenStreetMap) - Auf Anfrage

- Beschreibung: Haltestellen des öffentlichen Nahverkehrs
- Features: ~700 Haltestellen pro Bezirk (räumlich gefiltert)
- Aktualität: Täglich aktualisiert (Community-Daten)
- Qualität: Gut (0.80)

## Datenqualität und Vollständigkeit

- Gesamtbewertung der Datenabdeckung
- Bekannte Lücken und Einschränkungen
- Empfohlene Kombinationen für Analysen

## Nutzungsempfehlungen

- GIS-Software Hinweise (QGIS, ArcGIS)
- Analyse-Empfehlungen pro Datenlayer
- Räumliche Analysemöglichkeiten

## Rechtliche Hinweise

- Berlin Geoportal: CC BY 3.0 DE
- OpenStreetMap: Open Database License (ODbL)
```

**Context Preparation**:

- Dataset metadata aggregation
- Runtime statistics integration
- Usage note compilation
- Quality assessment summary

## API Specifications

### Berlin Geoportal WFS Services

**Bezirksgrenzen (District Boundaries)**:

- **Endpoint**: `https://gdi.berlin.de/services/wfs/alkis_bezirke`
- **Service Type**: WFS 2.0.0
- **Layer Name**: `alkis_bezirke:bezirke` (to be verified)
- **License**: Datenlizenz Deutschland – Zero – Version 2.0
- **CRS**: EPSG:25833 (ETRS89/UTM33N)
- **Contact**: fisbroker@senstadt.berlin.de

**Sample Request**:

```http
GET https://gdi.berlin.de/services/wfs/alkis_bezirke?
    SERVICE=WFS&
    VERSION=2.0.0&
    REQUEST=GetFeature&
    TYPENAME=alkis_bezirke:bezirke&
    OUTPUTFORMAT=application/json&
    CQL_FILTER=bezname='Pankow'
```

**Gebäude (Buildings)**:

- **Endpoint**: `https://gdi.berlin.de/services/wfs/alkis_gebaeude`
- **Service Type**: WFS 2.0.0
- **Layer Name**: `alkis_gebaeude:gebaeude` (to be verified)
- **License**: Datenlizenz Deutschland – Zero – Version 2.0
- **CRS**: EPSG:25833 (ETRS89/UTM33N)
- **Contact**: fisbroker@senstadt.berlin.de

**Sample Request**:

```http
GET https://gdi.berlin.de/services/wfs/alkis_gebaeude?
    SERVICE=WFS&
    VERSION=2.0.0&
    REQUEST=GetFeature&
    TYPENAME=alkis_gebaeude:gebaeude&
    OUTPUTFORMAT=application/json&
    BBOX=383000,5819000,384000,5820000,EPSG:25833
```

### OpenStreetMap Overpass API

**ÖPNV Haltestellen (Public Transport Stops)**:

- **Endpoint**: `https://overpass-api.de/api/interpreter`
- **Service Type**: Overpass QL
- **Query Type**: Nodes with `public_transport=stop_position`
- **License**: Open Database License (ODbL)
- **CRS**: WGS84 (EPSG:4326) - to be transformed to EPSG:25833

**Sample Query**:

```overpass
[out:json][timeout:25];
(
  node["public_transport"="stop_position"]
      ({{bbox}});
  node["highway"="bus_stop"]
      ({{bbox}});
);
out geom;
```

**Implementation Notes**:

- Bbox format: `south,west,north,east` in WGS84
- Transform coordinates from WGS84 to ETRS89/UTM33N
- Rate limiting: Max 2 requests per second
- Timeout: 25 seconds per request

## Service Integration

**Dependency Injection**: FastAPI dependency system
**Async Coordination**: asyncio.gather for parallel processing
**Error Propagation**: Structured exception hierarchy
**Resource Management**: Connection pooling and cleanup

## Performance Considerations

**Parallel Processing**: All external API calls run concurrently
**Caching Strategy**: API response caching for repeated requests
**Resource Limits**: Timeout configuration per service
**Memory Management**: Streaming processing for large datasets

## Monitoring and Logging

**Service Health Checks**: Individual service status monitoring
**Performance Metrics**: Response time and success rate tracking
**Error Logging**: Structured logging with correlation IDs
**Usage Analytics**: Request pattern analysis for optimization
