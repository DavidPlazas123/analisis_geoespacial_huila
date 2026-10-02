Análisis Geoespacial de Variables Climáticas - Villavieja, Huila

Demo: [Enlace a Streamlit Cloud]

Descripción

Aplicación web desarrollada en Streamlit para el modelado espacial continuo de variables climáticas (temperatura, precipitación, viento y radiación solar). El sistema procesa datos históricos de la API de NASA POWER (2005-2025) y genera mapas de interpolación sobre los límites geográficos del municipio de Villavieja, Huila.

Este proyecto sirve como herramienta base para evaluar la viabilidad de proyectos en los sectores agrícola y de energías renovables.

Tecnologías

Lenguaje: Python 3.10

Manipulación y Matemáticas: Pandas, NumPy, SciPy

Procesamiento Espacial: GeoPandas, Shapely

Visualización: Matplotlib

Interfaz: Streamlit

Metodología

Extracción: Consulta de series temporales mediante la API REST de NASA POWER.

Procesamiento: Delimitación poligonal del área de estudio utilizando datos vectoriales de GADM.

Modelado: Generación de mallas espaciales mediante interpolación lineal (griddata) y aplicación de filtros de kernel gaussiano para suavizado de isoclinas.

Instalación y Ejecución

Se recomienda utilizar conda para evitar problemas de dependencias en librerías espaciales basadas en C++.

# Clonar el repositorio
git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git
cd TU_REPOSITORIO

# Crear y activar entorno virtual
conda create --name clima_env python=3.10 -y
conda activate clima_env

# Instalar dependencias
conda install -c conda-forge --file requirements.txt -y

# Ejecutar la aplicación
streamlit run app.py


Nota Técnica (Modelado Estocástico)

Debido a la resolución nativa de los datos satelitales consultados por cuadrante, la varianza espacial inter-municipal en este prototipo se aproxima mediante una distribución normal centrada en la media histórica de la coordenada principal. El código fuente está modularizado para permitir la ingesta directa de datos distribuidos (ej. NetCDF) en entornos de producción.