# Sprint 6: Visualization and Reporting

**Duration:** 1 week
**Goal:** Create comprehensive visualizations and generate publication-ready figures

---

## Overview

Develop visualization tools for all quantum effects and generate figures for research papers. Create interactive dashboards and static plots.

---

## User Stories

### US-6.1: Static Visualizations
**As a** researcher
**I want** publication-quality static plots
**So that** I can include them in papers

**Acceptance Criteria:**
- [ ] Matplotlib/seaborn plots
- [ ] High resolution (300+ DPI)
- [ ] Consistent styling
- [ ] Proper axis labels and legends

### US-6.2: Interactive Visualizations
**As a** researcher
**I want** interactive exploratory visualizations
**So that** I can analyze results dynamically

**Acceptance Criteria:**
- [ ] Interactive plots (plotly/bokeh)
- [ ] Parameter sliders
- [ ] Real-time updates
- [ ] Export functionality

### US-6.3: Report Generation
**As a** researcher
**I want** automated report generation
**So that** I can quickly share results

**Acceptance Criteria:**
- [ ] HTML reports
- [ ] PDF export (via LaTeX)
- [ ] Include all figures and tables
- [ ] Summary statistics

---

## Implementation Tasks

### Task 6.1: Visualization Library
```python
# src/quantum_llm_sim/visualization/plots.py
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path

class QuantumLLMVisualizer:
    """Visualization tools for quantum LLM experiments"""

    def __init__(self, style: str = 'seaborn-v0_8-paper'):
        plt.style.use(style)
        self.figure_dir = Path('data/figures')
        self.figure_dir.mkdir(parents=True, exist_ok=True)

    def plot_uncertainty_principle(
        self,
        results: Dict,
        save_path: Optional[str] = None
    ):
        """Plot ΔH × ΔS vs Temperature"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        temperatures = results['temperatures']
        delta_h = results['delta_h']
        delta_s = results['delta_s']
        products = results['products']

        # ΔH vs T
        axes[0, 0].plot(temperatures, delta_h, 'o-', linewidth=2)
        axes[0, 0].set_xlabel('Temperature')
        axes[0, 0].set_ylabel('ΔH (Entropy Uncertainty)')
        axes[0, 0].set_title('Entropy Uncertainty vs Temperature')
        axes[0, 0].grid(True, alpha=0.3)

        # ΔS vs T
        axes[0, 1].plot(temperatures, delta_s, 's-', linewidth=2, color='orange')
        axes[0, 1].set_xlabel('Temperature')
        axes[0, 1].set_ylabel('ΔS (Semantic Spread)')
        axes[0, 1].set_title('Semantic Spread vs Temperature')
        axes[0, 1].grid(True, alpha=0.3)

        # Product vs T
        axes[1, 0].plot(temperatures, products, '^-', linewidth=2, color='green')
        axes[1, 0].axhline(y=0.5, color='r', linestyle='--',
                          linewidth=2, label='Bound (ℏ/2)')
        axes[1, 0].set_xlabel('Temperature')
        axes[1, 0].set_ylabel('ΔH × ΔS')
        axes[1, 0].set_title('Uncertainty Product vs Temperature')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)

        # Trade-off plot
        sc = axes[1, 1].scatter(delta_h, delta_s, c=temperatures,
                                cmap='viridis', s=100, edgecolors='black')
        axes[1, 1].set_xlabel('ΔH')
        axes[1, 1].set_ylabel('ΔS')
        axes[1, 1].set_title('Entropy-Spread Trade-off')
        axes[1, 1].grid(True, alpha=0.3)
        plt.colorbar(sc, ax=axes[1, 1], label='Temperature')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.savefig(self.figure_dir / 'uncertainty_principle.png',
                       dpi=300, bbox_inches='tight')

        return fig

    def plot_wave_collapse(
        self,
        collapse_data: Dict,
        save_path: Optional[str] = None
    ):
        """Visualize wave function collapse"""
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))

        before = collapse_data['before']
        after = collapse_data['after']

        # Amplitudes before
        indices = np.arange(len(before['amplitudes']))
        axes[0].bar(indices, np.abs(before['amplitudes']), alpha=0.7)
        axes[0].set_xlabel('Token Index')
        axes[0].set_ylabel('|Amplitude|')
        axes[0].set_title('Before Measurement\n(Superposition)')
        axes[0].grid(True, alpha=0.3)

        # Probabilities before
        axes[1].bar(indices, before['probabilities'], alpha=0.7, color='orange')
        axes[1].set_xlabel('Token Index')
        axes[1].set_ylabel('Probability')
        axes[1].set_title('Born Rule Probabilities')
        axes[1].grid(True, alpha=0.3)

        # After collapse
        axes[2].bar(indices, after['probabilities'], alpha=0.7, color='red')
        axes[2].set_xlabel('Token Index')
        axes[2].set_ylabel('Probability')
        axes[2].set_title(f'After Measurement\n(Collapsed to token {collapse_data["measurement"]["outcome"]})')
        axes[2].grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.savefig(self.figure_dir / 'wave_collapse.png',
                       dpi=300, bbox_inches='tight')

        return fig

    def plot_path_integral(
        self,
        path_data: Dict,
        save_path: Optional[str] = None
    ):
        """Visualize path integral results"""
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        # Path amplitudes
        if 'quantum_result' in path_data:
            amplitudes = path_data['quantum_result']['path_amplitudes']

            magnitudes = [p['magnitude'] for p in amplitudes]
            phases = [p['phase'] for p in amplitudes]

            axes[0].scatter(magnitudes, phases, alpha=0.6, s=50)
            axes[0].set_xlabel('Amplitude Magnitude')
            axes[0].set_ylabel('Phase (radians)')
            axes[0].set_title('Path Amplitudes in Complex Plane')
            axes[0].grid(True, alpha=0.3)

        # Comparison
        categories = ['Classical\nSum', 'Quantum\nAmplitude']
        values = [
            path_data.get('classical_sum', 0),
            path_data.get('quantum_probability', 0)
        ]

        axes[1].bar(categories, values, color=['blue', 'red'], alpha=0.7)
        axes[1].set_ylabel('Total Probability')
        axes[1].set_title('Classical vs Quantum Path Integral')
        axes[1].grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.savefig(self.figure_dir / 'path_integral.png',
                       dpi=300, bbox_inches='tight')

        return fig

    def plot_entanglement(
        self,
        entanglement_results: Dict,
        save_path: Optional[str] = None
    ):
        """Visualize entanglement measurements"""
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        # Bell states entanglement
        bell_states = list(entanglement_results['bell_states'].keys())
        entropies = [
            entanglement_results['bell_states'][s]['entropy']
            for s in bell_states
        ]
        concurrences = [
            entanglement_results['bell_states'][s]['concurrence']
            for s in bell_states
        ]

        x = np.arange(len(bell_states))
        width = 0.35

        axes[0].bar(x - width/2, entropies, width, label='Entropy', alpha=0.7)
        axes[0].bar(x + width/2, concurrences, width, label='Concurrence', alpha=0.7)
        axes[0].set_xlabel('Bell State')
        axes[0].set_ylabel('Entanglement Measure')
        axes[0].set_title('Entanglement in Bell States')
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(bell_states)
        axes[0].legend()
        axes[0].grid(True, alpha=0.3, axis='y')

        # Product states (no entanglement)
        product_states = list(entanglement_results['product_states'].keys())
        product_entropies = [
            entanglement_results['product_states'][s]['entropy']
            for s in product_states
        ]

        axes[1].bar(product_states, product_entropies, alpha=0.7, color='gray')
        axes[1].set_xlabel('Product State')
        axes[1].set_ylabel('Entropy')
        axes[1].set_title('Product States (No Entanglement)')
        axes[1].axhline(y=0.01, color='r', linestyle='--', label='Near Zero')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.savefig(self.figure_dir / 'entanglement.png',
                       dpi=300, bbox_inches='tight')

        return fig

    def create_summary_figure(
        self,
        all_results: Dict,
        save_path: Optional[str] = None
    ):
        """Create comprehensive summary figure for paper"""
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

        # Top row: Uncertainty principle
        ax1 = fig.add_subplot(gs[0, :])
        temps = all_results['uncertainty_principle']['temperatures']
        products = all_results['uncertainty_principle']['products']
        ax1.plot(temps, products, 'o-', linewidth=3, markersize=8)
        ax1.axhline(y=0.5, color='r', linestyle='--', linewidth=2, label='ℏ/2 Bound')
        ax1.set_xlabel('Temperature', fontsize=12)
        ax1.set_ylabel('ΔH × ΔS', fontsize=12)
        ax1.set_title('Uncertainty Principle: ΔH × ΔS ≥ ℏ/2', fontsize=14, fontweight='bold')
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3)

        # Middle row: Wave collapse and paths
        ax2 = fig.add_subplot(gs[1, 0])
        ax2.text(0.5, 0.5, 'Wave Function\nCollapse', ha='center', va='center',
                fontsize=14, fontweight='bold')
        ax2.axis('off')

        ax3 = fig.add_subplot(gs[1, 1])
        ax3.text(0.5, 0.5, 'Path Integrals', ha='center', va='center',
                fontsize=14, fontweight='bold')
        ax3.axis('off')

        ax4 = fig.add_subplot(gs[1, 2])
        ax4.text(0.5, 0.5, 'Entanglement', ha='center', va='center',
                fontsize=14, fontweight='bold')
        ax4.axis('off')

        # Bottom row: Summary statistics
        ax5 = fig.add_subplot(gs[2, :])
        summary_text = self._generate_summary_text(all_results)
        ax5.text(0.1, 0.5, summary_text, fontsize=10, family='monospace',
                verticalalignment='center')
        ax5.axis('off')

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.savefig(self.figure_dir / 'summary.png',
                       dpi=300, bbox_inches='tight')

        return fig

    @staticmethod
    def _generate_summary_text(results: Dict) -> str:
        """Generate summary text for figure"""
        text = "EXPERIMENTAL RESULTS SUMMARY\n"
        text += "=" * 60 + "\n\n"

        if 'uncertainty_principle' in results:
            products = results['uncertainty_principle']['products']
            text += f"Uncertainty Principle:\n"
            text += f"  Min Product: {min(products):.4f}\n"
            text += f"  Bound Satisfied: {'✓' if min(products) >= 0.5 else '✗'}\n\n"

        if 'entanglement' in results:
            bell = results['entanglement']['bell_states']
            max_entropy = max(s['entropy'] for s in bell.values())
            text += f"Entanglement:\n"
            text += f"  Max Bell State Entropy: {max_entropy:.4f}\n"
            text += f"  Maximal Entanglement: {'✓' if max_entropy > 0.5 else '✗'}\n"

        return text
```

### Task 6.2: Report Generator
```python
# src/quantum_llm_sim/reporting/generator.py
from pathlib import Path
from typing import Dict
import json
from datetime import datetime

class ReportGenerator:
    """Generate experiment reports"""

    def __init__(self, output_dir: str = 'data/reports'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_html_report(
        self,
        results: Dict,
        title: str = "Quantum LLM Experiment Results"
    ) -> str:
        """Generate HTML report"""
        report_path = self.output_dir / f"report_{datetime.now():%Y%m%d_%H%M%S}.html"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .success {{ color: green; font-weight: bold; }}
        .failure {{ color: red; font-weight: bold; }}
        pre {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

    <h2>Experiment Overview</h2>
    {self._generate_overview_table(results)}

    <h2>Detailed Results</h2>
    {self._generate_detailed_sections(results)}

    <h2>Raw Data</h2>
    <pre>{json.dumps(results, indent=2)}</pre>
</body>
</html>
"""

        with open(report_path, 'w') as f:
            f.write(html)

        return str(report_path)

    def _generate_overview_table(self, results: Dict) -> str:
        """Generate overview table HTML"""
        html = "<table><tr><th>Experiment</th><th>Status</th><th>Key Result</th></tr>"

        for exp_name, exp_results in results.items():
            status = "✓ Pass" if self._check_experiment_pass(exp_results) else "✗ Fail"
            key_result = self._extract_key_result(exp_results)

            html += f"<tr><td>{exp_name}</td><td>{status}</td><td>{key_result}</td></tr>"

        html += "</table>"
        return html

    def _generate_detailed_sections(self, results: Dict) -> str:
        """Generate detailed sections HTML"""
        html = ""

        for exp_name, exp_results in results.items():
            html += f"<h3>{exp_name.replace('_', ' ').title()}</h3>"
            html += f"<pre>{json.dumps(exp_results, indent=2)}</pre>"

        return html

    @staticmethod
    def _check_experiment_pass(results: Dict) -> bool:
        """Check if experiment passed"""
        if 'bound_holds' in results:
            return results['bound_holds']
        return True

    @staticmethod
    def _extract_key_result(results: Dict) -> str:
        """Extract key result"""
        if 'min_product' in results:
            return f"Min ΔH×ΔS = {results['min_product']:.4f}"
        if 'entropy' in results:
            return f"Entropy = {results['entropy']:.4f}"
        return "See details"
```

---

## Definition of Done

- [ ] All visualization functions working
- [ ] High-resolution figures generated
- [ ] Interactive plots functional
- [ ] HTML reports generated
- [ ] All experiments visualized
- [ ] Publication-ready figures
- [ ] Code coverage > 80%

---

## Deliverables

1. QuantumLLMVisualizer class with all plot types
2. ReportGenerator for HTML/PDF reports
3. Complete figure set for both research papers
4. Interactive dashboard (optional)
5. Example gallery of all visualizations
6. Documentation on customizing plots
