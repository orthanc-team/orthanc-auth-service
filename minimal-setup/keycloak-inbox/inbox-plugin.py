# SPDX-FileCopyrightText: 2022 - 2025 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import orthanc
import pprint
import json
import re
import time
import threading
import typing
import datetime
import base64

# This plugin adds API routes to perform custom actions after an upload in the inbox.

def from_dicom_date(dicom_date: str) -> datetime.date:
    if dicom_date is None or len(dicom_date) == 0:
        return None
    m = re.match('(?P<year>[0-9]{4})(?P<month>[0-9]{2})(?P<day>[0-9]{2})', dicom_date)
    if m is None:
        raise ValueError("Not a valid DICOM date: '{0}'".format(dicom_date))
    return datetime.date(int(m.group('year')), int(m.group('month')), int(m.group('day')))

def to_dicom_date(date: datetime.date) -> str:
    if date:
        return '{0:4}{1:02}{2:02}'.format(date.year, date.month, date.day)
    return None

def get_first_day_of_year(date):
    if date:
        return datetime.date(date.year, 1, 1)
    return None


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


def mark_invalid_field(result, field_name, message):
    result[field_name] = {
       "IsValid": False,
       "Message": message
    }

def mark_valid_field(result, field_name):
    result[field_name] = {
        "IsValid": True
    }

# Orthanc Rest API callback to validate the form of the inbox
def on_post_validate_form(output, uri, **request):

    if request['method'] != 'POST':
        output.SendMethodNotAllowed('POST')

    payload = json.loads(request['body'])
    form_fields = payload["FormFields"]

    result = {}

    if True:
        subject_id = form_fields['SubjectId']
        if not subject_id:
            mark_invalid_field(result, 'SubjectId', "The Subject Id is mandatory")
        elif not re.match('SUB\-[0-9]{3}', subject_id):
            mark_invalid_field(result, 'SubjectId', "Invalid format, expecting something like 'SUB-253'")
        else:
            mark_valid_field(result, 'SubjectId')

        visit_id = form_fields['VisitId']
        if not visit_id:
            mark_invalid_field(result, 'VisitId', "Select a visit")
        else:
            mark_valid_field(result, 'VisitId')

        site_id = form_fields.get('SiteId')
        if not site_id:
            mark_invalid_field(result, 'SiteId', "Select a site ID")
        else:
            mark_valid_field(result, 'SiteId')

        pdf_form = form_fields['PdfForm']
        if not pdf_form:
            mark_invalid_field(result, 'PdfForm', "Provide a PDF file")
        else:
            if pdf_form.startswith('data:application/pdf;base64,'):
                mark_valid_field(result, 'PdfForm')
            else:
                mark_invalid_field(result, 'PdfForm', "Make sure to upload a PDF file")
    else:
        mark_valid_field(result, 'VisitId')
        mark_valid_field(result, 'SubjectId')
        mark_valid_field(result, 'SiteId')
        mark_valid_field(result, 'PdfForm')

    output.AnswerBuffer(json.dumps(result), 'application/json')


# keep track of the currently running jobs and their source studies
store_lock = threading.Lock()
commit_jobs = {}
current_commit_id = 0


class StudyProcess:
    anonymization_progress: int = 0
    anonymization_completed: bool = False

    def __init__(self, uploaded_study_id: str):
        self.uploaded_study_id = uploaded_study_id
    
    def set_anonymization_complete(self):
        self.anonymization_completed = True
    
    def set_anonymization_progress(self, pct: int):
        self.anonymization_progress = pct

    def get_pct_complete(self):
        if self.anonymization_completed:
            return 100
        else:
            return self.anonymization_progress


class CommitJob:
    study_processes: typing.Dict[str, StudyProcess]

    current_message: str
    has_failed: bool = False
    is_complete: bool = False

    def __init__(self, uploaded_studies_ids: typing.List[str], form_fields: dict, current_message: str):
        self.current_message = current_message

        self.study_processes = {}
        for study_id in uploaded_studies_ids:
            self.study_processes[study_id] = StudyProcess(uploaded_study_id=study_id)

    def get_pct_complete(self):
        total_progress = 0
        
        for (study_id, study_process) in self.study_processes.items():
            total_progress += study_process.get_pct_complete()
        return total_progress / len(self.study_processes)



# Orthanc Rest API callback called after every upload in the inbox
def on_post_inbox_commit(output, uri, **request):
    global current_commit_id
    global store_lock
    global commit_jobs

    if request['method'] != 'POST':
        output.SendMethodNotAllowed('POST')

    payload = json.loads(request['body'])
    uploaded_studies_ids = payload["OrthancStudiesIds"]
    form_fields = payload["FormFields"]
    subject_id = form_fields['SubjectId']
    pdf_form = form_fields['PdfForm']

    orthanc.LogInfo(f"INBOX: committing upload for {subject_id}")

    if len(uploaded_studies_ids) > 1:
        message = f"Wait while {len(uploaded_studies_ids)} studies are being anonymized"
    else:
        message = f"Wait while the study is being anonymized"

    with store_lock:
        current_commit_id += 1
        commit_jobs[current_commit_id] = CommitJob(uploaded_studies_ids=uploaded_studies_ids,
                                                   form_fields=form_fields,
                                                   current_message=message)
        
        response = {
            "CommitId": current_commit_id,
            "Message": message
        } 

    # Already send the response although we will only start processing the data.
    # The monitoring callback will report the status that is shared through the commit_jobs data
    output.AnswerBuffer(json.dumps(response), 'application/json')

    for study_id in uploaded_studies_ids:
        anonymized_study_id = None
        orthanc.LogInfo(f"INBOX: processing {study_id}")

        study_info = json.loads(orthanc.RestApiGet(f"/studies/{study_id}"))

        # anonymize the study
        job = json.loads(orthanc.RestApiPost(f"/studies/{study_id}/anonymize", json.dumps({
            "Replace": {
                "PatientID": subject_id,
                "PatientName": subject_id,
                "StudyDescription": form_fields['VisitId'],
                "PatientBirthDate": to_dicom_date(get_first_day_of_year(from_dicom_date(study_info['PatientMainDicomTags'].get('PatientBirthDate')))),
                "PatientSex": study_info['PatientMainDicomTags'].get('PatientSex')
            },
            "Keep": [
                "StudyDate",
                "StudyTime"
            ],
            "Force": True,  # because we set the PatientID
            "Synchronous": False
        })))

        job_id = job['ID']
        orthanc.LogInfo(f"INBOX: Created anonymization job {job_id}")

        # monitor the anonymization job and report progress in the commit_jobs data
        has_failed = False
        job_completed = False
        while not job_completed and not has_failed:
            time.sleep(1)
            job = json.loads(orthanc.RestApiGet(f"/jobs/{job_id}"))
            if job['State'] == 'Success':
                job_completed = True
                with store_lock:
                    commit_jobs[current_commit_id].study_processes[study_id].anonymization_completed = True
                    commit_jobs[current_commit_id].study_processes[study_id].anonymization_progress = 100
                    anonymized_study_id = job['Content']['ID']
                    orthanc.LogInfo(f"INBOX: Anonymization job {job_id} completed: {anonymized_study_id}")
            elif job['State'] == 'Failure':
                has_failed = True
                with store_lock:
                    commit_jobs[current_commit_id].has_failed = True
                    commit_jobs[current_commit_id].current_message = f"One of the study could not be anonymized.  Ref job: {job_id}"
            else:
                with store_lock:
                    commit_jobs[current_commit_id].study_processes[study_id].anonymization_progress = job['Progress']

        # label the anonymized study
        if anonymized_study_id:
            orthanc.LogInfo(f"INBOX: Labelling anonymized study {anonymized_study_id}")
            orthanc.RestApiPut(f"/studies/{anonymized_study_id}/labels/processed", "")

        # attach the PDF as a new DICOM series
        try:
            orthanc.LogInfo(f"INBOX: Attaching PDF file {anonymized_study_id}")
            orthanc.RestApiPost("/tools/create-dicom",
                                json.dumps({
                                    'Parent': anonymized_study_id,
                                    'Tags': { 
                                        'SOPClassUID': '1.2.840.10008.5.1.4.1.1.104.1',
                                        'SeriesDescription': 'PDF Form'
                                    },
                                    'Content' : pdf_form
                                }))
        except Exception as e:
            with store_lock:
                orthanc.LogError(f"INBOX: failed to attach the PDF File: study {anonymized_study_id}")
                commit_jobs[current_commit_id].has_failed = True
                commit_jobs[current_commit_id].current_message = f"Failed to attach the PDF file.  Ref study: {anonymized_study_id}"
        finally:

            orthanc.LogInfo(f"INBOX: deleting the original study {study_id}")
            # delete the original study
            orthanc.RestApiDelete(f"/studies/{study_id}")

    with store_lock:
        commit_jobs[current_commit_id].is_complete = True
        if not commit_jobs[current_commit_id].has_failed:
            commit_jobs[current_commit_id].current_message = "All studies have been uploaded and anonymized."


# Orthanc Rest API callback called to monitor processing after a commit
def on_post_monitor_processing(output, uri, **request):
    global store_lock
    global commit_jobs

    if request['method'] != 'POST':
        output.SendMethodNotAllowed('POST')

    # the payload is the response from the commit route
    payload = json.loads(request['body'])

    commit_id = payload["CommitId"]
    response = {}

    with store_lock:
        if commit_id in commit_jobs:
            commit_job = commit_jobs[commit_id]

            pprint.pprint(commit_job)

            response = {
                "PctProcessed": commit_job.get_pct_complete(),
                "HasFailed": commit_job.has_failed,
                "IsComplete": commit_job.is_complete,
                "Message": commit_job.current_message
            }

    output.AnswerBuffer(json.dumps(response), 'application/json')





orthanc.RegisterRestCallback('/plugins/inbox/validate-form', on_post_validate_form)
orthanc.RegisterRestCallback('/plugins/inbox/commit', on_post_inbox_commit)
orthanc.RegisterRestCallback('/plugins/inbox/monitor-processing', on_post_monitor_processing)

orthanc.RegisterOnChangeCallback(on_change)