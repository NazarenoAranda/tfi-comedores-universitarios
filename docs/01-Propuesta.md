# Propuesta de Proyecto — Trabajo Final Integrador

**Integrantes:** Nazareno Aranda, Julian Blanco Cortes
**Carrera:** Tecnicatura Universitaria en Programación (UTN)
**Tipo de proyecto:** Inventiva propia (caso simulado)

---

## 1. Problemática

### Contexto
Se plantea el caso de una **cadena de comedores universitarios**: una administración central que gestiona varios comedores (sedes) dentro del ámbito de una o más universidades. Cada sede tiene un encargado de caja que registra las ventas del día, y existe además un encargado de compras responsable de gestionar los pedidos a los distintos proveedores (insumos, alimentos, bebidas, etc.) que abastecen a las sedes.

### Actores y necesidades

| Actor | Rol | Necesidad principal |
|---|---|---|
| Dueño / Administración | Supervisa todas las sedes | Visibilidad consolidada de ventas y gastos, sin depender de reportes manuales de cada sede |
| Encargado de caja (por sede) | Registra ventas diarias | Cargar comprobantes rápido y cerrar la caja sin perder tiempo en cálculos manuales |
| Encargado de compras | Gestiona pedidos a proveedores | Llevar registro claro de qué se pidió, a quién y en qué estado está cada pedido |

### Situación actual
Hoy el registro se lleva de forma manual e informal: **planillas de Excel no centralizadas y anotaciones en papel**, sin un criterio único entre sedes. Cada comedor maneja su información de manera aislada.

### Impacto medible
El costo principal identificado es el **tiempo que se pierde armando el cierre de caja**, agravado por tratarse de una cadena con múltiples sedes: no hay forma rápida de consolidar la información de todas ellas para tener una foto general del negocio.

### Por qué una solución tecnológica
Una planilla de Excel, aunque esté bien diseñada, depende de la disciplina manual de cada encargado de caja en cada sede y no ofrece una vista centralizada en tiempo real. Un sistema con una interfaz intuitiva reduce la fricción del registro diario y permite consolidar automáticamente la información de todas las sedes, algo que el enfoque actual no resuelve.

### Enunciado del problema
> *"El personal de una cadena de comedores universitarios —encargados de caja en cada sede, encargado de compras y la administración central— actualmente registra las ventas diarias y los pedidos a proveedores mediante Excel y anotaciones en papel, sin un criterio centralizado entre sedes. Esto genera una pérdida significativa de tiempo al armar el cierre de caja, especialmente al no poder consolidar rápidamente la información de las distintas sedes. Un sistema de gestión centralizaría el registro de comprobantes de venta y el seguimiento de pedidos a proveedores en una interfaz intuitiva, reduciendo el tiempo de cierre de caja y dando visibilidad consolidada a la administración."*

### Validación del problema
- **¿Ocurre ahora o es hipotético?** Es un caso simulado, pero modela una situación real y común en comercios con múltiples puntos de venta.
- **¿Los afectados reconocen el problema?** Sí — la pérdida de tiempo en el cierre de caja es un problema típico y reconocible en este tipo de operación.
- **¿Existe solución parcial hoy?** Sí, Excel y papel — insuficiente porque no centraliza información entre sedes ni agiliza el cierre.
- **¿Es técnicamente factible en los plazos?** Sí, ver sección de viabilidad.
- **¿Hay algo similar en el mercado?** Existen sistemas de punto de venta (POS) genéricos, pero no orientados específicamente a la gestión multi-sede de comedores con seguimiento de proveedores integrado en un mismo flujo.

---

## 2. Alcance del proyecto (MVP)

### Incluido en el MVP
- Registro de comprobantes de venta por sede (fecha, monto, medio de pago)
- Listado y consulta de comprobantes, con filtros por sede y fecha
- Cierre de caja por sede (cálculo automático de totales del período)
- Alta y listado de proveedores
- Alta y seguimiento de pedidos a proveedores (estado: pendiente / recibido)
- Panel consolidado para la administración: totales de todas las sedes

### Nice to have (si el tiempo lo permite)
- Reportes comparativos entre sedes
- Alertas de pedidos a proveedores con demora
- Exportación del cierre de caja a PDF/Excel
- Permisos diferenciados por rol (administración / cajero / compras)

### Fuera de alcance (explícito)
- Facturación electrónica / integración con AFIP
- Control de stock detallado a nivel de ingredientes/insumos
- Aplicación móvil nativa

---

## 3. Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Python + Django + Django REST Framework |
| Autenticación | Token Authentication de Django REST Framework |
| Base de datos | PostgreSQL |
| Frontend | React + Vite |
| Despliegue | Backend en Render, base de datos PostgreSQL en Supabase, frontend en Vercel |
| Control de versiones | GitHub (repositorio único) |

### Justificación

**Backend — Python + Django + DRF:**
Se eligió Python porque es un lenguaje que el equipo ya conoce de la cursada (Programación IV, POO en Python) y con el que se siente cómodo. Dentro del ecosistema Python, Django aporta un ORM maduro, sistema de autenticación y un panel de administración incorporado (Django Admin), lo que permite tener una base funcional para gestionar proveedores, pedidos y comprobantes desde el día uno, sin necesidad de construir primero toda la interfaz. Esto reduce el esfuerzo de desarrollo, algo clave dado el plazo académico. Django REST Framework se usa para exponer la API que consume el frontend en React.

**Autenticación — Token Authentication de DRF:**
Frontend y backend se despliegan en servicios distintos (Vercel y Render), por lo que las sesiones basadas en cookies traerían complicaciones entre dominios. El token viaja en el header `Authorization`, viene incluido en DRF sin librerías adicionales y evita la complejidad extra de JWT (refresh tokens, expiración), que no aporta valor real para el alcance de este proyecto.

**Base de datos — PostgreSQL:**
El dominio del problema (ventas, comprobantes, sedes, proveedores, pedidos) tiene una estructura de datos bien definida y con relaciones claras entre entidades (una venta pertenece a una sede, un pedido pertenece a un proveedor, etc.), por lo que un modelo relacional con integridad referencial es el más adecuado frente a una base NoSQL. Se aloja en Supabase porque las bases PostgreSQL gratuitas de Render expiran a los 30 días de creadas, un plazo menor al de este proyecto.

**Frontend — React + Vite:**
JavaScript es el lenguaje nativo de los navegadores, y React permite construir una interfaz de carga rápida e intuitiva para los encargados de caja, que es justamente uno de los objetivos centrales del proyecto (reducir la fricción frente al Excel actual).

**Despliegue — Render / Supabase / Vercel:**
Cumplen el requisito obligatorio de tener al menos un componente alojado en la nube, con planes gratuitos suficientes para el alcance de un MVP académico.

**Experiencia previa del equipo:** el equipo ya conoce Python (Programación IV) y la arquitectura en capas con Java/Spring Boot (Programación III), que se traslada de forma directa a Django. Lo nuevo a incorporar es el framework Django/DRF. Al ser un proyecto académico con condiciones flexibles y con el aprendizaje como parte del objetivo, esa curva de aprendizaje es asumible dentro de los plazos.

---

## 4. Plan de trabajo

| Etapa | Entregable | Fecha límite |
|---|---|---|
| 1 | Problemática definida, alcance, stack justificado, repo GitHub creado | 30/08 |
| 2 | Esquema de base de datos, listado de módulos, arquitectura y estructura del repositorio | 27/09 |
| 3 | Desarrollo completo, despliegue, informe, video | 14/11 |

### Módulos identificados
Detalle, descripción y prioridad de cada uno en [`02-Diseno-BD-Modulos.md`](./02-Diseno-BD-Modulos.md).

### Riesgos iniciales y mitigación
| Riesgo | Mitigación |
|---|---|
| Equipo sin experiencia previa en Django | Dedicar la primera semana de desarrollo a un mini-tutorial guiado antes de tocar el modelo de datos definitivo |
| Alcance multi-sede puede crecer de más | Mantener fija la lista de "fuera de alcance" y revisarla en cada entrega |
| Plazos ajustados para las entregas intermedias | Priorizar siempre el MVP sobre el "nice to have" |
| Los servicios gratuitos en la nube se "duermen" tras un rato sin uso (el primer pedido puede tardar hasta un minuto) | Aceptarlo para el MVP y avisarlo en la demo; revisar las condiciones de los planes gratuitos antes de desplegar |

---

## 5. Viabilidad

- **Técnica:** el equipo puede implementar la solución con el stack elegido; la única curva de aprendizaje real es Django, que tiene documentación extensa y comunidad grande.
- **Operativa:** al ser un caso simulado, no hay usuarios reales que adoptar, pero el diseño contempla un flujo de uso realista (cajero carga venta → cierre de caja → compras gestiona pedido → administración consolida).
- **Temporal:** el alcance del MVP es compatible con las fechas de entrega fijadas por la cátedra.

---

## 6. Estructura del repositorio

```
/backend      → Django + DRF (solo estructura inicial por ahora)
/frontend     → React + Vite (solo estructura inicial por ahora)
/database     → scripts DDL/DML y esquemas
/docs         → propuesta, diseño de BD, módulos y arquitectura
README.md     → descripción, tecnologías, integrantes y estado del proyecto
```
