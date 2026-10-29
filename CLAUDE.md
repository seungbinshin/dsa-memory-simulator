@AGENTS.md

<!-- hexaharness:start -->
## HexaHarness lifecycle

- Project: `dsa-memory-simulator`
- Language: `Python`
- Required commands:
  - Build: `python3.13 -B -m memory_dsa demo --output outputs`
  - Test: `python3.13 -B -m unittest discover -s tests -v`
  - Lint: `python3.13 -B -m compileall -q memory_dsa tests`
- Use the HexaHarness skill automatically for material project planning, implementation,
  verification, resumption, and maintenance when it is available.
- Let the skill operate its bundled CLI internally; do not require the user to manage task IDs or
  routine harness commands.
- Read `.hexaharness/GUIDES.md` for active failure-derived rules.
- Keep project-local reversible work autonomous. External or hard-to-reverse actions require
  authorization for the exact action and target. Reuse applicable authorization already given;
  otherwise finish local preparation and ask immediately before execution. Let the skill stage
  and bind the action internally.
<!-- hexaharness:end -->
