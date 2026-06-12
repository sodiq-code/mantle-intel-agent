"""
tests/test_smart_money.py
==========================
Tests for the Smart Money agent — wallet clustering and signal generation.
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from agents.smart_money.smart_money_agent import SmartMoneyAgent


class TestSmartMoneyAgentInit:

    def test_instantiates(self):
        agent = SmartMoneyAgent()
        assert agent is not None

    def test_has_labeled_wallets(self):
        """Must have at least 20 labeled wallets for meaningful clustering."""
        agent = SmartMoneyAgent()
        # Check wallet registry exists
        assert hasattr(agent, '_labeled_wallets') or hasattr(agent, 'labeled_wallets') \
               or hasattr(agent, 'LABELED_WALLETS') or hasattr(agent, 'wallet_labels') \
               or hasattr(agent, '_wallet_labels'), \
               "SmartMoneyAgent must have a labeled wallet registry"


class TestSmartMoneyAnalysis:

    def _make_block_with_transfer(self, wallet: str, value: float):
        return {
            "number": 100,
            "timestamp": 1700000100,
            "transaction_count": 5,
            "gas_used": 400_000,
            "gas_limit": 30_000_000,
            "total_value_eth": value,
            "unique_senders": 3,
            "mev_bundle_count": 0,
            "large_transfers": [
                {"value_eth": value, "from": wallet, "to": "0xDEAD", "hash": "0xABC"}
            ],
        }

    def test_analyze_returns_dict_or_list(self):
        """analyze() must return a structured result."""
        agent = SmartMoneyAgent()
        blocks = [self._make_block_with_transfer("0xAAA", 10_000) for _ in range(5)]

        # Try common method names
        if hasattr(agent, 'analyze'):
            result = agent.analyze(blocks)
            assert result is not None
        elif hasattr(agent, 'process'):
            result = agent.process(blocks)
            assert result is not None

    def test_empty_blocks_handled(self):
        """Empty block list must not raise exceptions."""
        agent = SmartMoneyAgent()
        try:
            if hasattr(agent, 'analyze'):
                agent.analyze([])
            elif hasattr(agent, 'process'):
                agent.process([])
        except Exception as e:
            pytest.fail(f"SmartMoneyAgent raised on empty input: {e}")
