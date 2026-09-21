# Human Semantic Annotation Protocol

## Status and scope

Status: protocol prepared; annotation has not been performed.

This document specifies a prospective validation of the semantic roles used in the controlled and natural-retrieval analyses. It does not report human-validated results. No label, agreement statistic, retained sample size, or effect estimate may be described as human-derived until independent annotation and adjudication are complete.

The study has two aims:

1. Verify that controlled support text states an accepted answer and that the foil expresses a concrete incompatible answer.
2. Verify that natural candidates contain reader-visible support or a concrete incompatible answer under the exact text shown to the answering model.

## Sampling frame

### Natural conflicts

Annotate all 70 automatically identified natural support/foil pairs. These cases are few enough that sampling would add avoidable uncertainty. Annotators see the exact 900-character candidate text supplied to the reader, not the longer 1,200-character labeling view.

### Controlled cases

Preferred design: annotate all 591 unique controlled semantic cases audited automatically.

Minimum feasible design: draw 250 unique cases with a fixed random seed before annotation. Stratify jointly as far as cell sizes permit by:

- dataset/task;
- endpoint family;
- stable-correct versus support-rescuable stratum;
- foil origin (baseline mode, binary complement, or donor);
- automatic-audit status (retained, rejected, or disputed).

Sample at least one case from every nonempty task-by-stratum-by-foil-origin cell. Store the sampling script, seed, ordered case IDs, and SHA-256 hash before labels are opened. Report inclusion probabilities or stratum weights if estimates are generalized beyond the annotated sample.

## Blinding and assignment

Two annotators label every case independently. Use stable anonymous case IDs and randomize item order separately for each annotator. Do not reveal:

- model or endpoint identity;
- stable-correct/support-rescuable stratum;
- evidence order or model answers;
- automatic labels, audit outcomes, or confidence;
- downstream correctness effects;
- the paper's directional hypotheses.

Annotators may see only the task name, question, accepted answer or answer aliases, and the evidence text needed for the assigned judgment. Images may be shown for image-dependent questions, but no model outputs or experimental outcomes may be shown.

Before production labeling, run a calibration round on 15-20 cases that are excluded from agreement estimates. Discuss the instructions, not target agreement. Freeze the codebook after calibration and record any later amendment with a timestamp and affected cases.

## Controlled-case labels

### Support label

Choose exactly one:

- `equivalent`: directly states an accepted answer or an unambiguous semantic equivalent.
- `partially_sufficient`: does not repeat the canonical answer exactly but contains enough information to infer it without outside facts.
- `insufficient`: related to the question but does not establish the accepted answer.
- `incorrect_contradictory`: asserts a claim incompatible with the accepted answer.
- `ambiguous`: two or more labels remain plausible from the visible text.

### Foil label

Choose exactly one:

- `concrete_incompatible_answer`: asserts a specific answer that cannot be true together with the accepted answer under the question's intended interpretation.
- `compatible_granularity_variant`: differs lexically or in specificity but can coexist with, entail, or be entailed by the accepted answer.
- `non_answer`: abstention, placeholder, malformed output, or text that does not propose an answer.
- `irrelevant`: content does not answer the question.
- `ambiguous`: incompatibility cannot be determined from the visible text and supplied answer aliases.

### Required fields

For both support and foil judgments, record:

- exact quoted evidence span;
- confidence on a 1-5 ordinal scale;
- a short rationale when confidence is 1-3 or the label is `ambiguous`;
- whether the question itself is underspecified (`yes`, `no`, or `uncertain`).

## Natural-candidate labels

Label each candidate independently, without forcing a support/foil pair:

- `support`: visible text supports an accepted answer or an unambiguous equivalent.
- `foil`: visible text supports a concrete answer incompatible with the accepted answer.
- `neutral`: visible text is relevant context but supports neither an accepted nor incompatible answer.
- `insufficient`: text is truncated, incomplete, or too weak to determine a role.
- `ambiguous`: more than one role remains plausible.

Record the exact quoted span, confidence 1-5, and a short rationale for `foil`, `insufficient`, `ambiguous`, or confidence 1-3. A candidate can receive only one primary label; competing propositions should be noted in the rationale for adjudication.

## Adjudication

Lock the two independent files before comparison. A third qualified annotator adjudicates every disagreement. If a third annotator is unavailable, the two annotators may reach consensus in a recorded meeting, but the original labels must remain unchanged and consensus must be stored in separate fields.

Adjudicators see the question, accepted answers, evidence, both labels, quotes, and rationales. They do not see model outcomes, effect sizes, or automatic labels. Record the adjudicated label, decisive quotation, rationale, adjudicator ID, and timestamp.

## Agreement reporting

Report before-adjudication agreement separately for support, controlled foil, and natural candidate tasks:

- raw exact agreement;
- Cohen's kappa;
- Gwet's AC1 when prevalence or marginal imbalance makes kappa unstable;
- class-wise positive agreement or per-class F1;
- the confusion matrix;
- agreement stratified by task and, where sample size permits, foil origin.

Confidence is descriptive and must not be used to discard disagreements after outcomes are inspected. Report the number of missing labels and protocol deviations.

## Frozen retention rules

Primary controlled semantic subset:

- support is adjudicated `equivalent` or `partially_sufficient`; and
- foil is adjudicated `concrete_incompatible_answer`.

Primary natural conflict subset:

- at least one candidate is adjudicated `support`; and
- at least one different candidate is adjudicated `foil`; and
- both decisive quoted spans occur within the exact 900-character reader-visible text.

All other labels, including `ambiguous`, are excluded from the corresponding primary semantic subset. Do not revise these rules after inspecting condition outcomes. Sensitivity analyses may additionally require support=`equivalent` and confidence at least 4, but must be labeled secondary.

## Analysis after labels exist

1. Freeze the two annotator files, adjudication file, codebook version, and hashes.
2. Report agreement and the flow from sampled to retained cases before reporting effect estimates.
3. Recompute the original controlled stratum effects and interaction on the adjudicated controlled subset, using the existing question-clustered bootstrap.
4. Recompute natural support/foil swap effects on the adjudicated natural-pair subset. Report retained pairs and endpoint-specific complete records.
5. Compare automatic and human labels with confusion matrices and class-specific precision/recall. Do not call the automatic audit validated solely because the downstream point estimate is similar.
6. Preserve the full-sample results as primary design-based estimates and present human-filtered estimates as construct-validity sensitivity analyses unless the manuscript prospectively changes its estimand before annotation.

## Resource plan

Minimum plan: two annotators for 70 natural pairs plus 250 controlled cases, followed by adjudication. Assuming 2-3 minutes per controlled case and 4-6 minutes per natural pair, budget about 14-22 annotator-hours plus 3-6 adjudication hours. Preferred all-controlled plan increases this to roughly 27-39 annotator-hours plus adjudication.

Annotators should be fluent in English and capable of checking the relevant benchmark domains. Domain experts are not required for ordinary factual cases, but uncertain specialized cases should be flagged for expert adjudication rather than guessed.

## Files

- `human_annotation/controlled_annotation_blank.csv`: one row per annotator and controlled case.
- `human_annotation/natural_candidate_annotation_blank.csv`: one row per annotator and candidate.

The templates intentionally contain headers only. Populating them with synthetic or model-generated labels would invalidate the claim of human annotation.
