#!/bin/bash

# 2025-09-26 최종 확인 (jmx_prometheus_javaagent-1.4.0.jar)
declare -a package_urls=(
  "https://github.com/prometheus/jmx_exporter/releases/download/1.4.0/jmx_prometheus_javaagent-1.4.0.jar"
)


declare -a packages=()

for url in "${package_urls[@]}"; do
    filename=$(basename "$url")
    packages+=("$filename")
done

for (( i=0; i<${#package_urls[@]}; i++ )); do
    if [ -f "${packages[$i]}" ]; then
        echo "${packages[$i]} ... existed"
    else
        wget "${package_urls[$i]}" -O "${packages[$i]}"
    fi
done
