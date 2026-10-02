import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import streamlit as st
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
from shapely.geometry import Point

# ==========================================
# 1. Configuración de la Interfaz
# ==========================================
st.set_page_config(page_title="Analizador Geoespacial - Villavieja", layout="wide")
st.title("Análisis Agroclimático Espacial - Villavieja, Huila")
st.markdown("""
Esta aplicación interactiva modela la distribución espacial de variables climáticas clave 
utilizando datos históricos de NASA POWER (2005-2025).
""")

# Diccionario centralizado 
VARIABLES_CONFIG = {
    "Temperatura": {
        "param": "T2M", "cmap": "plasma", "label": "Temperatura promedio (°C)", 
        "step": 0.5, "noise_scale": 0.6
    },
    "Precipitación": {
        "param": "PRECTOTCORR", "cmap": "viridis", "label": "Precipitación (mm/día)", 
        "step": 0.2, "noise_scale": 0.3
    },
    "Velocidad del Viento": {
        "param": "WS2M", "cmap": "coolwarm", "label": "Viento (m/s)", 
        "step": 0.2, "noise_scale": 0.3
    },
    "Radiación Solar": {
        "param": "ALLSKY_SFC_SW_DWN", "cmap": "inferno", "label": "Radiación (W/m²)", 
        "step": 10, "noise_scale": 10.0
    }
}

# ==========================================
# 2. Funciones de Extracción de Datos 
# ==========================================

@st.cache_data(show_spinner="Descargando límites geográficos...")
def load_shapefile():
    gdf = gpd.read_file(
        "https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_COL_shp.zip",
        layer="gadm41_COL_2"
    )
    villavieja = gdf[gdf["NAME_2"].str.upper() == "VILLAVIEJA"].to_crs(epsg=4326)
    return villavieja

@st.cache_data(show_spinner="Consultando NASA POWER API...")
def fetch_nasa_data(parameter):
    lat, lon = 3.218, -75.218
    url = (
        f"https://power.larc.nasa.gov/api/temporal/daily/point"
        f"?parameters={parameter}&start=20050101&end=20251231"
        f"&latitude={lat}&longitude={lon}&community=AG&format=JSON"
    )
    response = requests.get(url)
    data = response.json()["properties"]["parameter"][parameter]
    df = pd.DataFrame(data.items(), columns=["date", "value"])
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    return df.resample("Y").mean()["value"].mean()

# ==========================================
# 3. Función de Simulación e Interpolación
# ==========================================
def generate_spatial_grid(villavieja, base_value, noise_scale):
    bounds = villavieja.total_bounds
    minx, miny, maxx, maxy = bounds
    
    # Generar estaciones simuladas
    np.random.seed(42)
    points = []
    while len(points) < 120:
        p = Point(np.random.uniform(minx, maxx), np.random.uniform(miny, maxy))
        if villavieja.contains(p).bool():
            points.append(p)
            
    stations = gpd.GeoDataFrame(geometry=points, crs="EPSG:4326")
    stations["lon"] = stations.geometry.x
    stations["lat"] = stations.geometry.y
    stations["value"] = base_value + np.random.normal(0, noise_scale, len(stations))
    
    # Interpolación y malla
    x = np.linspace(minx, maxx, 600)
    y = np.linspace(miny, maxy, 600)
    X, Y = np.meshgrid(x, y)
    
    Z = griddata(
        (stations["lon"], stations["lat"]), stations["value"], 
        (X, Y), method="linear", fill_value=np.nanmean(stations["value"])
    )
    Z_smooth = gaussian_filter(Z, sigma=2)
    
    # Máscara
    grid_points = gpd.GeoDataFrame(
        geometry=[Point(xy) for xy in zip(X.flatten(), Y.flatten())], crs="EPSG:4326"
    )
    mask = grid_points.within(villavieja.geometry.iloc[0])
    Z_masked = np.where(mask.values.reshape(X.shape), Z_smooth, np.nan)
    
    return X, Y, Z_masked, bounds

# ==========================================
# 4. Interfaz de Usuario (Sidebar y Renderizado)
# ==========================================
st.sidebar.header("Parámetros del Modelo")
selected_var = st.sidebar.selectbox("Selecciona la variable a analizar:", list(VARIABLES_CONFIG.keys()))

st.sidebar.markdown("""
---
**Nota Técnica:** 
En este prototipo, la dispersión espacial se simula estocásticamente usando un kernel gaussiano sobre la media histórica del punto coordenado central de la API.
""")

# Flujo principal de ejecución
try:
    config = VARIABLES_CONFIG[selected_var]
    villavieja_gdf = load_shapefile()
    base_mean = fetch_nasa_data(config["param"])
    
    with st.spinner('Generando interpolación de isoclinas...'):
        X, Y, Z_masked, bounds = generate_spatial_grid(villavieja_gdf, base_mean, config["noise_scale"])
        
        # Plotting
        fig, ax = plt.subplots(figsize=(8, 8))
        img = ax.imshow(
            Z_masked, extent=(bounds[0], bounds[2], bounds[1], bounds[3]),
            origin="lower", cmap=config["cmap"], alpha=0.95
        )
        villavieja_gdf.boundary.plot(ax=ax, color="black", linewidth=1.2)
        
        levels = np.arange(np.nanmin(Z_masked), np.nanmax(Z_masked), config["step"])
        cs = ax.contour(X, Y, Z_masked, levels=levels, colors="black", linewidths=0.6, alpha=0.6)
        ax.clabel(cs, fmt="%.1f", inline=True, fontsize=8)
        
        cbar = plt.colorbar(img, ax=ax, shrink=0.8)
        cbar.set_label(config["label"], fontsize=11)
        
        ax.set_title(f"Gradiente Espacial de {selected_var} (2005-2025)", fontsize=14, fontweight="bold")
        ax.set_xlabel("Longitud")
        ax.set_ylabel("Latitud")
        ax.axis('off') # Se ve más limpio en web sin los ejes numéricos alrededor
        
        # Enviar el plot a Streamlit
        st.pyplot(fig)

except (requests.RequestException, KeyError, ValueError) as e:
    st.error(f"Error al procesar los datos: {e}")