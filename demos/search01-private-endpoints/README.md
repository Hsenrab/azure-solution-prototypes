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
- **Redeploy-safe once the VM exists.** `01_deploy_infra.ipynb` checks whether `vm-search01-dns` already exists and passes `deployVm=false` to the Bicep template on redeploy so the VM is skipped entirely — Azure treats `osProfile.customData` and `linuxConfiguration.ssh.publicKeys` as immutable on single VMs ([Microsoft Learn](https://learn.microsoft.com/en-us/azure/virtual-machines/custom-data#can-i-update-custom-data-after-the-vm-has-been-created)), so re-PUTting the VM fails with `PropertyChangeNotAllowed`. The SSH public key is persisted to `env/dns_vm_key.pub` and reused across runs. Search / Storage / VPN gateway all reconcile normally, so iterating on the rest of the stack doesn't force the 30-45 min VPN gateway redeploy.
- VPN client-side steps are manual and required before notebooks 03/04.
- Search SKU is Standard to support shared private link.
- **Region capacity varies by subscription.** `northeurope` is the default but any AZ-capable region with capacity for `VpnGw1AZ` + Standard AI Search + `Standard_B1s` works. If the default deployment fails with `ResourcesForSkuUnavailable` or similar, run `python scripts/check_region_capacity.py` to probe candidates and set `LOCATION` in `01_deploy_infra.ipynb` to the first region that comes back green.
- **DNS forwarder VM is a sidecar, not part of the demo surface.** It exists only so VPN clients can resolve `*.privatelink.*` FQDNs to private endpoint IPs. The VM has a public IP for operational visibility, but the attached NSG only permits inbound DNS (UDP/TCP 53) from the VPN client pool — SSH and all other inbound traffic from the internet are blocked by the implicit `DenyAllInBound` rule. The admin SSH key is persisted locally to `env/dns_vm_key.pub` (public key only; not a secret) and never used for ingress — the VM is intentionally not reachable for shell access.
- **NASA PDF download uses the unauthenticated GitHub contents API** (60 requests/hour limit per source IP). If your network shares an IP behind NAT and you hit the rate limit, the request will return a 403 JSON object instead of a list and the upload cell will fail with a `TypeError`. Wait an hour or set `GITHUB_TOKEN` and add an `Authorization: Bearer` header to the request if you need to retry.

## Future improvements / TODO

_None tracked. See git history for previously addressed items._
