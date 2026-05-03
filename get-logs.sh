#!/bin/bash

replicas=$1

ts=$(date +%s)
logfile="/tmp/nanopub-log-$ts"
logfiledb="$logfile-registry-db"
logfilequery="$logfile-query"
logfilerdf4j="$logfile-rdf4j"
logfileregistry="$logfile-registry-application"
pidfile="$logfile-pid"

for i in $(seq 1 $replicas); do
    logfiledb_now="$logfiledb-$i.log"
    nohup kubectl logs -f "nanopub-$i-registry-db-0" > $logfiledb_now 2>&1 < /dev/null &
    pid=$!
    echo "$pid" >> "$pidfile"
    echo "kubectl logs running as PID $pid"
    logfilequery_now="$logfilequery-$i.log"
    nohup kubectl logs -f "nanopub-$i-query-application-0" > $logfilequery_now 2>&1 < /dev/null &
    pid=$!
    echo "kubectl logs running as PID $pid"
    echo "$pid" >> "$pidfile"
    logfilerdf4j_now="$logfilerdf4j-$i.log"
    nohup kubectl logs -f "nanopub-$i-query-rdf4j-0" > $logfilerdf4j_now 2>&1 < /dev/null &
    pid=$!
    echo "kubectl logs running as PID $pid"
    echo "$pid" >> "$pidfile"
    logfileregistry_now="$logfileregistry-$i.log"
    nohup kubectl logs -f "nanopub-$i-registry-application-0" > $logfileregistry_now 2>&1 < /dev/null &
    pid=$!
    echo "kubectl logs running as PID $pid"
    echo "$pid" >> "$pidfile"
done

# then run xargs -r kill < "$pidfile"
# to kill processes 