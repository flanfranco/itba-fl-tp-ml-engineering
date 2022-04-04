create external schema spectrum_stage
from data catalog
database 'stage'
region 'us-east-1' 
iam_role 'arn:aws:iam::232483837258:role/AWSRedshiftServiceRoleDefault';
