# Test-Aware Multi-Reviewer Code Generation

## Overview

This project explores a software-delivery-inspired framework for code generation using large language models (LLMs).

Instead of relying solely on self-correction, we simulate a Continuous Integration (CI)-like pipeline:

Coder → Tester → Multi-Reviewer → Merge

The goal is to evaluate whether multi-agent review governance improves code reliability compared to traditional self-refinement methods.

---

## Research Motivation

Existing code generation systems often rely on **self-correction loops**, where a single model generates, critiques, and refines its own code.

However, this introduces risks such as:

- Confirmation bias
- Limited self-evaluation reliability
- False-positive fixes

We hypothesize that introducing a **multi-reviewer approval stage**, informed by execution results, can improve merge reliability and functional correctness.

---

## Pipeline Architecture

1. **Coder**
   - Generates code from problem prompts.

2. **Tester**
   - Executes code using unit tests.
   - Produces pass/fail results and error logs.

3. **Multi-Reviewer (N ≥ 3)**
   - Evaluates code + execution evidence.
   - Provides approval or rejection.

4. **Merge Policy**
   - Majority voting.
   - Optional regeneration on rejection.

---

## Benchmarks

We evaluate on executable code generation benchmarks:

- **HumanEval**
- **MBPP** (optional extension)

Metrics include:

- Pass@1
- Execution success rate
- Merge accuracy
- False merge rate

---

## Baselines

We compare against:

1. **Single-pass Code Generation**
2. **Self-Refine (Iterative Self-Correction)**

---

## Installation

### 1. System Setup

```bash
chmod +x setup.sh
./setup.sh

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh


# Pull ollama model
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:7b
