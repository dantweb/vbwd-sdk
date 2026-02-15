# Sprint 1: Uncertainty Principle Measurement Framework

**Duration:** 2 weeks
**Goal:** Implement measurement system for ΔH × ΔS ≥ 1/2 uncertainty relation in LLM sampling

---

## Overview

Build the core measurement framework to empirically validate the uncertainty principle in temperature-controlled language models. Measure entropy (ΔH) and semantic spread (ΔS) across different temperature settings.

---

## User Stories

### US-1.1: Entropy Measurement
**As a** researcher
**I want** to measure token selection entropy at different temperatures
**So that** I can quantify determinism in generation

**Acceptance Criteria:**
- [ ] Compute Shannon entropy from token probability distributions
- [ ] Measure entropy variance (ΔH) across multiple samples
- [ ] Support temperature range [0.1, 2.0]
- [ ] Output includes mean, variance, and distribution

### US-1.2: Semantic Spread Measurement
**As a** researcher
**I want** to measure semantic diversity in generated outputs
**So that** I can quantify creativity

**Acceptance Criteria:**
- [ ] Compute semantic spread using embedding distances
- [ ] Measure variance in output diversity (ΔS)
- [ ] Support multiple distance metrics (cosine, euclidean)
- [ ] Normalize measurements for comparison

### US-1.3: Uncertainty Bound Verification
**As a** researcher
**I want** to verify ΔH × ΔS ≥ 1/2
**So that** I can validate the theoretical bound empirically

**Acceptance Criteria:**
- [ ] Compute product ΔH × ΔS for each temperature
- [ ] Verify bound holds across temperature range
- [ ] Generate violation report if bound is broken
- [ ] Statistical significance testing

---

## TDD Test Cases

### Test 1.1: Entropy Calculation
```python
# tests/unit/test_entropy.py
import numpy as np
import pytest
from quantum_llm_sim.metrics.entropy import EntropyCalculator

class TestEntropyCalculator:
    def test_entropy_uniform_distribution(self):
        """Test entropy of uniform distribution"""
        calc = EntropyCalculator()
        probs = np.array([0.25, 0.25, 0.25, 0.25])
        entropy = calc.calculate_shannon_entropy(probs)
        expected = np.log(4)  # ln(4) for uniform over 4 outcomes
        assert np.isclose(entropy, expected, rtol=1e-5)

    def test_entropy_deterministic(self):
        """Test entropy of deterministic distribution"""
        calc = EntropyCalculator()
        probs = np.array([1.0, 0.0, 0.0, 0.0])
        entropy = calc.calculate_shannon_entropy(probs)
        assert np.isclose(entropy, 0.0, atol=1e-10)

    def test_entropy_variance(self):
        """Test calculation of entropy variance"""
        calc = EntropyCalculator()
        samples = [
            np.array([0.9, 0.1]),
            np.array([0.8, 0.2]),
            np.array([0.85, 0.15]),
        ]
        delta_h = calc.calculate_entropy_variance(samples)
        assert delta_h >= 0
        assert isinstance(delta_h, float)

    def test_entropy_invalid_probabilities(self):
        """Test error handling for invalid probabilities"""
        calc = EntropyCalculator()
        with pytest.raises(ValueError):
            calc.calculate_shannon_entropy(np.array([0.5, 0.6]))  # Don't sum to 1
        with pytest.raises(ValueError):
            calc.calculate_shannon_entropy(np.array([-0.1, 1.1]))  # Negative prob
```

### Test 1.2: Semantic Spread Calculation
```python
# tests/unit/test_semantic_spread.py
import numpy as np
import pytest
from quantum_llm_sim.metrics.semantic_spread import SemanticSpreadCalculator

class TestSemanticSpreadCalculator:
    def test_spread_identical_outputs(self):
        """Test spread when all outputs are identical"""
        calc = SemanticSpreadCalculator()
        embeddings = np.array([
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ])
        spread = calc.calculate_spread(embeddings)
        assert np.isclose(spread, 0.0, atol=1e-10)

    def test_spread_diverse_outputs(self):
        """Test spread increases with diversity"""
        calc = SemanticSpreadCalculator()

        # Low diversity
        emb_low = np.array([
            [1.0, 0.0],
            [0.9, 0.1],
            [0.95, 0.05],
        ])
        spread_low = calc.calculate_spread(emb_low)

        # High diversity
        emb_high = np.array([
            [1.0, 0.0],
            [0.0, 1.0],
            [0.5, 0.5],
        ])
        spread_high = calc.calculate_spread(emb_high)

        assert spread_high > spread_low

    def test_spread_variance(self):
        """Test calculation of spread variance (ΔS)"""
        calc = SemanticSpreadCalculator()
        samples = [
            np.random.randn(10, 128),  # 10 samples, 128-dim embeddings
            np.random.randn(10, 128),
            np.random.randn(10, 128),
        ]
        delta_s = calc.calculate_spread_variance(samples)
        assert delta_s >= 0
        assert isinstance(delta_s, float)
```

### Test 1.3: Uncertainty Bound Verification
```python
# tests/integration/test_uncertainty_bound.py
import numpy as np
import pytest
from quantum_llm_sim.metrics.uncertainty import UncertaintyPrincipleValidator

class TestUncertaintyBound:
    def test_bound_holds_across_temperatures(self):
        """Test that ΔH × ΔS ≥ 1/2 for various temperatures"""
        validator = UncertaintyPrincipleValidator()

        temperatures = [0.1, 0.5, 0.7, 1.0, 1.5, 2.0]

        for temp in temperatures:
            delta_h, delta_s, product = validator.measure_at_temperature(
                temperature=temp,
                num_samples=100,
                vocab_size=1000
            )

            # Check bound
            assert product >= 0.5, f"Bound violated at T={temp}: {product} < 0.5"

    def test_trade_off_behavior(self):
        """Test that low T gives low ΔH, high ΔS and vice versa"""
        validator = UncertaintyPrincipleValidator()

        # Low temperature: deterministic (low ΔH), but not diverse (high ΔS)
        delta_h_low, delta_s_low, _ = validator.measure_at_temperature(
            temperature=0.1, num_samples=100, vocab_size=1000
        )

        # High temperature: high entropy (high ΔH), but more uniform diversity (low ΔS)
        delta_h_high, delta_s_high, _ = validator.measure_at_temperature(
            temperature=2.0, num_samples=100, vocab_size=1000
        )

        assert delta_h_low < delta_h_high
        # Note: ΔS behavior depends on semantic model

    def test_statistical_significance(self):
        """Test statistical significance of bound measurement"""
        validator = UncertaintyPrincipleValidator()

        results = validator.run_multiple_trials(
            temperature=1.0,
            num_trials=10,
            samples_per_trial=100
        )

        assert results['p_value'] < 0.05  # Statistically significant
        assert results['mean_product'] >= 0.5
```

---

## Implementation Tasks

### Task 1.1: Entropy Calculator
```python
# src/quantum_llm_sim/metrics/entropy.py
import numpy as np
from typing import List, Union

class EntropyCalculator:
    """Calculate Shannon entropy and related metrics"""

    def calculate_shannon_entropy(
        self,
        probabilities: np.ndarray
    ) -> float:
        """
        Calculate Shannon entropy H = -Σ p_i log(p_i)

        Args:
            probabilities: Probability distribution (must sum to 1)

        Returns:
            Shannon entropy in nats (natural log)

        Raises:
            ValueError: If probabilities invalid
        """
        # Validate
        if not np.isclose(probabilities.sum(), 1.0, rtol=1e-5):
            raise ValueError("Probabilities must sum to 1")
        if np.any(probabilities < 0):
            raise ValueError("Probabilities must be non-negative")

        # Filter out zeros to avoid log(0)
        probs_filtered = probabilities[probabilities > 0]

        # Calculate entropy
        entropy = -np.sum(probs_filtered * np.log(probs_filtered))

        return float(entropy)

    def calculate_entropy_variance(
        self,
        probability_samples: List[np.ndarray]
    ) -> float:
        """
        Calculate variance in entropy (ΔH)

        Args:
            probability_samples: List of probability distributions

        Returns:
            Standard deviation of entropies (ΔH)
        """
        entropies = [
            self.calculate_shannon_entropy(probs)
            for probs in probability_samples
        ]

        return float(np.std(entropies))

    def entropy_at_temperature(
        self,
        logits: np.ndarray,
        temperature: float
    ) -> float:
        """
        Calculate entropy after temperature-scaled softmax

        Args:
            logits: Raw logit scores
            temperature: Sampling temperature

        Returns:
            Entropy of temperature-scaled distribution
        """
        probs = self._softmax_with_temperature(logits, temperature)
        return self.calculate_shannon_entropy(probs)

    @staticmethod
    def _softmax_with_temperature(
        logits: np.ndarray,
        temperature: float
    ) -> np.ndarray:
        """Apply temperature-scaled softmax"""
        scaled_logits = logits / temperature
        exp_logits = np.exp(scaled_logits - np.max(scaled_logits))  # Numerical stability
        return exp_logits / exp_logits.sum()
```

### Task 1.2: Semantic Spread Calculator
```python
# src/quantum_llm_sim/metrics/semantic_spread.py
import numpy as np
from typing import List, Literal

class SemanticSpreadCalculator:
    """Calculate semantic diversity and spread metrics"""

    def __init__(self, metric: Literal['cosine', 'euclidean'] = 'cosine'):
        self.metric = metric

    def calculate_spread(
        self,
        embeddings: np.ndarray
    ) -> float:
        """
        Calculate semantic spread as average pairwise distance

        Args:
            embeddings: Array of shape (n_samples, embedding_dim)

        Returns:
            Average pairwise distance (spread measure)
        """
        n_samples = embeddings.shape[0]

        if n_samples < 2:
            return 0.0

        # Calculate pairwise distances
        distances = []
        for i in range(n_samples):
            for j in range(i + 1, n_samples):
                if self.metric == 'cosine':
                    dist = self._cosine_distance(embeddings[i], embeddings[j])
                elif self.metric == 'euclidean':
                    dist = self._euclidean_distance(embeddings[i], embeddings[j])
                distances.append(dist)

        return float(np.mean(distances))

    def calculate_spread_variance(
        self,
        embedding_samples: List[np.ndarray]
    ) -> float:
        """
        Calculate variance in semantic spread (ΔS)

        Args:
            embedding_samples: List of embedding arrays

        Returns:
            Standard deviation of spreads (ΔS)
        """
        spreads = [
            self.calculate_spread(embs)
            for embs in embedding_samples
        ]

        return float(np.std(spreads))

    @staticmethod
    def _cosine_distance(v1: np.ndarray, v2: np.ndarray) -> float:
        """Calculate cosine distance (1 - cosine similarity)"""
        similarity = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        return 1.0 - similarity

    @staticmethod
    def _euclidean_distance(v1: np.ndarray, v2: np.ndarray) -> float:
        """Calculate Euclidean distance"""
        return float(np.linalg.norm(v1 - v2))
```

### Task 1.3: Uncertainty Principle Validator
```python
# src/quantum_llm_sim/metrics/uncertainty.py
import numpy as np
from typing import Dict, Tuple
from .entropy import EntropyCalculator
from .semantic_spread import SemanticSpreadCalculator

class UncertaintyPrincipleValidator:
    """Validate ΔH × ΔS ≥ 1/2 uncertainty principle"""

    def __init__(self):
        self.entropy_calc = EntropyCalculator()
        self.spread_calc = SemanticSpreadCalculator()

    def measure_at_temperature(
        self,
        temperature: float,
        num_samples: int,
        vocab_size: int
    ) -> Tuple[float, float, float]:
        """
        Measure ΔH, ΔS, and their product at given temperature

        Args:
            temperature: Sampling temperature
            num_samples: Number of samples to generate
            vocab_size: Size of vocabulary

        Returns:
            (delta_h, delta_s, product)
        """
        # Generate random logits (simulating model outputs)
        logit_samples = [
            np.random.randn(vocab_size) for _ in range(num_samples)
        ]

        # Calculate probability distributions
        prob_samples = [
            self.entropy_calc._softmax_with_temperature(logits, temperature)
            for logits in logit_samples
        ]

        # Calculate ΔH (entropy variance)
        delta_h = self.entropy_calc.calculate_entropy_variance(prob_samples)

        # Generate embeddings (simulating semantic space)
        # Sample from distributions to get token indices
        embedding_dim = 128
        embedding_samples = []

        for probs in prob_samples:
            # Sample tokens and get their embeddings
            tokens = np.random.choice(vocab_size, size=10, p=probs)
            embeddings = np.random.randn(len(tokens), embedding_dim)
            embedding_samples.append(embeddings)

        # Calculate ΔS (spread variance)
        delta_s = self.spread_calc.calculate_spread_variance(embedding_samples)

        # Calculate product
        product = delta_h * delta_s

        return delta_h, delta_s, product

    def run_multiple_trials(
        self,
        temperature: float,
        num_trials: int,
        samples_per_trial: int
    ) -> Dict:
        """
        Run multiple trials and perform statistical analysis

        Args:
            temperature: Sampling temperature
            num_trials: Number of independent trials
            samples_per_trial: Samples per trial

        Returns:
            Dictionary with statistical results
        """
        products = []

        for _ in range(num_trials):
            _, _, product = self.measure_at_temperature(
                temperature=temperature,
                num_samples=samples_per_trial,
                vocab_size=1000
            )
            products.append(product)

        products = np.array(products)

        # Statistical tests
        violations = np.sum(products < 0.5)
        p_value = violations / num_trials

        return {
            'mean_product': float(np.mean(products)),
            'std_product': float(np.std(products)),
            'min_product': float(np.min(products)),
            'max_product': float(np.max(products)),
            'violations': int(violations),
            'p_value': float(p_value),
            'bound_holds': violations == 0
        }
```

---

## Definition of Done

- [ ] All Sprint 1 tests passing
- [ ] Entropy calculation validated against known distributions
- [ ] Semantic spread calculation working for various inputs
- [ ] Uncertainty bound ΔH × ΔS ≥ 1/2 verified empirically
- [ ] Code coverage > 85%
- [ ] Documentation complete with examples
- [ ] Experiment notebook demonstrating measurements

---

## Dependencies

- Sprint 0: Project setup complete

---

## Deliverables

1. EntropyCalculator class with tests
2. SemanticSpreadCalculator class with tests
3. UncertaintyPrincipleValidator class with tests
4. Jupyter notebook: `experiments/notebooks/01_uncertainty_principle.ipynb`
5. Experimental results validating bound
6. Visualization of ΔH × ΔS across temperature range

---

## Experimental Validation Script

```python
# experiments/scripts/validate_uncertainty_principle.py
import numpy as np
import matplotlib.pyplot as plt
from quantum_llm_sim.metrics.uncertainty import UncertaintyPrincipleValidator

def main():
    validator = UncertaintyPrincipleValidator()

    temperatures = np.linspace(0.1, 2.0, 20)
    results = {'T': [], 'ΔH': [], 'ΔS': [], 'product': []}

    for temp in temperatures:
        delta_h, delta_s, product = validator.measure_at_temperature(
            temperature=temp,
            num_samples=100,
            vocab_size=1000
        )

        results['T'].append(temp)
        results['ΔH'].append(delta_h)
        results['ΔS'].append(delta_s)
        results['product'].append(product)

    # Plot results
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # ΔH vs Temperature
    axes[0, 0].plot(results['T'], results['ΔH'])
    axes[0, 0].set_xlabel('Temperature')
    axes[0, 0].set_ylabel('ΔH (Entropy Uncertainty)')
    axes[0, 0].set_title('Entropy Uncertainty vs Temperature')

    # ΔS vs Temperature
    axes[0, 1].plot(results['T'], results['ΔS'])
    axes[0, 1].set_xlabel('Temperature')
    axes[0, 1].set_ylabel('ΔS (Semantic Spread)')
    axes[0, 1].set_title('Semantic Spread vs Temperature')

    # Product vs Temperature
    axes[1, 0].plot(results['T'], results['product'], label='ΔH × ΔS')
    axes[1, 0].axhline(y=0.5, color='r', linestyle='--', label='Bound (1/2)')
    axes[1, 0].set_xlabel('Temperature')
    axes[1, 0].set_ylabel('ΔH × ΔS')
    axes[1, 0].set_title('Uncertainty Product vs Temperature')
    axes[1, 0].legend()

    # Trade-off plot
    axes[1, 1].scatter(results['ΔH'], results['ΔS'], c=results['T'], cmap='viridis')
    axes[1, 1].set_xlabel('ΔH')
    axes[1, 1].set_ylabel('ΔS')
    axes[1, 1].set_title('Entropy-Spread Trade-off')
    plt.colorbar(axes[1, 1].collections[0], ax=axes[1, 1], label='Temperature')

    plt.tight_layout()
    plt.savefig('data/results/uncertainty_principle_validation.png')
    print("Results saved to data/results/uncertainty_principle_validation.png")

if __name__ == '__main__':
    main()
```
