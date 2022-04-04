# Trabajo Práctico Final
### ML Engineering

Bienvenido al TP Final de la [Diplomatura en Cloud Data Engineering del ITBA](https://innovacion.itba.edu.ar/educacion-ejecutiva/tic/cloud-data-engineering/).

### Descripción del requerimiento:

Se solicita crear un DAG de Airflow que actúe de ETL utilizando el dataset de [demoras y cancelaciones de viajes aéreos](https://www.kaggle.com/datasets/yuanyuwendymu/airline-delay-and-cancellation-data-2009-2018) siguiendo los [requerimientos detallados por la cátedra](https://github.com/flanfranco/itba-fl-tp-ml-engineering/blob/main/docs/%5BRFC%5D%20Trabajo%20Pr%C3%A1ctico%20Final.pdf).

### Objetivo:

Poner en práctica los conocimientos adquiridos a lo largo del cursado de la [diplomatura](https://innovacion.itba.edu.ar/educacion-ejecutiva/tic/cloud-data-engineering/): 

* Módulo 1: AWS Cloud Architecture
* Módulo 2: Python Data Applications
* Módulo 3: Machine Learning Engineering


## Resolución

### Descripción

Se propone resolver los [requerimientos](https://github.com/flanfranco/itba-fl-tp-ml-engineering/blob/main/docs/%5BRFC%5D%20Trabajo%20Pr%C3%A1ctico%20Final.pdf) implementando una arquitectura del tipo [lake house](https://aws.amazon.com/blogs/big-data/build-a-lake-house-architecture-on-aws/) en AWS. Para tal fin se van a utilizar los siguientes servicios:
* MWAA (Amazon Managed Workflows for Apache Airflow) para orquestar la ejecución de las tareas de extracción, transformación y carga de datos (ETL).
* S3 como datalake
* Glue para procesar y transformar los datos.
* Glue Data Catalog como catálogo de datos de la solución.
* Redshift Spectrum como DW con la posibilidad de consumir tablas "externas" del datalake (lake house).
* QuickSight para exponer de manera visual los datos procesados.
* Athena para poder analizar tablas del datalake.
* IAM para gestionar los roles y permisos relacionados a los servicios enunciados.
* VPC y servicios relacionados para poder desplegar todo el newtorking de la solución.

La solución tiene el objetivo de poner en práctica (de manera introductoria) el despligue en AWS de una arquitectura productiva de procesamiento de datos moderna, escalable, robusta y segura, mostrando: 

* la utilización de un datalake como repositorio de datos escalable
* la utilización de spark para procesar grandes volúmenes de datos
* la posibilidad de combinar tablas de un schema de DW agregadas con tablas externas (del datalake) al máximo nivel de detalle.

Notas: Es necesario tener en cuenta la variable costo ya que en un despligue productivo real sería conveniente analizar en detalle:
* implementar Airflow en EKS, en vez de MWAA. Analizando tiempo y recursos asociados a mantener en EKS el ambiente de Airflow con alta disponibilidad, auto escalado, etc... (como lo ofrece MWAA) 
* utilizar EMR, en vez de Glue


### Arquitectura

![Image of the data architecture](https://raw.githubusercontent.com/flanfranco/itba-fl-tp-ml-engineering/main/docs/img/01_aws_architecture.png) 

La arquitectura principalmente expone:
* el despliegue del ambiente de MWAA [creando una VPC y sus componentes](https://docs.aws.amazon.com/mwaa/latest/userguide/vpc-create.html#vpc-create-template-private-or-public) a través de un [stack de CloudFormation](https://docs.aws.amazon.com/mwaa/latest/userguide/samples/cfn-vpc-public-private.zip) proporcionado por AWS.
* el despligue de una subnet group en las subnets privadas de la VPC anteriormente creada.
* el despliegue de un cluster de Redshift en la subnet group anteriormente creada.
* el despligue de un Gateway Endpoint para comunicar Redshift con S3 de manera privada.

### Flujo de procesamiento de datos

A continuación se presenta el flujo del procesamiento de datos basado en la ejecución del [DAG desarrollado](https://github.com/flanfranco/itba-fl-tp-ml-engineering/blob/main/aws-deploy/mwaa/dags/aws_etl_dag.py):

![Image of the data flow](https://raw.githubusercontent.com/flanfranco/itba-fl-tp-ml-engineering/main/docs/img/02_flow.png) 

![Image of the airflow dag](https://raw.githubusercontent.com/flanfranco/itba-fl-tp-ml-engineering/main/docs/img/03_airflow_aws_etl_dag.png) 

A continuación se detalla la estructura de buckets desplegada:

![Image of buckets](https://raw.githubusercontent.com/flanfranco/itba-fl-tp-ml-engineering/main/docs/img/07_s3_buckets.png) 

* itbafl-**airflow**-useast1-232483837258-prd: bucket correspondiente al despliegue del ambiente de MWAA. El mismo almacena los dags, plugins y requirements con configuraciones.
* itbafl-**raw**-useast1-232483837258-prd: bucket del datalake correspondiente a almacenar los datos en su formato original (csv, json, etc.) para luego ser procesados.
* itbafl-**stage**-useast1-232483837258-prd: bucket del datalake correspondiente a almacenar en formato parquet (y con particionado) los datos originales transformados y procesados con lógica de negocio (aplicando filtros, joins, etc.).
* itbafl-**analytics**-useast1-232483837258-prd: bucket del datalake correspondiente a almacenar en formato parquet (y con particionado) datos agregados y depurados para que sean consumidos por usuarios de análisis o para su posterior carga en el DW.
* itbafl-**reports**-useast1-232483837258-prd: bucket correspondiente al almacenamiento de reportes generados como resultado de la ejecución de los dags de procesamiento de datos.
* itbafl-**scripts**-useast1-232483837258-prd: bucket donde se almacenan los scripts correspondientes a los servicios de procesamientos de datos utilizados en la arquitectura desplegada. En este caso los scripts de pyspark (AWS Glue).
* itbafl-**logs**-useast1-232483837258-prd: bucket donde se depositan los logs resultantes de los servicios de procesamientos de datos utilizados en la arquitectura desplegada.
* itbafl-**temp**-useast1-232483837258-prd: bucket donde se depositan temporalmente los resultados de la utilización de los servicios de la arquitectura desplegada, como por ejemplo las queries resultantes de Athena, o los parquets temporales resultantes de utilizar [AWS Data Wrangler](https://github.com/awslabs/aws-data-wrangler).

En referencia a los **scripts de pyspark** responsables de transformar los datos a través de la ejecución de tareas de Glue es importante remarcar:

* Script [raw --> stage](https://github.com/flanfranco/itba-fl-tp-ml-engineering/blob/main/aws-deploy/scripts/glue/raw_to_stage_us_flights_airline_delay_cancellation.py):
- recibe como parámetro el año de procesamiento (ptn_year).
- en base al mismo realiza un push_down_predicate filtrando solo lo relacionado a ese año en la data fuente (raw).
- tiene configurado "spark.conf.set("spark.sql.sources.partitionOverwriteMode","dynamic")" para poder "pisar" particiones preexistentes.  
- almacena los datos en parquet particionados por ptn_year.

* Script [stage --> analytics](https://github.com/flanfranco/itba-fl-tp-ml-engineering/blob/main/aws-deploy/scripts/glue/stage_to_analytics_agg_flights_delay_by_date_airport.py):
- recibe como parámetro el año de procesamiento (ptn_year).
- en base al mismo realiza un push_down_predicate filtrando solo lo relacionado a ese año en la data input (stage).
- tiene configurado "spark.conf.set("spark.sql.sources.partitionOverwriteMode","dynamic")" para poder "pisar" particiones preexistentes.  
- aplica lógica de negocio para filtrar vuelos que no han sido cancelados y que tengan valor en los campos fl_date, origin y dep_delay.
- aplica una agregación por fl_date y origin.
- suma 2 campos (año y mes) y renombra columnas.
- almacena los datos en parquet particionados por flight_year, flight_month, y flight_date.

En referencia a la tarea [process_anomaly_detection](https://github.com/flanfranco/itba-fl-tp-ml-engineering/blob/bd350a8a67e0ab906a69b084ae0c4d8a9320bed1/aws-deploy/mwaa/dags/aws_etl_dag.py#L9) perteneciente al [dag aws_etl_dag](https://github.com/flanfranco/itba-fl-tp-ml-engineering/blob/main/aws-deploy/mwaa/dags/aws_etl_dag.py) la misma consta de 4 partes importantes:
* La primera parte se encarga de leer los datos correspondientes a la fuente previamente agregada para el año ejecutado en la recarga. Para esto se utiliza el método s3.read_parquet de la librería awswrangler.
* La segunda parte es la encargada de aplicar el algoritmo de detección de anomalias (sklearn --> Isolation Forest) y generar un dataframe con el cálculo del modelo para cada aeropuerto.
* La tercera parte es la encargada de persistir ese dataframe en el DW utilizando nuevamente la librería awswrangler pero ahora con el método wr.redshift.copy que lo que hace es generar en el bucket temporal un archivo parquet y persistirlo con el comando COPY en el DW. Esta inserción el DW se trabaja con el modo "upsert" para no generar duplicados ante un reprocesamiento.
* La última parte es la encargada de generar los reportes por aeropuerto y almacenarlos en el bucket de reportes.

Nota: Sería conveniente utilizar Airflow solamente como orquestador y no como procesamiento. En base a esto en una próxima iteración sería recomendable llevar el procesamiento del Modelo de ML a SageMaker o ECS/EKS, y abrir las otras partes en otras tareas.


### Reportes de ejemplo

A continuación se muestran algunas capturas correspondientes a los reportes generados por el dag. En algunos casos pueden denotarse rápidamente faltante de datos (raw) (julio 2011 y octubre 2009 por ej.):

![Image of 2009 report](https://raw.githubusercontent.com/flanfranco/itba-fl-tp-ml-engineering/main/aws-deploy/reports_example/2009_CSG_anual_report.png) 

![Image of 2011 report](https://raw.githubusercontent.com/flanfranco/itba-fl-tp-ml-engineering/main/aws-deploy/reports_example/2011_LAX_anual_report.png) 

![Image of 2014 report](https://raw.githubusercontent.com/flanfranco/itba-fl-tp-ml-engineering/main/aws-deploy/reports_example/2014_DAL_anual_report.png) 

![Image of 2018 report](https://raw.githubusercontent.com/flanfranco/itba-fl-tp-ml-engineering/main/aws-deploy/reports_example/2018_ABE_anual_report.png) 


### Dashboard QuickSight

A continuación se muestran capturas del dashboard básico de QuickSight diseñado que busca exponer la utilización conjunta de datos agregados provenientes del DW junto a datos con máximo nivel de detalle provenientes del datalake (stage).

![Image of quicksight](https://raw.githubusercontent.com/flanfranco/itba-fl-tp-ml-engineering/main/docs/img/08_quicksight_dashboard.png) 

En la configuración del dataset de QuickSight puede verse la [query](https://github.com/flanfranco/itba-fl-tp-ml-engineering/blob/main/aws-deploy/scripts/redshift/dw_spectrum_quicksight_query.sql) utilizada para integrar el datalake con el dw de la siguiente manera:

![Image of quicksight datasource](https://raw.githubusercontent.com/flanfranco/itba-fl-tp-ml-engineering/main/docs/img/09_quicksight_datasource.png) 


### Detalle del despliegue

Antes es importante remarcar que la etapa de desarrollo de la solución se realizó en Ubuntu, configurando AWS CLI con un usuario con permisos y levantando un ambiente de airflow de desarrollo/test con docker-compose. Luego, una vez validada la solucion, se levantó el ambiente de MWAA y se desplegó el dag desarrollado en el mismo. 

A continuación se detallan los pasos necesarios para replicar la solución implementada:

1) Creación de la estructura de buckets en S3 según lo comentado anteriormente en esta guía.

En el bucket itbafl-airflow-useast1-232483837258-prd se desplegaron los [archivos compartidos](https://github.com/flanfranco/itba-fl-tp-ml-engineering/tree/main/aws-deploy/mwaa).

En el bucket itbafl-raw-useast1-232483837258-prd se organizaron los archivos fuente csv con el esquema de folders year=yyyy. Esto es para que luego se pueda ejecutar en la tarea raw --> stage el push_down_predicate sobre la partición year.

2) Despliegue del ambiente de MWAA [creando una VPC y sus componentes](https://docs.aws.amazon.com/mwaa/latest/userguide/vpc-create.html#vpc-create-template-private-or-public) a través de un [stack de CloudFormation](https://docs.aws.amazon.com/mwaa/latest/userguide/samples/cfn-vpc-public-private.zip) proporcionado por AWS.

Nota: el "web server access" se configuró como Public network pero en caso de un despliegue formal debería optarse por private.

3) IAM Roles:
- Se modificó el role "AmazonMWAA-itbafl-airflow-environment-xxxxxx" agregándole los siguientes permisos: AmazonS3FullAccess, AWSGlueConsoleFullAccess, AmazonSageMakerFullAccess (para probar scripts spark con glue notebook de sagemaker).
- Se creó el role "AWSGlueServiceRoleDefault" agregándole los siguientes permisos: AmazonS3FullAccess, AWSGlueServiceRole.
- Se creó el role "AWSRedshiftServiceRoleDefault" agregándole los siguientes permisos: AmazonS3FullAccess, AWSGlueConsoleFullAccess.
4) Glue:
- En la sección Databases se crearon: raw, stage y analytics.
- Se crearon 3 crawlers ejecutando los estos [scripts](https://github.com/flanfranco/itba-fl-tp-ml-engineering/tree/main/aws-deploy/scripts/glue/crawlers) en CloudShell. 
- Se crearon 2 jobs de tipo spark (Glue Version 2 - Worker type G.1X - y Maximum capacity 2) donde:

-- raw_to_stage_us_flights_airline_delay_cancellation --> Script location: s3://itbafl-scripts-useast1-232483837258-prd/glue/raw_to_stage_us_flights_airline_delay_cancellation.py

-- stage_to_analytics_agg_flights_delay_by_date_airport --> Script location: s3://itbafl-scripts-useast1-232483837258-prd/glue/stage_to_analytics_agg_flights_delay_by_date_airport.py

Ambos tienen Job parameters --ptn_year.


Redshift

Quicksight
Se creó un Security Group siguiendo las [indicaciones](https://docs.aws.amazon.com/quicksight/latest/user/enabling-access-redshift.html) y luego se lo asoció al Cluster de Redshift.


👨🏽‍💻 Flavio Lanfranco
