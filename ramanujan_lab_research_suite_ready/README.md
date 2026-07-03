# Ramanujan Laboratory Pro - Research Suite 5.0

A public Streamlit research environment for eta quotients, q-series, dissections, arithmetic progressions, modular-form certificates, operators, sequence identification, and reproducible reports.

## Included modules

- Automatic 2-, 3-, and 5-dissection from a verified identity library
- Coefficient-based 7- and 11-dissection components
- Composite sums/differences and deep progressions such as `a(8n+7)`
- Step-by-step identity paths and LaTeX proof exports
- Correct eta-quotient modularity, cusp-order, character, and multiplier checks
- Sturm-bound certificate for compatible integral-weight eta quotients
- `U_p`, `V_p`, integral `T_p`, half-integral `T(p^2)`, and theta operators
- Rank and crank moment generation
- Exact nullspace and LLL relation search
- Congruence mining, infinite-family pattern search, and Euler-product recognition
- Animated coefficient plots, p-adic valuations, and congruence heatmaps
- Optional OEIS lookup
- Password-protected personal identity vault with JSON export/import
- Shareable compressed analysis links
- LaTeX/PDF report studio
- Session-local background computation queue
- FastAPI companion service
- Optional SageMath bridge
- Ten-section manual inside the app, with Markdown, LaTeX, and PDF downloads

## Fastest deployment: Streamlit Community Cloud

1. Upload every file in this folder to the root of a GitHub repository.
2. Create a new app in Streamlit Community Cloud.
3. Choose the repository and branch.
4. Set the main file path to `app.py`.
5. Deploy.

`requirements.txt` installs the Python dependencies. `packages.txt` installs a LaTeX engine so the PDF compiler can typeset reports. If the cloud build is too large, remove `packages.txt`; PDF generation will still use the wrapped ReportLab fallback.

The personal identity database is stored under `RAMANUJAN_DATA_DIR`. On Streamlit Community Cloud this storage is normally ephemeral, so export the identity library JSON regularly.

## Full local deployment with Docker Compose

```bash
docker compose up --build
```

Open:

- Web app: `http://localhost:8501`
- REST API documentation: `http://localhost:8000/docs`

The Compose configuration mounts a persistent volume for the identity vault.

## Local Python launch

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## REST API

Run separately with:

```bash
uvicorn api_service:app --host 0.0.0.0 --port 8000
```

Endpoints:

- `GET /health`
- `POST /expand`
- `POST /dissect`
- `POST /congruence/check`

Example request:

```json
{
  "formula": "\\frac{1}{f_1}",
  "limit": 100
}
```

## Optional SageMath bridge

`sage_bridge.py` must run under Sage's Python environment. It exposes modular-form dimensions and Sturm bounds. A commented Sage service template is included in `docker-compose.yml` because the Sage image is large.

```bash
sage -pip install fastapi uvicorn pydantic
sage -python -m uvicorn sage_bridge:app --host 0.0.0.0 --port 8001
```

Set `SAGE_BRIDGE_URL` in the web app environment to the bridge address.

## Mathematical status labels

- **Exact identity path:** algebraic substitution from coefficient-audited identities, followed by an independent coefficient comparison.
- **Certified:** modular hypotheses and the exact Sturm bound were checked.
- **Coefficient identity/evidence:** verified only through the displayed truncation.
- **Candidate:** pattern, OEIS, Euler-product, or LLL discovery requiring a separate proof.

## Important limits

- Stored finite symbolic dissections currently cover bases 2, 3, and 5. Bases 7 and 11 always return coefficient components, but no finite eta-product formula is claimed unless one is supplied and verified.
- The background queue uses threads in the Streamlit process; it is not a durable distributed worker system.
- The identity vault is suitable for a personal or small research deployment. For institutional multiuser use, connect a managed database and established authentication provider.
- Half-integral Hecke normalizations differ in the literature. The app displays the exact convention used and exposes the effective character factors.

## Manual

The app contains a ten-section manual under **Ten-Page Manual**. Standalone copies are also included:

- `RESEARCH_MANUAL.md`
- `RESEARCH_MANUAL.tex`
- `RESEARCH_MANUAL.pdf`

## Validation

See `VALIDATION_LOG.txt` for the build tests, including all 22 stored dissection identities, composite and deep extraction tests, Sturm certification, relation finding, moments, PDF compilation, API endpoints, all 20 Streamlit routes, and a live health check.
