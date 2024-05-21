To simplify other languages using the YAML device definition models, this directory contains a completely
flattened version of each definition without imports. Thus, if Adobe HIML style YAML config mechanism
does not exist in that language (Go, Rust, etc) the flatten YAML files can easily be used instead.

These are generated from files in library/ as .github/workflow hooks so they are always up-to-date with
the latest models that have been checked in.

See flatten-yaml-library tool
