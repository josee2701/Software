import os

from storages.backends.azure_storage import AzureStorage


class AzureMediaStorage(AzureStorage):
    account_name = os.environ.get(
        "AZURE_ACCOUNT_NAME"
    )  # Must be replaced by your <storage_account_name>
    account_key = os.environ.get(
        "AZURE_ACCOUNT_KEY"
    )  # Must be replaced by your <storage_account_key>
    azure_container = "media"
    expiration_secs = None
    overwrite_files = True


class AzureStaticStorage(AzureStorage):
    account_name = os.environ.get(
        "AZURE_ACCOUNT_NAME"
    )  # Must be replaced by your storage_account_name
    account_key = os.environ.get(
        "AZURE_ACCOUNT_KEY"
    )  # Must be replaced by your <storage_account_key>
    azure_container = "static"
    expiration_secs = None
