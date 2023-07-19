###############################################################################
# SHETRAN Run - executes the simulation part of SHETRAN
# Ben Smith, Robin Wardle
# October 2022
###############################################################################

###############################################################################
# Python libraries
###############################################################################
import subprocess
import shutil
from glob import glob
import os
import sys
import datetime
import logging
import pathlib


###############################################################################
# Constants
###############################################################################
SHETRAN_RUN_FILENAME = "success"
SHETRAN_RUN_LOG_FILENAME = "read-ea.log"
METADATA_FILENAME = "metadata.json"

###############################################################################
# Paths
###############################################################################
data_path = os.getenv('DATA_PATH', '/data')

input_path = os.path.join(data_path, 'inputs')
output_path = os.path.join(data_path, 'outputs')

# Remove existing outputs and recreate output_path folder (useful locally):
if os.path.exists(output_path):
    shutil.rmtree(output_path)
#os.mkdir(output_path)

#run_path = os.path.join(output_path, 'shetran')
run_path = output_path
shutil.copytree(input_path, run_path)


###############################################################################
# Logging
###############################################################################
# Configure logging
logging.basicConfig()
logging.root.setLevel(logging.INFO)

# Logging instance
logger = logging.getLogger(pathlib.PurePath(__file__).name)
logger.propagate = False

# Console messaging
console_formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
console_handler = logging.StreamHandler(stream=sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# File logging
file_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')
file_handler = logging.FileHandler(output_path / pathlib.Path(SHETRAN_RUN_LOG_FILENAME))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

logger.info("Logger initialised")

# Some additional logging info
logger.info("DATA_PATH = {}".format(data_path))
logger.info("output_path = {}".format(output_path))


###############################################################################
# Environmental Parameters
#   Parameters are passed as environment variables,
#   i.e. they are strings and will need to be converted where necessary
###############################################################################
def validate_boolean_parameter(p_string):
    p_val = os.getenv(p_string, "false")
    if p_val == "true":
      p_val = True
    elif p_val == "false":
        p_val = False
    else:
        e = "Model run terminated: undefined value provided for parameter {} --- {}".format(p_string, p_val)
        logger.error(e)
        raise ValueError(e)
    return p_val

# Simulation duration
start_date = os.getenv("RUN_START_DATE", "2023-06-20")
end_date = os.getenv("RUN_END_DATE", "2023-06-30")

# Hotstart boolean parameters
b_hot_rd = validate_boolean_parameter("B_HOT_RD")
b_hot_pr = validate_boolean_parameter("B_HOT_PR")

# Hotstart duration parameters
try:
    b_hot_ti = float(os.getenv("B_HOT_TI", "1.0"))
    b_hot_st = float(os.getenv("B_HOT_ST", "1.0"))
    edt_step = float(os.getenv("ETD_STEP", "1.0"))
except (TypeError, ValueError, Exception) as e:
    logger.error("Error converting parameter: {}".format(e))
    raise

# Case D is not permitted
if b_hot_rd and b_hot_pr:
    e = "Parameter combination not permitted: B_HOT_RD==True and B_HOT_PR==True"
    logger.error(e)
    raise(e)




###############################################################################
# Auxiliary functions
###############################################################################
def handle_hotstart():
    pass

###############################################################################
# Simulator execution
###############################################################################
# Find the rundata file from the inputs:
try:
    rundata_file = glob(os.path.join(run_path, 'rundata_*'))[0]
except IndexError:
    raise Exception('rundata file missing')

handle_hotstart()

# Run the SHETRAN model:
subprocess.call(['./Shetran-Linux', '-f', rundata_file])

title = os.getenv('TITLE', 'SHETRAN Simulation')
description = 'Run a SHETRAN simulation using outputs from a SHETRAN prepare model/workflow.'
geojson = {}
metadata = f"""{{
  "@context": ["metadata-v1"],
  "@type": "dcat:Dataset",
  "dct:language": "en",
  "dct:title": "{title}",
  "dct:description": "{description}",
  "dcat:keyword": [
    "shetran"
  ],
  "dct:subject": "Environment",
  "dct:license": {{
    "@type": "LicenseDocument",
    "@id": "https://creativecommons.org/licences/by/4.0/",
    "rdfs:label": null
  }},
  "dct:creator": [{{"@type": "foaf:Organization"}}],
  "dcat:contactPoint": {{
    "@type": "vcard:Organization",
    "vcard:fn": "DAFNI",
    "vcard:hasEmail": "support@dafni.ac.uk"
  }},
  "dct:created": "{datetime.datetime.now().isoformat()}Z",
  "dct:PeriodOfTime": {{
    "type": "dct:PeriodOfTime",
    "time:hasBeginning": null,
    "time:hasEnd": null
  }},
  "dafni_version_note": "created",
  "dct:spatial": {{
    "@type": "dct:Location",
    "rdfs:label": null
  }},
  "geojson": {geojson}
}}
"""
with open(os.path.join(output_path, METADATA_FILENAME), 'w') as f:
    f.write(metadata)
