# search01-private-endpoints architecture notes

```text
Local laptop
  -> Azure VPN Client (AAD/OpenVPN)
  -> P2S tunnel (172.16.201.0/24)
  -> vnet-search01
     - GatewaySubnet: VPN gateway (VpnGw1)
     - snet-dns: Ubuntu DNS forwarder VM (dnsmasq)
     - snet-pe: private endpoints for Storage blob + Search service

Private DNS zones (linked to VNet)
  - privatelink.blob.core.windows.net
  - privatelink.search.windows.net

Search shared private link resource
  Search -> Storage(blob) (approved in notebook 03)
```

## DNS flow

1. Laptop query goes to VPN profile custom DNS (`DNS_FORWARDER_PRIVATE_IP`).
2. DNS forwarder VM forwards to Azure DNS `168.63.129.16`.
3. Azure private DNS zones resolve service FQDNs to private endpoint IPs.
4. Notebook and SDK traffic stays private through VPN + private endpoints.

## RBAC

- Deployer principal:
  - Storage Blob Data Contributor (storage scope)
  - Search Service Contributor (search scope)
  - Search Index Data Contributor (search scope)
- Search managed identity:
  - Storage Blob Data Reader (storage scope)
