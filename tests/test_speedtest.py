#!/usr/bin/env python3
# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
"""speedtest."""
# %%
from src.speedtest import __version__


def test_version() -> None:
    """Test version."""
    assert __version__ == "0.1.0"
