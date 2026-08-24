# Pre-Sensory-KB V0 Archive

- Archive event: 2026-08-24
- Artifact baseline date: 2026-06-22
- Status: historical, non-canonical

This archive freezes the Coffee Flavor Atlas product, frontend, methodology,
and decision documents that predate the PostgreSQL-backed Coffee Sensory
Knowledge Base V0 research round. The files are retained for historical
traceability and to keep earlier reasoning reviewable; they are not the current
implementation specification.

The superseding engineering contract is the
[Coffee Sensory Knowledge Base V0 research specification](../../research/coffee-sensory-kb-v0/00_RESEARCH_SOURCE.md).
That contract establishes a language-neutral, typed, polyhierarchical knowledge
base with explicit provenance and separates canonical knowledge, raw corpus
observations, model inference, and independent evaluation.

Archival status does not mean every earlier idea was wrong. The static React
application, its accessibility and motion boundaries, and useful interface
lessons remain available as a compatibility/public baseline. What changed is
which material governs future sensory-data engineering.

## Preservation policy

- The five archived documents were moved with Git rename operations so their
  repository history remains discoverable.
- Replacement documents now occupy `README.md` and `docs/ARCHITECTURE.md` and
  point readers to the current research architecture.
- Three pure documentation artifacts had no application runtime dependency and
  were safe to move without replacements at their old paths.
- Five legacy data/runtime modules remain in `packages/flavor-data/src/`. They
  are deliberately not copied or moved because the public static application
  still imports them.
- No external Deep Research PDF or protected third-party sensory content is
  stored in this archive.

See [MANIFEST.md](./MANIFEST.md) for the complete five-document archive record
and the separately counted `LEGACY_BUT_RUNTIME_REFERENCED` set.

## Contents

- `product/`: the former repository README and public product baseline.
- `architecture/`: the former frontend-only architecture note.
- `design/`: the former visual and interaction redesign direction.
- `research/`: the former draft descriptor-data methodology.
- `decisions/`: the former product/frontend decision log.
