variable "google_credentials_file" {
    default = "account.json"
    description = "Service account key file, in JSON format"
}

variable "google_project" {
    default = "my-project-id"  # FIXME I have no clue what your projects are
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
    default = "sles-deploy-cap-byos"
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

    labels = merge({
        openqa_created_by = var.name
        # Error: Error creating instance: googleapi: Error 400: Invalid value for field 'resource.labels': ''. Label value '2020-07-31T19:20:20Z' violates format constraints. The value can only contain lowercase letters, numeric characters, underscores and dashes. The value can be at most 63 characters long. International characters are allowed., invalid
        # openqa_created_date = "${timestamp()}"
        openqa_created_id = "${element(random_id.service.*.hex, count.index)}"
        asmorodskyi = true
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
