# -*- coding: utf-8 -*-
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""
This module contains Google Cloud Storage download operator.
"""

import sys
import warnings

from airflow.contrib.hooks.gcs_hook import GoogleCloudStorageHook
from airflow.models import BaseOperator
from airflow.models.xcom import MAX_XCOM_SIZE
from airflow.utils.decorators import apply_defaults
from airflow import AirflowException


class GoogleCloudStorageDownloadOperator(BaseOperator):
    """
    Downloads a file from Google Cloud Storage.

    If a filename is supplied, it writes the file to the specified location, alternatively one can
    set the ``store_to_xcom_key`` parameter to True push the file content into xcom. When the file size
    exceeds the maximum size for xcom it is recommended to write to a file.

    :param bucket: The Google cloud storage bucket where the object is. (templated)
    :type bucket: str
    :param object: The name of the object to download in the Google cloud
        storage bucket. (templated)
    :type object: str
    :param filename: The file path on the local file system (where the
        operator is being executed) that the file should be downloaded to. (templated)
        If no filename passed, the downloaded data will not be stored on the local file
        system.
    :type filename: str
    :param store_to_xcom_key: If this param is set, the operator will push
        the contents of the downloaded file to XCom with the key set in this
        parameter. If not set, the downloaded data will not be pushed to XCom. (templated)
    :type store_to_xcom_key: str
    :param gcp_conn_id: (Optional) The connection ID used to connect to Google Cloud Platform.
    :type gcp_conn_id: str
    :param google_cloud_storage_conn_id: (Deprecated) The connection ID used to connect to Google Cloud
        Platform. This parameter has been deprecated. You should pass the gcp_conn_id parameter instead.
    :type google_cloud_storage_conn_id: str
    :param delegate_to: The account to impersonate, if any.
        For this to work, the service account making the request must have
        domain-wide delegation enabled.
    :type delegate_to: str
    """
    template_fields = ('bucket', 'object', 'filename', 'store_to_xcom_key',)
    ui_color = '#f0eee4'

    @apply_defaults
    def __init__(self,
                 bucket,
                 object_name=None,
                 filename=None,
                 store_to_xcom_key=None,
                 gcp_conn_id='google_cloud_default',
                 google_cloud_storage_conn_id=None,
                 delegate_to=None,
                 *args,
                 **kwargs):
        # To preserve backward compatibility
        # TODO: Remove one day
        if object_name is None:
            if 'object' in kwargs:
                object_name = kwargs['object']
                DeprecationWarning("Use 'object_name' instead of 'object'.")
            else:
                TypeError("__init__() missing 1 required positional argument: 'object_name'")

        if filename is not None and store_to_xcom_key is not None:
            raise ValueError("Either filename or store_to_xcom_key can be set")

        if google_cloud_storage_conn_id:
            warnings.warn(
                "The google_cloud_storage_conn_id parameter has been deprecated. You should pass "
                "the gcp_conn_id parameter.", DeprecationWarning, stacklevel=3)
            gcp_conn_id = google_cloud_storage_conn_id

        super().__init__(*args, **kwargs)
        self.bucket = bucket
        self.object = object_name
        self.filename = filename
        self.store_to_xcom_key = store_to_xcom_key
        self.gcp_conn_id = gcp_conn_id
        self.delegate_to = delegate_to

    def execute(self, context):
        self.log.info('Executing download: %s, %s, %s', self.bucket,
                      self.object, self.filename)
        hook = GoogleCloudStorageHook(
            google_cloud_storage_conn_id=self.gcp_conn_id,
            delegate_to=self.delegate_to
        )

        if self.store_to_xcom_key:
            file_bytes = hook.download(bucket_name=self.bucket,
                                       object_name=self.object)
            if sys.getsizeof(file_bytes) < MAX_XCOM_SIZE:
                context['ti'].xcom_push(key=self.store_to_xcom_key, value=file_bytes)
            else:
                raise AirflowException(
                    'The size of the downloaded file is too large to push to XCom!'
                )
        else:
            hook.download(bucket_name=self.bucket,
                          object_name=self.object,
                          filename=self.filename)
