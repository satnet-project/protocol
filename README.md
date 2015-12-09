[![Circle CI](https://circleci.com/gh/satnet-project/protocol.svg?style=shield)](https://circleci.com/gh/satnet-project/protocol)
[![Build Status](https://travis-ci.org/satnet-project/protocol.svg)](https://travis-ci.org/satnet-project/protocol)
[![Coverage Status](https://coveralls.io/repos/satnet-project/protocol/badge.svg?branch=jrpc_if&service=github)](https://coveralls.io/github/satnet-project/protocol?branch=jrpc_if)
[![Code Health](https://landscape.io/github/satnet-project/protocol/master/landscape.svg?style=flat)](https://landscape.io/github/satnet-project/protocol/master)

### Protocol communications for SATNet project.

This repository contains the communications real time protocol based on Twisted for the SatNet network.

#### Installation

Steps to install the generic client for the SATNet network:

1. To install the dependencies run, from the Scripts folder:

`./setup.sh`

You will need root privileges.

#### Dependencies

Before starting the script should be activate the corresponding virtualenv to satisfy the required dependencies.

```source .venv/bin/activate```

#### Normal operation

To run the procotol communications you must execute: 

```python server_amp.py```
