# Use Case 7 — Wafer Alignment / Registration

This use case demonstrates a simple wafer-alignment workflow.
The simulation uses template matching, translation/rotation registration,
and a simple SPC summary to make alignment behaviour visible without a full
machine-vision stack.

## Workflow

1. Create a synthetic reference pattern and a shifted test image.
2. Use template matching to locate the pattern in the test image.
3. Estimate translation offsets with a registration analysis step.
4. Summarise alignment measurements with SPC-style metrics.

## Typical inputs

- Reference template image
- Test image with misalignment
- Shift and rotation parameters

## Typical outputs

- Match score and best-match location
- Translation offsets in x and y
- SPC metrics such as Cpk and mean shift

## Run it from the command line

```bash
source .venv/bin/activate
python examples/run_uc7_wafer_alignment.py
```

## Explore it interactively in a notebook

Open the notebook at [examples/uc7_wafer_alignment_playground.ipynb](../examples/uc7_wafer_alignment_playground.ipynb) to explore the workflow interactively.

## Why this use case matters

This workflow is useful for wafer inspection, alignment verification, and
registration studies where understanding offsets and process stability is key.
