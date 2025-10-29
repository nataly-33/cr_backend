import boto3
from botocore.exceptions import ClientError
import os
from decouple import config

def create_s3_bucket():
    """Crea el bucket S3 si no existe"""
    
    # Configuración
    bucket_name = config('AWS_STORAGE_BUCKET_NAME')
    region = config('AWS_S3_REGION_NAME', default='us-east-1')
    
    s3_client = boto3.client(
        's3',
        aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'),
        region_name=region
    )
    
    try:
        # Crear bucket
        if region == 'us-east-1':
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        
        print(f"✅ Bucket '{bucket_name}' creado exitosamente")
        
        # Configurar encriptación
        s3_client.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                'Rules': [
                    {
                        'ApplyServerSideEncryptionByDefault': {
                            'SSEAlgorithm': 'AES256'
                        }
                    }
                ]
            }
        )
        print("✅ Encriptación configurada")
        
        # Bloquear acceso público
        s3_client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        print("✅ Acceso público bloqueado")
        
        # Configurar versionamiento
        s3_client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        print("✅ Versionamiento habilitado")
        
        # Configurar lifecycle para archivos temporales
        s3_client.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration={
                'Rules': [
                    {
                        'Id': 'DeleteOldVersions',
                        'Status': 'Enabled',
                        'NoncurrentVersionExpiration': {
                            'NoncurrentDays': 90
                        },
                        'Prefix': ''
                    }
                ]
            }
        )
        print("✅ Lifecycle policy configurada")
        
        print(f"\n🎉 Bucket S3 configurado completamente: {bucket_name}")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            print(f"⚠️  El bucket '{bucket_name}' ya existe y te pertenece")
        elif e.response['Error']['Code'] == 'BucketAlreadyExists':
            print(f"❌ El bucket '{bucket_name}' ya existe y pertenece a otra cuenta")
        else:
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    create_s3_bucket()