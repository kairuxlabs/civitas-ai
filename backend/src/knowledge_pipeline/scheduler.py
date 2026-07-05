"""Future implementation (v2, post-hackathon) — not implemented in v1.

Planned design:
- An APScheduler job, running weekly, re-runs WikipediaCollector.collect()
  only (OSM / Government PDF / GeoJSON change rarely and stay manual —
  re-run bootstrap.py by hand when they do).
- Re-chunks and re-embeds any changed pages, upserting into the same
  `city_knowledge` Qdrant collection. qdrant_loader.load_chunks() is
  already idempotent (deterministic point ids from title + chunk_index),
  so re-running it on a schedule is safe without any loader changes.
- Reuses the exact collector/processor/loader interfaces bootstrap.py
  already uses — no changes needed there when this is implemented.

See docs/superpowers/specs/2026-07-05-knowledge-bootstrap-pipeline-design.md
for the full v1/v2/v3 roadmap.
"""
