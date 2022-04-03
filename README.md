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
* el despligue de un Gateway Endpoint para comunicar Redsfhit con S3 de manera privada.

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

### Reportes de ejemplo

A continuación se muestran algunas capturas correspondientes a los reportes generados por el dag. En algunos casos pueden denotarse rápidamente faltante de datos (raw) (julio 2011 y octubre 2009 por ej.):

![Image of 2009 report](https://raw.githubusercontent.com/flanfranco/itba-fl-tp-ml-engineering/main/aws-deploy/reports_example/2009_CSG_anual_report.png) 

![Image of 2011 report](https://raw.githubusercontent.com/flanfranco/itba-fl-tp-ml-engineering/main/aws-deploy/reports_example/2011_LAX_anual_report.png) 

![Image of 2014 report](https://raw.githubusercontent.com/flanfranco/itba-fl-tp-ml-engineering/main/aws-deploy/reports_example/2014_DAL_anual_report.png) 

![Image of 20184 report](https://raw.githubusercontent.com/flanfranco/itba-fl-tp-ml-engineering/main/aws-deploy/reports_example/2018_ABE_anual_report.png) 


### Capturas del Dasboard Quicksight


### Detalle del despliegue


👨🏽‍💻 Flavio Lanfranco
