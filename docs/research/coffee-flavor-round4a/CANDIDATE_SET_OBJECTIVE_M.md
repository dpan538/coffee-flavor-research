# Candidate-set objective M

For context `x = C0 + C1 + Q1–Q5` and set `S = {d1,…,d8}`, the implementation
uses the conceptual objective:

```text
M(S|x) = IndividualRelevance
       + λp ProfessionalCoherence
       + λs SemanticConnectivity
       + λc ContextConsistency
       + λe DirectEvidenceCoverage
       - λo UnsupportedOutlierPenalty
       - λr RedundancyPenalty
```

Professional weights are accepted only from typed P1/P2 effective-record edges
and are shrunk toward zero at low support. Ontology links remain project-curated
typed links. Community language has a capped auxiliary contribution and cannot
become professional evidence.

The outlier penalty applies only when a candidate lacks connection to every
selected candidate, C0/C1 support, Q support, direct professional support, and a
reviewed ontology relation. Redundancy rejects repeated canonical targets.
