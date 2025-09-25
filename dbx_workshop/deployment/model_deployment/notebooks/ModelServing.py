# Databricks notebook source
##################################################################################
# Helper notebook to transition the model stage. This notebook is run
# after the Train.py notebook as part of a multi-task job, in order to transition model
# to target stage after training completes.
#
# Note that we deploy the model to the stage in MLflow Model Registry equivalent to the
# environment in which the multi-task job is executed (e.g deploy the trained model to
# stage=Production if triggered in the prod environment). In a practical setting, we would
# recommend enabling the model validation step between  model training and automatically
# registering the model to the Production stage in prod.
#
# This notebook has the following parameters:
#
#  * env (required)  - String name of the current environment for model deployment, which decides the target stage.
#  * model_uri (required)  - URI of the model to deploy. Must be in the format "models:/<name>/<version-id>", as described in
#                            https://www.mlflow.org/docs/latest/model-registry.html#fetching-an-mlflow-model-from-the-model-registry
#                            This parameter is read as a task value
#                            (https://learn.microsoft.com/azure/databricks/dev-tools/databricks-utils),
#                            rather than as a notebook widget. That is, we assume a preceding task (the Train.py
#                            notebook) has set a task value with key "model_uri".
##################################################################################

# COMMAND ----------

# MAGIC %pip install -r ../../../requirements.txt

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# List of input args needed to run the notebook as a job.
# Provide them via DB widgets or notebook arguments.
#
# Name of the current environment
dbutils.widgets.dropdown("env", "None", ["None", "staging", "prod"], "Environment Name")
dbutils.widgets.text("endpoint_name", "", label="Input Serving endpoint name")
dbutils.widgets.text("model_name", "dev.dbx_workshop.dbx_workshop-model", label="Full (Three-Level) Model Name")
dbutils.widgets.dropdown("workload_size", "Small", ["Small", "Medium", "Large"], "Input workload_size")
dbutils.widgets.text("workload_type", "CPU", label="Input workload_type")
dbutils.widgets.text("scale_to_zero_enabled", "", label="Enable Scale to zero")
dbutils.widgets.text("serve_model", "", label="Do you want to serve model?")

# COMMAND ----------

run_mode = dbutils.widgets.get("serve_model").lower()
assert run_mode == "false" or run_mode == "true"

if run_mode == "false":
    print(
        "Model Serving is in DISABLED mode. Exit model serving without blocking"
    )
    dbutils.notebook.exit(0)

# COMMAND ----------

# DBTITLE 1,Define input and output variables
env = dbutils.widgets.get("env")
endpoint_name = dbutils.widgets.get("endpoint_name")
model_name = dbutils.widgets.get("model_name")
workload_size = dbutils.widgets.get("workload_size")
workload_type = dbutils.widgets.get("workload_type")
scale_to_zero_enabled = True if dbutils.widgets.get("scale_to_zero_enabled") == "true" else False
alias = "champion"
model_uri = f"models:/{model_name}@{alias}"
catalog_name, schema_name, served_model_name = model_name.split('.')
inferance_log_table = f"{endpoint_name}_{model_name}_inference_log"

# COMMAND ----------
import os
import sys
from mlflow.deployments import get_deploy_client
from mlflow import MlflowClient

notebook_path =  '/Workspace/' + os.path.dirname(dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())
%cd $notebook_path
%cd ..
sys.path.append("../..")

# COMMAND ----------
# Get model version from alias
client = MlflowClient(registry_uri="databricks-uc")
model_version = client.get_model_version_by_alias(model_name, alias).version
served_model_name = f"{served_model_name}-{model_version}"
deploy_client = get_deploy_client("databricks")
endpoint = deploy_client.create_endpoint(
    name=endpoint_name,
    config={
        "served_entities": [
            {
                "entity_name": #TODO <ADD-Model-Name>,
                "entity_version": model_version,
                "workload_size": #TODO <add workload-size>,
                "workload_type" : workload_type,
                "scale_to_zero_enabled": scale_to_zero_enabled
            }
        ],
        "traffic_config": {
            "routes": [
                {
                    "served_model_name": #TODO <Add served model name>,
                    "traffic_percentage": #TODO <Add traffic percentage>
                }
            ]
        },
        "auto_capture_config": {
            "catalog_name": catalog_name,
            "schema_name": schema_name,
            "table_name_prefix": inferance_log_table
        }
    }
)
