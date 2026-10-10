# validaruc-python

Cliente Python mínimo para **ValidaRUC**: validación de RUC peruano sobre el Padrón Reducido de la SUNAT (dataset público, actualizado a diario).

- ✅ Checksum módulo 11 offline (cero requests)
- ✅ Consulta en vivo: razón social, estado, condición de domicilio
- ✅ Ficha fiscal completa del padrón (razón social, estado, condición, ubigeo y domicilio fiscal)
- ✅ Manejo de 404 / 429 con `Retry-After`
- ✅ Frescura de datos visible (`actualizado_en` en cada respuesta)

## Instalación

```bash
pip install validaruc
```

*(Nombre de paquete tentativo: confirmar disponibilidad en PyPI antes de publicar.)*

## Quickstart

```python
from validaruc import ValidaRUC

api = ValidaRUC(api_key="TU_RAPIDAPI_KEY")

# 1. Checksum offline: gratis, instantáneo, sin red
api.checksum("10452159428")   # True
api.checksum("10452159429")   # False

# 2. Consulta en vivo contra el padrón SUNAT
r = api.consultar("10452159428")
print(r.razon_social)    # GARCIA CHANCO CARLOS AUGUSTO
print(r.estado)          # ACTIVO
print(r.condicion)       # HABIDO
print(r.actualizado_en)  # 2026-10-09  ← frescura de los datos
print(r.fuente)          # SUNAT Padrón Reducido

# 3. Ficha completa (domicilio fiscal, ubigeo, etc.)
ficha = api.ficha("10452159428")

# 4. Health: gratis, no consume cuota
print(api.health()["data"]["actualizado_en"])
```

## Manejo de errores

```python
from validaruc import ValidaRUC, RucNoEncontrado, CuotaSuperada

api = ValidaRUC(api_key="TU_RAPIDAPI_KEY")
try:
    r = api.consultar("99999999999")
except RucNoEncontrado:
    print("Ese RUC no existe en el padrón.")
except CuotaSuperada as e:
    print(f"Cuota superada, reintenta en {e.retry_after}s.")
```

## Cómo conseguir tu API key (gratis)

1. Entra a https://rapidapi.com/MohsinIshaq/api/validaruc
2. Suscríbete al plan **Free: 100 consultas/mes, $0, sin tarjeta**
3. Copia tu `x-rapidapi-key` desde el dashboard de RapidAPI

## Diseño

El cliente valida el checksum **antes** de hacer el request: si el RUC no pasa el módulo 11, ni se consume cuota. Cada respuesta del API incluye `fuente` y `actualizado_en`; el SDK los expone como atributos para que los muestres en tu UI o logs.

## Nota legal

ValidaRUC es un servicio independiente de terceros construido sobre datos públicos de la SUNAT. **No está afiliado a la SUNAT**, no es un servicio oficial de la SUNAT y no representa a ninguna entidad gubernamental. Los datos se entregan TAL CUAL (as-is), sin garantías de exactitud o actualización. Para trámites oficiales, usa el portal de la SUNAT.

## Licencia

MIT
