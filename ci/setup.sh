#!/bin/bash
set -e
set -o pipefail

# Sets up everything required for integration testing into the ci/artifacts folder
SCRIPT_SIGNATURE='setup.sh [CLUSTER_NAME: string]'

CLUSTER_NAME=$1
if [ "x" = "x$CLUSTER_NAME" ]; then
  echo -e "[ERROR] CLUSTER_NAME missing! Please adhere to the following signature:\\n $SCRIPT_SIGNATURE"
  exit 1
fi

set -ex

# Normalizes the file paths so this script can be excecuted from anywhere.
FILE_FOLDER=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
CLUSTERS_FOLDER="$FILE_FOLDER/clusters"
ARTIFACTS_FOLDER="$FILE_FOLDER/artifacts"

mkdir -p "$ARTIFACTS_FOLDER"

for MODEL in cpu-example gpu-example; do
  cp -r "${FILE_FOLDER}/models/${MODEL}" "${ARTIFACTS_FOLDER}/${MODEL}"
done

for CLUSTER_XPU_TYPE in cpu gpu; do
  sed "s/{{CLUSTER_NAME}}/$CLUSTER_NAME/" "$CLUSTERS_FOLDER/${CLUSTER_XPU_TYPE}_test_cluster.yml" > "$ARTIFACTS_FOLDER/${CLUSTER_XPU_TYPE}_test_cluster.yml"
  echo "kubernetes_version: '$KUBERNETES_VERSION'" >> "$ARTIFACTS_FOLDER/${CLUSTER_XPU_TYPE}_test_cluster.yml"
done
