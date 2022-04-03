import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql.functions import year
from pyspark.sql.functions import month
from pyspark.sql.functions import col

# Job Parameters handling section
args = getResolvedOptions(sys.argv, ['JOB_NAME','ptn_year'])
ptn_year = args['ptn_year']

# Spark configurations section
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
spark.conf.set("spark.sql.sources.partitionOverwriteMode","dynamic")
job.init(args['JOB_NAME'], args)

# Data handling section
stage_data = glueContext.create_dynamic_frame.from_catalog(
    database="stage", 
    table_name="us_flights_airline_delay_cancellation",
    push_down_predicate ="year={ptn_year}".format(ptn_year=ptn_year)
)
df_stage = stage_data.toDF()
# Flights not cancelled with values in 'FL_DATE','ORIGIN','DEP_DELAY' features.
df_filtered = df_stage.filter(
    (df_stage['cancelled']==0.0) &
    (df_stage['fl_date'].isNotNull() & df_stage['origin'].isNotNull() & df_stage['dep_delay'].isNotNull())
)
# Average delay time by date and origin airport.
df_stg_agg = df_filtered.groupBy(['fl_date','origin']).avg('dep_delay')
# Columns formats
df_stg_agg = df_stg_agg.withColumn("flight_year", year(df_stg_agg.fl_date))
df_stg_agg = df_stg_agg.withColumn("flight_month", month(df_stg_agg.fl_date))
df_stg_agg_formatted = df_stg_agg.select(
    col("flight_year").alias("flight_year"), 
    col("flight_month").alias("flight_month"), 
    col("fl_date").alias("flight_date"), 
    col("origin").alias("origin_airport"),
    col("avg(dep_delay)").alias("avg_dep_delay_time")
)

df_stg_agg_formatted = df_stg_agg_formatted.coalesce(1)

bucket = 'itbafl-analytics-useast1-232483837258-prd'
table = 'agg-flights-delay-by-date-airport'
path_s3 = 's3://' + bucket + '/' + table
df_stg_agg_formatted.write.mode("overwrite").format("parquet").partitionBy("flight_year","flight_month","flight_date").save(path_s3)
