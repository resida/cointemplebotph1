# Coin Temple

## Requirements
- Python 2.7
- Virtualenv
- Google Cloud Engine SDK

## Installation
1. Create a virtualenv: `virutalenv environment`
2. Source the virtualenv: `source environment/bin/activate`
3. Install the requirements `pip install -r requirements.txt`


Install the Google Cloud SDK:
https://cloud.google.com/appengine/docs/standard/python/download. Ensure
that the `gcloud` and `dev_appserver.py` executables are within your
shell $PATH. The binaries are located in `google-cloud-sdk/bin`.

## Running Locally

### Running the GCE Application
1. `dev_appserver.py --enable sendmail yes app.yaml` from root
   directory where the root directory represents the root directory of
   this repository.

### Running the Flask Application

1. Navigate to `<root>/GCE`, where `<root>` represents the root of
   this repository.
2. Export the `FLASK_APP` shell variable with the value of
   `exchange_server.py`.
3. Execute `python -m flask run` from the `<root>/GCE` directory.

### Running the Test Scripts

1. Navigate to `<root>`
2. Source the virtualenv: `source environment/bin/activate`
3. Execute `python -m GCE.tests.test_x` where `test_x` is the module
   to execute

To make the example above more complete, an example of a test that can
be ran is. `python -m GCE.tests.test_get_balance`.
