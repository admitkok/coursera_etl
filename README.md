# Coursera ETL Pipeline

This pipeline extracts Data Science courses from Coursera API, transforms the data, and loads it to BigQuery and GCS.

## Deployment

1. **Prerequisites**:
   - Google Cloud Project
   - Existing GCS bucket: `chess_hs_bucket-1`
   - Enabled APIs: Cloud Run, BigQuery, Cloud Storage

2. **Deploy**:
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```

3. **Schedule**:
   ```bash
   gcloud scheduler jobs create http coursera-etl-daily \
     --schedule="0 2 * * *" \
     --uri="$(gcloud run services describe coursera-etl --format 'value(status.url)')" \
     --http-method=GET \
     --oidc-service-account-email=$(gcloud config get-value account)
   ```

## GitHub Integration

1. Connect your repository to Cloud Build
2. Push changes to trigger automatic deployments# coursera_etl
