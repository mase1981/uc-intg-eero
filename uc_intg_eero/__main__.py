"""
Entry point for running the integration as a module.

This allows running: python -m uc_intg_eero

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
from uc_intg_eero import main

if __name__ == "__main__":
    asyncio.run(main())
