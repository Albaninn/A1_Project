# 🚀 Final Project: Cybersecurity Analysis with Machine Learning

[![Pt-Br](https://img.shields.io/badge/lang-pt--br-green.svg)](README.md)

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Scikit-learn](https://img.shields.io/badge/SciKit--Learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)

> Final work developed for the Special Topics in Software course.
>
> The objective of this project is a complete web application, developed in Python with Streamlit, capable of performing ingestion, processing, exploratory analysis, and Machine Learning modeling on a cybersecurity incident dataset.
>
> The application fulfills all the requirements of the work, including dynamic upload of new databases, automatic model retraining, and an interactive analytical dashboard.

---

## 🌟 Key Features

The application is divided into three main pages:

### 1. Update Database (The "Engine")

This page is the system's entry point and fulfills the requirement for "flexibility" and "dynamic retraining."

* **Flexible Upload**: Allows the upload of a new dataset in `.zip` format (containing multiple CSVs) or a single `.csv` file.
* **Smart Detection**: Automatically detects the CSV separator (comma or semicolon). (This functionality was in your original code).
* **Robust Processing**: Executes the entire ETL pipeline (defined in `backend_tasks.py`) to clean, optimize types, and save the data in a **SQLite** database (`CyberSec.db`).
* **Automatic Retraining**: After data processing, the system automatically retrains the Machine Learning model (**Random Forest Classifier**) and saves it (`modelo_classificador.pkl`) to be used in the simulator.

### 2. Exploratory Analysis (The "Dashboard")

A BI dashboard (like Power BI) built directly in Python.

* **Interactive Visualizations**: Uses **Plotly** to generate dynamic charts (choropleth map, bars, scatter, histogram).
* **KPI Metrics**: Presents a summary with the main indicators (Total Incidents, Total Loss, etc.).
* **Pattern Analysis**: Allows the strategic user (Manager, CISO) to visually identify which attacks are more expensive, more frequent, and the efficiency of the response team.

### 3. Prediction Simulator (The "ML Model")

This is the predictive tool of the system, which uses the trained model.

* **Real-Time Inference**: The user (Tactical/Operational) enters the characteristics of an *ongoing* incident.
* **Probability Prediction**: The loaded **Random Forest** model (`.pkl`) predicts not only the most likely type of attack but the **probability distribution** (e.g., 40% SQL Injection, 21% Ransomware).
* **Decision Support**: Helps the incident response team to **prioritize actions** (moving from a Reactive to a Proactive posture) and trigger the correct team.

---

## 🛠️ Technologies Used

* **Python 3.10+**
* **Streamlit**: For building the web interface (frontend).
* **Pandas**: For data manipulation and processing (ETL).
* **Scikit-learn**: For the entire Machine Learning pipeline (Feature Engineering, Training, `RandomForestClassifier`).
* **Plotly Express**: For creating interactive charts.
* **Joblib**: For saving and loading the trained ML model (`.pkl`).
* **SQLite**: (Native to Python) For storing processed data in an optimized way.

---

## ⚙️ How to Run the Project Locally

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
    cd seu-repositorio
    ```

2.  **Create a virtual environment (Recommended):**
    ```bash
    python -m venv venv
    - On macOS/Linux: source venv/bin/activate  
    - On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Streamlit application:**
    ```bash
    streamlit run app.py
    ```

5.  Access `http://localhost:8501` in your browser.

---

## 🚀 How to Use the Application (Workflow)

1.  **First Run:**
    * Upon starting the application for the first time, the system will detect that the database (`CyberSec.db`) and the model (`modelo_classificador.pkl`) do not exist.

2.  **Upload:**
    * You will be automatically directed to the "**Update Database**" page.

3.  **Processing:**
    * Upload the data file (e.g., CyberSec.zip or Brasil_Cybersecurity_Threats_2015-2024.csv).

4.  **Training:**
    * Click the "**Process and Train New Base**" button. Wait a few minutes while the backend processes the data and trains the model.

5.  **Reloading:**
    * The application will reload automatically.

6.  **Explore:**
    * Now, with the data and model loaded, you can navigate freely between the "**Exploratory Analysis**" and "**Prediction Simulator**" pages.

---

## 📂 Project Structure

```
A1_Project/
│
├── .streamlit/
│   └── config.toml         # (Dark theme configuration)
│
├── CyberSec/
│   ├── CyberSec.db         # (Created by the app - The optimized database)
│   └── modelo_classificador.pkl # (Created by the app - The trained model)
│
├── app.py                  # (The web interface code - Streamlit)
├── backend_tasks.py        # (The processing and ML "engine" - Pandas/Sklearn)
├── requirements.txt        # (Python dependency list)
├── README.md               # (Documentation in portuguese)
├── README.en.md            # (This documentation)
└── CyberSec.zip            # (Example of raw data for upload)
```

---

## 📊 Presentation and Database used
- [Presentation on Canvas](https://www.canva.com/design/DAG3kcG_G7A/KoHOwSSRpPu-q8qupP0cOg/edit?utm_content=DAG3kcG_G7A&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton)
- [Global Cybersecurity Threats Database (2015-2024)](https://www.kaggle.com/datasets/atharvasoundankar/global-cybersecurity-threats-2015-2024)
  
---

### 👥 Members and LinkedIn Profiles

- [CAIO HENRIQUE PORCEL](https://www.linkedin.com/in/caio-henrique-porcel-702340243/)
- [KAUAN ALEXANDRE MENDES DA SILVA](https://www.linkedin.com/in/mendeskauan/)
- [LUCAS ALBANO RIBAS SERENATO](https://www.linkedin.com/in/lucas-albano-serenato-345306200/)
