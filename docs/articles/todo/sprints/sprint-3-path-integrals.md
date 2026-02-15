# Sprint 3: Feynman Path Integrals for Text Generation

**Duration:** 2 weeks
**Goal:** Implement path integral formulation of sequence generation

---

## Overview

Model text generation as sum-over-paths, analogous to Feynman path integrals in quantum mechanics. Compare beam search (classical approximation) with full quantum path integral.

---

## User Stories

### US-3.1: Path Enumeration
**As a** researcher
**I want** to enumerate all possible generation paths
**So that** I can compute path integral

**Acceptance Criteria:**
- [ ] Generate all possible sequences up to length L
- [ ] Calculate action S[path] = log P(path) for each
- [ ] Support vocabulary subsetting for tractability
- [ ] Handle exponential growth efficiently

### US-3.2: Classical Path Integral (Beam Search)
**As a** researcher
**I want** to implement beam search as classical path sampling
**So that** I can compare with full quantum integral

**Acceptance Criteria:**
- [ ] Implement standard beam search
- [ ] Track K highest-probability paths
- [ ] Calculate approximate path integral
- [ ] Measure approximation error

### US-3.3: Quantum Path Integral Simulation
**As a** researcher
**I want** to simulate quantum path interference
**So that** I can demonstrate quantum advantages

**Acceptance Criteria:**
- [ ] Compute amplitude for each path
- [ ] Simulate constructive/destructive interference
- [ ] Calculate exact quantum amplitude
- [ ] Compare classical vs quantum results

---

## TDD Test Cases

```python
# tests/unit/test_path_generator.py
import pytest
from quantum_llm_sim.simulations.paths import PathGenerator

class TestPathGenerator:
    def test_enumerate_paths_small(self):
        """Test path enumeration for small vocab/length"""
        gen = PathGenerator(vocab_size=2, max_length=3)
        paths = gen.enumerate_all_paths()

        # Should have 2^3 = 8 paths
        assert len(paths) == 8

    def test_path_probability(self):
        """Test path probability calculation"""
        gen = PathGenerator(vocab_size=10, max_length=5)

        # Mock probability function
        def mock_prob(token, context):
            return 0.1  # Uniform

        path = [1, 2, 3]
        prob = gen.calculate_path_probability(path, mock_prob)

        expected = 0.1 ** 3  # P(1) * P(2|1) * P(3|1,2)
        assert pytest.approx(prob) == expected

    def test_action_calculation(self):
        """Test action S[path] = log P(path)"""
        gen = PathGenerator(vocab_size=10, max_length=5)

        path = [1, 2, 3]
        prob = 0.001
        action = gen.calculate_action(prob)

        expected = np.log(0.001)
        assert pytest.approx(action) == expected


# tests/unit/test_beam_search.py
from quantum_llm_sim.simulations.beam_search import BeamSearch

class TestBeamSearch:
    def test_beam_search_convergence(self):
        """Test beam search finds high-probability paths"""
        beam = BeamSearch(beam_width=5, vocab_size=100)

        # Mock scoring function
        def score_fn(token, context):
            return -abs(token - 50)  # Prefer token 50

        paths = beam.search(max_length=10, score_fn=score_fn)

        # Best path should contain mostly token 50
        best_path = paths[0]['sequence']
        assert best_path.count(50) > 5

    def test_beam_width_effect(self):
        """Test larger beam explores more paths"""
        def score_fn(token, context):
            return np.random.randn()

        beam_small = BeamSearch(beam_width=3, vocab_size=10)
        beam_large = BeamSearch(beam_width=10, vocab_size=10)

        paths_small = beam_small.search(max_length=5, score_fn=score_fn)
        paths_large = beam_large.search(max_length=5, score_fn=score_fn)

        # Larger beam should explore more unique paths
        unique_small = len(set(tuple(p['sequence']) for p in paths_small))
        unique_large = len(set(tuple(p['sequence']) for p in paths_large))

        assert unique_large >= unique_small


# tests/integration/test_path_integral.py
from quantum_llm_sim.simulations.path_integral import PathIntegralSimulator

class TestPathIntegral:
    def test_classical_vs_quantum(self):
        """Test quantum path integral differs from classical"""
        sim = PathIntegralSimulator(vocab_size=3, max_length=4)

        # Define simple probability model
        def prob_model(token, context):
            return 1.0 / 3  # Uniform

        result = sim.compare_classical_quantum(prob_model)

        # Quantum should have interference effects
        assert 'classical_amplitude' in result
        assert 'quantum_amplitude' in result

        # They may differ due to interference
        # (though for this simple case might be similar)

    def test_interference_detection(self):
        """Test detection of constructive/destructive interference"""
        sim = PathIntegralSimulator(vocab_size=2, max_length=3)

        def prob_model(token, context):
            return 0.5  # Equal superposition

        result = sim.analyze_interference(prob_model)

        assert 'constructive_paths' in result
        assert 'destructive_paths' in result
        assert 'total_interference' in result
```

---

## Implementation Tasks

### Task 3.1: Path Generator
```python
# src/quantum_llm_sim/simulations/paths.py
import numpy as np
from typing import List, Callable, Dict
from itertools import product

class PathGenerator:
    """Generate and analyze sequence paths"""

    def __init__(self, vocab_size: int, max_length: int):
        self.vocab_size = vocab_size
        self.max_length = max_length

    def enumerate_all_paths(
        self,
        length: int = None
    ) -> List[List[int]]:
        """
        Enumerate all possible paths

        Args:
            length: Path length (defaults to max_length)

        Returns:
            List of all possible token sequences

        Warning:
            Exponential in length! Only use for small vocab/length
        """
        if length is None:
            length = self.max_length

        # Generate all combinations
        paths = list(product(range(self.vocab_size), repeat=length))

        return [list(path) for path in paths]

    def calculate_path_probability(
        self,
        path: List[int],
        prob_fn: Callable[[int, List[int]], float]
    ) -> float:
        """
        Calculate probability of path: P(path) = ∏ P(token_i | context)

        Args:
            path: Sequence of token indices
            prob_fn: Function that returns P(token | context)

        Returns:
            Path probability
        """
        prob = 1.0
        context = []

        for token in path:
            prob *= prob_fn(token, context)
            context.append(token)

        return prob

    def calculate_action(self, probability: float) -> float:
        """
        Calculate action S[path] = log P(path)

        In quantum path integrals, action determines phase.
        For probabilistic case, we use log probability.

        Args:
            probability: Path probability

        Returns:
            Action (log probability)
        """
        return float(np.log(probability + 1e-10))  # Avoid log(0)

    def calculate_path_weights(
        self,
        paths: List[List[int]],
        prob_fn: Callable
    ) -> Dict[tuple, float]:
        """
        Calculate weights for all paths

        Args:
            paths: List of token sequences
            prob_fn: Probability function

        Returns:
            Dictionary mapping path tuple to weight
        """
        weights = {}

        for path in paths:
            path_tuple = tuple(path)
            prob = self.calculate_path_probability(path, prob_fn)
            action = self.calculate_action(prob)
            weights[path_tuple] = {
                'probability': prob,
                'action': action,
                'path': path
            }

        return weights
```

### Task 3.2: Beam Search Implementation
```python
# src/quantum_llm_sim/simulations/beam_search.py
import numpy as np
from typing import List, Callable, Dict
import heapq

class BeamSearch:
    """Classical beam search as path integral approximation"""

    def __init__(self, beam_width: int, vocab_size: int):
        self.beam_width = beam_width
        self.vocab_size = vocab_size

    def search(
        self,
        max_length: int,
        score_fn: Callable[[int, List[int]], float]
    ) -> List[Dict]:
        """
        Perform beam search

        Args:
            max_length: Maximum sequence length
            score_fn: Function that scores token given context

        Returns:
            List of beam_width best paths with scores
        """
        # Initialize beam with empty sequence
        beam = [(0.0, [])]  # (cumulative_score, sequence)

        for step in range(max_length):
            candidates = []

            for score, sequence in beam:
                # Expand with all possible next tokens
                for token in range(self.vocab_size):
                    token_score = score_fn(token, sequence)
                    new_score = score + token_score
                    new_sequence = sequence + [token]

                    candidates.append((new_score, new_sequence))

            # Keep top beam_width candidates
            beam = heapq.nlargest(
                self.beam_width,
                candidates,
                key=lambda x: x[0]
            )

        # Format results
        results = []
        for score, sequence in beam:
            results.append({
                'sequence': sequence,
                'score': score,
                'probability': np.exp(score)  # If scores are log probs
            })

        return results

    def compare_to_exhaustive(
        self,
        max_length: int,
        score_fn: Callable,
        true_best_path: List[int]
    ) -> Dict:
        """
        Compare beam search result to true best path

        Args:
            max_length: Sequence length
            score_fn: Scoring function
            true_best_path: Known optimal path

        Returns:
            Comparison metrics
        """
        beam_results = self.search(max_length, score_fn)
        beam_best = beam_results[0]['sequence']

        # Calculate scores
        beam_score = beam_results[0]['score']
        true_score = sum(score_fn(token, true_best_path[:i])
                        for i, token in enumerate(true_best_path))

        return {
            'beam_path': beam_best,
            'true_path': true_best_path,
            'beam_score': beam_score,
            'true_score': true_score,
            'found_optimal': beam_best == true_best_path,
            'score_ratio': beam_score / true_score if true_score != 0 else 0
        }
```

### Task 3.3: Path Integral Simulator
```python
# src/quantum_llm_sim/simulations/path_integral.py
import numpy as np
from typing import Callable, Dict, List
from .paths import PathGenerator

class PathIntegralSimulator:
    """Simulate quantum path integrals for text generation"""

    def __init__(self, vocab_size: int, max_length: int):
        self.vocab_size = vocab_size
        self.max_length = max_length
        self.path_gen = PathGenerator(vocab_size, max_length)

    def compute_classical_sum(
        self,
        prob_fn: Callable
    ) -> float:
        """
        Compute classical path integral (sum of probabilities)

        Args:
            prob_fn: Probability function

        Returns:
            Total probability (should be 1 for complete enumeration)
        """
        paths = self.path_gen.enumerate_all_paths()
        total_prob = 0.0

        for path in paths:
            prob = self.path_gen.calculate_path_probability(path, prob_fn)
            total_prob += prob

        return total_prob

    def compute_quantum_amplitude(
        self,
        prob_fn: Callable,
        target_sequence: List[int]
    ) -> complex:
        """
        Compute quantum amplitude for target sequence via path integral

        Amplitude = Σ_paths exp(iS[path]/ℏ) δ(path, target)

        For probabilistic case:
        Amplitude = Σ_paths √P(path) exp(iθ[path])

        Args:
            prob_fn: Probability function
            target_sequence: Desired output sequence

        Returns:
            Quantum amplitude (complex number)
        """
        paths = self.path_gen.enumerate_all_paths(len(target_sequence))
        amplitude = 0.0 + 0.0j

        for path in paths:
            prob = self.path_gen.calculate_path_probability(path, prob_fn)

            # Amplitude contribution: √P(path)
            magnitude = np.sqrt(prob)

            # Phase from action: exp(iS/ℏ)
            action = self.path_gen.calculate_action(prob)
            phase = np.exp(1.0j * action)  # Using ℏ=1 units

            # Add contribution if path ends at target
            if path == target_sequence:
                amplitude += magnitude * phase

        return amplitude

    def analyze_interference(
        self,
        prob_fn: Callable
    ) -> Dict:
        """
        Analyze constructive/destructive interference in path integral

        Args:
            prob_fn: Probability function

        Returns:
            Dictionary with interference analysis
        """
        paths = self.path_gen.enumerate_all_paths()
        path_amplitudes = []

        for path in paths:
            prob = self.path_gen.calculate_path_probability(path, prob_fn)
            magnitude = np.sqrt(prob)
            action = self.path_gen.calculate_action(prob)
            phase = np.exp(1.0j * action)

            amplitude = magnitude * phase
            path_amplitudes.append({
                'path': path,
                'amplitude': amplitude,
                'magnitude': magnitude,
                'phase': np.angle(amplitude)
            })

        # Analyze interference
        total_amplitude = sum(p['amplitude'] for p in path_amplitudes)

        return {
            'total_amplitude': total_amplitude,
            'total_probability': np.abs(total_amplitude) ** 2,
            'path_amplitudes': path_amplitudes,
            'num_paths': len(paths),
            'mean_magnitude': np.mean([p['magnitude'] for p in path_amplitudes]),
            'phase_spread': np.std([p['phase'] for p in path_amplitudes])
        }

    def compare_classical_quantum(
        self,
        prob_fn: Callable
    ) -> Dict:
        """
        Compare classical and quantum path integrals

        Args:
            prob_fn: Probability function

        Returns:
            Comparison results
        """
        # Classical: sum of probabilities
        classical_sum = self.compute_classical_sum(prob_fn)

        # Quantum: sum of amplitudes (squared for probability)
        quantum_result = self.analyze_interference(prob_fn)
        quantum_prob = quantum_result['total_probability']

        return {
            'classical_sum': classical_sum,
            'quantum_probability': quantum_prob,
            'difference': abs(classical_sum - quantum_prob),
            'interference_effects': quantum_result['phase_spread'] > 0.1,
            'quantum_result': quantum_result
        }
```

---

## Definition of Done

- [ ] All tests passing
- [ ] Path enumeration working for small cases
- [ ] Beam search implemented correctly
- [ ] Quantum path integral simulated
- [ ] Interference effects demonstrated
- [ ] Classical vs quantum comparison complete
- [ ] Code coverage > 85%
- [ ] Visualization notebook complete

---

## Deliverables

1. PathGenerator class
2. BeamSearch implementation
3. PathIntegralSimulator class
4. Jupyter notebook: `experiments/notebooks/03_path_integrals.ipynb`
5. Comparison of classical beam search vs quantum path integral
6. Visualization of path interference patterns
