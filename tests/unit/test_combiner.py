# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime

import ibis.pandas
import pandas
import pandas.testing
import pytest

from data_validation import metadata


@pytest.fixture
def module_under_test():
    from data_validation import combiner

    return combiner


def test_generate_report_with_different_columns(module_under_test):
    source = pandas.DataFrame({"count": [1], "sum": [3]})
    target = pandas.DataFrame({"count": [2]})
    pandas_client = ibis.pandas.connect(
        {
            module_under_test.DEFAULT_SOURCE: source,
            module_under_test.DEFAULT_TARGET: target,
        }
    )
    with pytest.raises(
        ValueError, match="Expected source and target to have same schema"
    ):
        module_under_test.generate_report(
            pandas_client,
            # Schema validation occurs before run_metadata is needed.
            None,
        )


@pytest.mark.parametrize(
    ("source_df", "target_df", "run_metadata", "expected"),
    (
        (
            pandas.DataFrame({"count": [1]}),
            pandas.DataFrame({"count": [2]}),
            metadata.RunMetadata(
                validations={
                    "count": metadata.ValidationMetadata(
                        source_table_name="test_source",
                        source_column_name=None,
                        target_table_name="test_target",
                        target_column_name=None,
                        validation_type="Column",
                        aggregation_type="count",
                    ),
                },
                start_time=datetime.datetime(1998, 9, 4, 7, 30, 1),
                end_time=datetime.datetime(1998, 9, 4, 7, 31, 42),
            ),
            pandas.DataFrame(
                {
                    "start_time": [datetime.datetime(1998, 9, 4, 7, 30, 1)],
                    "end_time": [datetime.datetime(1998, 9, 4, 7, 31, 42)],
                    "source_table_name": ["test_source"],
                    "source_column_name": [None],
                    "target_table_name": ["test_target"],
                    "target_column_name": [None],
                    "validation_type": ["Column"],
                    "aggregation_type": ["count"],
                    "validation_name": ["count"],
                    "source_agg_value": ["1"],
                    "target_agg_value": ["2"],
                    "source_group_by_columns": [[]],
                    "target_group_by_columns": [[]],
                }
            ),
        ),
        (
            pandas.DataFrame({"count": [12], "sum__ttteeesssttt": [-1]}),
            pandas.DataFrame({"count": [13], "sum__ttteeesssttt": [1]}),
            metadata.RunMetadata(
                validations={
                    "count": metadata.ValidationMetadata(
                        source_table_name="test_source",
                        source_column_name=None,
                        target_table_name="test_target",
                        target_column_name=None,
                        validation_type="Column",
                        aggregation_type="count",
                    ),
                    "sum__ttteeesssttt": metadata.ValidationMetadata(
                        source_table_name="test_source",
                        source_column_name="test_col",
                        target_table_name="test_target",
                        target_column_name="ttteeesssttt_col",
                        validation_type="Column",
                        aggregation_type="sum",
                    ),
                },
                start_time=datetime.datetime(1998, 9, 4, 7, 30, 1),
                end_time=datetime.datetime(1998, 9, 4, 7, 31, 42),
            ),
            pandas.DataFrame(
                {
                    "start_time": [datetime.datetime(1998, 9, 4, 7, 30, 1)] * 2,
                    "end_time": [datetime.datetime(1998, 9, 4, 7, 31, 42)] * 2,
                    "source_table_name": ["test_source", "test_source"],
                    "source_column_name": [None, "test_col"],
                    "target_table_name": ["test_target", "test_target"],
                    "target_column_name": [None, "ttteeesssttt_col"],
                    "validation_type": ["Column", "Column"],
                    "aggregation_type": ["count", "sum"],
                    "validation_name": ["count", "sum__ttteeesssttt"],
                    "source_agg_value": ["12", "-1"],
                    "target_agg_value": ["13", "1"],
                    "source_group_by_columns": [[], []],
                    "target_group_by_columns": [[], []],
                }
            ),
        ),
    ),
)
def test_generate_report_without_group_by(
    module_under_test, source_df, target_df, run_metadata, expected
):
    pandas_client = ibis.pandas.connect(
        {"test_source": source_df, "test_target": target_df}
    )
    report = module_under_test.generate_report(
        pandas_client,
        run_metadata,
        source_table="test_source",
        target_table="test_target",
    )
    # Sort columns by name to order in the comparison.
    # https://stackoverflow.com/a/11067072/101923
    # Sort rows by name to order in the comparison.
    report = (
        report.sort_values("validation_name")
        .reset_index(drop=True)
        .reindex(sorted(report.columns), axis=1)
    )
    expected = (
        expected.sort_values("validation_name")
        .reset_index(drop=True)
        .reindex(sorted(expected.columns), axis=1)
    )
    pandas.testing.assert_frame_equal(report, expected)