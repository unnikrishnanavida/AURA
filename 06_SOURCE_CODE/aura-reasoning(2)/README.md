# AURA Reasoning Engine v3

A production-oriented reasoning subsystem built around explicit claims, assumptions, evidence, verification, uncertainty, causal and probabilistic reasoning, symbolic structures, search, traceability, replay, safety, routing and evaluation.

## Architecture rule

Quality > file count > line count. Modules are kept separate only when their responsibility is genuinely distinct. Claims and assumptions are canonical objects; abduction consumes the authoritative hypothesis model; provenance records origin; verification determines whether a conclusion is sufficiently supported.

## Core flow

context -> claims -> assumptions -> evidence -> inference -> reasoning -> verification -> uncertainty -> explanation -> trace -> replay
