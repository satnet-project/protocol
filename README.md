[![Circle CI](https://circleci.com/gh/satnet-project/protocol.svg?style=shield)](https://circleci.com/gh/satnet-project/protocol)
[![Build Status](https://travis-ci.org/satnet-project/protocol.svg)](https://travis-ci.org/satnet-project/protocol)
[![Coverage Status](https://coveralls.io/repos/satnet-project/protocol/badge.svg?branch=jrpc_if&service=github)](https://coveralls.io/github/satnet-project/protocol?branch=jrpc_if)
[![Code Health](https://landscape.io/github/satnet-project/protocol/jrpc_if/landscape.svg?style=flat)](https://landscape.io/github/satnet-project/protocol/jrpc_if)

### Protocol communications for the SATNet project

This repository contains the communications real time protocol based on Twisted for the SatNet network.

#### Installation

Steps to install the generic client for the SATNet network:

1. To install the dependencies run, from the Scripts folder:

`./setup.sh -install`

You will need root privileges.

2. To uninstall the dependencies and the satnet daemon run:

`./setup.sh -uninstall`

#### Dependencies

Before starting the script should be activate the corresponding virtualenv to satisfy the required dependencies.

```source .venv/bin/activate```

#### Normal operation

Installation script will create a daemon which, in every system start, will execute SATNet protocol. This process is transparent for the user.

This daemon creates a serie of logs that reports the operation. They are located at `/logs` folder, which can be found at the main folder.
