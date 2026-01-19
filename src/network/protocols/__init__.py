"""
Protocol implementations package.

This package contains protocol-specific implementations of the
ProjectorProtocol interface. Each protocol module provides encoding,
decoding, and command building for its respective projector brand.

Implemented Protocols:
    - PJLinkProtocol: Standard PJLink Class 1 & 2 protocol (FULL)
    - HitachiProtocol: Hitachi native binary protocol (TCP 23/9715) (FULL)

Stub Protocols (Not Yet Implemented):
    - SonyProtocol: Sony ADCP protocol (TCP 53595)
    - BenQProtocol: BenQ text protocol (TCP 4352)
    - NECProtocol: NEC binary protocol (TCP 7142)
    - JVCProtocol: JVC D-ILA protocol (TCP 20554) - Note: Does NOT support PJLink

Example:
    from src.network.protocols import PJLinkProtocol
    from src.network.protocol_factory import ProtocolFactory, ProtocolType

    # Direct instantiation
    protocol = PJLinkProtocol(pjlink_class=2)

    # Via factory
    protocol = ProtocolFactory.create(ProtocolType.PJLINK, pjlink_class=2)

Author: Backend Infrastructure Developer
Version: 1.1.0
"""

from src.network.protocols.pjlink import PJLinkProtocol
from src.network.protocols.hitachi import HitachiProtocol
from src.network.protocols.sony import SonyProtocol
from src.network.protocols.benq import BenQProtocol
from src.network.protocols.nec import NECProtocol
from src.network.protocols.jvc import JVCProtocol

__all__ = [
    "PJLinkProtocol",
    "HitachiProtocol",
    "SonyProtocol",
    "BenQProtocol",
    "NECProtocol",
    "JVCProtocol",
]
