#!/usr/bin/env python3
"""
Import or regenerate the v1.1 schema Kibana dashboards.

Usage:
    # Import into a running Kibana instance
    python update_kibana.py --kibana-url http://localhost:5601 --stack mds_elk

    # Just regenerate the NDJSON files without importing
    python update_kibana.py --generate-only

Both stacks (mds_elk, honeytraps) use the same index pattern and schema, so the
generated NDJSON is identical for each. Running with --stack just sets which
export.ndjson path to write/read from.
"""

import argparse
import json
import os
import sys
import time

try:
    import requests
except ImportError:
    requests = None

KIBANA_DEFAULT = "http://localhost:5601"
IMPORT_ENDPOINT = "/api/saved_objects/_import?overwrite=true"
KBN_HEADERS = {"kbn-xsrf": "true"}

# Stable IDs so repeated imports are idempotent.
IP_ID = "hp-attacks-index-pattern"
DASH_ID = "hp-dashboard-threat-intel"
VIZ_TIMELINE = "hp-viz-timeline"
VIZ_ATTACK_TYPE = "hp-viz-attack-types"
VIZ_SEVERITY = "hp-viz-severity"
VIZ_COUNTRIES = "hp-viz-countries"
VIZ_MITRE = "hp-viz-mitre"
VIZ_HONEYTRAP = "hp-viz-honeytrap"
VIZ_PERSONA = "hp-viz-persona"

INDEX_TITLE = "honeypot-attacks-*"

UPDATED_AT = "2026-06-11T00:00:00.000Z"


def _vis(vis_id, title, vis_type, params, aggs):
    """Return a Kibana 7.17 visualization saved-object dict."""
    vis_state = json.dumps(
        {"title": title, "type": vis_type, "params": params, "aggs": aggs, "listeners": {}},
        separators=(",", ":"),
    )
    search_source = json.dumps(
        {"index": IP_ID, "filter": [], "query": {"query": "", "language": "kuery"}},
        separators=(",", ":"),
    )
    return {
        "id": vis_id,
        "type": "visualization",
        "attributes": {
            "title": title,
            "visState": vis_state,
            "uiStateJSON": "{}",
            "description": "",
            "kibanaSavedObjectMeta": {"searchSourceJSON": search_source},
        },
        "references": [
            {
                "id": IP_ID,
                "name": "kibanaSavedObjectMeta.searchSourceJSON.index",
                "type": "index-pattern",
            }
        ],
        "migrationVersion": {"visualization": "7.14.0"},
        "updated_at": UPDATED_AT,
        "version": "WzEwMCwxXQ==",
    }


def build_objects():
    """Build all Kibana saved objects that make up the threat intelligence dashboard."""

    objects = []

    # -- Index pattern ---------------------------------------------------------
    # Lists the key v1.1 schema fields so Kibana can aggregate on them immediately.
    # Kibana will discover any additional sub-fields on first query.
    fields = [
        {"name": "@timestamp", "type": "date", "esTypes": ["date"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "event_type", "type": "string", "esTypes": ["keyword"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "event_envelope.version", "type": "string", "esTypes": ["keyword"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "event_envelope.node_id", "type": "string", "esTypes": ["keyword"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "event_envelope.honeypot_ip", "type": "string", "esTypes": ["keyword"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "event_envelope.aws_region", "type": "string", "esTypes": ["keyword"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "event_envelope.timestamp", "type": "string", "esTypes": ["keyword"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "persona_context.name", "type": "string", "esTypes": ["keyword"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "persona_context.profile", "type": "string", "esTypes": ["keyword"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "attack_classification.type", "type": "string", "esTypes": ["keyword"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "attack_classification.severity", "type": "string", "esTypes": ["keyword"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "attack_classification.honeytrap_triggered", "type": "boolean",
         "esTypes": ["boolean"], "count": 0, "scripted": False, "searchable": True,
         "aggregatable": True, "readFromDocValues": True},
        {"name": "attack_classification.honeytrap_rule_id", "type": "string",
         "esTypes": ["keyword"], "count": 0, "scripted": False, "searchable": True,
         "aggregatable": True, "readFromDocValues": True},
        {"name": "attack_classification.cve_triggered", "type": "string", "esTypes": ["keyword"],
         "count": 0, "scripted": False, "searchable": True, "aggregatable": True,
         "readFromDocValues": True},
        {"name": "mitre_attack", "type": "string", "esTypes": ["keyword"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "geoip2.country", "type": "string", "esTypes": ["keyword"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "geoip2.city", "type": "string", "esTypes": ["keyword"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "geoip2.asn", "type": "string", "esTypes": ["keyword"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "geoip2.isp", "type": "string", "esTypes": ["keyword"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "geoip2.latitude", "type": "number", "esTypes": ["float"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "geoip2.longitude", "type": "number", "esTypes": ["float"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "transaction.remote_address", "type": "string", "esTypes": ["keyword"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "transaction.remote_port", "type": "number", "esTypes": ["long"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "transaction.transaction_id", "type": "string", "esTypes": ["keyword"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "request.request_line", "type": "string", "esTypes": ["text"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": False, "readFromDocValues": False},
        {"name": "response.status", "type": "number", "esTypes": ["long"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "response.honeytoken_triggered", "type": "boolean", "esTypes": ["boolean"],
         "count": 0, "scripted": False, "searchable": True, "aggregatable": True,
         "readFromDocValues": True},
        {"name": "feed_metadata.batch_id", "type": "string", "esTypes": ["keyword"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "feed_metadata.export_timestamp", "type": "date", "esTypes": ["date"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "persona_rotation.previous_persona", "type": "string", "esTypes": ["keyword"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "persona_rotation.new_persona", "type": "string", "esTypes": ["keyword"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "persona_rotation.trigger", "type": "string", "esTypes": ["keyword"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "persona_rotation.trigger_detail", "type": "string", "esTypes": ["text"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": False, "readFromDocValues": False},
        {"name": "persona_rotation.timestamp", "type": "date", "esTypes": ["date"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
        {"name": "persona_rotation.shodan_honeyscore", "type": "number", "esTypes": ["float"], "count": 0,
         "scripted": False, "searchable": True, "aggregatable": True, "readFromDocValues": True},
    ]

    index_pattern = {
        "id": IP_ID,
        "type": "index-pattern",
        "attributes": {
            "title": INDEX_TITLE,
            "timeFieldName": "@timestamp",
            "fields": json.dumps(fields, separators=(",", ":")),
        },
        "migrationVersion": {"index-pattern": "7.6.0"},
        "references": [],
        "updated_at": UPDATED_AT,
        "version": "WzEsMV0=",
    }
    objects.append(index_pattern)

    # -- Visualizations --------------------------------------------------------

    # 1. Attack timeline (date histogram)
    objects.append(_vis(
        VIZ_TIMELINE,
        "Attack Timeline",
        "histogram",
        {
            "type": "histogram",
            "grid": {"categoryLines": False, "style": {"color": "#eee"}},
            "categoryAxes": [
                {"id": "CategoryAxis-1", "type": "category", "position": "bottom",
                 "show": True, "style": {}, "scale": {"type": "linear"},
                 "labels": {"show": True, "truncate": 100},
                 "title": {}}
            ],
            "valueAxes": [
                {"id": "ValueAxis-1", "name": "LeftAxis-1", "type": "value",
                 "position": "left", "show": True, "style": {},
                 "scale": {"type": "linear", "mode": "normal"},
                 "labels": {"show": True, "rotate": 0, "filter": False, "truncate": 100},
                 "title": {"text": "Count"}}
            ],
            "seriesParams": [
                {"show": True, "type": "histogram", "mode": "stacked",
                 "data": {"label": "Count", "id": "1"},
                 "valueAxis": "ValueAxis-1", "drawLinesBetweenPoints": True,
                 "showCircles": True}
            ],
            "addTooltip": True,
            "addLegend": True,
            "legendPosition": "right",
            "times": [],
            "addTimeMarker": False,
        },
        [
            {"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}},
            {"id": "2", "enabled": True, "type": "date_histogram", "schema": "segment",
             "params": {"field": "@timestamp", "useNormalizedEsInterval": True,
                        "interval": "auto", "drop_partials": False,
                        "min_doc_count": 1, "extended_bounds": {}}},
        ],
    ))

    # 2. Attack type breakdown (pie)
    objects.append(_vis(
        VIZ_ATTACK_TYPE,
        "Attack Type Breakdown",
        "pie",
        {
            "type": "pie",
            "addTooltip": True,
            "addLegend": True,
            "legendPosition": "right",
            "isDonut": True,
            "labels": {"show": False, "values": True, "last_level": True, "truncate": 100},
        },
        [
            {"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}},
            {"id": "2", "enabled": True, "type": "terms", "schema": "segment",
             "params": {"field": "attack_classification.type", "orderBy": "1",
                        "order": "desc", "size": 10,
                        "otherBucket": True, "otherBucketLabel": "Other",
                        "missingBucket": False, "missingBucketLabel": "Missing"}},
        ],
    ))

    # 3. Severity distribution (pie)
    objects.append(_vis(
        VIZ_SEVERITY,
        "Severity Distribution",
        "pie",
        {
            "type": "pie",
            "addTooltip": True,
            "addLegend": True,
            "legendPosition": "right",
            "isDonut": False,
            "labels": {"show": False, "values": True, "last_level": True, "truncate": 100},
        },
        [
            {"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}},
            {"id": "2", "enabled": True, "type": "terms", "schema": "segment",
             "params": {"field": "attack_classification.severity", "orderBy": "1",
                        "order": "desc", "size": 10,
                        "otherBucket": False, "otherBucketLabel": "Other",
                        "missingBucket": False, "missingBucketLabel": "Missing"}},
        ],
    ))

    # 4. Top source countries (horizontal bar)
    objects.append(_vis(
        VIZ_COUNTRIES,
        "Top Source Countries",
        "horizontal_bar",
        {
            "type": "histogram",
            "grid": {"categoryLines": False},
            "categoryAxes": [
                {"id": "CategoryAxis-1", "type": "category", "position": "left",
                 "show": True, "style": {}, "scale": {"type": "linear"},
                 "labels": {"show": True, "truncate": 100, "rotate": 0},
                 "title": {}}
            ],
            "valueAxes": [
                {"id": "ValueAxis-1", "name": "LeftAxis-1", "type": "value",
                 "position": "bottom", "show": True, "style": {},
                 "scale": {"type": "linear", "mode": "normal"},
                 "labels": {"show": True, "rotate": 0, "filter": True, "truncate": 100},
                 "title": {"text": "Count"}}
            ],
            "seriesParams": [
                {"show": True, "type": "histogram", "mode": "stacked",
                 "data": {"label": "Count", "id": "1"},
                 "valueAxis": "ValueAxis-1", "drawLinesBetweenPoints": True,
                 "showCircles": True}
            ],
            "addTooltip": True,
            "addLegend": True,
            "legendPosition": "right",
            "times": [],
            "addTimeMarker": False,
        },
        [
            {"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}},
            {"id": "2", "enabled": True, "type": "terms", "schema": "segment",
             "params": {"field": "geoip2.country", "orderBy": "1",
                        "order": "desc", "size": 15,
                        "otherBucket": False, "otherBucketLabel": "Other",
                        "missingBucket": True, "missingBucketLabel": "Unknown"}},
        ],
    ))

    # 5. MITRE ATT&CK techniques (table)
    objects.append(_vis(
        VIZ_MITRE,
        "MITRE ATT&CK Techniques",
        "table",
        {
            "perPage": 10,
            "showPartialRows": False,
            "showMetricsAtAllLevels": False,
            "sort": {"columnIndex": None, "direction": None},
            "showTotal": False,
            "totalFunc": "sum",
            "dimensions": {
                "metrics": [{"accessor": 1, "format": {"id": "number"}, "params": {},
                             "aggType": "count"}],
                "buckets": [{"accessor": 0, "format": {"id": "terms",
                             "params": {"id": "string", "otherBucketLabel": "Other",
                                        "missingBucketLabel": "Missing"}},
                             "params": {}, "aggType": "terms"}],
            },
        },
        [
            {"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}},
            {"id": "2", "enabled": True, "type": "terms", "schema": "bucket",
             "params": {"field": "mitre_attack", "orderBy": "1",
                        "order": "desc", "size": 20,
                        "otherBucket": False, "missingBucket": False}},
        ],
    ))

    # 6. Honeytrap trigger rate (metric)
    objects.append(_vis(
        VIZ_HONEYTRAP,
        "Honeytrap Triggers",
        "metric",
        {
            "addTooltip": True,
            "addLegend": False,
            "type": "metric",
            "metric": {
                "percentageMode": False,
                "useRanges": False,
                "colorSchema": "Green to Red",
                "metricColorMode": "None",
                "colorsRange": [{"from": 0, "to": 10000}],
                "labels": {"show": True},
                "invertColors": False,
                "style": {"bgFill": "#000", "bgColor": False, "labelColor": False,
                          "subText": "", "fontSize": 60},
            },
        },
        [
            {"id": "1", "enabled": True, "type": "count", "schema": "metric",
             "params": {},
             "label": "Total Honeytrap Triggers"},
            {"id": "2", "enabled": True, "type": "filters", "schema": "group",
             "params": {"filters": [
                 {"input": {"query": "attack_classification.honeytrap_triggered:true",
                            "language": "kuery"},
                  "label": "Honeytrap"},
             ]}},
        ],
    ))

    # 7. Persona breakdown (horizontal bar)
    objects.append(_vis(
        VIZ_PERSONA,
        "Active Persona Breakdown",
        "horizontal_bar",
        {
            "type": "histogram",
            "grid": {"categoryLines": False},
            "categoryAxes": [
                {"id": "CategoryAxis-1", "type": "category", "position": "left",
                 "show": True, "style": {}, "scale": {"type": "linear"},
                 "labels": {"show": True, "truncate": 200, "rotate": 0},
                 "title": {}}
            ],
            "valueAxes": [
                {"id": "ValueAxis-1", "name": "LeftAxis-1", "type": "value",
                 "position": "bottom", "show": True, "style": {},
                 "scale": {"type": "linear", "mode": "normal"},
                 "labels": {"show": True, "rotate": 0, "filter": True, "truncate": 100},
                 "title": {"text": "Count"}}
            ],
            "seriesParams": [
                {"show": True, "type": "histogram", "mode": "stacked",
                 "data": {"label": "Count", "id": "1"},
                 "valueAxis": "ValueAxis-1", "drawLinesBetweenPoints": True,
                 "showCircles": True}
            ],
            "addTooltip": True,
            "addLegend": True,
            "legendPosition": "right",
            "times": [],
            "addTimeMarker": False,
        },
        [
            {"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}},
            {"id": "2", "enabled": True, "type": "terms", "schema": "segment",
             "params": {"field": "persona_context.name", "orderBy": "1",
                        "order": "desc", "size": 10,
                        "otherBucket": False, "missingBucket": True,
                        "missingBucketLabel": "unknown"}},
        ],
    ))

    # -- Dashboard -------------------------------------------------------------
    # Each panel references a visualization by index in the references array.
    panels = [
        # row 1: timeline spans full width
        {"panelIndex": "1", "gridData": {"x": 0, "y": 0, "w": 48, "h": 10, "i": "1"},
         "version": "7.17.10", "type": "visualization",
         "panelRefName": "panel_1"},
        # row 2: attack type + severity side by side
        {"panelIndex": "2", "gridData": {"x": 0, "y": 10, "w": 24, "h": 12, "i": "2"},
         "version": "7.17.10", "type": "visualization",
         "panelRefName": "panel_2"},
        {"panelIndex": "3", "gridData": {"x": 24, "y": 10, "w": 24, "h": 12, "i": "3"},
         "version": "7.17.10", "type": "visualization",
         "panelRefName": "panel_3"},
        # row 3: countries + mitre
        {"panelIndex": "4", "gridData": {"x": 0, "y": 22, "w": 24, "h": 12, "i": "4"},
         "version": "7.17.10", "type": "visualization",
         "panelRefName": "panel_4"},
        {"panelIndex": "5", "gridData": {"x": 24, "y": 22, "w": 24, "h": 12, "i": "5"},
         "version": "7.17.10", "type": "visualization",
         "panelRefName": "panel_5"},
        # row 4: honeytrap metric + persona
        {"panelIndex": "6", "gridData": {"x": 0, "y": 34, "w": 12, "h": 10, "i": "6"},
         "version": "7.17.10", "type": "visualization",
         "panelRefName": "panel_6"},
        {"panelIndex": "7", "gridData": {"x": 12, "y": 34, "w": 36, "h": 10, "i": "7"},
         "version": "7.17.10", "type": "visualization",
         "panelRefName": "panel_7"},
    ]

    viz_ids = [VIZ_TIMELINE, VIZ_ATTACK_TYPE, VIZ_SEVERITY,
               VIZ_COUNTRIES, VIZ_MITRE, VIZ_HONEYTRAP, VIZ_PERSONA]

    dash_references = [
        {
            "id": IP_ID,
            "name": "kibanaSavedObjectMeta.searchSourceJSON.index",
            "type": "index-pattern",
        }
    ]
    for i, vid in enumerate(viz_ids, start=1):
        dash_references.append({"id": vid, "name": f"panel_{i}", "type": "visualization"})

    search_source = json.dumps(
        {"index": IP_ID, "filter": [], "query": {"query": "", "language": "kuery"}},
        separators=(",", ":"),
    )

    dashboard = {
        "id": DASH_ID,
        "type": "dashboard",
        "attributes": {
            "title": "Honeypot Threat Intelligence",
            "description": "Attack timeline, type breakdown, severity, GeoIP, MITRE ATT&CK, and honeytrap activity across both ELK stacks.",
            "panelsJSON": json.dumps(panels, separators=(",", ":")),
            "optionsJSON": json.dumps(
                {"useMargins": True, "syncColors": False, "hidePanelTitles": False},
                separators=(",", ":"),
            ),
            "timeRestore": False,
            "kibanaSavedObjectMeta": {"searchSourceJSON": search_source},
        },
        "references": dash_references,
        "migrationVersion": {"dashboard": "7.14.0"},
        "updated_at": UPDATED_AT,
        "version": "WzIwMCwxXQ==",
    }
    objects.append(dashboard)

    return objects


def write_ndjson(objects, path):
    """Serialise saved objects to NDJSON and write to path."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for obj in objects:
            f.write(json.dumps(obj, separators=(",", ":"), ensure_ascii=False))
            f.write("\n")
    print(f"Written {len(objects)} objects to {path}")


def wait_for_kibana(base_url, timeout=120):
    deadline = time.monotonic() + timeout
    print(f"Waiting for Kibana at {base_url} (up to {timeout}s)...")
    while time.monotonic() < deadline:
        try:
            r = requests.get(f"{base_url}/api/status", timeout=5)
            if r.status_code == 200:
                state = r.json().get("status", {}).get("overall", {}).get("state", "")
                if state == "green":
                    print("Kibana is ready.")
                    return
        except Exception:
            pass
        time.sleep(5)
    sys.exit(f"Kibana at {base_url} did not become ready within {timeout}s.")


def import_ndjson(base_url, ndjson_path):
    with open(ndjson_path, "rb") as f:
        r = requests.post(
            f"{base_url}{IMPORT_ENDPOINT}",
            headers=KBN_HEADERS,
            files={"file": ("export.ndjson", f, "application/ndjson")},
            timeout=30,
        )
    r.raise_for_status()
    result = r.json()
    if not result.get("success"):
        errors = result.get("errors", [])
        sys.exit(f"Import failed: {errors}")
    print(f"Imported {result.get('successCount', 0)} saved objects successfully.")


def main():
    parser = argparse.ArgumentParser(
        description="Import honeypot v1.1 Kibana dashboards or regenerate NDJSON files."
    )
    parser.add_argument(
        "--kibana-url", default=KIBANA_DEFAULT,
        help="Kibana base URL (default: %(default)s)",
    )
    parser.add_argument(
        "--stack", choices=["mds_elk", "honeytraps"], default="mds_elk",
        help="Which stack's kibana/ directory to read/write (default: %(default)s)",
    )
    parser.add_argument(
        "--generate-only", action="store_true",
        help="Only write the NDJSON files, do not import into Kibana",
    )
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))

    stack_paths = {
        "mds_elk": os.path.join(project_root, "mds_elk", "kibana", "export.ndjson"),
        "honeytraps": os.path.join(project_root, "honeytraps", "waf_elk", "kibana", "export.ndjson"),
    }

    objects = build_objects()

    # Regenerate both NDJSON files - both stacks share the same schema and index pattern.
    for path in stack_paths.values():
        write_ndjson(objects, path)

    if args.generate_only:
        return

    if requests is None:
        sys.exit("requests library not found. Install with: pip install requests")

    ndjson_path = stack_paths[args.stack]
    wait_for_kibana(args.kibana_url)
    print(f"Importing from {ndjson_path}...")
    import_ndjson(args.kibana_url, ndjson_path)
    print(
        f"\nDone. Open {args.kibana_url}/app/dashboards to view the "
        f"'Honeypot Threat Intelligence' dashboard."
    )


if __name__ == "__main__":
    main()
