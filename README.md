This repository contains the test infrastructure configuration of the Nanopublication ecosystem.

The `nanopub` directory contains separate subcharts for Query ( as `query`) and Registry ( as `registry`) instances. They can be deployed separately or as a part of the larger `nanopub` chart. If deployed as a part of the `nanopub` chart, both Query and Registry instances will be connected by default and can be configured to be deployed together on a separate node (through setting `global.nodeSelectorLabel` in the `nanopub/values.yaml` file). 

`general-query-service.yaml` and `general-registry-service.yaml` specify overarching services that will connect to all Query instances and all Registry instances in the cluster regardless of the release. The services use the default Kubernetes load balancer of your distribution.  

