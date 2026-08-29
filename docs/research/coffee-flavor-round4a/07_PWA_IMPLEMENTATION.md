# PWA implementation

The public prototype provides a web app manifest, project-authored 192px and
512px icons, a service worker, app-shell cache, versioned public knowledge
snapshot, update notice, responsive layout, keyboard operation, and
reduced-motion behavior.

The service worker only handles same-origin GET requests and explicitly avoids
database, restricted, reviewer, and rights-decision paths. The cached knowledge
snapshot contains only the 24 already-public project-curated descriptor IDs and
rule metadata. No restricted raw source text, private reviewer record, model
weight, or participant record is bundled.

The core `/prototype/` interaction is prerendered and cached for offline
opening after initial installation.
