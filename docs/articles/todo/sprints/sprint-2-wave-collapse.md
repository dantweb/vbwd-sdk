# Sprint 2: Wave Function Collapse and Token Sampling

**Duration:** 2 weeks
**Goal:** Simulate wave function collapse in token sampling process

---

## Overview

Implement simulation of quantum measurement and wave function collapse during token generation. Model the probabilistic collapse of superposition into definite tokens.

---

## User Stories

### US-2.1: Superposition State Modeling
**As a** researcher
**I want** to model token probabilities as quantum superposition
**So that** I can simulate pre-measurement state

**Acceptance Criteria:**
- [ ] Represent probability distribution as quantum state vector
- [ ] Support complex amplitudes (for quantum simulation)
- [ ] Normalize states properly (⟨ψ|ψ⟩ = 1)
- [ ] Visualize superposition before collapse

### US-2.2: Measurement Simulation
**As a** researcher
**I want** to simulate quantum measurement of token states
**So that** I can observe collapse dynamics

**Acceptance Criteria:**
- [ ] Implement Born rule: P(outcome) = |⟨outcome|ψ⟩|²
- [ ] Simulate measurement-induced collapse
- [ ] Track state before and after measurement
- [ ] Support repeated measurements (show irreversibility)

### US-2.3: Decoherence Modeling
**As a** researcher
**I want** to model decoherence via temperature
**So that** I can simulate quantum-to-classical transition

**Acceptance Criteria:**
- [ ] Temperature controls decoherence rate
- [ ] T→0: Complete decoherence (classical)
- [ ] T→∞: Maximum coherence (quantum)
- [ ] Visualize decoherence process

---

## TDD Test Cases

```python
# tests/unit/test_quantum_state.py
import numpy as np
import pytest
from quantum_llm_sim.simulations.quantum_state import QuantumState

class TestQuantumState:
    def test_state_normalization(self):
        """Test quantum state is properly normalized"""
        amplitudes = np.array([0.6, 0.8j, 0.0])
        state = QuantumState(amplitudes)
        assert np.isclose(state.norm(), 1.0)

    def test_probability_from_amplitude(self):
        """Test Born rule: P = |amplitude|²"""
        amplitudes = np.array([0.6, 0.8])
        state = QuantumState(amplitudes)
        probs = state.get_probabilities()

        expected = np.array([0.36, 0.64])
        np.testing.assert_array_almost_equal(probs, expected)

    def test_measurement_collapse(self):
        """Test state collapses after measurement"""
        amplitudes = np.array([0.6, 0.8, 0.0])
        state = QuantumState(amplitudes)

        # Perform measurement
        outcome = state.measure()

        # After measurement, state should be eigenstate
        assert state.is_collapsed()
        assert outcome in [0, 1, 2]

    def test_repeated_measurements(self):
        """Test repeated measurements give same result"""
        amplitudes = np.array([0.6, 0.8])
        state = QuantumState(amplitudes)

        outcome1 = state.measure()
        outcome2 = state.measure()

        assert outcome1 == outcome2  # Irreversible collapse


# tests/unit/test_collapse_simulator.py
from quantum_llm_sim.simulations.collapse import CollapseSimulator

class TestCollapseSimulator:
    def test_collapse_statistics(self):
        """Test measurement statistics match quantum predictions"""
        sim = CollapseSimulator(vocab_size=2)

        # Prepare equal superposition
        logits = np.array([0.0, 0.0])
        results = sim.run_measurements(
            logits=logits,
            temperature=1.0,
            num_measurements=1000
        )

        # Should get ~50/50 split for equal superposition
        counts = results['outcome_counts']
        assert 400 < counts[0] < 600
        assert 400 < counts[1] < 600

    def test_decoherence_temperature(self):
        """Test low temperature causes decoherence"""
        sim = CollapseSimulator(vocab_size=10)

        logits = np.random.randn(10)

        # Low temperature: nearly deterministic
        results_low = sim.run_measurements(
            logits=logits,
            temperature=0.01,
            num_measurements=100
        )
        entropy_low = results_low['entropy']

        # High temperature: more uncertainty
        results_high = sim.run_measurements(
            logits=logits,
            temperature=2.0,
            num_measurements=100
        )
        entropy_high = results_high['entropy']

        assert entropy_low < entropy_high
```

---

## Implementation Tasks

### Task 2.1: Quantum State Class
```python
# src/quantum_llm_sim/simulations/quantum_state.py
import numpy as np
from typing import Optional

class QuantumState:
    """Represents a quantum state vector"""

    def __init__(self, amplitudes: np.ndarray, normalize: bool = True):
        """
        Initialize quantum state

        Args:
            amplitudes: Complex amplitudes (can be real)
            normalize: Whether to normalize state
        """
        self.amplitudes = amplitudes.astype(complex)

        if normalize:
            norm = self.norm()
            if norm > 0:
                self.amplitudes /= norm

        self._collapsed = False
        self._collapsed_state = None

    def norm(self) -> float:
        """Calculate norm ⟨ψ|ψ⟩"""
        return float(np.sqrt(np.sum(np.abs(self.amplitudes) ** 2)))

    def get_probabilities(self) -> np.ndarray:
        """Get measurement probabilities via Born rule: P_i = |⟨i|ψ⟩|²"""
        return np.abs(self.amplitudes) ** 2

    def measure(self) -> int:
        """
        Perform quantum measurement (collapse state)

        Returns:
            Measured outcome (index)
        """
        if self._collapsed:
            return self._collapsed_state

        # Born rule: sample according to |amplitude|²
        probs = self.get_probabilities()
        outcome = np.random.choice(len(self.amplitudes), p=probs)

        # Collapse state
        self._collapse_to(outcome)

        return outcome

    def is_collapsed(self) -> bool:
        """Check if state has been measured"""
        return self._collapsed

    def entropy(self) -> float:
        """Calculate von Neumann entropy S = -Σ p_i log(p_i)"""
        probs = self.get_probabilities()
        probs_nonzero = probs[probs > 0]
        return float(-np.sum(probs_nonzero * np.log(probs_nonzero)))

    def _collapse_to(self, state: int) -> None:
        """Collapse to eigenstate"""
        self.amplitudes = np.zeros_like(self.amplitudes)
        self.amplitudes[state] = 1.0 + 0.0j
        self._collapsed = True
        self._collapsed_state = state

    @classmethod
    def from_logits(
        cls,
        logits: np.ndarray,
        temperature: float = 1.0
    ) -> 'QuantumState':
        """Create quantum state from logits with temperature"""
        # Temperature-scaled softmax gives probabilities
        scaled_logits = logits / temperature
        probs = np.exp(scaled_logits - np.max(scaled_logits))
        probs /= probs.sum()

        # Amplitudes are sqrt of probabilities (for real case)
        amplitudes = np.sqrt(probs)

        return cls(amplitudes)
```

### Task 2.2: Collapse Simulator
```python
# src/quantum_llm_sim/simulations/collapse.py
import numpy as np
from typing import Dict, List
from .quantum_state import QuantumState

class CollapseSimulator:
    """Simulate wave function collapse in token sampling"""

    def __init__(self, vocab_size: int):
        self.vocab_size = vocab_size

    def run_measurements(
        self,
        logits: np.ndarray,
        temperature: float,
        num_measurements: int
    ) -> Dict:
        """
        Run multiple measurements from same initial state

        Args:
            logits: Model logits
            temperature: Sampling temperature
            num_measurements: Number of independent measurements

        Returns:
            Dictionary with measurement statistics
        """
        outcomes = []
        entropies_before = []
        entropies_after = []

        for _ in range(num_measurements):
            # Prepare fresh quantum state (each measurement is independent)
            state = QuantumState.from_logits(logits, temperature)

            # Record entropy before measurement
            entropies_before.append(state.entropy())

            # Perform measurement (collapse)
            outcome = state.measure()
            outcomes.append(outcome)

            # Record entropy after measurement (should be 0)
            entropies_after.append(state.entropy())

        # Analyze results
        outcome_counts = np.bincount(outcomes, minlength=self.vocab_size)

        return {
            'outcomes': outcomes,
            'outcome_counts': outcome_counts.tolist(),
            'outcome_probabilities': (outcome_counts / num_measurements).tolist(),
            'mean_entropy_before': float(np.mean(entropies_before)),
            'mean_entropy_after': float(np.mean(entropies_after)),
            'entropy': float(np.mean(entropies_before)),  # Alias
            'entropy_decrease': float(
                np.mean(entropies_before) - np.mean(entropies_after)
            )
        }

    def compare_temperatures(
        self,
        logits: np.ndarray,
        temperatures: List[float],
        num_measurements: int = 100
    ) -> Dict:
        """
        Compare collapse behavior at different temperatures

        Args:
            logits: Model logits
            temperatures: List of temperatures to test
            num_measurements: Measurements per temperature

        Returns:
            Dictionary with comparative results
        """
        results = {}

        for temp in temperatures:
            results[f'T={temp}'] = self.run_measurements(
                logits=logits,
                temperature=temp,
                num_measurements=num_measurements
            )

        return results

    def visualize_collapse(
        self,
        logits: np.ndarray,
        temperature: float
    ) -> Dict:
        """
        Get detailed collapse visualization data

        Args:
            logits: Model logits
            temperature: Sampling temperature

        Returns:
            Data for visualization
        """
        state = QuantumState.from_logits(logits, temperature)

        # Before measurement
        amplitudes_before = state.amplitudes.copy()
        probs_before = state.get_probabilities()
        entropy_before = state.entropy()

        # Perform measurement
        outcome = state.measure()

        # After measurement
        amplitudes_after = state.amplitudes
        probs_after = state.get_probabilities()
        entropy_after = state.entropy()

        return {
            'before': {
                'amplitudes': amplitudes_before,
                'probabilities': probs_before,
                'entropy': entropy_before,
                'is_superposition': True
            },
            'measurement': {
                'outcome': outcome
            },
            'after': {
                'amplitudes': amplitudes_after,
                'probabilities': probs_after,
                'entropy': entropy_after,
                'is_superposition': False
            }
        }
```

---

## Definition of Done

- [ ] All tests passing
- [ ] Quantum state normalization validated
- [ ] Born rule probabilities verified
- [ ] Measurement collapse simulated correctly
- [ ] Decoherence via temperature demonstrated
- [ ] Visualization notebook complete
- [ ] Code coverage > 85%

---

## Deliverables

1. QuantumState class with full test coverage
2. CollapseSimulator class
3. Visualization tools for collapse process
4. Jupyter notebook: `experiments/notebooks/02_wave_function_collapse.ipynb`
5. Experimental validation of collapse statistics
