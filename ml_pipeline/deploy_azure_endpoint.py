import os
import sys
from dotenv import load_dotenv
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from azure.ai.ml.entities import (
    ManagedOnlineEndpoint,
    ManagedOnlineDeployment,
    Model
)
from azure.core.exceptions import HttpResponseError

# Cargar variables de entorno
load_dotenv()

subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
resource_group = os.getenv("AZURE_RESOURCE_GROUP")
workspace_name = os.getenv("AZURE_WORKSPACE_NAME")
model_name = os.getenv("AZURE_MODEL_NAME")
model_version = os.getenv("AZURE_MODEL_VERSION", "1")

if not all([subscription_id, resource_group, workspace_name, model_name]):
    print("[ERROR] ERROR: Faltan variables de entorno en el archivo .env")
    print("Asegúrate de definir: AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP, AZURE_WORKSPACE_NAME, AZURE_MODEL_NAME")
    sys.exit(1)

# Autenticación
try:
    print("Autenticando con Azure...")
    credential = DefaultAzureCredential()
    ml_client = MLClient(
        credential, subscription_id, resource_group, workspace_name
    )
    print("[OK] Autenticación exitosa.")
except Exception as e:
    print(f"[ERROR] ERROR al autenticar: {e}")
    sys.exit(1)

endpoint_name = "predictivo-triatlon-endpoint"

# Crear Endpoint
print(f"\n[1] Comprobando/Creando Endpoint: {endpoint_name}...")
try:
    endpoint = ManagedOnlineEndpoint(
        name=endpoint_name,
        description="Endpoint para la predicción de Triatlón Élite Masculino",
        auth_mode="key"
    )
    ml_client.begin_create_or_update(endpoint).wait()
    print("[OK] Endpoint creado o ya existía.")
except Exception as e:
    print(f"[ERROR] ERROR al crear el endpoint: {e}")
    sys.exit(1)

# Despliegue
deployment_name = "blue"
print(f"\n[2] Desplegando el modelo '{model_name}' v{model_version} al deployment '{deployment_name}'...")
print("[WAIT] Esto puede tardar entre 10 y 15 minutos (creando recursos de cómputo). Si falla por cuota, verás el error aquí abajo.")

try:
    # Asumimos que es un modelo MLflow (típico de AutoML) o que no necesita script custom
    deployment = ManagedOnlineDeployment(
        name=deployment_name,
        endpoint_name=endpoint_name,
        model=f"azureml:{model_name}:{model_version}",
        instance_type="Standard_DS2_v2", # Máquina virtual pequeña estándar para test
        instance_count=1
    )
    ml_client.begin_create_or_update(deployment).wait()
    print(f"[OK] ¡Despliegue {deployment_name} completado!")
    
    # Derivar el 100% del tráfico al nuevo despliegue
    endpoint.traffic = {deployment_name: 100}
    ml_client.begin_create_or_update(endpoint).wait()
    print("[OK] Tráfico enrutado al 100%.")
    
except HttpResponseError as e:
    print("\n[ERROR] ERROR DE AZURE DURANTE EL DESPLIEGUE:")
    print(e.message)
    print("\n💡 Si el error habla de 'QuotaExceeded', significa que la suscripción no tiene cores libres para la máquina Standard_DS2_v2.")
    sys.exit(1)
except Exception as e:
    print(f"\n[ERROR] ERROR INESPERADO: {e}")
    sys.exit(1)

# Mostrar la URL de Scoring y la Key
try:
    endpoint_result = ml_client.online_endpoints.get(endpoint_name)
    keys = ml_client.online_endpoints.get_keys(endpoint_name)
    print("\n[!] ¡TODO LISTO! [!]")
    print(f"Scoring URI: {endpoint_result.scoring_uri}")
    print(f"Primary Key: {keys.primary_key}")
except Exception as e:
    print(f"No se pudieron obtener las claves automáticamente: {e}")
