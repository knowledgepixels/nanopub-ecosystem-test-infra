#!/bin/bash

replicas=$1

ts=$(date +%s)
logfile="/tmp/nanopub-log-$ts"
logfiledb="$logfile-registry-db"
logfilequery="$logfile-query"
logfileregistry="$logfile-registry-application"

for i in $(seq 1 $replicas); do
    logfiledb_now="$logfiledb-$i.log"
    kubectl logs -f "nanopub-$i-registry-db-0" > $logfiledb_now 2>&1 &
    pid=$!
    echo "kubectl logs running as PID $pid"
    logfilequery_now="$logfilequery-$i.log"
    kubectl logs -f "nanopub-$i-query-application-0" > $logfilequery_now 2>&1 &
    pid=$!
    echo "kubectl logs running as PID $pid"
    logfileregistry_now="$logfileregistry-$i.log"
    kubectl logs -f "nanopub-$i-registry-application-0" > $logfileregistry_now 2>&1 &
    pid=$!
    echo "kubectl logs running as PID $pid"
done