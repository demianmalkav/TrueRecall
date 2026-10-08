# Tests and Regression Probes

This directory holds machine-checkable assertions and regression probes.

Initial targets:

- canonical ROM hash verification
- reset/header/vector assertions
- known internal diagnostic strings
- player callback assignments
- weapon selector/ownership table
- cutscene descriptor structure
- gameplay package dimensions and decompressed sizes
- no-op LZBeam round trip
- no-op map/resource rebuild

Every engine extension should add or reuse a regression probe that proves original behavior remains intact unless an explicit decision says otherwise.
