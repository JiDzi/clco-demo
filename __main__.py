import pulumi
from pulumi_azure_native import resources, storage, web
from pulumi import AssetArchive, FileArchive

# 1. Resource Group erstellen
resource_group = resources.ResourceGroup("resource_group")

# 2. Storage Account erstellen
account = storage.StorageAccount(
    "sa",
    resource_group_name=resource_group.name,
    sku={"name": storage.SkuName.STANDARD_LRS},
    kind=storage.Kind.STORAGE_V2,
    allow_blob_public_access=True,  # Enable public access at the storage account level
)

# 3. Storage Container für den Blob erstellen
storage_container = storage.BlobContainer(
    "zip-container",
    resource_group_name=resource_group.name,
    account_name=account.name,
    public_access=storage.PublicAccess.CONTAINER,  # Enable public access
)

# 4. Lokale Dateien in ein AssetArchive packen (Quellcode ZIP)
archive = AssetArchive({
    ".": FileArchive(".")  # Lokaler Ordner der Anwendung
})


# 5. ZIP-Archiv in den Blob hochladen
blob = storage.Blob(
    "app-zip-blob",
    resource_group_name=resource_group.name,
    account_name=account.name,
    container_name=storage_container.name,
    type=storage.BlobType.BLOCK,
    source=archive,  # Hier wird das Archiv hochgeladen
    content_type="application/zip",
)

# 6. SAS-URL (Signierte URL) für den Blob generieren
blob_url = pulumi.Output.concat(
    "https://", account.name, ".blob.core.windows.net/",
    storage_container.name, "/", blob.name
)

# 7. App Service Plan erstellen
app_service_plan = web.AppServicePlan(
    "app-service-plan",
    resource_group_name=resource_group.name,
    location=resource_group.location,
    sku=web.SkuDescriptionArgs(
        tier="Basic",
        name="B1",  # Hosting-Plan
    ),
)

# 8. Web App erstellen und Blob als Quellcode referenzieren
web_app = web.WebApp(
    "web-app",
    resource_group_name=resource_group.name,
    location=resource_group.location,
    server_farm_id=app_service_plan.id,
    site_config=web.SiteConfigArgs(
        app_settings=[
            web.NameValuePairArgs(name="WEBSITES_ENABLE_APP_SERVICE_STORAGE", value="true"),  # Ermöglicht Dateizugriff
        ],
    ),
)

# 9. Exportiere die Ergebnisse
pulumi.export("app_url", pulumi.Output.concat("http://", web_app.default_host_name))
pulumi.export("blob_url", blob_url)