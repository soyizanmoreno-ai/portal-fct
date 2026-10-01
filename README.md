# Portal FCT

MVP para alumnado, empresas y tutores: ofertas, candidaturas, perfiles, CV y seguimiento de horas de prácticas.

## Requisitos

- Python 3.10 o posterior
- Node.js 20 o posterior

## Arranque local

Instala las dependencias e inicia la API con una clave de desarrollo estable:

```bash
python -m pip install -r requirements.txt
export SECRET_KEY="pega-aqui-una-clave-aleatoria-de-al-menos-32-caracteres"
uvicorn app.main:app --reload
```

En otra terminal, exporta **la misma `SECRET_KEY`** y crea el primer administrador. El comando pide email y contraseña de forma interactiva:

```bash
export SECRET_KEY="la-misma-clave-del-backend"
python -m app.db.create_admin
```

Después inicia la interfaz:

```bash
cd frontend
npm install
npm run dev
```

Abre `http://localhost:5173`. La API queda en `http://localhost:8000` y su documentación OpenAPI en `/docs`. Los alumnos pueden registrarse desde la pantalla de acceso; el administrador crea cuentas de empresa y tutor.

Para otro origen del frontend, configura `FRONTEND_ORIGINS` como lista de URLs separadas por comas. Para apuntar Vite a otra API, configura `VITE_API_URL` antes de ejecutar el frontend; el valor por defecto es `http://127.0.0.1:8000/api/v1`.

## Pruebas

```bash
python -m pip install -r requirements-dev.txt
python -W error::DeprecationWarning -m unittest discover -s tests -v
cd frontend && npm run build
```

El parser del CV sugiere tecnologías encontradas en PDFs con texto seleccionable. El alumno revisa y confirma esas sugerencias; PDFs escaneados se completan manualmente.
