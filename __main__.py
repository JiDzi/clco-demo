"""An Azure RM Python Pulumi program"""

import pulumi
from pulumi_azure_native import storage, resources, web
from pulumi import AssetArchive, FileAsset

# Create an Azure Resource Group
resource_group = resources.ResourceGroup("resource_group")

# Create an Azure resource (Storage Account)
account = storage.StorageAccount(
    "sa",
    resource_group_name=resource_group.name,
    sku={
        "name": storage.SkuName.STANDARD_LRS,
    },
    kind=storage.Kind.STORAGE_V2,
)

# Storage Container für den Blob erstellen
storage_container = storage.BlobContainer(
    "zip-container",
    resource_group_name=resource_group.name,
    account_name=account.name,
)

# Lokale Dateien in ein AssetArchive packen (Quellcode ZIP)
archive = AssetArchive({
    ".": FileAsset("./app.py")  # Lokaler Ordner der Anwendung
})

# ZIP-Archiv in den Blob hochladen
blob = storage.Blob(
    "app-zip-blob",
    resource_group_name=resource_group.name,
    account_name=account.name,
    container_name=storage_container.name,
    type=storage.BlobType.BLOCK,
    source=archive,  # Hier wird das Archiv hochgeladen
)

# SAS-URL (Signierte URL) für den Blob generieren
blob_url = pulumi.Output.concat(
    "https://", account.name, ".blob.core.windows.net/",
    storage_container.name, "/", blob.name
)

# App Service Plan erstellen
app_service_plan = web.AppServicePlan(
    "app-service-plan",
    resource_group_name=resource_group.name,
    location=resource_group.location,
    sku=web.SkuDescriptionArgs(
        tier="Basic",
        name="B1",  # Hosting-Plan
    ),
)

# Web App erstellen und Blob als Quellcode referenzieren
web_app = web.WebApp(
    "web-app",
    resource_group_name=resource_group.name,
    location=resource_group.location,
    server_farm_id=app_service_plan.id,
    site_config=web.SiteConfigArgs(
        app_settings=[
            web.NameValuePairArgs(
                name="WEBSITE_RUN_FROM_PACKAGE",
                value=blob_url,  # Verweist auf das ZIP-Archiv im Blob
            ),
        ],
    ),
)



# Export the primary key of the Storage Account
primary_key = (
    pulumi.Output.all(resource_group.name, account.name)
    .apply(
        lambda args: storage.list_storage_account_keys(
            resource_group_name=args[0], account_name=args[1]
        )
    )
    .apply(lambda accountKeys: accountKeys.keys[0].value)
)

pulumi.export("primary_storage_key", primary_key)
pulumi.export("web_app_url", pulumi.Output.concat("https://", web_app.default_host_name))
pulumi.export("blob_url", blob_url)