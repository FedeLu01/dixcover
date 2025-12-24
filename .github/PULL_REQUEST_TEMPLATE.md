<!--
Please provide a clear, short description of the change and any context
needed for reviewers. Use the checklist below and link related issues.
-->

## Summary

A short description of the change (one or two sentences).

## Type of change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing behavior to change)
- [ ] Documentation update
- [ ] Infrastructure / CI

## Related issues

- Fixes: # (issue number)
- Related: # (issue number)

## Description

Explain the motivation for the change and any design decisions made. Keep
it concise and focused for reviewers.

## How to test

Provide steps to reproduce or validate the change locally. Include commands
where helpful. Example:

```
# create and activate a venv
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# run tests
pytest -q
```

## Checklist

- [ ] I have read the contribution guidelines
- [ ] Tests added/updated where applicable
- [ ] Documentation updated if needed (README, CHANGELOG)
- [ ] Migration files added if the DB schema changed
- [ ] All CI checks pass

## Migration notes (if any)

Describe Alembic migrations or other deployment steps required for this change.

## Notes for reviewers

Anything specific reviewers should focus on (e.g., security concerns, edge
cases, performance implications). If nothing special, remove this section.
