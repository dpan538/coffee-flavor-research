# Semantic coherence hypothesis

Coffee Flavor Atlas models flavor output as a structured candidate set rather
than eight independent labels. The system combines individual descriptor
relevance with professional co-assertion evidence, semantic connectivity and
context, aiming to improve professional-reference coverage while reducing
unsupported outliers and redundant suggestions.

The intended set is coherent but not homogeneous. A missing observed pair is
unknown, not contradictory. A rare descriptor with direct answer or reference
support remains eligible even when graph degree is low. Two supported clusters
may be preferable to one narrow synonym cluster.

The hypothesis is supported only if a coherence reranker preserves or improves
Reference Coverage@8 and nDCG@8, reduces isolated unsupported candidates, does
not materially increase redundancy, preserves rare direct evidence, and
generalizes across coffee identity, year, or family. Those empirical conditions
are not currently testable.
