# M0.6 Branch Integration

This note records why the M0.6 engineering history is being reconciled rather than allowing two technical branches to continue diverging.

The common merge base is `3df55b9791d68aa4a721127441b1117424e546e9`.

At integration time:

- `m0.6d-authoring-vm` carries the more mature object-VM source tooling, including `.raw` / mixed-region support, plus scene-transition, computer-objective and ambient-bird probes.
- `m0.6c-level-stream` carries complementary authoring proofs added after the divergence: VM relocation builds M0.6E/F, LZBeam encoder and mass round-trip probe, gameplay-map relocation/edit builds M0.6G/H, and a conservative native-spawn boundary probe.

The integration policy is:

1. use the `m0.6d-authoring-vm` tree as the conflict-resolution base;
2. retain its VM assembler/disassembler/source-export implementations where paths overlap;
3. overlay only complementary `m0.6c-level-stream` files;
4. create a real Git merge commit with both branch heads as parents;
5. continue all new work from `m0.6-integration` only.

Neither parent branch should be treated as the canonical continuation after the integration commit.
