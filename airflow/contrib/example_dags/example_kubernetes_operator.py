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
This is an example dag for using the KubernetesPodOperator.
"""
from airflow.utils.dates import days_ago
from airflow.utils.log.logging_mixin import LoggingMixin
from airflow.models import DAG

log = LoggingMixin().log

try:
    # Kubernetes is optional, so not available in vanilla Airflow
    # pip install 'apache-airflow[kubernetes]'
    from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator

    args = {
        'owner': 'Airflow',
        'start_date': days_ago(2)
    }

    dag = DAG(
        dag_id='example_kubernetes_operator',
        default_args=args,
        schedule_interval=None)

    tolerations = [
        {
            'key': "key",
            'operator': 'Equal',
            'value': 'value'
        }
    ]

    k = KubernetesPodOperator(
        namespace='airflow',
        image="ubuntu:16.04",
        cmds=["bash", "-cx"],
        arguments=["echo", "10"],
        labels={"foo": "bar"},
        name="airflow-test-pod",
        in_cluster=False,
        task_id="task",
        get_logs=True,
        dag=dag,
        is_delete_operator_pod=False,
        tolerations=tolerations
    )

except ImportError as e:
    log.warning("Could not import KubernetesPodOperator: " + str(e))
    log.warning("Install kubernetes dependencies with: "
                "    pip install 'apache-airflow[kubernetes]'")
