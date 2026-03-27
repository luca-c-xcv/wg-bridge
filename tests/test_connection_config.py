# test_connection_config.py
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

import pytest
from core.config.connection_config import PeerConfig, ConnectionConfig

def test_peer_config_defaults():
    """Test PeerConfig initialization with default values.
    
    Verifies that preshared_key defaults to None and persistent_keepalive
    defaults to 25 seconds.
    """
    peer = PeerConfig(
        public_key="pubkey123",
        endpoint_host="vpn.example.com",
        endpoint_port=51820,
        allowed_ips=["0.0.0.0/0"],
    )

    assert peer.public_key == "pubkey123"
    assert peer.endpoint_host == "vpn.example.com"
    assert peer.endpoint_port == 51820
    assert peer.allowed_ips == ["0.0.0.0/0"]
    assert peer.preshared_key is None
    assert peer.persistent_keepalive == 25

def test_peer_config_custom_values():
    """Test PeerConfig initialization with custom values.
    
    Verifies that custom preshared_key and persistent_keepalive values are
    properly assigned and override defaults.
    """
    peer = PeerConfig(
        public_key="pubkey123",
        endpoint_host="vpn.example.com",
        endpoint_port=51820,
        allowed_ips=["10.0.0.0/24"],
        preshared_key="psk123",
        persistent_keepalive=10,
    )

    assert peer.preshared_key == "psk123"
    assert peer.persistent_keepalive == 10

def test_connection_config_minimal():
    """Test ConnectionConfig with only required fields.
    
    Verifies that optional fields (dns, peers, otp_token, hooks) default to
    None or empty list as appropriate.
    """
    conn = ConnectionConfig(
        interface_name="wg0",
        private_key="privkey123",
        address="10.0.0.2/24",
    )

    assert conn.interface_name == "wg0"
    assert conn.private_key == "privkey123"
    assert conn.address == "10.0.0.2/24"
    assert conn.dns is None
    assert conn.peers == []
    assert conn.otp_token is None
    assert conn.pre_up_hook is None
    assert conn.post_up_hook is None

def test_connection_config_with_peer():
    """Test ConnectionConfig with peer configuration.
    
    Verifies that peers can be properly added and retrieved from
    a ConnectionConfig instance.
    """
    peer = PeerConfig(
        public_key="peerkey",
        endpoint_host="vpn.example.com",
        endpoint_port=51820,
        allowed_ips=["0.0.0.0/0"],
    )

    conn = ConnectionConfig(
        interface_name="wg0",
        private_key="privkey",
        address="10.0.0.2/24",
        peers=[peer],
    )

    assert len(conn.peers) == 1
    assert conn.peers[0] == peer

def test_default_peers_list_is_not_shared():
    """Test that each ConnectionConfig instance has its own peers list.
    
    Verifies that the default_factory=list prevents sharing a single mutable
    list across multiple instances, which would be a common Python gotcha.
    """
    conn1 = ConnectionConfig(
        interface_name="wg0",
        private_key="key1",
        address="10.0.0.1/24",
    )

    conn2 = ConnectionConfig(
        interface_name="wg1",
        private_key="key2",
        address="10.0.1.1/24",
    )

    conn1.peers.append(
        PeerConfig(
            public_key="peerkey",
            endpoint_host="vpn.example.com",
            endpoint_port=51820,
            allowed_ips=["0.0.0.0/0"],
        )
    )

    assert len(conn1.peers) == 1
    assert len(conn2.peers) == 0
