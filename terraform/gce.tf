variable "google_credentials_file" {
    default = "account.json"
    description = "Service account key file, in JSON format"
}

variable "google_project" {
    default = "suse-sle-qa"
    description = "GCP project to run VM in"
}

variable "google_region" {
    default = "europe-west3-b"
    description = "Region to run VM in; see https://cloud.google.com/compute/docs/regions-zones#available"
}

variable "name" {
    default = "openqa-gce"
    description = "base name for VM (will be appended with a random string and counter)"
}

variable "type" {
    default = "e2-highcpu-2"
    description = "Machine type to start VM as; see https://cloud.google.com/compute/docs/machine-types"
}

variable "instance_count" {
    default = 1
    type = number
}

variable "image_family" {
    default = "cap-deploy-testing"
    description = "Image family; for finding current image without explicit version"
}

variable "tags" {
    type = map(string)
    default = {}
}

provider "google" {
    credentials = file(var.google_credentials_file)
    project = var.google_project
    region = var.google_region
}

resource "random_id" "service" {
    count = var.instance_count
    keepers = {
        name = var.name
    }
    byte_length = 8
}

data "google_compute_image" "vm_image" {
    project = var.google_project
    family = var.image_family
}

resource "google_compute_instance" "openqa-vm" {
    name = "${var.name}-${element(random_id.service.*.hex, count.index)}"
    machine_type = var.type
    zone = var.google_region
    count = var.instance_count

    boot_disk {
        initialize_params {
            image = data.google_compute_image.vm_image.self_link
        }
    }

    network_interface {
        network = "default"

        access_config {
            // Ephemeral IP
        }
    }

    tags = ["http-server"]

    metadata = merge({
            openqa_created_by = "blue-horizon"
            openqa_created_date = "${timestamp()}"
            openqa_created_id = "${element(random_id.service.*.hex, count.index)}"
        }, var.tags)
}

output "vm_name" {
    value = google_compute_instance.openqa-vm[*].name
}

output "instance_id" {
    value = google_compute_instance.openqa-vm[*].instance_id
}

output "public_ip" {
    value = google_compute_instance.openqa-vm[*].network_interface.0.access_config.0.nat_ip
}
