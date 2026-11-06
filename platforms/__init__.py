"""
Platform contest fetchers for Codeforces and AtCoder.
"""

from .codeforces import fetch_codeforces_contests
from .atcoder import fetch_atcoder_contests

__all__ = ["fetch_codeforces_contests", "fetch_atcoder_contests"]
