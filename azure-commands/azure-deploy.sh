#!/bin/bash
# aqui se van a quedar lo comandos de creacin de recursos azure para una posible automatizacion futura de los levntamientos en produccion

# creacion del recurso de azure container registry ACR

az acr create \
    --resource-group TestingNP \
    --name azsmartacr \
    --sku Basic \
    --location eastus \
    # para el SKU en basic no funcionan los siguientes comandos tener en cuenta para futuras actualizaciones
    # --public-network-enabled false \
    # --zone-redundancy Disabled

# creacion del recurso de azure kubernetes services AKS

az aks create \
    --resource-group TestingNP \
    --name azsmart-k8s \
    --location eastus \
    --kubernetes-version 1.23.12 \
    --node-vm-size Standard_B4ms \
    --node-count 1 \
    --network-plugin azure \
    --network-policy azure \
    --attach-acr azsmartacr \
    --generate-ssh-keys

az storage account create \
    --name azsmartblob \
    --resource-group TestingNP \
    --location eastus \
    --sku Standard_LRS \
    --min-tls-version TLS1_2 \
    --access-tier Hot


az network public-ip create \
    -n myPublicIp \
    --resource-group TestingNP \
    --allocation-method Static \
    --sku Standard

az network vnet create \
    -n myVnet \
    --resource-group TestingNP \
    --address-prefix 10.0.0.0/16 \
    --subnet-name mySubnet \
    --subnet-prefix 10.0.0.0/24

az network application-gateway create \
    -n myApplicationGateway \
    -l eastus \
    --resource-group TestingNP \
    --sku Standard_v2 \
    --public-ip-address myPublicIp \
    --vnet-name myVnet \
    --subnet mySubnet \
    --priority 1

appgwId=$(az network application-gateway show -n myApplicationGateway --resource-group TestingNP -o tsv --query "id")

az aks enable-addons \
    -n azsmart-k8s \
    --resource-group TestingNP \
    -a ingress-appgw \
    --appgw-id $appgwId

nodeResourceGroup=$(az aks show -n azsmart-k8s -g TestingNP -o tsv --query "nodeResourceGroup")

aksVnetName=$(az network vnet list -g $nodeResourceGroup -o tsv --query "[0].name")

aksVnetId=$(az network vnet show -n $aksVnetName -g $nodeResourceGroup -o tsv --query "id")

az network vnet peering create \
    -n AppGWtoAKSVnetPeering \
    --resource-group TestingNP \
    --vnet-name myVnet \
    --remote-vnet $aksVnetId \
    --allow-vnet-access

appGWVnetId=$(az network vnet show -n myVnet -g TestingNP -o tsv --query "id")

az network vnet peering create \
    -n AKStoAppGWVnetPeering \
    -g $nodeResourceGroup \
    --vnet-name $aksVnetName \
    --remote-vnet $appGWVnetId \
    --allow-vnet-access

az aks update \
    --name azsmart-k8s \
    --resource-group TestingNP \
    --attach-acr azsmartacr
