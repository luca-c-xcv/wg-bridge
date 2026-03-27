# connection_config.py
#
# Copyright (C) 2026  MoonyFringers
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.


from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PeerConfig:
    """Configuration for a WireGuard peer node.
    
    Attributes:
        public_key: The peer's public WireGuard key.
        endpoint_host: Hostname or IP address of the peer's WireGuard endpoint.
        endpoint_port: UDP port number of the peer's WireGuard service.
        allowed_ips: List of CIDR subnets allowed to route through this peer.
        preshared_key: Optional pre-shared key for additional security layer.
        persistent_keepalive: Seconds between keepalive packets (0 disables). Default: 25.
    """
    public_key: str
    endpoint_host: str
    endpoint_port: int
    allowed_ips: list[str]
    preshared_key: Optional[str] = None
    persistent_keepalive: int = 25


@dataclass
class ConnectionConfig:
    """Configuration for a WireGuard connection/interface.
    
    Attributes:
        interface_name: Name of the WireGuard interface (e.g., 'wg0').
        private_key: The local WireGuard private key.
        address: IP address and CIDR prefix for the interface (e.g., '10.0.0.2/24').
        dns: Optional DNS server(s) to configure for this interface.
        peers: List of PeerConfig objects representing connected peers.
        otp_token: Reserved for future authentication enhancement. Not currently used.
        pre_up_hook: Reserved for future lifecycle hook. Not currently used.
        post_up_hook: Reserved for future lifecycle hook. Not currently used.
    """
    interface_name: str
    private_key: str
    address: str
    dns: Optional[str] = None
    peers: list[PeerConfig] = field(default_factory=list)
    otp_token: Optional[str] = None  # TODO: implement authentication hook
    pre_up_hook: Optional[str] = None  # TODO: implement pre-connection lifecycle
    post_up_hook: Optional[str] = None  # TODO: implement post-connection lifecycle

