# Negative-test receipt

The following rejection/detection contracts pass:

1. duplicate external snapshot key;
2. mismatched source file hash;
3. wrong declared row count;
4. missing license/rights decision;
5. public export of blocked raw text;
6. direct participant identifier import;
7. silent unit conversion;
8. source-local raw value overwritten by normalized value;
9. external observation used as canonical ontology support;
10. recurrent industry term automatically promoted;
11. candidate question marked user-validated/comprehension-ready without evidence;
12. model run using Round 3E data despite the prohibition;
13. stale generated artifact;
14. unformatted generated artifact;
15. nondeterministic manifest/artifact output; and
16. unified CI success after an internal failed step.

The Python artifact contract, SQL negative suite, Prettier artifact check,
double-generation hash comparison and shell fail-fast regression collectively
cover the list. Assertions are not weakened and retries/timeouts are not used as
the repair.

`NEGATIVE_TEST_PASS=true`
