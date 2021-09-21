#!/bin/bash
set -ex
set -o pipefail

# Runs the system tests, if no second argument is provided it runs all tests
# EX: run_system_tests.sh cluster-name helper,gpu
SCRIPT_SIGNATURE="run_system_tests.sh [TEST_CLUSTER_NAME: string]\
(optional) [TESTS_TO_RUN: comma seperated list of (helper, cluster, cpu, gpu)"

TEST_CLUSTER_NAME=$1
if [ "x" = "x$TEST_CLUSTER_NAME" ]; then
  echo -e "[ERROR]\\t CLUSTER_NAME missing! Please adhere to the following signature:\\n\\t $SCRIPT_SIGNATURE"
  exit 1
fi

shift
TESTS_TO_RUN=$1
if [ "x" = "x$TESTS_TO_RUN" ]; then
  TESTS_TO_RUN="all"
fi

CLI_NAME=sigopt
# Set working directory to be ci/artifacts and makes sure bin/$CLI_NAME gets used
FILE_FOLDER=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
ROOT="$FILE_FOLDER/../"
ARTIFACTS_FOLDER="$ROOT/ci/artifacts"
cd "$ARTIFACTS_FOLDER"

echo "Test cluster name: $TEST_CLUSTER_NAME"

function ecr-login() {
  PW=$( aws --region="${AWS_DEFAULT_REGION}" ecr get-login-password )
  docker login -u AWS --password "${PW}" "https://${AWS_ECR_URL}"
}

function test-helper-commands() {
  $CLI_NAME -h
  $CLI_NAME version
  (
    cd "$(mktemp -d)"
    $CLI_NAME init
  )
}

function test-optimize() {
  ecr-login
  # TODO(dan) confirm this loop works as expected
  local EXAMPLES=($@)
  for example in "${EXAMPLES[@]}"; do
    pushd "${example}"
    EXPERIMENT_LABEL=$($CLI_NAME optimize -s -e experiment.yml)
    popd
    echo "Created experiment: $EXPERIMENT_LABEL"

    $CLI_NAME cluster status "$EXPERIMENT_LABEL"
    while $CLI_NAME cluster status "$EXPERIMENT_LABEL" | grep -P "(Pending|Running)" ; do sleep 1 ; done

    sleep 30

    $CLI_NAME cluster stop "$EXPERIMENT_LABEL"
  done
}

function test-cluster-commands() {
  $CLI_NAME cluster test
  if $CLI_NAME cluster connect -n "$TEST_CLUSTER_NAME" --provider aws &>/dev/null; then
    echo "Cluster already connected, did not expect cluster connect to succeed!" >&2
  fi
  if $CLI_NAME cluster disconnect -n this-cluster-should-not-exist &>/dev/null; then
    echo "Disconnecting from a non-existent cluster succeeded!" >&2
    exit 1
  fi
  $CLI_NAME cluster disconnect -n "$TEST_CLUSTER_NAME"
  if $CLI_NAME cluster test &>/dev/null; then
    echo "Disconnecting from $TEST_CLUSTER_NAME failed (still connected)!" >&2
    exit 1
  fi
  if $CLI_NAME cluster connect -n this-cluster-should-not-exist --provider aws &>/dev/null; then
    echo "Connected to a non-existent cluster!" >&2
    exit 1
  fi
  $CLI_NAME cluster connect -n "$TEST_CLUSTER_NAME" --provider aws
  $CLI_NAME cluster test

  cat "$HOME/.sigopt/cluster/config-$TEST_CLUSTER_NAME" > kubeconfig.yml
  $CLI_NAME cluster disconnect --all

  $CLI_NAME cluster connect --kubeconfig kubeconfig.yml -n "not-$TEST_CLUSTER_NAME" --provider custom
  $CLI_NAME cluster test
  $CLI_NAME cluster disconnect -n "not-$TEST_CLUSTER_NAME"

  $CLI_NAME cluster connect -n "$TEST_CLUSTER_NAME" --provider aws
  $CLI_NAME cluster test
}

# $1 string to be searched for
# $2 csv to search in
function should-run-test(){
  local REGEX="(,?|^\\s*)$1"
  [[ $2 =~ $REGEX ]] || [ "$2" = "all" ]
}

CPU_EXAMPLES=(cpu-example)
GPU_EXAMPLES=(gpu-example)
EXAMPLES=()
if should-run-test "cpu" $TESTS_TO_RUN; then
  EXAMPLES+=("${CPU_EXAMPLES[@]}")
fi
if should-run-test "gpu" $TESTS_TO_RUN; then
  EXAMPLES+=("${GPU_EXAMPLES[@]}")
fi

# TESTS:
if should-run-test "helper" $TESTS_TO_RUN; then
  test-helper-commands
fi
if should-run-test "cluster" $TESTS_TO_RUN; then
  test-cluster-commands
fi
if [ ${#EXAMPLES[@]} -ne 0 ]; then
  test-optimize "${EXAMPLES[@]}"
fi
