provider "azurerm" {
   version = "<= 1.33"
}

variable "instance_count" {
    default = "1"
}

variable "name" {
    default = "openqa-aks-vm"
}

variable "type" {
    default = "Standard_B1ms"
}

variable "region" {
    default = "westeurope"
}

variable "tags" {
    type = map(string)
    default = {}
}

variable "ssh_file" {
    default="/root/.ssh/id_rsa.pub"
}

resource "random_id" "service" {
    count = var.instance_count
    keepers = {
        name = var.name
    }
    byte_length = 8
}


resource "azurerm_resource_group" "openqa-group" {
    name     = "${var.name}-${element(random_id.service.*.hex, 0)}"
    location = var.region

    tags = merge({
            openqa_created_by = var.name
            openqa_created_date = "${timestamp()}"
            openqa_created_id = "${element(random_id.service.*.hex, 0)}"
        }, var.tags)
}

resource "azurerm_virtual_network" "openqa-network" {
    name                = "${azurerm_resource_group.openqa-group.name}-vnet"
    address_space       = ["10.0.0.0/16"]
    location            = var.region
    resource_group_name = azurerm_resource_group.openqa-group.name
}

resource "azurerm_subnet" "openqa-subnet" {
    name                 = "${azurerm_resource_group.openqa-group.name}-subnet"
    resource_group_name  = azurerm_resource_group.openqa-group.name
    virtual_network_name = azurerm_virtual_network.openqa-network.name
    address_prefix       = "10.0.1.0/24"
}

resource "azurerm_public_ip" "openqa-publicip" {
    name                         = "${var.name}-${element(random_id.service.*.hex, count.index)}-public-ip"
    location                     = var.region
    resource_group_name          = azurerm_resource_group.openqa-group.name
    allocation_method            = "Dynamic"
    count                        = var.instance_count
}

resource "azurerm_network_security_group" "openqa-nsg" {
    name                = "${azurerm_resource_group.openqa-group.name}-nsg"
    location            = var.region
    resource_group_name = azurerm_resource_group.openqa-group.name

    security_rule {
        name                       = "SSH"
        priority                   = 1001
        direction                  = "Inbound"
        access                     = "Allow"
        protocol                   = "Tcp"
        source_port_range          = "*"
        destination_port_range     = "22"
        source_address_prefix      = "*"
        destination_address_prefix = "*"
    }

    security_rule {
        name                       = "Port80"
        priority                   = 1002
        direction                  = "Inbound"
        access                     = "Allow"
        protocol                   = "Tcp"
        source_port_range          = "*"
        destination_port_range     = "80"
        source_address_prefix      = "*"
        destination_address_prefix = "*"
    }
}

resource "azurerm_network_interface" "openqa-nic" {
    name                      = "${var.name}-${element(random_id.service.*.hex, count.index)}-nic"
    location                  = var.region
    resource_group_name       = azurerm_resource_group.openqa-group.name
    network_security_group_id = azurerm_network_security_group.openqa-nsg.id
    count                     = var.instance_count

    ip_configuration {
        name                          = "${element(random_id.service.*.hex, count.index)}-nic-config"
        subnet_id                     = azurerm_subnet.openqa-subnet.id
        private_ip_address_allocation = "dynamic"
        public_ip_address_id          = element(azurerm_public_ip.openqa-publicip.*.id, count.index)
    }
}

resource "azurerm_dns_zone" "openqa-dns-zone" {
  name                = "openqa.com"
  resource_group_name = azurerm_resource_group.openqa-group.name
}

resource "azurerm_virtual_machine" "openqa-vm" {
    name                  = "${var.name}-${element(random_id.service.*.hex, count.index)}"
    location              = var.region
    resource_group_name   = azurerm_resource_group.openqa-group.name
    network_interface_ids = ["${azurerm_network_interface.openqa-nic[count.index].id}"]
    vm_size               = var.type
    count                 = var.instance_count

    storage_image_reference {
        publisher = "SUSE"
        offer     = "cap-deploy-byos"
        sku       = "gen1"
        version   = "latest"
    }

    storage_os_disk {
        name              = "${var.name}-${element(random_id.service.*.hex, count.index)}-osdisk"
        caching           = "ReadWrite"
        create_option     = "FromImage"
        managed_disk_type = "Standard_LRS"
    }

    os_profile {
        computer_name  = "${var.name}-${element(random_id.service.*.hex, count.index)}"
        admin_username = "azureuser"
    }

    os_profile_linux_config {
        disable_password_authentication = true
        ssh_keys {
            path     = "/home/azureuser/.ssh/authorized_keys"
            key_data = file("${var.ssh_file}")
        }
    }

    tags = merge({
            openqa_created_by = var.name
            openqa_created_date = "${timestamp()}"
            openqa_created_id = "${element(random_id.service.*.hex, count.index)}"
            asmorodskyi=true
        }, var.tags)
}

output "vm_name" {
    value = "${azurerm_virtual_machine.openqa-vm.*.name}"
}

data "azurerm_public_ip" "openqa-publicip" {
    name                = "${azurerm_public_ip.openqa-publicip[count.index].name}"
    resource_group_name = "${azurerm_virtual_machine.openqa-vm.0.resource_group_name}"
    count               = var.instance_count
}

output "public_ip" {
    value = "${data.azurerm_public_ip.openqa-publicip.*.ip_address}"
}
