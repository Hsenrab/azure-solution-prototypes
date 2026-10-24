from pathlib import Path
import shutil
from collections.abc import Mapping
from uuid import UUID


def resolve_az_cli() -> str | None:
    """Return the Azure CLI executable path visible to the notebook kernel."""
    az_in_path = shutil.which("az")
    if az_in_path:
        return az_in_path

    windows_fallbacks = [
        Path(r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"),
        Path(r"C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"),
    ]
    for candidate in windows_fallbacks:
        if candidate.exists():
            return str(candidate)

    return None


ENV_OUTPUTS = {
    "AZURE_SUBSCRIPTION_ID": "subscriptionId",
    "AZURE_TENANT_ID": "tenantId",
    "AZURE_RESOURCE_GROUP": "resourceGroupName",
    "AZURE_RESOURCE_GROUP_ID": "resourceGroupId",
    "AZURE_LOCATION": "location",
    "AZURE_SEARCH_SERVICE_NAME": "searchServiceName",
    "AZURE_SEARCH_RESOURCE_ID": "searchResourceId",
    "AZURE_SEARCH_ENDPOINT": "searchEndpoint",
    "AZURE_OPERATOR_OBJECT_ID": "operatorObjectId",
}


def validate_environment(
    values: Mapping[str, str | None],
    *,
    subscription_id: str,
    tenant_id: str,
    resource_group: str,
    operator_object_id: str,
) -> dict[str, str]:
    """Validate the non-secret contract against the explicitly selected CLI user."""
    environment: dict[str, str] = {}
    for key in ENV_OUTPUTS:
        value = values[key]
        if not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value:
            raise ValueError(f"Missing or invalid environment value: {key}")
        environment[key] = value

    for key, expected in (
        ("AZURE_SUBSCRIPTION_ID", subscription_id),
        ("AZURE_TENANT_ID", tenant_id),
        ("AZURE_OPERATOR_OBJECT_ID", operator_object_id),
    ):
        if UUID(environment[key]) != UUID(expected):
            raise ValueError(f"Environment does not match the selected CLI context: {key}")

    group_id = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
    service_name = environment["AZURE_SEARCH_SERVICE_NAME"]
    service_id = f"{group_id}/providers/Microsoft.Search/searchServices/{service_name}"
    expected_values = {
        "AZURE_RESOURCE_GROUP": resource_group,
        "AZURE_RESOURCE_GROUP_ID": group_id,
        "AZURE_LOCATION": "northeurope",
        "AZURE_SEARCH_RESOURCE_ID": service_id,
        "AZURE_SEARCH_ENDPOINT": f"https://{service_name}.search.windows.net",
    }
    for key, expected in expected_values.items():
        if environment[key].casefold() != expected.casefold():
            raise ValueError(f"Inconsistent environment value: {key}")
    if not service_name or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in service_name):
        raise ValueError("Invalid Search service name")
    return environment


def environment_from_outputs(
    outputs: Mapping[str, object],
    *,
    subscription_id: str,
    tenant_id: str,
    resource_group: str,
    operator_object_id: str,
) -> dict[str, str]:
    """Extract only the nine declared outputs; never synthesize missing values."""
    values: dict[str, str] = {}
    for key, name in ENV_OUTPUTS.items():
        output = outputs[name]
        if not isinstance(output, Mapping):
            raise ValueError(f"Invalid deployment output: {name}")
        value = output["value"]
        if not isinstance(value, str):
            raise ValueError(f"Invalid deployment output value: {name}")
        values[key] = value
    return validate_environment(
        values,
        subscription_id=subscription_id,
        tenant_id=tenant_id,
        resource_group=resource_group,
        operator_object_id=operator_object_id,
    )
