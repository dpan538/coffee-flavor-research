# Model pipeline smoke

The smoke test uses three synthetic rows and disjoint coffee/source groups. A
majority fixture exercises training, temporary JSON serialization, inference,
metric calculation, and model-card generation. All files live inside an
automatically deleted temporary directory.

This is `MODEL_RUN_TYPE=PIPELINE_SMOKE_TEST`, not an empirical model. The
fixture metric is explicitly non-claimable. No synthetic row, model weight, or
model card enters the production artifact set.
