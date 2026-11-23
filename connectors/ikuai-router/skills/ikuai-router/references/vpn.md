---
name: ikuai-vpn
description: iKuai VPN — PPTP, L2TP, OpenVPN, IKEv2, IPSec, WireGuard server config, client CRUD, tunnels and peers.
---

# VPN

## PPTP / L2TP

```bash
# 服务配置
ikuai-cli vpn pptp get --format json
ikuai-cli vpn pptp set --enabled no --format json

# 客户端 CRUD
ikuai-cli vpn pptp clients --format json
ikuai-cli vpn pptp clients --key name --pattern pptpoffice --format json
ikuai-cli vpn pptp client-create --name pptpoffice --server "vpn.example.com" --username user1 --password "<example-password>" --interface auto --enabled no --format json
ikuai-cli vpn pptp client-get <ID> --format json
ikuai-cli vpn pptp client-update <ID> --server "vpn2.example.com" --format json
ikuai-cli vpn pptp client-toggle <ID> --enabled no --format json
ikuai-cli vpn pptp client-delete <ID> --yes --format json
ikuai-cli vpn pptp kick <ID> --yes --format json
```

L2TP 命令同理：`vpn l2tp get/set/clients/client-create/client-get/client-update/client-toggle/client-delete/kick`。PPTP/L2TP clients 支持 `--key/--pattern` 模糊搜索；L2TP 客户端 name 需以 `l2tp` 开头。

## OpenVPN

```bash
ikuai-cli vpn openvpn get --format json
ikuai-cli vpn openvpn set --enabled no --format json
ikuai-cli vpn openvpn clients --format json
ikuai-cli vpn openvpn clients --key name --pattern ovpnoffice --format json
ikuai-cli vpn openvpn client-create --name ovpnoffice --remote-addr "vpn.example.com" --username user1 --password "<example-password>" --ca "<CA证书>" --interface auto --enabled no --format json
ikuai-cli vpn openvpn client-get <ID> --format json
ikuai-cli vpn openvpn client-update <ID> --comment "updated" --format json
ikuai-cli vpn openvpn client-toggle <ID> --enabled no --format json
ikuai-cli vpn openvpn client-delete <ID> --yes --format json
ikuai-cli vpn openvpn kick <ID> --yes --format json
```

`--ca` 必须传真实 CA 证书内容。

## IKEv2

```bash
ikuai-cli vpn ikev2 get --format json
ikuai-cli vpn ikev2 set --enabled no --format json
ikuai-cli vpn ikev2 clients --format json
ikuai-cli vpn ikev2 clients --key name --pattern ikedoffice --format json
ikuai-cli vpn ikev2 client-create --name ikedoffice --remote-addr "vpn.example.com" --interface auto --left-id "localid" --username user1 --password "<example-password>" --enabled no --format json
ikuai-cli vpn ikev2 client-get <ID> --format json
ikuai-cli vpn ikev2 client-update <ID> --comment "updated" --format json
ikuai-cli vpn ikev2 client-toggle <ID> --enabled no --format json
ikuai-cli vpn ikev2 client-delete <ID> --yes --format json
ikuai-cli vpn ikev2 kick <ID> --yes --format json
```

name 需以 `iked` 开头，authby=mschapv2 时 username 必填。

## IPSec

```bash
ikuai-cli vpn ipsec clients --format json
ikuai-cli vpn ipsec clients --key name --pattern ipsecsite --format json
ikuai-cli vpn ipsec client-create --name ipsecsite --remote-addr "10.0.0.1" --interface wan1 --left-subnet "192.168.1.0/24" --right-subnet "192.168.2.0/24" --secret "<example-psk>" --enabled no --format json
ikuai-cli vpn ipsec client-get <ID> --format json
ikuai-cli vpn ipsec client-update <ID> --comment "updated" --format json
ikuai-cli vpn ipsec client-toggle <ID> --enabled no --format json
ikuai-cli vpn ipsec client-delete <ID> --yes --format json
ikuai-cli vpn ipsec kick <ID> --yes --format json
# defaults: keyexchange=ikev2, authby=secret, dpdaction=none, ikelifetime=3, lifetime=1
```

## WireGuard

```bash
# 隧道
ikuai-cli vpn wireguard list --format json
ikuai-cli vpn wireguard list --key name --pattern wgsite --format json
ikuai-cli vpn wireguard create --name wgsite --address "10.9.0.1/24" --interface auto --private-key "<base64>" --public-key "<base64>" --enabled no --format json
# defaults: interface=auto, port=5000, mtu=1420
ikuai-cli vpn wireguard get <ID> --format json
ikuai-cli vpn wireguard update <ID> --interface auto --port 5001 --format json
ikuai-cli vpn wireguard toggle <ID> --enabled no --format json
ikuai-cli vpn wireguard delete <ID> --yes --format json

# 对端
ikuai-cli vpn wireguard peers <TUNNEL_ID> --format json
ikuai-cli vpn wireguard peers <TUNNEL_ID> --key interface --pattern wgsite --format json
ikuai-cli vpn wireguard peer-create <TUNNEL_ID> --public-key "<base64>" --allow-ips "10.9.0.2/32" --interface wgsite --enabled no --format json
ikuai-cli vpn wireguard peer-get <TUNNEL_ID> <PEER_ID> --format json
ikuai-cli vpn wireguard peer-update <TUNNEL_ID> <PEER_ID> --interface wgsite --comment "updated" --format json
ikuai-cli vpn wireguard peer-toggle <TUNNEL_ID> <PEER_ID> --enabled no --format json
ikuai-cli vpn wireguard peer-delete <TUNNEL_ID> <PEER_ID> --yes --format json
```
