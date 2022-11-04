#!/bin/bash

DEBUG=
DEBUG=echo

if ${DEBUG};
then
  echo "Running in debug mode";
else
  echo "Running in normal mode";
fi


if [ "${PLATFORM}" == "DOCKER" ];
then
    DATA_ROOT="/";
else
    DATA_ROOT="../";
fi

DATA_PATH=${DATA_PATH:=${DATA_ROOT}data}
INPUTS=${DATA_PATH}/inputs
OUTPUTS=${DATA_PATH}/outputs


$DEBUG rm -r ${OUTPUTS}

declare -x RUN_PATH=${OUTPUTS}

$DEBUG cp -r ${INPUTS} ${RUN_PATH}

declare -x LIBRARY=$(find ${RUN_PATH} -name *.xml)
if [ -z "${LIBRARY}" ];
then
    echo "Library file missing";
    exit 1;
fi

$DEBUG ./shetran-prepare-snow ${LIBRARY}

TITLE=${TITLE:="SHETRAN Prepare Outputs"}
DESCRIPTION="Outputs for the SHETRAN Prepare script to be used in a SHETRAN simulation"
CREATED=$(date --iso-8601=s)
GEOJSON=

read -r -d '' METADATA << EOF
{{
  "@context": ["metadata-v1"],
  "@type": "dcat:Dataset",
  "dct:language": "en",
  "dct:title": "${TITLE}",
  "dct:description": "${DESCRIPTION}",
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
  "dct:created": "${CREATED}"
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
  "geojson": "${GEOJSON}"
}}
EOF

echo "${METADATA}" > metadata.json
