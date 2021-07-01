CLI_NAME = 'sigopt'
CONTROLLER_IMAGE_VERSION = "2021-05-05"
CONTROLLER_REPOSITORY = "orchestrate/controller"
DEFAULT_CONTROLLER_IMAGE = f"{CONTROLLER_REPOSITORY}:{CONTROLLER_IMAGE_VERSION}"
CONTROLLER_IMAGE_URL = (
  f"https://public.sigopt.com/orchestrate/controller/releases/{CONTROLLER_IMAGE_VERSION}/controller.tar"
)
