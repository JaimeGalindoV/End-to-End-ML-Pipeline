variable "aws_profile" {
    description = "Perfil de AWS a usar"
    type = string
    default = null
}

variable "aws_region" {
    description = "Región de AWS para desplegar los recursos"
    type = string 
    default = "us-east-1"
    
}