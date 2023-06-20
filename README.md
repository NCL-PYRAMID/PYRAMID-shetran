# PYRAMID-shetran
Containerised version of SHETRAN for DAFNI, using Docker.

## About
This repository holds a containerised version of SHETRAN for DAFNI. The version of SHETRAN here is split into two components:

- a `shetran-prepare` model, which takes static and dynamic environmental inputs and creates data for running SHETRAN proper
- a `shetran-run` model which runs the actual SHETRAN simulator using the correct SHETRAN-format input files

Each of these two components have their own Python script, Dockerfile, and DAFNI `model-definition.yml` description. The repository is configured to build a docker container on commit (although at present no testing of this container is performed), and to build an upload a new model version of both models to DAFNI on the creation of a new project release in GitHub.

More information about SHETRAN can be found on the [public SHETRAN repository](https://github.com/nclwater/Shetran-public) and the [main project website](https://research.ncl.ac.uk/shetran/). The version of SHETRAN included in this DAFNI repository is [release V4.5.2](https://github.com/nclwater/Shetran-public/releases/tag/V4.5.2).

### Project Team
Ben Smith, Newcastle University  ([ben.smith4@newcastle.ac.uk](mailto:ben.smith4@newcastle.ac.uk))  
Elizabeth Lewis, Newcastle University  ([elizabeth.lewis2@newcastle.ac.uk](mailto:elizabeth.lewis2@newcastle.ac.uk))  

### RSE Contact
Robin Wardle  
RSE Team, NICD  
Newcastle University NE1 7RU  
([robin.wardle@newcastle.ac.uk](mailto:robin.wardle@newcastle.ac.uk))  

## Built With
[SHETRAN release V4.5.2](https://github.com/nclwater/Shetran-public/releases/tag/V4.5.2).

[Python 3](https://www.python.org/)

[Docker](https://www.docker.com)  

Other required tools: [tar](https://www.unix.com/man-page/linux/1/tar/), [zip](https://www.unix.com/man-page/linux/1/gzip/).

## Getting Started

### Prerequisites
Python 3.8 is required to run the SHETRAN Python scripts, and Docker also needs to be installed. If working on a Windows system, it is recommended that [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) is used for any local Docker builds; a) because DAFNI requires Linux Docker images, and b) native command-line Linux tools are much superior to those provided by Windows.

### Installation
The models are Python 3 scripts and need no installation for local execution. Deployment to DAFNI is covered below.

### Running Locally
The model can be run with the example case studies in the repository in a `bash` shell by doing the following from within the repository directory.

```
cd Shetran-Model-Linux-EasySetup-Snow_4_5_2
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:$(pwd)
chmod +x shetran-prepare-snow
chmod +x Shetran-Linux
cd Example_Catchment_Data
```
Choose an example to run, e.g. `SHETRAN_UK_7006_raw_inputs`:
```
cd SHETRAN_UK_7006_raw_inputs
../../shetran-prepare-snow 7006_LibraryFile.xml
../../Shetran-Linux -f rundata_7006.txt
```
The simulation should run and produce a set of results files. To clean up and reset the file and environment state to previously, enter the following shell commands:
```
rm *.txt
rm output_7006_*
cd ../..
chmod -x shetran-prepare-snow
chmod -x Shetran-Linux
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH/:$(pwd)/}
```

### Running Tests
There are no additional tests for DAFNI SHETRAN.

## Deployment

### Local
The input data location must be created and appropriate test data copied there, e.g. from within the repository root:
```
mkdir -p data/inputs
cp Shetran-Model-Linux-EasySetup-Snow_4_5_2/Example_Catchment_Data/SHETRAN_UK_7006_raw_inputs/* data/inputs/
```
A local Docker container that mounts the test data can be built and executed using:

```
docker build . -t pyramid-shetran-prepare -f Dockerfile-prepare
docker run -v "$(pwd)/data:/data" pyramid-shetran-prepare:latest
```
``` 
cp data/outputs/* data/inputs
docker build . -t pyramid-shetran-run -f Dockerfile-run
docker run -v "$(pwd)/data:/data" pyramid-shetran-run:latest
```
Note that output from the container, placed in the `./data` subdirectory, will have `root` ownership as a result of the way in which Docker's access permissions work. To clean up, from within the repository root. WARNING, BE VERY CAREFUL RUNNING `sudo rm -r` FROM WITHIN THE WRONG DIRECTORY!
```
sudo rm -r data
```

### Production
#### Manual upload to DAFNI
The model is containerised using Docker, and the image is _tar_'ed and _zip_'ed for uploading to DAFNI. Use the following commands in a *nix shell to accomplish this. Two separate models need to be build, `prepare` and `run`.

```
docker build . -t pyramid-shetran-prepare -f Dockerfile-prepare
docker save -o pyramid-shetran-prepare.tar pyramid-shetran-prepare:latest
gzip pyramid-shetran-prepare.tar
```

```
docker build . -t pyramid-shetran-run -f Dockerfile-run
docker save -o pyramid-shetran-run.tar pyramid-shetran-run:latest
gzip pyramid-shetran-run.tar
```

The `pyramid-shetran-prepare.tar.gz` and `pyramid-shetran-prepare.tar.gz` Docker images and accompanying DAFNI model definition files (`model-definition-prepare.yml` and `model-definition-prepare.yml`) can be uploaded as new models using the "Add model" facility at [https://facility.secure.dafni.rl.ac.uk/models/](https://facility.secure.dafni.rl.ac.uk/models/). Alternatively, the existing SHETRAN Prepare and SHETRAN Run models can be updated manually in DAFNI by locating the relevant model through the DAFNI UI, selecting "Edit Model", uploading a new image and / or metadata file, and incrementing the semantic version number in the "Version Message" field appropriately.

As of 19/06/2023 the SHETRAN DAFNI parent model UUIDs are
| Model | UUID |
| --- | --- |
| SHETRAN Prepare | eb77ac58-c528-437c-ab45-5ba6d464d45b |
| SHETRAN Run | 6756ebb2-b1f6-41cf-87e1-58533583801d |

#### CI/CD with GitHub Actions
The SHETRAN models can be deployed to DAFNi using GitHub Actions. The relevant workflows are built into the SHETRAN model repository and use the [DAFNI Model Uploader Action](https://github.com/dafnifacility/dafni-model-uploader) to update the DAFNI model. The workflows trigger on the creation of a new release tag which follows [semantic versioning](https://semver.org/) and takes the format `vx.y.z` where `x` is a major release, `y` a minor release, and `z` a patch release.

The DAFNI model upload process is prone to failing, often during model ingestion, in which case a deployment action will show a failed status. Such deployment failures might be a result of a DAFNI timeout, or there might be a problem with the model build. It is possible to re-run the action in GitHub if it is evident that the failure is as a result of a DAFNI timeout. However, deployment failures caused by programming errors (e.g. an error in the model definition file) that are fixed as part of the deployment process will **not** be included in the tagged release! It is thus best practice in case of a deployment failure always to delete the version tag and to go through the release process again, re-creating the version tag and re-triggering the workflows.

The DAFNI model upload process requires valid user credentials. These are stored in the NCL-PYRAMID organization "Actions secrets and variables", and are:
```
DAFNI_SERVICE_ACCOUNT_USERNAME
DAFNI_SERVICE_ACCOUNT_PASSWORD
```
Any NCL-PYRAMID member with a valid DAFNI login may update these credentials.

## Usage
The deployed models can be run in a DAFNI workflow. See the [DAFNI workflow documentation](https://docs.secure.dafni.rl.ac.uk/docs/how-to/how-to-create-a-workflow) for details.

## Roadmap
- [x] Initial Research  
- [x] Minimum viable product
- [x] Alpha Release  
- [ ] Feature-Complete Release  

## Contributing
The PYRAMID SHETRAN for DAFNI project has ended. Pull requests from outside the project team will be ignored.

### Main Branch
The stable branch is `main`. All development should take place on new branches. Pull requests are enabled on `main`.

## License
This code is private to the PYRAMID project.

## Acknowledgements
This work was funded by NERC, grant ref. NE/V00378X/1, “PYRAMID: Platform for dYnamic, hyper-resolution, near-real time flood Risk AssessMent Integrating repurposed and novel Data sources”. See the project funding [URL](https://gtr.ukri.org/projects?ref=NE/V00378X/1).
