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
* implementar Airflow en EKS, en vez de MWAA analizando tiempo y recursos asociados a mantener en EKS el ambiente de Airflow con alta disponibilidad, auto escalado, etc 
* utilizar EMR, en vez de Glue


### Arquitectura

![Image of the data architecture](https://raw.githubusercontent.com/flanfranco/itba-fl-tp-ml-engineering/main/docs/img/01_architecture.png) 

### Flujo de procesamiento de datos

![Image of the data architecture](https://raw.githubusercontent.com/flanfranco/itba-fl-tp-ml-engineering/main/docs/img/02_flow.png) 

👨🏽‍💻 Flavio Lanfranco
