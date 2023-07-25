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
#
#   b_hot_rd: hotstart read, possible values: {"F", "T"}
#   b_hot_pr: hotstart write (print), possible values: {"F", "T"}
#   b_hot_ti: hotstart initiation value: Float 0.00 in hrs from start of
#             simulation. Time when previous model is started. <=7 characters.
#   b_hot_st: hotstart output timestep: Float 0.00 in hrs from start of 
#             simulation - i.e.-  when we want to restart the model
#   etd_step: # [0 days 00:15:00]?
###############################################################################
def validate_boolean_parameter(p_string):
    # Boolean parameters are passed in from DAFNI as "True" and "False"
    # but to avoid any pointless errors e.g. maybe this might change,
    # it is a good idea to lowercase the parameter strings.
    p_val = str.lower(os.getenv(p_string, "false"))
    if p_val == "true":
      p_val = "T"
    elif p_val == "false":
        p_val = "F"
    else:
        e = "Model run terminated: undefined value provided for parameter {} --- {}".format(p_string, p_val)
        logger.error(e)
        raise ValueError(e)
    return p_val

# Simulation duration
start_date = os.getenv("RUN_START_DATE", "2023-06-20")
end_date = os.getenv("RUN_END_DATE", "2023-06-30")
toon_monsoon = os.getenv("TOON_MONSOON", "2012-06-28")

# Hotstart boolean parameters
b_hot_rd = validate_boolean_parameter("B_HOT_RD")
b_hot_pr = validate_boolean_parameter("B_HOT_PR")

# Hotstart duration parameters
try:
    b_hot_ti = float(os.getenv("B_HOT_TI", "1.0"))
    b_hot_st = float(os.getenv("B_HOT_ST", "0.0"))
    etd_step = float(os.getenv("ETD_STEP", "1.0"))
except (TypeError, ValueError, Exception) as e:
    logger.error("Error converting parameter", exc_info=e)
    raise

# Case D is not permitted
if b_hot_rd == "T" and b_hot_pr == "T":
    emsg = "Parameter combination not permitted: B_HOT_RD==True and B_HOT_PR==True"
    logger.error(emsg)
    raise ValueError(emsg)


###############################################################################
# Other setup
###############################################################################
livedata_pathname = os.path.join(run_path, "SHETRAN")
rainfall_filepath = glob(os.path.join(livedata_pathname, "*_Precip.csv"))
if len(rainfall_filepath) == 0:
    logger.warning("No precipitation files found, using default (results may be unreliable)")
elif len(rainfall_filepath) > 1:
    logger.warning("Multiple precipitation files found, using first one (results may be unreliable):")
    for f in rainfall_filepath:
        logger.warning("\t{}".format(f))
    shutil.copyfile(rainfall_filepath[0], os.path.join(run_path, os.path.basename(rainfall_filepath[0])))
else:
  logger.info("Using precipitation file {}".format(rainfall_filepath))
  shutil.copyfile(rainfall_filepath[0], os.path.join(run_path, os.path.basename(rainfall_filepath[0])))


###############################################################################
# Simulator execution
###############################################################################
# Find the rundata file from the inputs:
try:
    rundata_file = glob(os.path.join(run_path, 'rundata_*'))[0]
except IndexError as e:
    logger.error('Rundata file missing', exc_info=e)
    raise

######################
# HOTSTART SECTION
######################
# 0. Define functions
# 1. Change the frd file to the correct hotstart parameters
# 2. Make sure that b_hot_ti is <= etd_step
# 3. Change the frd file to have the relevant time periods
# 4. Change the run data file so that it can find the hotstart output file
# 5. Change the ETD file to the correct timestep.
# 6. Change the hotstart file so that it is initiated immediately.

# -0- Define functions:
def edit_text(file_path, frame_name, new_frame_text=None, print_only=False):
    # frame_name should be the start of the frame identifier in the text file.
    # e.g. ":FR26" for the HOTSTART PARAMETERS in the _frd file.
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # If you only want to see the value, not edit it, then use print_only= True
    if print_only:
        return lines[frame_search(lines, frame_name) + 1]
    else:
        lines[frame_search(lines, frame_name) + 1] = new_frame_text
        with open(file_path, 'w') as file:
            file.writelines(lines)


def frame_search(file_lines, string):
    # This will look for a frame number in the lines of a text file.
    # Frame numbering typically starts with the ':' then the first 2 letters of the SHETRAN file type e.g. FR for _frd
    return [x for x in range(0, len(file_lines)) if file_lines[x].startswith(string)][0]


def check_hotstart_parameter(hs_param):
    if hs_param not in ["T", "F"]:
        emsg = f"ERROR: hotstart parameter '{hs_param}' incorrectly set. Should be 'T' or 'F'."
        logger.error(emsg)
        raise ValueError(emsg)


def make_date(date_string):
    return datetime.datetime.strptime(date_string, '%Y-%m-%d')


def visualisation_plan_remove_item(item_number, vis_file_in=str, vis_file_out=None):
    """
    Don't forget that if you use this is combination with the number altering that you need to match the altered number.
    If you are removing multiple items, remove the higher numbers first.
    item_number can be a string or integer.
    Do not specify file_out if you want to overwrite.
    """

    if vis_file_out == None:
        vis_file_out = vis_file_in

    with open(vis_file_in, 'r') as vis:
        updated_text = ""
        number_corrector = 0

        for line in vis:
            line = line.strip().split(" : ")

            # IF the line starts with item then skip ('item' will be written later)
            if line[0] == "item":
                continue

            # IF the line starts with NUMBER, decide whether to read or write:
            if line[0][0:len(line[0]) - 2] == "NUMBER":

                # IF it is the number of interest read the next line too, not writing either
                # and add one to the index corrector:
                if line[0][-1] == str(item_number):
                    next(vis)
                    number_corrector += 1

                # IF a different number:
                if line[0][-1] != str(item_number):
                    new_number = int(line[0][-1]) - number_corrector
                    line[0] = str(line[0][0:len(line[0]) - 1] + str(new_number))
                    updated_text = updated_text + 'item \n' + " : ".join(line) + "\n" + next(vis)

            # If neither, just copy the line:
            else:
                updated_text = updated_text + " : ".join(line) + "\n"

    with open(vis_file_out, "w") as new_vis:
        new_vis.write(updated_text)

    if new_number == 0:
        return "WARNING: No lines were edited"



# TODO - undo this botch by setting HiPIMS to read data from SHETRAN using 
# parameters, instead of being hardcoded to toon monsoon. This code will make 
# SHETRAN think that it is always starting on 28th June 2012.
toon_monsoon_dt = make_date(toon_monsoon)
start_date_dt = make_date(start_date)
end_date_dt = make_date(end_date)
date_offset = toon_monsoon_dt - start_date_dt

start_date_dt += date_offset
end_date_dt += date_offset
start_date_toon = start_date_dt.strftime("%Y-%m-%d")
end_date_toon = end_date_dt.strftime("%Y-%m-%d")


# Raise errors if hotstart parameters are not T/F:
check_hotstart_parameter(b_hot_rd)
check_hotstart_parameter(b_hot_pr)
        

# -1- Edit the frd file to read / write the hotstart:
if "T" in [b_hot_rd, b_hot_pr]:
    # Find the _frd.txt file for hotstart:
    try:
        frd_file_path = glob(os.path.join(run_path, '*_frd.txt'))[0]
    except IndexError as e:
        logger.error('FRD file missing', exc_info=e)
        raise

    # Create the new line of parameters. This will only change the rainfall parameter. Future hotstarts may require
    # more of the parameters changing, e.g. if you use PET of different resolution to the main simulation.
    edit_text(frd_file_path, ":FR26",
              f"{b_hot_rd:>7}{b_hot_pr:>7}{b_hot_ti:>7}{b_hot_st:>7}\n")


if b_hot_rd == "T":
    # Find the _hot.txt file for hotstart:
    try:
        hotstart_file = glob(os.path.join(run_path, '*_hot.txt'))[0]
    except IndexError as e:
        logger.error('Hotstart file missing, checking for fort.28 file.', exc_info=e)
        try:
            hotstart_file = glob(os.path.join(run_path, 'fort.28'))[0]
            shutil.copyfile(hotstart_file, os.path.join(run_path, 'fort28_hotstart.txt'))
            hotstart_file = os.path.join(run_path, 'fort28_hotstart.txt')
            print('hotstart file incorrectly named; renaming and using fort.28 file.')
        except IndexError as e:
            logger.error('fort.28 hotstart file also missing. No hotstart inputs.', exc_info=e)
            raise
    

    #  Find the _etd.txt file for hotstart:
    try:
        etd_file = glob(os.path.join(run_path, '*_etd.txt'))[0]
    except IndexError as e:
        logger.error('ETD file missing', exc_info=e)
        raise

    # -2- Make sure that b_hot_ti is <= etd_step
    # Ensure that the hotstart initiation timestep is less than the etd timestep so that the hotstart conditions are
    # set immediately in the simulation, else the first x met data values will be skipped until the
    # b_hot_ti is crossed.
    if b_hot_ti > etd_step:
        print(f"Setting b_hot_ti ({b_hot_ti}) to etd_step ({etd_step})")
        b_hot_ti = etd_step

    # -3- Change the frd file to have the relevant time periods:
    # These should be taken from parameters so that the model knows when to start and end. The main purpose of this is
    # so that it only runs for as long as there is inout data. This will run up until 00:00 on the end date, not beyond.
    # If you want to change the times then you will need to add this into the parameter set.
    s_dates = [str(int(d)) for d in start_date_toon.split("-")]
    e_dates = [str(int(d)) for d in end_date_toon.split("-")]
    edit_text(frd_file_path, ":FR4", f"{s_dates[0]:>7}{s_dates[1]:>7}{s_dates[2]:>7}{0:>7}{0:>7}\n")  # Start
    edit_text(frd_file_path, ":FR6", f"{e_dates[0]:>7}{e_dates[1]:>7}{e_dates[2]:>7}{0:>7}{0:>7}\n")  # End

    # -4- Edit the run data file to find the hotstart file:
    # Direct the rundata file to the hotstart data. This is needed as the simulation _inputs.txt files have been made
    # by a prepare.exe that does not write hotstart parameters.
    edit_text(rundata_file, "28: hostart file", hotstart_file.split(run_path)[-1] + "\n")

    # -5- Change the ETD file to the correct timestep.
    # This will edit the timestep of the rainfall. We are not editing the timestep of the temp/PET as this will use the
    # first X days of the original data. This is a shortcut and future versions should read in new temp/PET data and
    # update the etd time steps as appropriate.
    text = edit_text(etd_file, ":ET3", print_only=True).split()
    edit_text(etd_file, ":ET3", f"{text[0]:>7}{etd_step:>7}{text[2]:>7}\n")

    # -6- Change hotstart time.
    # In theory, the hotstart timestep parameter is the time, in hrs, from the start of the simulation at which
    # you want to restart the simulation. If this is after 5 years, and the simulation is 15 years long, then you
    # will have 4 entries in the _hot.txt file: t=0yrs, 5yrs, 10yrs, 15yrs. We will always want the second entry, so
    # this code will clip the hotstart to just that time entry. We, in this version, always restart the simulation from
    # timestep 1, so we read in the _hot data, then immediately take the new rainfall CSV. We are choosing to use
    # whatever temp/PET data there is at the start of the existing csvs. This is because we don't think this matters
    # much for the short hotstarted run. If this is to be run properly, as a loop, then this data will need to be added
    # else our error will propagate.
    with open(hotstart_file, 'r') as file:
        lines = file.readlines()

    time_lines = []
    l = 0
    while len(time_lines) <= 2 and l<len(lines):
        if lines[l].startswith(" time="):
            time_lines.append(l)
        l += 1

        # If using a premade Hotstart file with 1 time entry:
        if len(time_lines)==1:
            new_hot_text = lines
          
        # If not then set the second timestep to be the first:
        else:
            if len(time_lines)==3:
                l = l-1
            new_hot_text = [lines[0]]
            new_hot_text.extend(lines[time_lines[1]+1 : l])

    with open(hotstart_file, 'w') as file:
        file.writelines(new_hot_text)


    # -7- Change Visualisation Plan:
    # Change the visualisation plan to reduce outputs and to ensure hourly outputs:
    try:
        vis_plan_file = glob(os.path.join(run_path, '*_visualisation_plan.txt'))[0]
    except IndexError:
        raise Exception('visualisation_plan file missing')
    print(vis_plan_file)

    for line in ["6", "5", "3", "2", "1"]:
        visualisation_plan_remove_item(line, vis_plan_file)
    edit_text(vis_plan_file, "9 1 !", "1 876000 !every hour for 10 years, or until the end of the simulation.\n")


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
