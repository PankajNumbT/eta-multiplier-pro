# Deployment checklist

## GitHub

- [ ] `app.py` is in the repository root.
- [ ] `requirements.txt` is in the repository root.
- [ ] `.streamlit/config.toml` is committed.
- [ ] `packages.txt` is committed if native LaTeX compilation is desired.
- [ ] No `.streamlit/secrets.toml`, database file, password, or token is committed.

## Streamlit Community Cloud

- [ ] Main file path is `app.py`.
- [ ] Build completes without a missing-package error.
- [ ] Home page opens.
- [ ] `1/f_1` returns `1,1,2,3,5,7,...`.
- [ ] The verified identity library reports 22 passing identities.
- [ ] The ten-section manual opens and its PDF downloads.
- [ ] If TeX installation is too heavy, remove `packages.txt` and redeploy; the fallback PDF remains available.

## Docker Compose

- [ ] `docker compose up --build` completes.
- [ ] `http://localhost:8501/_stcore/health` returns `ok`.
- [ ] `http://localhost:8000/health` returns JSON with status `ok`.
- [ ] `http://localhost:8000/docs` opens the API documentation.
- [ ] The `ramanujan-data` volume is present for identity persistence.

## Public deployment

- [ ] HTTPS is enabled by the host or reverse proxy.
- [ ] Coefficient and branch limits are appropriate for available memory.
- [ ] The identity-vault persistence warning is understood.
- [ ] External OEIS and Sage requests are clearly optional.
- [ ] A backup/export policy exists for saved identities.
