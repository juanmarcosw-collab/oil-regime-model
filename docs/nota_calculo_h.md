# Cómo se calcula h en el modelo y en la Figura 1 del dashboard

Hay dos cosas distintas que merecen separarse: cómo h se usa como variable
del modelo, y cómo se calcula el `h_actual` que aparece como marcador en la
figura.

---

## 1. h como variable independiente (eje x de Figura 1)

**No se "calcula", se barre.** En `app/app.py:208`:

```python
h_grid = np.linspace(0.001, 1.5, 600)
```

Es decir, h se evalúa en 600 puntos equiespaciados entre 0,001 y 1,5. Para
cada valor de h en esa grilla, se computan las cuatro curvas ($P_C$, $P_R$,
$P$ composite, $P^\ast$) llamando a las funciones de `model/core.py`.

**¿Por qué [0,001, 1,5]?**

- Cota inferior > 0 porque $P_C$ y $P_R$ requieren $h > 0$ ($\dot R$ necesita
  evaluarse).
- Cota superior 1,5 es generosa: con $h^\ast = 0{,}30$ y $\sigma \approx 0{,}08$,
  el régimen clásico domina mucho antes ($q \approx 0$ para $h > 0{,}5$).
  Los 1,5 dan headroom para ver el plateau de $P_{\rm floor}$.

**En este sentido, h en el eje de la figura es puramente abstracto** — un
parámetro de estado, no un dato observado.

---

## 2. h_actual (marcador del punto observado)

Acá sí hay un cálculo concreto. Viene del **mapeo lineal de la Extensión 2**:

$$h(\text{Stock}) = h^\ast \cdot \frac{\text{Stock} - \text{Stock}_{\rm floor}}{\text{Stock}_{\rm stress} - \text{Stock}_{\rm floor}}$$

En el código (`app/app.py:149-154`):

```python
def h_from_stock(stock, stock_floor, stock_stress, h_star):
    return max(0.0, h_star * (stock - stock_floor) / (stock_stress - stock_floor))
```

### Anclajes operacionales

| Stock | h |
|---|---|
| 6.800 mb (floor JPM) | 0 |
| 7.600 mb (stress JPM) | $h^\ast$ = 0,30 |
| 8.200 mb (Stock_opt) | 0,525 |

### Cálculo con stock al 30-abril-2026 (último IEA OMR)

Con Stock_actual = 7.951 mb:

$$h_{\rm actual} = 0{,}30 \cdot \frac{7\,951 - 6\,800}{7\,600 - 6\,800} = 0{,}30 \cdot \frac{1\,151}{800} \approx 0{,}432$$

Eso es el valor de h donde se planta el marcador rojo en la figura.

---

## 3. Mapeo inverso (para la curva P\*)

Para la línea morada ($P^\ast$ con reposición), se hace el camino contrario:
dado h en la grilla, se calcula el stock equivalente, luego $R_{\rm repl}$,
luego $P^\ast$. Función `stock_from_h` en `app/app.py:157-160`:

$$\text{Stock}(h) = \text{Stock}_{\rm floor} + h \cdot \frac{\text{Stock}_{\rm stress} - \text{Stock}_{\rm floor}}{h^\ast}$$

Esto permite que cada punto de la curva $P^\ast(h)$ corresponda al stock
implícito a ese nivel de buffer.

---

## Qué decir si en la presentación preguntan

> *"h es una variable abstracta del paper, sin unidades. Para anclarla a un
> observable, hicimos un mapeo lineal contra los thresholds operacionales
> JPMorgan: el floor (6.800 mb) corresponde a h = 0 y el stress threshold
> (7.600 mb) corresponde a h = h\*. El mapeo es lineal por parsimonia.
> Para el stock de 7.951 mb (IEA OMR al 30-abril-2026), eso da h ≈ 0,43. En la figura, el eje x
> recorre h ∈ [0, 1,5] como parámetro abstracto; el marcador del punto
> observado se planta exactamente en h = 0,43 usando este mapeo."*

### Punto de cuidado

**La elección de Stock_floor y Stock_stress como anclajes es nuestra
decisión** (basada en thresholds JPM), no es del paper original. El paper
trata h como abstracto sin anclaje empírico; la Extensión 2 es lo que lo
conecta a stocks observables.
