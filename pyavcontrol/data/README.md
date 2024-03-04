
### Why configuration language?

Basically PyAVControl is about defining configuration (definitions) for how devices interfaces are defined. Implementing the API definitions directly into a specific language does not achieve the ability for reuse of those definitions across multiple languages/clients. Initially using JSON and YAML was explored as the easiest way to define these interfaces (especially in a way that non-developers could create their own definitions which was often a request from users in example libraries like pyxantech, pymonoprice, pyanthem-serial, etc).

However, the sheer volume of models and slightly different definitions evolved into needing some sort of import/include/replacement mechanism. While this can be implemented (for the thousandth time) overtop of JSON/YAML, this doesn't make sense since existing configuration language exists that already have implementations in many languages AND this isn't really the point of PyAVControl to define new languages.

Exploring configuration languages that provided basic support for imports/includes, variables, and a few other features without evolving into a Turing complete language just makes sense. Further, if those languages enable generating a library or repository of these configuration files flattened into raw JSON or YAML, this is a huge bonus since new clients in other languages could use the flattened definitions instead of having to implement the config language if a library didn't already exist.

This indicates that there should be a build pipeline that converts the definition (config) files into flattened variations as part of the check-in or repository workflow. This provides a nice balance in sufficinet flexibility in defining the interfaces, while keeping the dependencies and simplicity of interacting with common file formats optimized for multiple languages and clients.

### Requirements/Goals

* minimize the amount of config required to define interfaces to devices
* enable reuse across device models by sharing large portions of the definitions
* enable non-developers to use an easy to read/understand format for contributing their own equipment definitions
* support access to the intrefaces via JSON by clients (no need to implement complex config parsing for new languages IF it is acceptable to tradeoff "compiling" the definitions down into a large repository of JSON files)
* separate the definition from the runtime dependency
* schema/limited type checking

#### Config Languages Considered

* [RCL](https://github.com/ruuda/rcl): see [more](https://ruudvanasseldonk.com/2024/a-reasonable-configuration-language), tooling support might be weak (e.g. VSCode extensions, etc)
* [PKL](https://github.com/apple/pkl): no Python implementation yet (2024-03)
* [Nix])(https://nixos.wiki/wiki/Overview_of_the_Nix_Language): to specialized to package management
* [Nickel](https://github.com/tweag/nickel): evolution of Nix
* [HCL](https://github.com/hashicorp/hcl): primarily targeted towards devops/infrastructure config
* [CUE](https://cuelang.org/)
* Dhall

And of course raw formats, which was the initial implementation, but quickly abandoned due to the sheer volume of files and duplicate config needed to support minute differences between a vast array of physical device features:

* JSON: most compatible and frequently used for data interfaces
* YAML: more readable than json, with some limited support for references
* TOML

Neither JSON or YAML solve the issues of reuse across configuration files, composition, etc.
Decided on RCL as it was most inline with json, could export the equipment definition files to json
files as part of the build process to make integration into other languages easy where RCL
libraries may not be available.

### Why RCL?

#### See Also

* https://news.ycombinator.com/item?id=39250320
* https://ruudvanasseldonk.com/2024/a-reasonable-configuration-language


