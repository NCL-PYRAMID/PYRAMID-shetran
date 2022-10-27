# PYRAMID-shetran
Containerised version of SHETRAN for DAFNI

## About
Containerised version of SHETRAN for DAFNI

### Project Team
Ben Smith, Newcastle University  ([ben.smith4@newcastle.ac.uk](mailto:ben.smith4@newcastle.ac.uk))  
Elizabeth Lewis, Newcastle University  ([elizabeth.lewis2@newcastle.ac.uk](mailto:elizabeth.lewis2@newcastle.ac.uk))  

### RSE Contact
Robin Wardle  
RSE Team, Newcastle Data  
Newcastle University NE1 7RU  
([robin.wardle@newcastle.ac.uk](mailto:robin.wardle@newcastle.ac.uk))  

## Built With

TBC

[Docker](https://www.docker.com)  

Other required tools: [tar](https://www.unix.com/man-page/linux/1/tar/), [zip](https://www.unix.com/man-page/linux/1/gzip/).

## Getting Started

### Prerequisites
TBC

### Installation
TBC

### Running Locally
TBC

### Running Tests
TBC

## Deployment

### Local
A local Docker container that mounts the test data can be built and executed using:

```
docker build . -t pyramid-shetran-prepare -f Dockerfile-prepare
docker run -v "$(pwd)/data:/data" pyramid-shetran-prepare
```

``` 
docker build . -t pyramid-shetran-run -f Dockerfile-run
docker run -v "$(pwd)/data:/data" pyramid-shetran-run
```


Note that output from the container, placed in the `./data` subdirectory, will have `root` ownership as a result of the way in which Docker's access permissions work.

### Production
#### DAFNI upload
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

The `pyramid-shetran-prepare.tar.gz` and `pyramid-shetran-prepare.tar.gz` Docker images and accompanying DAFNI model definition files (`model-definition-prepare.yml` and 'model-definition-prepare.yml') can be uploaded as new models using the "Add model" facility at [https://facility.secure.dafni.rl.ac.uk/models/](https://facility.secure.dafni.rl.ac.uk/models/).

## Usage
The deployed models can be run in a DAFNI workflow. See the [DAFNI workflow documentation](https://docs.secure.dafni.rl.ac.uk/docs/how-to/how-to-create-a-workflow) for details.


## Roadmap
- [x] Initial Research  
- [ ] Minimum viable product <-- You are Here  
- [ ] Alpha Release  
- [ ] Feature-Complete Release  

## Contributing
TBD

### Main Branch
All development can take place on the main branch. 

## License
This code is private to the PYRAMID project.

## Acknowledgements
This work was funded by NERC, grant ref. NE/V00378X/1, “PYRAMID: Platform for dYnamic, hyper-resolution, near-real time flood Risk AssessMent Integrating repurposed and novel Data sources”. See the project funding [URL](https://gtr.ukri.org/projects?ref=NE/V00378X/1).
