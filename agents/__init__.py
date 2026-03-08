"""Agents package — organized by functional category.

Import agents from their respective subpackages:
- agents.data
- agents.analysis  
- agents.reasoning
- agents.reporting
"""

# Expose subpackages for easy access
from agents import data
from agents import analysis
from agents import reasoning
from agents import reporting

__all__ = [
    "data",
    "analysis",
    "reasoning",
    "reporting",
]
