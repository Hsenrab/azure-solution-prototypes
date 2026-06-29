# search01-private-endpoints

## Problem statement

Recreate the AOAI_Labs `04_AzureSearchDataSource` workflow (blob data source → index → indexer → keyword query) while Azure AI Search and Blob Storage stay private-only from day one.

## Hypothesis

A Point-to-Site VPN (AAD auth) and a DNS forwarder VM can enable local notebook-driven indexing over private endpoints only, using managed identity/AAD and no keys.

## Scope

- In scope:
  - Search + Storage with `publicNetworkAccess: Disabled`
  - Search `disableLocalAuth: true`; Storage `allowSharedKeyAccess: false`
  - P2S OpenVPN with AAD auth and DNS forwarder VM
  - Search shared private link to Blob with explicit approval step
  - NASA earth book PDFs, one index/indexer, simple keyword query
- Out of scope:
  - Vectorization, skillsets, semantic ranking customization
  - Multi-region/DR, production hardening, public ingress patterns

## Notebook journey

| Notebook | What it does |
|---|---|
| `00_setup.ipynb` | Create venv/kernel, check VPN app consent prerequisite, authenticate Azure, install dependencies |
| `01_deploy_infra.ipynb` | Deploy Bicep and write deployment outputs to `env/.env` |
| `02_connect_vpn.ipynb` | Generate/import Azure VPN Client profile, set custom DNS, verify private DNS resolution |
| `03_configure.ipynb` | Approve shared private link connection, download NASA PDFs, upload with Blob SDK + AAD |
| `04_search.ipynb` | Create data source/index/indexer via AAD clients and run keyword query (`argentina`) |
| `X_destroy.ipynb` | Standard destroy/purge notebook copied from speech01 |

## P2S VPN prerequisites

- `VpnGw1` gateway provisioning commonly takes **30-45 minutes**.
- Tenant admin must grant one-time consent for Azure VPN Client app ID `c632b3df-fb67-4d84-bdcf-b95ad541b5c8`.
- Azure VPN Client requires Windows 10 build 17763+ (or macOS Azure VPN Client app).
- Imported VPN profile must use custom DNS = deployed `DNS_FORWARDER_PRIVATE_IP`.

## Known limitations

- Single-VNet feasibility setup only.
- VPN client-side steps are manual and required before notebooks 03/04.
- Search SKU is Standard to support shared private link.
