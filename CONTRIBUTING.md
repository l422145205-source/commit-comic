# Make the next story easier to tell

Useful feedback is small and concrete: the kind of change you tried, the step that failed, or a panel that did not explain the source faithfully. Use the [try-out report](https://github.com/l422145205-source/commit-comic/issues/new?template=try-it.yml). No private code or personal details are needed.

Contributions can be an original vector scene, a font/layout fix, a clearer Agent workflow, or a reviewed example grounded in a public change. Keep the input scope and source links with the example. Identify maintainer examples, synthetic inputs and actual external-user reports accurately; do not turn one into another.

For code changes, run `python -m unittest discover -s tests -v` and the relevant CLI path. For art changes, inspect the resulting image. A real-project case can be rerendered with `python tools/render_cases.py --out work/my-cases --locale en --images`; this does not rerun the source experiments. Please don't regenerate unrelated frozen evidence.

This repository accepts project technical material. Leave private logs, contact information, credentials and non-public project details out of issues and PRs.
