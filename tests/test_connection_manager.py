# test_connection_manager.py
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
from unittest.mock import patch, MagicMock
from wireguard_tools import WireguardKey


from core.config.connection_config import ConnectionConfig, PeerConfig
from core.network.connection_manager import Connector


# Helper to create a dummy ConnectionConfig
def make_dummy_config():
    """Create a minimal valid ConnectionConfig for testing.
    
    Returns:
        ConnectionConfig: Test configuration with one peer, suitable for mocking tests.
    """
    peerkey = WireguardKey.generate()
    key = WireguardKey.generate()
    peer = PeerConfig(
        public_key=str(peerkey),
        endpoint_host="vpn.example.com",
        endpoint_port=51820,
        allowed_ips=["10.0.0.0/24"]
    )
    return ConnectionConfig(
        interface_name="wg0",
        private_key=str(key),
        address="10.0.0.2/24",
        peers=[peer]
    )


# Test Connector.connect
@patch("core.network.connection_manager.IPRoute")
@patch("core.network.connection_manager.WireguardDevice")
def test_connect(mock_wg_class, mock_iproute_class):
    """Test that Connector.connect() creates interface and applies configuration.
    
    Verifies that connect() performs all required netlink operations:
    - Creates WireGuard interface
    - Assigns IP address and prefix length
    - Brings interface up
    - Configures WireGuard settings (keys/peers)
    - Adds routing entries
    """
    # Setup mock for IPRoute context manager
    mock_iproute = MagicMock()
    mock_iproute_class.return_value.__enter__.return_value = mock_iproute
    # link_lookup returns a dummy interface index
    mock_iproute.link_lookup.return_value = [5]

    # Setup mock for WireguardDevice
    mock_device = MagicMock()
    mock_wg_class.get.return_value = mock_device

    config = make_dummy_config()
    connector = Connector(config)

    connector.connect()

    # --- Assertions ---
    # IPRoute calls
    mock_iproute.link.assert_any_call("add", ifname="wg0", kind="wireguard")
    mock_iproute.addr.assert_any_call("add", index=5, address="10.0.0.2", prefixlen=24)
    mock_iproute.link.assert_any_call("set", index=5, state="up")

    # WireguardDevice.set_config called once
    mock_device.set_config.assert_called_once()

    # Route addition must be verified
    mock_iproute.route.assert_any_call("add", dst="10.0.0.0/24", oif=5)


# Test Connector.disconnect
@patch("core.network.connection_manager.IPRoute")
def test_disconnect(mock_iproute_class):
    """Test that Connector.disconnect() removes the WireGuard interface.
    
    Verifies that disconnect() properly deletes the interface by its index.
    """
    mock_iproute = MagicMock()
    mock_iproute_class.return_value.__enter__.return_value = mock_iproute
    mock_iproute.link_lookup.return_value = [7]

    config = make_dummy_config()
    connector = Connector(config)

    connector.disconnect()

    mock_iproute.link.assert_called_once_with("del", index=7)


# Test Connector.status when interface is up
@patch("core.network.connection_manager.WireguardDevice")
def test_status_up(mock_wg_class):
    """Test that Connector.status() returns correct data when interface is up.
    
    Verifies that status() retrieves peer count, configuration, and up status
    from the active WireGuard interface.
    """
    mock_device = MagicMock()
    mock_device.get_config.return_value.asdict.return_value = {"dummy": "cfg"}
    mock_device.get_config.return_value.peers = [1, 2]

    mock_wg_class.get.return_value = mock_device

    config = make_dummy_config()
    connector = Connector(config)

    status = connector.status()
    assert status["up"] is True
    assert status["peers"] == 2
    assert status["config"] == {"dummy": "cfg"}


# Test Connector.status when interface is down
@patch("core.network.connection_manager.WireguardDevice")
def test_status_down(mock_wg_class):
    """Test that Connector.status() handles missing interface gracefully.
    
    Verifies that status() returns {"up": False} when the WireGuard device
    is not found or raises an exception.
    """
    # simulate FileNotFoundError when trying to get device (interface not found)
    mock_wg_class.get.side_effect = FileNotFoundError("Device not found")

    config = make_dummy_config()
    connector = Connector(config)

    status = connector.status()
    assert status["up"] is False
