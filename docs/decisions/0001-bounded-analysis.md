# ADR 0001: Bounded operations instead of arbitrary generated Python

Status: accepted.

The application needs reproducible analysis without allowing uploaded instructions or model output to become executable programs. The v1 interface therefore accepts reviewed operation definitions. It runs the deterministic executor as a separate process with clean environment, input/time/resource bounds, and captures operation/source/executor hashes.

Advantages: exact arithmetic, inspectable behavior, predictable replay and a smaller attack surface. Tradeoff: unsupported analyses require implementing and reviewing a new operation. The optional sandbox image strengthens isolation for supported operations; it does not justify arbitrary generated Python.

This follows the roadmap's priority to prefer tested deterministic functions. General generated-code execution remains intentionally unsupported.
