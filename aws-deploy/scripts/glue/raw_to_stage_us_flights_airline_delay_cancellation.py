import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext

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
raw_data = glueContext.create_dynamic_frame.from_catalog(
    database="raw", 
    table_name="us_flights_airline_delay_cancellation",
    push_down_predicate ="year={ptn_year}".format(ptn_year=ptn_year)
)
raw_df = raw_data.toDF()
raw_df = raw_df.drop("unnamed: 27")

# Data store section
bucket = 'itbafl-stage-useast1-232483837258-prd'
table = 'external/kaggle/us-flights-airline-delay-cancellation'
path_s3 = 's3://' + bucket + '/' + table
raw_df.write.mode("overwrite").format("parquet").partitionBy("year").save(path_s3)