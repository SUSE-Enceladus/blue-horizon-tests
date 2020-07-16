variable "region" {
    default = "eu-central-1"
}

provider "aws" {
    region = var.region
}

variable "instance_count" {
    default = "1"
}

variable "name" {
    default = "openqa-eks"
}

variable "type" {
    default = "t2.large"
}

variable "image_id" {
    default = ""
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

resource "aws_key_pair" "openqa-keypair" {
    key_name   = "openqa-${element(random_id.service.*.hex, 0)}"
    public_key = file("${var.ssh_file}")
}

resource "aws_security_group" "basic_sg" {
    name        = "openqa-${element(random_id.service.*.hex, 0)}"

    ingress {
        from_port   = 22
        to_port     = 22
        protocol    = "tcp"
        cidr_blocks     = ["0.0.0.0/0"]
    }

    ingress {
        from_port   = 80
        to_port     = 80
        protocol    = "tcp"
        cidr_blocks     = ["0.0.0.0/0"]
    }

    egress {
        from_port       = 0
        to_port         = 0
        protocol        = "-1"
        cidr_blocks     = ["0.0.0.0/0"]
    }

    tags = merge({
            openqa_created_by = var.name
            openqa_created_date = "${timestamp()}"
            openqa_created_id = "${element(random_id.service.*.hex, 0)}"
        }, var.tags)
}

resource "aws_instance" "openqa" {
    count           = var.instance_count
    ami             = var.image_id
    instance_type   = var.type
    key_name        = aws_key_pair.openqa-keypair.key_name
    security_groups = ["${aws_security_group.basic_sg.name}"]

    tags = merge({
            openqa_created_by = var.name
            openqa_created_date = "${timestamp()}"
            openqa_created_id = "${element(random_id.service.*.hex, count.index)}"
        }, var.tags)
}

output "public_ip" {
    value = "${aws_instance.openqa.*.public_ip}"
}

output "vm_name" {
    value = "${aws_instance.openqa.*.id}"
}
