# SPDX-FileCopyrightText: 2022 - 2025 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import orthanc
import pprint
import json

# This plugin adds an API route to perform custom actions after an upload in the inbox


# Orthanc "change" handlers
def on_change(changeType, level, resource):

  if changeType == orthanc.ChangeType.ORTHANC_STARTED:

    # after a startup, there might be unprocessed and even untagged studies in case
    # Orthanc has been killed during an upload -> we must delete all these studies

    untagged_studies_ids = json.loads(orthanc.RestApiPost("/tools/find", json.dumps({
       "Level": "Study",
       "Query": {},
       "Labels": ["processed"],
       "LabelsConstraint": "None",
       "Expand": False
    })))

    if len(untagged_studies_ids) > 0:
        orthanc.LogWarning(f"INBOX: deleting {len(untagged_studies_ids)} un-processed studies at Orthanc startup")
        orthanc.RestApiPost("/tools/bulk-delete", json.dumps({
           "Resources": untagged_studies_ids
        }))
        orthanc.LogWarning(f"INBOX: deleting: done")
    else:
        orthanc.LogWarning(f"INBOX: no un-processed studies at Orthanc startup")

  elif changeType == orthanc.ChangeType.STABLE_STUDY:

    # If a study becomes stable and if it is not tagged as processed, it means that it has stayed too long in Orthanc.
    # This is probably a study whose upload has been interrupted
    # NOTE: define "StableStudy" to e.g 600 seconds to determine the duration 
    study_info = json.loads(orthanc.RestApiGet(f"/studies/{resource}"))
    if not "processed" in study_info["Labels"]:
        orthanc.LogWarning(f"INBOX: study {resource} stabilized without being processed -> deleting it")
        orthanc.RestApiDelete(f"/studies/{resource}")


# Orthanc Rest API callback called after every upload in the inbox
def on_post_inbox_commit(output, uri, **request):

    if request['method'] != 'POST':
        output.SendMethodNotAllowed('POST')

    payload = json.loads(request['body'])
    uploaded_studies_ids = payload["OrthancStudiesIds"]
    form_fields = payload["FormFields"]
    subject_id = form_fields['SubjectId']

    print(f"committing inbox upload for {subject_id}")

    for study_id in uploaded_studies_ids:
        r = json.loads(orthanc.RestApiPost(f"/studies/{study_id}/anonymize", json.dumps({
            "Replace": {
                "PatientID": subject_id,
                "PatientName": subject_id
            },
            "Force": True,  # because we set the PatientID
            "Synchronous": True
        })))
        anonymized_study_id = r["ID"]

        orthanc.RestApiPut(f"/studies/{anonymized_study_id}/labels/processed", "")

        # delete the original study
        orthanc.RestApiDelete(f"/studies/{study_id}")

    output.AnswerBuffer("", 'application/json')


orthanc.RegisterRestCallback('/plugins/inbox/commit', on_post_inbox_commit)

orthanc.RegisterOnChangeCallback(on_change)