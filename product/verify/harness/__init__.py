"""ReaCompare unified verification harness (task A-1 / M0).

This package is the single entry point for black-box Oracle comparison against
Beyond Compare installs.  It owns nothing outside ``D:\\Rea\\product\\verify``.

Modules
-------
taxonomy   result verdicts + the per-test record
normalize  versioned, reviewable report normalisation rules
installs   install identity discovery (version + digests)
oracle     Oracle invocation (text / folder recipes)
candidate  candidate CLI adapter config (reserved for the future product)
manifests  loaders for the read-only golden / layout / dir fixture manifests
runner     orchestration + aggregation
report     machine-readable and human-readable run reports
"""

RULESET_VERSION = "norm-1"
HARNESS_VERSION = "0.1.0"
