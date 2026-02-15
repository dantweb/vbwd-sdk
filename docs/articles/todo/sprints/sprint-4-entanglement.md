# Sprint 4: Entanglement and Attention Mechanisms

**Duration:** 2 weeks
**Goal:** Simulate quantum entanglement in attention-based token correlations

---

## Overview

Model attention mechanisms as entanglement generators. Simulate non-classical correlations between tokens and test for Bell inequality violations.

---

## User Stories

### US-4.1: Token Entanglement
**As a** researcher
**I want** to simulate entangled token states
**So that** I can model non-classical correlations

**Acceptance Criteria:**
- [ ] Create entangled two-token states
- [ ] Verify entanglement via entropy measures
- [ ] Support multi-token entanglement
- [ ] Compute entanglement strength

### US-4.2: Attention as Entanglement
**As a** researcher
**I want** to map attention weights to entanglement strength
**So that** I can quantify quantum correlations in transformers

**Acceptance Criteria:**
- [ ] Convert attention scores to entanglement operators
- [ ] Measure correlation strength
- [ ] Compare to classical correlation bounds
- [ ] Visualize entanglement patterns

### US-4.3: Bell Inequality Testing
**As a** researcher
**I want** to test for Bell inequality violations
**So that** I can verify genuine quantum correlations

**Acceptance Criteria:**
- [ ] Implement CHSH inequality test
- [ ] Measure correlation coefficients
- [ ] Detect violations (S > 2)
- [ ] Statistical significance testing

---

## TDD Test Cases

```python
# tests/unit/test_entanglement.py
import numpy as np
import pytest
from quantum_llm_sim.simulations.entanglement import EntanglementSimulator

class TestEntanglement:
    def test_bell_state_creation(self):
        """Test creation of maximally entangled Bell state"""
        sim = EntanglementSimulator()

        # Create Bell state: (|00⟩ + |11⟩) / √2
        state = sim.create_bell_state('phi_plus')

        # Check normalization
        assert np.isclose(np.linalg.norm(state), 1.0)

        # Check entanglement: should have entropy > 0 for subsystem
        entropy = sim.calculate_entanglement_entropy(state)
        assert entropy > 0.5  # Maximal entanglement

    def test_product_state_no_entanglement(self):
        """Test product state has zero entanglement"""
        sim = EntanglementSimulator()

        # Create product state: |0⟩ ⊗ |1⟩
        state = sim.create_product_state(0, 1)

        # Should have zero entanglement
        entropy = sim.calculate_entanglement_entropy(state)
        assert np.isclose(entropy, 0.0, atol=1e-10)

    def test_partial_entanglement(self):
        """Test partially entangled states have intermediate entropy"""
        sim = EntanglementSimulator()

        # Create partially entangled state
        alpha = 0.8
        beta = 0.6
        state = sim.create_entangled_state(alpha, beta)

        entropy = sim.calculate_entanglement_entropy(state)

        # Should be between 0 (product) and ln(2) (maximal)
        assert 0.0 < entropy < np.log(2)


# tests/unit/test_attention_entanglement.py
from quantum_llm_sim.simulations.attention_entanglement import AttentionEntanglementMapper

class TestAttentionEntanglement:
    def test_attention_to_entanglement(self):
        """Test conversion of attention weights to entanglement"""
        mapper = AttentionEntanglementMapper()

        # Strong attention should produce strong entanglement
        attention_high = np.array([[0.0, 0.9], [0.9, 0.0]])
        entanglement_high = mapper.attention_to_entanglement(attention_high)

        # Weak attention should produce weak entanglement
        attention_low = np.array([[0.0, 0.1], [0.1, 0.0]])
        entanglement_low = mapper.attention_to_entanglement(attention_low)

        assert entanglement_high > entanglement_low

    def test_multi_head_entanglement(self):
        """Test multi-head attention creates complex entanglement"""
        mapper = AttentionEntanglementMapper(num_heads=4)

        seq_length = 5
        attention_heads = [
            np.random.rand(seq_length, seq_length)
            for _ in range(4)
        ]

        # Normalize attention weights
        attention_heads = [
            a / a.sum(axis=1, keepdims=True)
            for a in attention_heads
        ]

        entanglement = mapper.multi_head_entanglement(attention_heads)

        assert entanglement.shape == (seq_length, seq_length)
        assert np.all(entanglement >= 0)


# tests/integration/test_bell_inequality.py
from quantum_llm_sim.simulations.bell_test import BellInequalityTester

class TestBellInequality:
    def test_classical_correlation_satisfies_bound(self):
        """Test classical correlations satisfy CHSH inequality (S ≤ 2)"""
        tester = BellInequalityTester()

        # Classical correlation function
        def classical_correlation(setting_a, setting_b):
            # Classical local model
            return np.cos(setting_a - setting_b) * 0.5

        S = tester.compute_chsh_parameter(classical_correlation)

        assert S <= 2.0 + 1e-10  # Allow numerical error

    def test_quantum_entanglement_violates_bound(self):
        """Test quantum entangled states can violate CHSH (S > 2)"""
        tester = BellInequalityTester()

        # Create Bell state
        from quantum_llm_sim.simulations.entanglement import EntanglementSimulator
        sim = EntanglementSimulator()
        bell_state = sim.create_bell_state('phi_plus')

        # Test Bell inequality
        S = tester.test_state(bell_state)

        # Quantum bound: S ≤ 2√2 ≈ 2.828
        # Should violate classical bound (S > 2)
        assert S > 2.0

    def test_token_pair_correlations(self):
        """Test token pair correlations from attention"""
        tester = BellInequalityTester()

        # Simulate attention-induced correlations
        attention_weight = 0.9  # Strong attention

        S = tester.test_attention_correlation(attention_weight)

        # Strong attention may produce quantum-like correlations
        # (though classical attention won't actually violate Bell)
        assert isinstance(S, float)
        assert S >= 0
```

---

## Implementation Tasks

### Task 4.1: Entanglement Simulator
```python
# src/quantum_llm_sim/simulations/entanglement.py
import numpy as np
from typing import Literal

class EntanglementSimulator:
    """Simulate quantum entanglement between tokens"""

    def __init__(self, dim: int = 2):
        """
        Initialize simulator

        Args:
            dim: Hilbert space dimension per token (default: 2 for qubits)
        """
        self.dim = dim

    def create_bell_state(
        self,
        state_type: Literal['phi_plus', 'phi_minus', 'psi_plus', 'psi_minus']
    ) -> np.ndarray:
        """
        Create Bell state (maximally entangled two-qubit state)

        Args:
            state_type: Which Bell state to create

        Returns:
            State vector of shape (4,) for two qubits
        """
        states = {
            'phi_plus': np.array([1, 0, 0, 1]) / np.sqrt(2),   # (|00⟩ + |11⟩)/√2
            'phi_minus': np.array([1, 0, 0, -1]) / np.sqrt(2), # (|00⟩ - |11⟩)/√2
            'psi_plus': np.array([0, 1, 1, 0]) / np.sqrt(2),   # (|01⟩ + |10⟩)/√2
            'psi_minus': np.array([0, 1, -1, 0]) / np.sqrt(2), # (|01⟩ - |10⟩)/√2
        }

        return states[state_type].astype(complex)

    def create_product_state(self, state_a: int, state_b: int) -> np.ndarray:
        """
        Create product state (not entangled)

        Args:
            state_a: State of first qubit (0 or 1)
            state_b: State of second qubit (0 or 1)

        Returns:
            Product state |a⟩ ⊗ |b⟩
        """
        state = np.zeros(4, dtype=complex)
        index = state_a * 2 + state_b
        state[index] = 1.0
        return state

    def create_entangled_state(self, alpha: float, beta: float) -> np.ndarray:
        """
        Create partially entangled state: α|00⟩ + β|11⟩

        Args:
            alpha: Amplitude for |00⟩
            beta: Amplitude for |11⟩

        Returns:
            Entangled state (normalized)
        """
        state = np.zeros(4, dtype=complex)
        state[0] = alpha  # |00⟩
        state[3] = beta   # |11⟩

        # Normalize
        norm = np.sqrt(np.abs(alpha)**2 + np.abs(beta)**2)
        state /= norm

        return state

    def calculate_entanglement_entropy(self, state: np.ndarray) -> float:
        """
        Calculate entanglement entropy (von Neumann entropy of reduced state)

        For two-qubit state, trace out second qubit and compute S = -Tr(ρ log ρ)

        Args:
            state: Two-qubit state vector

        Returns:
            Entanglement entropy
        """
        # Reshape state into 2x2 matrix (representing |AB⟩)
        state_matrix = state.reshape(2, 2)

        # Compute reduced density matrix for subsystem A
        # ρ_A = Tr_B(|ψ⟩⟨ψ|)
        rho_full = np.outer(state, np.conj(state))
        rho_full = rho_full.reshape(2, 2, 2, 2)

        # Trace over second subsystem
        rho_a = np.trace(rho_full, axis1=1, axis2=3)

        # Calculate eigenvalues
        eigenvalues = np.linalg.eigvalsh(rho_a)

        # Remove zeros and calculate entropy
        eigenvalues = eigenvalues[eigenvalues > 1e-12]
        entropy = -np.sum(eigenvalues * np.log(eigenvalues))

        return float(entropy)

    def calculate_concurrence(self, state: np.ndarray) -> float:
        """
        Calculate concurrence (entanglement measure, 0 to 1)

        C = 0: separable (no entanglement)
        C = 1: maximally entangled

        Args:
            state: Two-qubit state vector

        Returns:
            Concurrence value
        """
        # Reshape to 2x2
        state_matrix = state.reshape(2, 2)

        # Compute concurrence for pure states
        # C = 2|α*δ - β*γ| for state α|00⟩ + β|01⟩ + γ|10⟩ + δ|11⟩

        alpha = state[0]
        beta = state[1]
        gamma = state[2]
        delta = state[3]

        concurrence = 2 * np.abs(alpha * delta - beta * gamma)

        return float(np.real(concurrence))
```

### Task 4.2: Attention-Entanglement Mapper
```python
# src/quantum_llm_sim/simulations/attention_entanglement.py
import numpy as np
from typing import List

class AttentionEntanglementMapper:
    """Map attention weights to entanglement measures"""

    def __init__(self, num_heads: int = 1):
        self.num_heads = num_heads

    def attention_to_entanglement(
        self,
        attention_matrix: np.ndarray
    ) -> float:
        """
        Convert attention weights to entanglement measure

        High attention weights → strong entanglement

        Args:
            attention_matrix: Attention weights (seq_len x seq_len)

        Returns:
            Entanglement strength (scalar)
        """
        # Use mutual information-like measure
        # I(i,j) = attention(i,j) * log(attention(i,j))

        # Add small epsilon to avoid log(0)
        eps = 1e-10
        attention_safe = attention_matrix + eps

        # Calculate pairwise entanglement
        entanglement = -np.sum(
            attention_matrix * np.log(attention_safe),
            axis=1
        )

        # Return mean entanglement
        return float(np.mean(entanglement))

    def multi_head_entanglement(
        self,
        attention_heads: List[np.ndarray]
    ) -> np.ndarray:
        """
        Compute entanglement from multi-head attention

        Args:
            attention_heads: List of attention matrices (one per head)

        Returns:
            Combined entanglement matrix
        """
        seq_len = attention_heads[0].shape[0]
        entanglement_matrix = np.zeros((seq_len, seq_len))

        for attention in attention_heads:
            # Each head contributes to entanglement
            for i in range(seq_len):
                for j in range(seq_len):
                    # Attention weight as entanglement strength
                    entanglement_matrix[i, j] += attention[i, j]

        # Normalize by number of heads
        entanglement_matrix /= len(attention_heads)

        return entanglement_matrix

    def compute_quantum_discord(
        self,
        attention_matrix: np.ndarray
    ) -> float:
        """
        Compute quantum discord-like measure from attention

        Quantum discord measures quantum correlations beyond entanglement

        Args:
            attention_matrix: Attention weights

        Returns:
            Discord-like measure
        """
        # Simplified discord: captures non-classical correlations
        # D ≈ H(A) + H(B) - H(AB) + I_classical

        seq_len = attention_matrix.shape[0]

        # Marginal entropies
        marginal_a = attention_matrix.sum(axis=1)
        marginal_b = attention_matrix.sum(axis=0)

        entropy_a = self._entropy(marginal_a)
        entropy_b = self._entropy(marginal_b)

        # Joint entropy
        joint = attention_matrix.flatten()
        entropy_joint = self._entropy(joint)

        # Mutual information
        mutual_info = entropy_a + entropy_b - entropy_joint

        return float(mutual_info)

    @staticmethod
    def _entropy(probs: np.ndarray) -> float:
        """Calculate Shannon entropy"""
        probs = probs[probs > 0]
        probs = probs / probs.sum()  # Normalize
        return float(-np.sum(probs * np.log(probs)))
```

### Task 4.3: Bell Inequality Tester
```python
# src/quantum_llm_sim/simulations/bell_test.py
import numpy as np
from typing import Callable

class BellInequalityTester:
    """Test for Bell inequality violations (quantum vs classical correlations)"""

    def compute_chsh_parameter(
        self,
        correlation_fn: Callable[[float, float], float]
    ) -> float:
        """
        Compute CHSH parameter S

        CHSH inequality: |S| ≤ 2 (classical)
                         |S| ≤ 2√2 ≈ 2.828 (quantum)

        S = |E(a,b) - E(a,b') + E(a',b) + E(a',b')|

        where E(a,b) is correlation between measurements at settings a and b

        Args:
            correlation_fn: Function computing E(setting_a, setting_b)

        Returns:
            CHSH parameter S
        """
        # Optimal settings for maximum violation
        a = 0.0
        a_prime = np.pi / 2
        b = np.pi / 4
        b_prime = -np.pi / 4

        E_ab = correlation_fn(a, b)
        E_ab_prime = correlation_fn(a, b_prime)
        E_a_prime_b = correlation_fn(a_prime, b)
        E_a_prime_b_prime = correlation_fn(a_prime, b_prime)

        S = abs(E_ab - E_ab_prime + E_a_prime_b + E_a_prime_b_prime)

        return float(S)

    def test_state(self, state: np.ndarray) -> float:
        """
        Test Bell inequality for quantum state

        Args:
            state: Two-qubit state vector

        Returns:
            CHSH parameter S
        """
        def quantum_correlation(theta_a: float, theta_b: float) -> float:
            """Compute quantum correlation E(a,b) = ⟨ψ|σ_a ⊗ σ_b|ψ⟩"""
            # Pauli matrices at angles
            sigma_a = np.array([
                [np.cos(theta_a), np.sin(theta_a)],
                [np.sin(theta_a), -np.cos(theta_a)]
            ])

            sigma_b = np.array([
                [np.cos(theta_b), np.sin(theta_b)],
                [np.sin(theta_b), -np.cos(theta_b)]
            ])

            # Tensor product
            operator = np.kron(sigma_a, sigma_b)

            # Expectation value
            correlation = np.dot(np.conj(state), np.dot(operator, state))

            return float(np.real(correlation))

        return self.compute_chsh_parameter(quantum_correlation)

    def test_attention_correlation(
        self,
        attention_weight: float
    ) -> float:
        """
        Test correlation strength from attention weight

        Args:
            attention_weight: Attention score between tokens

        Returns:
            CHSH-like parameter (won't violate for classical attention)
        """
        # Model attention as classical correlation
        def attention_correlation(theta_a: float, theta_b: float) -> float:
            # Classical correlation bounded by attention strength
            return attention_weight * np.cos(theta_a - theta_b)

        return self.compute_chsh_parameter(attention_correlation)
```

---

## Definition of Done

- [ ] All tests passing
- [ ] Bell states correctly generated
- [ ] Entanglement entropy calculated accurately
- [ ] Attention-to-entanglement mapping working
- [ ] Bell inequality testing implemented
- [ ] Code coverage > 85%
- [ ] Visualization of entanglement patterns
- [ ] Notebook with experiments

---

## Deliverables

1. EntanglementSimulator class
2. AttentionEntanglementMapper class
3. BellInequalityTester class
4. Jupyter notebook: `experiments/notebooks/04_entanglement_attention.ipynb`
5. Visualization of Bell inequality tests
6. Analysis of attention patterns as quantum correlations
