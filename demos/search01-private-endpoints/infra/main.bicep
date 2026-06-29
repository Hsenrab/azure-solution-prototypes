@description('Azure region for all resources')
param location string = 'eastus2'

@description('Demo ID used for naming')
param demoId string = 'search01-private-endpoints'

@description('AAD tenant ID for VPN auth settings')
param tenantId string

@description('Object ID of signed-in deployer for RBAC assignments')
param deployerPrincipalId string

@description('P2S VPN client address pool')
param vpnClientAddressPool string = '172.16.201.0/24'

@description('VNet CIDR')
param vnetAddressPrefix string = '10.50.0.0/16'

@description('Private endpoint subnet CIDR')
param privateEndpointSubnetPrefix string = '10.50.1.0/24'

@description('DNS forwarder subnet CIDR')
param dnsSubnetPrefix string = '10.50.2.0/24'

@description('Gateway subnet CIDR')
param gatewaySubnetPrefix string = '10.50.255.0/27'

@description('SSH public key for DNS VM admin account')
param adminPublicKey string = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCtdaFMV58WOhoND+sYs4saGP9IYkO/g11xGKL/99qIm88MODhNi4O4Lx3BZPX7ntnjm/MyqfPKozt2GUpfvR8lZ84FxcUwFTKPwsc6oY+G7dmL7bbE7etRQqWR5CUTV0e7J3auG1yDG1u5LEaKlXOWRLBh5NVA2DhHSLXBBu4yWtb5sfGNk1CNXzwJGsooJZWOw/E60qeAaslAq3PysRA8fG7w6bmVvY5HnBMwyr+tLHYOaXAKBu5l0/6oWUPzP2bqgq1ngqrLpxdUdVLI41LEf1Od7JQz4SSK3YiRWAmwmRL8JBlf10L/e9PoFpaVA1fUL/serzIqU6doQlWFR2hh demo@search01'

var uniqueSuffix = take(uniqueString(subscription().id, resourceGroup().id), 5)
var normalizedDemoId = toLower(replace(demoId, '-', ''))
var storageAccountName = take('st${normalizedDemoId}${uniqueSuffix}', 24)
var searchServiceName = take('srch-${normalizedDemoId}-${uniqueSuffix}', 60)
var vnetName = 'vnet-search01'
var vnetGatewayName = 'vpngw-search01'
var containerName = 'nasa'

var storageBlobDataReaderRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1')
var storageBlobDataContributorRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
var searchServiceContributorRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7ca78c08-252a-4471-8644-bb5ff32d4ba0')
var searchIndexDataContributorRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8ebe5a00-799e-43f5-93ac-243d3dce84a7')

resource vnet 'Microsoft.Network/virtualNetworks@2023-11-01' = {
  name: vnetName
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: [
        vnetAddressPrefix
      ]
    }
    subnets: [
      {
        name: 'snet-pe'
        properties: {
          addressPrefix: privateEndpointSubnetPrefix
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
      {
        name: 'snet-dns'
        properties: {
          addressPrefix: dnsSubnetPrefix
        }
      }
      {
        name: 'GatewaySubnet'
        properties: {
          addressPrefix: gatewaySubnetPrefix
        }
      }
    ]
  }
}

resource vpnPublicIp 'Microsoft.Network/publicIPAddresses@2023-11-01' = {
  name: 'pip-search01-vpngw'
  location: location
  sku: {
    name: 'Standard'
  }
  properties: {
    publicIPAllocationMethod: 'Static'
  }
}

resource vnetGateway 'Microsoft.Network/virtualNetworkGateways@2023-11-01' = {
  name: vnetGatewayName
  location: location
  properties: {
    enableBgp: false
    gatewayType: 'Vpn'
    vpnType: 'RouteBased'
    sku: {
      name: 'VpnGw1'
      tier: 'VpnGw1'
    }
    ipConfigurations: [
      {
        name: 'gw-ipconfig'
        properties: {
          privateIPAllocationMethod: 'Dynamic'
          publicIPAddress: {
            id: vpnPublicIp.id
          }
          subnet: {
            id: resourceId('Microsoft.Network/virtualNetworks/subnets', vnet.name, 'GatewaySubnet')
          }
        }
      }
    ]
    vpnClientConfiguration: {
      vpnAuthenticationTypes: [
        'AAD'
      ]
      vpnClientAddressPool: {
        addressPrefixes: [
          vpnClientAddressPool
        ]
      }
      vpnClientProtocols: [
        'OpenVPN'
      ]
      aadTenant: 'https://login.microsoftonline.com/${tenantId}/'
      aadAudience: 'c632b3df-fb67-4d84-bdcf-b95ad541b5c8'
      aadIssuer: 'https://sts.windows.net/${tenantId}/'
    }
  }
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    defaultToOAuthAuthentication: true
    minimumTlsVersion: 'TLS1_2'
    publicNetworkAccess: 'Disabled'
    supportsHttpsTrafficOnly: true
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  name: 'default'
  parent: storage
}

resource nasaContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: containerName
  parent: blobService
  properties: {
    publicAccess: 'None'
  }
}

resource search 'Microsoft.Search/searchServices@2023-11-01' = {
  name: searchServiceName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'standard'
  }
  properties: {
    disableLocalAuth: true
    publicNetworkAccess: 'disabled'
    semanticSearch: 'free'
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
  }
}

resource blobPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.blob.core.windows.net'
  location: 'global'
}

resource searchPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.search.windows.net'
  location: 'global'
}

resource blobPrivateDnsZoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: blobPrivateDnsZone
  name: 'link-vnet-search01'
  location: 'global'
  properties: {
    virtualNetwork: {
      id: vnet.id
    }
    registrationEnabled: false
  }
}

resource searchPrivateDnsZoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: searchPrivateDnsZone
  name: 'link-vnet-search01'
  location: 'global'
  properties: {
    virtualNetwork: {
      id: vnet.id
    }
    registrationEnabled: false
  }
}

resource storagePrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: 'pe-${storageAccountName}-blob'
  location: location
  properties: {
    subnet: {
      id: resourceId('Microsoft.Network/virtualNetworks/subnets', vnet.name, 'snet-pe')
    }
    privateLinkServiceConnections: [
      {
        name: 'storage-blob-connection'
        properties: {
          privateLinkServiceId: storage.id
          groupIds: [
            'blob'
          ]
        }
      }
    ]
  }
}

resource storagePrivateEndpointDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = {
  parent: storagePrivateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'blob-zone-config'
        properties: {
          privateDnsZoneId: blobPrivateDnsZone.id
        }
      }
    ]
  }
}

resource searchPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: 'pe-${searchServiceName}-search'
  location: location
  properties: {
    subnet: {
      id: resourceId('Microsoft.Network/virtualNetworks/subnets', vnet.name, 'snet-pe')
    }
    privateLinkServiceConnections: [
      {
        name: 'search-service-connection'
        properties: {
          privateLinkServiceId: search.id
          groupIds: [
            'searchService'
          ]
        }
      }
    ]
  }
}

resource searchPrivateEndpointDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = {
  parent: searchPrivateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'search-zone-config'
        properties: {
          privateDnsZoneId: searchPrivateDnsZone.id
        }
      }
    ]
  }
}

resource searchSharedPrivateLink 'Microsoft.Search/searchServices/sharedPrivateLinkResources@2023-11-01' = {
  name: 'storage-blob-splr'
  parent: search
  properties: {
    privateLinkResourceId: storage.id
    groupId: 'blob'
    requestMessage: 'Allow Search managed identity blob access over shared private link for this demo.'
  }
}

resource dnsNsg 'Microsoft.Network/networkSecurityGroups@2023-11-01' = {
  name: 'nsg-search01-dns'
  location: location
  properties: {
    securityRules: [
      {
        name: 'allow-dns-udp-from-vpn-pool'
        properties: {
          access: 'Allow'
          direction: 'Inbound'
          priority: 100
          protocol: 'Udp'
          sourceAddressPrefix: vpnClientAddressPool
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '53'
        }
      }
      {
        name: 'allow-dns-tcp-from-vpn-pool'
        properties: {
          access: 'Allow'
          direction: 'Inbound'
          priority: 110
          protocol: 'Tcp'
          sourceAddressPrefix: vpnClientAddressPool
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '53'
        }
      }
    ]
  }
}

resource dnsPublicIp 'Microsoft.Network/publicIPAddresses@2023-11-01' = {
  name: 'pip-search01-dns'
  location: location
  sku: {
    name: 'Standard'
  }
  properties: {
    publicIPAllocationMethod: 'Static'
  }
}

resource dnsNic 'Microsoft.Network/networkInterfaces@2023-11-01' = {
  name: 'nic-search01-dns'
  location: location
  properties: {
    networkSecurityGroup: {
      id: dnsNsg.id
    }
    ipConfigurations: [
      {
        name: 'ipconfig1'
        properties: {
          privateIPAllocationMethod: 'Dynamic'
          subnet: {
            id: resourceId('Microsoft.Network/virtualNetworks/subnets', vnet.name, 'snet-dns')
          }
          publicIPAddress: {
            id: dnsPublicIp.id
          }
        }
      }
    ]
  }
}

resource dnsForwarderVm 'Microsoft.Compute/virtualMachines@2023-09-01' = {
  name: 'vm-search01-dns'
  location: location
  properties: {
    hardwareProfile: {
      vmSize: 'Standard_B2s'
    }
    osProfile: {
      computerName: 'vm-search01-dns'
      adminUsername: 'azureuser'
      customData: base64('''#cloud-config
package_update: true
packages:
  - dnsmasq
write_files:
  - path: /etc/dnsmasq.d/azure-forwarder.conf
    permissions: "0644"
    content: |
      no-resolv
      server=168.63.129.16
      bind-interfaces
      listen-address=0.0.0.0
runcmd:
  - systemctl enable dnsmasq
  - systemctl restart dnsmasq
''')
      linuxConfiguration: {
        disablePasswordAuthentication: true
        ssh: {
          publicKeys: [
            {
              path: '/home/azureuser/.ssh/authorized_keys'
              keyData: adminPublicKey
            }
          ]
        }
      }
    }
    storageProfile: {
      imageReference: {
        publisher: 'Canonical'
        offer: '0001-com-ubuntu-server-jammy'
        sku: '22_04-lts-gen2'
        version: 'latest'
      }
      osDisk: {
        createOption: 'FromImage'
        managedDisk: {
          storageAccountType: 'Standard_LRS'
        }
      }
    }
    networkProfile: {
      networkInterfaces: [
        {
          id: dnsNic.id
          properties: {
            primary: true
          }
        }
      ]
    }
  }
}

resource deployerStorageBlobDataContributorRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, deployerPrincipalId, 'StorageBlobDataContributor')
  scope: storage
  properties: {
    principalId: deployerPrincipalId
    roleDefinitionId: storageBlobDataContributorRoleDefinitionId
    principalType: 'User'
  }
}

resource deployerSearchServiceContributorRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(search.id, deployerPrincipalId, 'SearchServiceContributor')
  scope: search
  properties: {
    principalId: deployerPrincipalId
    roleDefinitionId: searchServiceContributorRoleDefinitionId
    principalType: 'User'
  }
}

resource deployerSearchIndexDataContributorRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(search.id, deployerPrincipalId, 'SearchIndexDataContributor')
  scope: search
  properties: {
    principalId: deployerPrincipalId
    roleDefinitionId: searchIndexDataContributorRoleDefinitionId
    principalType: 'User'
  }
}

resource searchStorageBlobDataReaderRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, search.id, 'StorageBlobDataReader')
  scope: storage
  properties: {
    principalId: search.identity.principalId
    roleDefinitionId: storageBlobDataReaderRoleDefinitionId
    principalType: 'ServicePrincipal'
  }
}

output storageAccountName string = storage.name
output containerName string = nasaContainer.name
output storageAccountResourceId string = storage.id
output searchServiceName string = search.name
output searchEndpoint string = 'https://${search.name}.search.windows.net'
output searchResourceId string = search.id
output vnetGatewayName string = vnetGateway.name
output dnsForwarderPrivateIp string = reference(dnsNic.id, '2023-11-01').ipConfigurations[0].properties.privateIPAddress
output vnetId string = vnet.id
output snetPePrefix string = privateEndpointSubnetPrefix
output vpnClientAddressPool string = vpnClientAddressPool
output resourceGroupName string = resourceGroup().name
output tenantId string = tenantId
