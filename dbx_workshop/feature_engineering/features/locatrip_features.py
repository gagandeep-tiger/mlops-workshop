"""
This sample module contains features logic that can be used to generate and populate tables in Feature Store. 
You should plug in your own features computation logic in the compute_features_fn method below.
"""
import pyspark.sql.functions as F


def compute_features_fn(pickup_feature, dropoff_feature):
    """Contains logic to compute features.

    Given an input dataframe and time ranges, this function should compute features, populate an output dataframe and
    return it. This method will be called from a  Feature Store pipeline job and the output dataframe will be written
    to a Feature Store table. You should update this method with your own feature computation logic.

    The timestamp_column, start_date, end_date args are optional but strongly recommended for time-series based
    features.

    TODO: Update and adapt the sample code for your use case

    :param input_df: Input dataframe.
    :param timestamp_column: Column containing the timestamp. This column is used to limit the range of feature
    computation. It is also used as the timestamp key column when populating the feature table, so it needs to be
    returned in the output.
    :param start_date: Start date of the feature computation interval.
    :param end_date:  End date of the feature computation interval.
    :return: Output dataframe containing computed features given the input arguments.
    """

    df_merged = pickup_feature.join(dropoff_feature, on="zip", how="full_outer")
    df_localtrip = df_merged.withColumn(
        "local_trip",
        F.when(
            F.col("count_trips_window_1h_pickup_zip").isNotNull() & F.col("count_trips_window_30m_dropoff_zip").isNotNull(),
            F.lit(1)
        ).otherwise(F.lit(0))
    ).select("zip","local_trip") 

    return df_localtrip
