# example-policy.hcl
path "secret/data/*" {
    capabilities = ["create", "read", "update", "delete", "list"]
}

path "secret/metadata/*" {
    capabilities = ["create", "read", "update", "delete", "list"]
}
