import datetime as dt
from airflow.utils.dates import days_ago
from airflow.providers.amazon.aws.operators.glue_crawler import AwsGlueCrawlerOperator
from airflow.providers.amazon.aws.operators.glue import AwsGlueJobOperator
from airflow import DAG
from airflow.operators.python import PythonOperator


def process_anomaly_detection(**context):
    import awswrangler as wr
    import pandas as pd
    from sklearn.ensemble import IsolationForest
    import plotly.express as px
    import boto3
    from datetime import datetime, timezone    

    print("DAG INFO: Running Anomaly Detection for each Airport")
    execution_date = f"{context['execution_date']:%Y-%m-%d}"
    print(f"DAG INFO: Execution date: {execution_date}...")
    execution_year = f"{context['execution_date']:%Y}"
    print(f"DAG INFO:Execution year: {execution_year}...")

    print("DAG INFO: Begin to read agg_flights_delay_by_date_airport table from analytics.")
    df_stg_agg = wr.s3.read_parquet(
        's3://itbafl-analytics-useast1-232483837258-prd/agg-flights-delay-by-date-airport/flight_year={}/'.format(execution_year), 
        dataset=True
    )
    print("DAG INFO: End read agg_flights_delay_by_date_airport table from analytics")
    
    print("DAG INFO: Applying Column formatting...")
    df_stg_agg['flight_year']=df_stg_agg['flight_year'].astype('int32')
    df_stg_agg['flight_month']=df_stg_agg['flight_month'].astype('int32')     
    df_stg_agg['flight_date']=df_stg_agg['flight_date'].astype('datetime64[ns]')
    print(df_stg_agg.info())
    print(df_stg_agg.head(10))

    # -------------------------------
    # To prevent numpy warning in sklearn model execution:
    # WARNING - .... RuntimeWarning: invalid value encountered in true_divide
    import warnings
    warnings.filterwarnings("ignore")    
    # -------------------------------

    print("DAG INFO: Begin ML Processing --> Isolation Forest to classify anomalies")
    df_airports_results = pd.DataFrame()
    airports = df_stg_agg['origin_airport'].unique()
    for airport in airports:
        print('DAG INFO: Isolation Forest running for Airport: {}'.format(airport))
        df_airport = df_stg_agg[df_stg_agg['origin_airport']==airport].copy()
        model_isf = IsolationForest(contamination=float(0.05))
        model_isf.fit(df_airport[['avg_dep_delay_time']])
        df_airport['score']=model_isf.decision_function(df_airport[['avg_dep_delay_time']])
        df_airport['outlier']=pd.Series(model_isf.predict(df_airport[['avg_dep_delay_time']])).apply(lambda x: 'yes' if (x == -1) else 'no' ).values
        df_airports_results = pd.concat([df_airports_results, df_airport])
    print(f"DAG INFO: {len(df_airports_results)} processed records")
    print(df_airports_results.head(10))
    # print("DAG INFO: Outliers:")
    # print(df_airports_results[df_airports_results['outlier']=='yes'])
    print("DAG INFO: End ML Processing")

    print("DAG INFO: Adding columns and applying formatting...")
    df_airports_results['date_time_dag_run'] = datetime.now(timezone.utc) # Used to validate consistency
    df_airports_results['outlier']=df_airports_results['outlier'].astype('string')
    print(df_airports_results.info())

    print("DAG INFO: Begin to store resulting data frame with anomaly columns into Redshift...")
    redshift_con = wr.redshift.connect("Redshift-DW") # From Glue connections catalog.
    tmp_awsdatawrangler_path = 's3://itbafl-temp-useast1-232483837258-prd/aws-data-wrangler/'
    wr.redshift.copy(
        df=df_airports_results,
        path=tmp_awsdatawrangler_path,
        con=redshift_con,
        schema="dw",
        table="airports_departure_anomalies",
        mode="upsert",
        primary_keys=['flight_date','origin_airport']
    )
    redshift_con.close()
    print("DAG INFO: Resulting data frame with anomaly columns stored in Redshift...")

    print("DAG INFO: Begin report generation for each airport and upload to S3 reports bucket")
    for airport in airports:
        airport_df = df_airports_results[df_airports_results['origin_airport']==airport]
        print('DAG INFO: Generating {} anual report for airport {} '.format(execution_year, airport))
        fig = px.scatter(
            airport_df.reset_index(), 
            x='flight_date', 
            y='avg_dep_delay_time', 
            color='outlier', 
            color_discrete_map={"no": 'blue', "yes": 'red'},
            labels={
                "flight_date":"flight date",
                "avg_dep_delay_time":"avg departure delay time",
                "outlier":"outlier"
                },
            title='{} anual report for airport {}'.format(execution_year, airport)
        )        
        print('DAG INFO: Uploading {} anual report for airport {} '.format(execution_year, airport))
        img_bytes = fig.to_image(format="png")
        s3 = boto3.resource('s3')
        bucket = s3.Bucket('itbafl-reports-useast1-232483837258-prd')
        key = 'us_flights_reports/{}/{}/anual_report.png'.format(execution_year,airport)
        bucket.put_object(Body=img_bytes, ContentType='image/png', Key=key)
    print("DAG INFO: Ended Report generation for each airport and upload to S3 Reports bucket")
    print("DAG INFO: Anomaly Detection process ended successfully")


default_args = {  
    'owner': 'dataengineer',
    'start_date': dt.datetime(2009, 1, 1), 
    'end_date': dt.datetime(2018, 11, 1),
}

dag = DAG(  
    'aws_etl_dag',
    default_args=default_args,
    max_active_runs=1,
    catchup=True,
    schedule_interval='@yearly'
)

glue_crawler_raw_us_flights = AwsGlueCrawlerOperator(
    task_id="crawler_raw_flights",
    config={"Name": "raw-us-flights-airline-delay-cancellation-crawler"},
    dag=dag)

glue_task_raw_to_stage_us_flights = AwsGlueJobOperator(  
    task_id="task_raw_to_stage_flights",  
    job_name='raw_to_stage_us_flights_airline_delay_cancellation',  
    iam_role_name='AWSGlueServiceRoleDefault',
    script_args = {"--ptn_year":"{{ execution_date.year }}"},
    dag=dag) 

glue_crawler_stage_us_flights = AwsGlueCrawlerOperator(
    task_id="crawler_stage_flights",
    config={"Name": "stage-us-flights-airline-delay-cancellation-crawler"},
    dag=dag)

glue_task_stage_to_analytics_agg_flights_delay_by_date_airport = AwsGlueJobOperator(  
    task_id="task_stage_to_analytics_agg_flights",  
    job_name='stage_to_analytics_agg_flights_delay_by_date_airport',  
    iam_role_name='AWSGlueServiceRoleDefault', 
    script_args = {"--ptn_year":"{{ execution_date.year }}"}, 
    dag=dag) 

glue_crawler_agg_flights_delay_by_date_airport = AwsGlueCrawlerOperator(
    task_id="crawler_agg_flights",
    config={"Name": "analytics-agg-flights-delay-by-date-airport-crawler"},
    dag=dag)

process_anomaly_detection = PythonOperator(
    task_id = 'process_anomaly_detection',
    python_callable = process_anomaly_detection,
    dag = dag
)

glue_crawler_raw_us_flights >> glue_task_raw_to_stage_us_flights >> glue_crawler_stage_us_flights >> glue_task_stage_to_analytics_agg_flights_delay_by_date_airport >> glue_crawler_agg_flights_delay_by_date_airport >> process_anomaly_detection