"""
Unit tests for protocol type normalization.

Tests the ProtocolType.normalize_protocol_type() method which handles
corrupted or display-formatted protocol type strings.

Author: Test Engineer
Version: 1.0.0
"""

import pytest
from src.network.base_protocol import ProtocolType


class TestProtocolTypeNormalization:
    """Test protocol type normalization logic."""

    def test_normalize_exact_match(self):
        """Exact match should return as-is."""
        assert ProtocolType.normalize_protocol_type("pjlink") == "pjlink"
        assert ProtocolType.normalize_protocol_type("hitachi") == "hitachi"
        assert ProtocolType.normalize_protocol_type("sony") == "sony"
        assert ProtocolType.normalize_protocol_type("benq") == "benq"
        assert ProtocolType.normalize_protocol_type("nec") == "nec"
        assert ProtocolType.normalize_protocol_type("jvc") == "jvc"

    def test_normalize_display_name_class1(self):
        """'PJLink Class 1' should normalize to 'pjlink'."""
        assert ProtocolType.normalize_protocol_type("PJLink Class 1") == "pjlink"

    def test_normalize_display_name_class2(self):
        """'PJLink Class 2' should normalize to 'pjlink'."""
        assert ProtocolType.normalize_protocol_type("PJLink Class 2") == "pjlink"

    def test_normalize_case_insensitive(self):
        """Case variations should normalize correctly."""
        assert ProtocolType.normalize_protocol_type("PJLINK") == "pjlink"
        assert ProtocolType.normalize_protocol_type("PJLink") == "pjlink"
        assert ProtocolType.normalize_protocol_type("Hitachi") == "hitachi"
        assert ProtocolType.normalize_protocol_type("SONY") == "sony"
        assert ProtocolType.normalize_protocol_type("BenQ") == "benq"

    def test_normalize_hitachi_display(self):
        """'Hitachi (Native Protocol)' should normalize to 'hitachi'."""
        assert ProtocolType.normalize_protocol_type("Hitachi (Native Protocol)") == "hitachi"

    def test_normalize_sony_display(self):
        """'Sony ADCP' should normalize to 'sony'."""
        assert ProtocolType.normalize_protocol_type("Sony ADCP") == "sony"

    def test_normalize_jvc_display(self):
        """'JVC D-ILA' should normalize to 'jvc'."""
        assert ProtocolType.normalize_protocol_type("JVC D-ILA") == "jvc"
        assert ProtocolType.normalize_protocol_type("JVC") == "jvc"

    def test_normalize_empty_returns_default(self):
        """Empty string should return default 'pjlink'."""
        assert ProtocolType.normalize_protocol_type("") == "pjlink"

    def test_normalize_none_returns_default(self):
        """None should return default 'pjlink'."""
        assert ProtocolType.normalize_protocol_type(None) == "pjlink"

    def test_normalize_whitespace_stripped(self):
        """Whitespace should be stripped before normalization."""
        assert ProtocolType.normalize_protocol_type("  pjlink  ") == "pjlink"
        assert ProtocolType.normalize_protocol_type("\tpjlink\n") == "pjlink"

    def test_normalize_invalid_raises(self):
        """Invalid protocol type should raise ValueError."""
        with pytest.raises(ValueError, match="Cannot normalize protocol type"):
            ProtocolType.normalize_protocol_type("InvalidProtocol")

    def test_normalize_invalid_has_helpful_message(self):
        """ValueError should include valid protocol types."""
        with pytest.raises(ValueError, match="Valid types: pjlink"):
            ProtocolType.normalize_protocol_type("BadProtocol")

    def test_normalize_all_valid_types(self):
        """All valid enum types should normalize correctly."""
        for proto_type in ProtocolType:
            result = ProtocolType.normalize_protocol_type(proto_type.value)
            assert result == proto_type.value, f"Failed to normalize {proto_type.value}"

    def test_normalize_idempotent(self):
        """Normalizing an already normalized value should return the same value."""
        test_values = ["pjlink", "hitachi", "sony", "benq", "nec", "jvc"]
        for value in test_values:
            normalized_once = ProtocolType.normalize_protocol_type(value)
            normalized_twice = ProtocolType.normalize_protocol_type(normalized_once)
            assert normalized_once == normalized_twice, f"Normalization not idempotent for {value}"

    def test_normalize_real_world_corrupted_values(self):
        """Test real-world corrupted values from SQL Server bug."""
        # The actual bug case
        assert ProtocolType.normalize_protocol_type("PJLink Class 1") == "pjlink"

        # Potential variations
        assert ProtocolType.normalize_protocol_type("pjlink class 1") == "pjlink"
        assert ProtocolType.normalize_protocol_type("pjlink class 2") == "pjlink"
        assert ProtocolType.normalize_protocol_type("PJLink") == "pjlink"
