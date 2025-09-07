# Meta-Analysis Flask + SQLite — środowisko startowe

Ten dokument prowadzi Cię przez **przygotowanie środowiska lokalnego** do aplikacji Flask z bazą **SQLite**,
w której będziesz importował/edytował dane do metaanalizy oraz uruchamiał skrypty analityczne (pandas).

## Wymagania wstępne

- Zainstalowany **Miniconda/Conda** (u Ciebie jest już Miniconda).
- System: macOS / Linux / Windows (instrukcje poleceniowe są uniwersalne).
- (Opcjonalnie) **VS Code** lub inny IDE oraz **git**.

## 1) Utwórz i aktywuj środowisko

W katalogu projektu zapisz plik `environment.yml`, a następnie:

```bash
# macOS / Linux
conda env create -f environment.yml
conda activate meta-flask

# Windows (Anaconda Prompt / PowerShell)
conda env create -f environment.yml
conda activate meta-flask
```

> Jeśli używasz ręcznej ścieżki do conda:  
> `/Users/piotrlewandowski/miniconda3/bin/conda env create -f environment.yml`  
> `/Users/piotrlewandowski/miniconda3/bin/conda activate meta-flask`

Zarejestruj kernel do Jupyter (przydatne do EDA):

```bash
python -m ipykernel install --user --name meta-flask
```

## 2) Przygotuj plik `.env` i katalogi instancyjne

Skopiuj `.env.example` do `.env` i **zmień** `SECRET_KEY` na losowy długi ciąg:

```bash
cp .env.example .env
# edytuj .env i ustaw własny SECRET_KEY
```

Utwórz katalogi lokalne (w repo):

```bash
mkdir -p instance/uploads data notebooks
```

- `instance/` — trzymamy tam pliki specyficzne dla instancji (np. `meta.sqlite3`), poza git.
- `data/` — surowe pliki wejściowe (np. Excel/CSV) do importu.
- `notebooks/` — notatniki Jupyter do analizy.

## 3) Formatowanie i linting

Zainstaluj hooki pre-commit (po sklonowaniu repozytorium i dodaniu pliku `.pre-commit-config.yaml`):

```bash
pre-commit install
# ręczne uruchomienie na całym repo (opcjonalnie):
pre-commit run --all-files
```

## 4) Szybki test środowiska

```bash
python -c "import flask, sqlalchemy, pandas, openpyxl; print('OK')"
```

Jeśli zobaczysz `OK`, podstawowe biblioteki są dostępne.

## 5) Szkielet projektu (propozycja)

```
your-project/
├── app/                # kod aplikacji Flask (factory, modele, blueprints, formularze)
├── migrations/         # pliki migracji (Flask-Migrate / Alembic)
├── instance/           # pliki instancji (SQLite, uploady) — poza git
├── data/               # surowe pliki danych (xlsx/csv)
├── notebooks/          # analizy w Jupyter
├── tests/              # testy jednostkowe/integracyjne (pytest)
├── environment.yml
├── .env.example
├── .pre-commit-config.yaml
└── README.md
```

## 6) Co dalej (skrót czynności po środowisku)

1. **Model danych** (schemat SQLAlchemy) na bazie struktury Excela.
2. **Migracje**: `flask db init`, `flask db migrate`, `flask db upgrade`.
3. **Importer** XLSX/CSV → SQLite (pandas + walidacja).
4. **CRUD** dla rekordów (Flask Blueprints, formularze Flask-WTF).
5. **Filtrowanie/eksport** (CSV/XLSX) oraz proste wykresy (opcjonalnie Plotly offline).
6. **Testy** (pytest) i **backup** bazy.
7. **Notatniki EDA** w `notebooks/` (kernel: `meta-flask`).

> Gdy środowisko będzie gotowe, dostarczę listę **kolejnych zadań** (tasków) do wdrożenia funkcji krok po kroku.
