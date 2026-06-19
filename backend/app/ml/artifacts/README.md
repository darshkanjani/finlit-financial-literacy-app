# ML artifacts

The trained `cutback_model.joblib` file is intentionally not committed in this public portfolio version.

The app can still run without it because the stress-test service falls back to rule-based defaults. To regenerate the model locally:

```bash
cd backend
python -m app.ml.cutback_model
```
