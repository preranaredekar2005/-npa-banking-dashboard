# NPA Banking Intelligence Dashboard

A Streamlit dashboard for the academic project **Analysis of Non-Performing Assets (NPAs) in Indian Public and Private Sector Banks**.

## Included files
- `app.py` — dashboard application
- `requirements.txt` — Python packages
- `NPA_Banking_Sector_India_Dataset (1).xlsx` — workbook used by the dashboard

## Run locally (Windows)
1. Install Python 3.10 or later.
2. Extract this folder.
3. Open the folder in VS Code.
4. Open Terminal in VS Code and run:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   streamlit run app.py
   ```

5. Streamlit will show a local URL, normally `http://localhost:8501`.

## Publish a public URL with Streamlit Community Cloud
1. Sign in to GitHub and create a **new public repository**, for example `npa-banking-dashboard`.
2. Upload `app.py`, `requirements.txt`, and the Excel workbook to the repository's root folder.
3. Visit https://share.streamlit.io/ and sign in using GitHub.
4. Select **Create app** (or **Deploy an app**), choose your repository, branch (usually `main`), and main file path `app.py`.
5. Deploy. Wait for the build to finish. Streamlit will provide a public `*.streamlit.app` URL.
6. Open the URL in an incognito/private browser window to verify that it is publicly accessible.

## Important
- Keep the workbook filename exactly as shown, or update `DATA_FILE` near the top of `app.py`.
- A public GitHub repository makes the dataset publicly downloadable too. Only publish it if you have permission to share the workbook.
- This is a static academic dataset dashboard; it does not fetch live RBI/bank data.
- The dashboard calculates sector NPA ratios as aggregated sector NPA divided by aggregated sector exposure, multiplied by 100. KPI cards show simple averages of the selected bank-year records.
