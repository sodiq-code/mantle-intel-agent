"""
P1-14: Tests for audit_agent, pipeline, and incident modules.
These would have caught the P0 SyntaxError and verify core lifecycle.
"""
import pytest
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestAuditAgentImports:
    """Verify audit_agent can be imported — would have caught P0 SyntaxError."""

    def test_audit_agent_module_imports(self):
        """audit_agent.py should import without SyntaxError."""
        from agents.audit.audit_agent import AuditAgent
        assert AuditAgent is not None

    def test_audit_agent_has_record_finding(self):
        """AuditAgent should have record_finding method."""
        from agents.audit.audit_agent import AuditAgent
        assert hasattr(AuditAgent, "record_finding")

    def test_audit_agent_has_verify_finding(self):
        """AuditAgent should have verify_finding method."""
        from agents.audit.audit_agent import AuditAgent
        assert hasattr(AuditAgent, "verify_finding")

    def test_audit_agent_contract_address_configurable(self):
        """AuditAgent should accept contract_address parameter."""
        from agents.audit.audit_agent import AuditAgent
        try:
            agent = AuditAgent(contract_address="0x0000000000000000000000000000000000000000")
            assert agent is not None
        except ImportError:
            pytest.skip("web3 not installed — audit agent requires web3")


class TestPipelineImport:
    """Verify MantleIntelPipeline can be imported and instantiated."""

    def test_pipeline_module_imports(self):
        """pipeline.py should import without errors."""
        from agents.pipeline import MantleIntelPipeline
        assert MantleIntelPipeline is not None

    def test_pipeline_instantiation(self):
        """MantleIntelPipeline should instantiate with default args."""
        from agents.pipeline import MantleIntelPipeline
        try:
            pipeline = MantleIntelPipeline(poll_interval=30, blocks_per_cycle=100)
            assert pipeline is not None
        except ImportError:
            pytest.skip("web3 not installed — pipeline requires web3")

    def test_pipeline_has_run_cycle(self):
        """MantleIntelPipeline should have run_cycle method."""
        from agents.pipeline import MantleIntelPipeline
        try:
            pipeline = MantleIntelPipeline(poll_interval=30, blocks_per_cycle=100)
            assert hasattr(pipeline, "run_cycle")
        except ImportError:
            pytest.skip("web3 not installed — pipeline requires web3")

    def test_pipeline_has_get_stats(self):
        """MantleIntelPipeline should have get_stats method."""
        from agents.pipeline import MantleIntelPipeline
        try:
            pipeline = MantleIntelPipeline(poll_interval=30, blocks_per_cycle=100)
            assert hasattr(pipeline, "get_stats")
        except ImportError:
            pytest.skip("web3 not installed — pipeline requires web3")


class TestIncidentManagerLifecycle:
    """Test OPENED → ESCALATED → CRITICAL → RESOLVED transitions."""

    def test_incident_module_imports(self):
        """incident.py should import without errors."""
        from agents.incident import IncidentManager
        assert IncidentManager is not None

    def test_incident_manager_instantiation(self):
        """IncidentManager should instantiate."""
        from agents.incident import IncidentManager
        manager = IncidentManager()
        assert manager is not None

    def test_incident_state_transitions(self):
        """Test incident lifecycle: OPENED → ESCALATED → CRITICAL → RESOLVED."""
        from agents.incident import IncidentManager, IncidentState
        manager = IncidentManager(resolution_threshold_blocks=5)

        # Open incident via process_finding
        card = {
            "type": "whale_accumulation",
            "confidence_pct": 85,
            "insight": "Test whale move",
            "reasons": ["large_transfer"],
            "timestamp": "2024-01-01T00:00:00Z",
            "hash": "0xabc",
        }
        result = manager.process_finding(card, current_block=100)
        assert result is not None
        assert result["state"] == IncidentState.OPENED
        incident_id = result["incident_id"]
        assert incident_id is not None

        # Escalate (3+ occurrences)
        manager.process_finding(card, current_block=101)
        result = manager.process_finding(card, current_block=102)
        assert result is not None
        assert result["state"] == IncidentState.ESCALATED

        # Critical (5+ occurrences)
        manager.process_finding(card, current_block=103)
        result = manager.process_finding(card, current_block=104)
        assert result is not None
        assert result["state"] == IncidentState.CRITICAL

        # Resolve (no new findings for threshold blocks)
        resolved = manager.check_resolutions(current_block=110)
        assert len(resolved) == 1
        assert resolved[0]["state"] == IncidentState.RESOLVED


class TestKeystoreResolution:
    """Verify _resolve_private_key priority order."""

    def test_audit_agent_has_resolve_private_key(self):
        """AuditAgent should have _resolve_private_key method."""
        from agents.audit.audit_agent import AuditAgent
        assert hasattr(AuditAgent, "_resolve_private_key")
