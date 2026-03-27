# connection_manager.py #
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

from wireguard_tools import WireguardConfig, WireguardDevice
from core.config.connection_config import ConnectionConfig
from pyroute2 import IPRoute
from pyroute2.netlink.exceptions import NetlinkError


class Connector:
    """Manages WireGuard interface lifecycle and configuration.
    
    Handles creating, configuring, and monitoring WireGuard interfaces using
    netlink UAPI and pyroute2. Supports both setup (connect) and teardown
    (disconnect) operations.
    
    Attributes:
        config: ConnectionConfig instance containing interface and peer settings.
    """
    def __init__(self, config: ConnectionConfig):
        """Initialize connector with WireGuard connection configuration.
        
        Args:
            config: ConnectionConfig containing interface name, keys, address, and peers.
        """
        self.config = config

    def connect(self) -> None:
        """Establish WireGuard interface and configure all settings.
        
        Performs the following steps:
        1. Create WireGuard interface (netlink)
        2. Assign IP address to interface
        3. Bring interface up
        4. Apply WireGuard configuration (private key and peers)
        5. Add routes for each peer's allowed IPs
        
        Raises:
            Exception: If interface creation or configuration fails.
        """
        iface = self.config.interface_name
        try:
            with IPRoute() as ipr:
                # 1. Create the WireGuard interface
                ipr.link("add", ifname=iface, kind="wireguard")
                idx = ipr.link_lookup(ifname=iface)[0]

                # 2. Assign IP address
                ipr.addr(
                    "add",
                    index=idx,
                    address=self._parse_ip(),
                    prefixlen=self._parse_prefix(),
                )

                # 3. Bring interface up
                ipr.link("set", index=idx, state="up")

                # 4. Apply WireGuard config (keys, peers) via Netlink UAPI
                wg_cfg = self._build_wg_config()
                device = WireguardDevice.get(iface)
                device.set_config(wg_cfg)

                # 5. Add routes for each peer's allowed_ips
                for peer in self.config.peers:
                    for allowed_ip in peer.allowed_ips:
                        ipr.route("add", dst=allowed_ip, oif=idx)
        except Exception:
            # Clean up half-configured interface on any failure
            self.disconnect()
            raise

    def disconnect(self) -> None:
        """Remove WireGuard interface and associated routes.
        
        Safely tears down the interface if it exists. Does not raise an error
        if the interface is already down.
        """
        with IPRoute() as ipr:
            idx = ipr.link_lookup(ifname=self.config.interface_name)
            if idx:
                ipr.link("del", index=idx[0])

    def status(self) -> dict:
        """Query current status of the WireGuard interface.
        
        Returns:
            dict: Status information containing:
                - 'up': bool indicating if interface is active
                - 'peers': int count of connected peers (if up)
                - 'config': dict of current WireGuard configuration (if up)
        """
        try:
            device = WireguardDevice.get(self.config.interface_name)
            cfg = device.get_config()
            return {"up": True, "peers": len(cfg.peers), "config": cfg.asdict()}
        except (FileNotFoundError, KeyError, NetlinkError):
            return {"up": False}

    def _build_wg_config(self) -> WireguardConfig:
        """Build WireGuardConfig object from connection configuration.
        
        Converts internal ConnectionConfig to WireGuardConfig format required
        by the wireguard_tools library, preparing peer data and private key.
        
        Returns:
            WireguardConfig: Configuration object ready for device.set_config()
        """
        peers = []
        for p in self.config.peers:
            peer_dict = {
                "public_key": p.public_key,
                "endpoint_host": p.endpoint_host,
                "endpoint_port": p.endpoint_port,
                "allowed_ips": p.allowed_ips,
                "persistent_keepalive": p.persistent_keepalive,
            }
            # Only include preshared_key if it is not None
            if p.preshared_key is not None:
                peer_dict["preshared_key"] = p.preshared_key
            peers.append(peer_dict)
        return WireguardConfig.from_dict({
            "private_key": self.config.private_key,
            "peers": peers,
        })

    def _parse_ip(self) -> str:
        """Extract IP address from CIDR address string.
        
        Returns:
            str: IPv4 or IPv6 address portion (before '/')
        """
        return self.config.address.split("/")[0]

    def _parse_prefix(self) -> int:
        """Extract network prefix length from CIDR address string.
        
        Returns:
            int: Prefix length as integer (after '/')
        """
        return int(self.config.address.split("/")[1])
