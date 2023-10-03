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
from __future__ import annotations

from airflow.models.dag import DAG
from airflow.models.dagrun import DagRun
from airflow.utils.session import create_session
from airflow.utils.state import DagRunState
from airflow.utils.types import DagRunType
from tests.models import DEFAULT_DATE


def test_dagrun_state_enum_escape():
    """
    Make sure DagRunState.QUEUED is converted to string 'queued' when
    referenced in DB query
    """
    with create_session() as session:
        dag = DAG(dag_id="test_dagrun_state_enum_escape", start_date=DEFAULT_DATE)
        dag.create_dagrun(
            run_type=DagRunType.SCHEDULED,
            state=DagRunState.QUEUED,
            execution_date=DEFAULT_DATE,
            start_date=DEFAULT_DATE,
            session=session,
        )

        query = session.query(DagRun.dag_id, DagRun.state, DagRun.run_type,).filter(
            DagRun.dag_id == dag.dag_id,
            # make sure enum value can be used in filter queries
            DagRun.state == DagRunState.QUEUED,
        )
        assert str(query.statement.compile(compile_kwargs={"literal_binds": True})) == (
            "SELECT dag_run.dag_id, dag_run.state, dag_run.run_type \n"
            "FROM dag_run \n"
            "WHERE dag_run.dag_id = 'test_dagrun_state_enum_escape' AND dag_run.state = 'queued'"
        )

        rows = query.all()
        assert len(rows) == 1
        assert rows[0].dag_id == dag.dag_id
        # make sure value in db is stored as `queued`, not `DagRunType.QUEUED`
        assert rows[0].state == "queued"

        session.rollback()