# Video script — University Dining Halls Cash & Supplier Management System

**Team:** Nazareno Aranda, Julian Blanco Cortes
**Target length:** about 6 minutes (maximum 7) · **Language:** English (the course asks for it, preferably)
**Where to host it:** YouTube as *Unlisted* (or Google Drive with link access). Put the link in the final `README.md`.

> **Notas para ustedes (en español):** este guion está pensado para leerlo en voz alta, repartido entre los dos (**N** = Naza, **J** = Julian). Las frases son cortas a propósito, para que se entiendan aunque el inglés no sea perfecto: pueden adaptarlas con sus palabras, pero conserven el orden. Los tiempos son aproximados. Antes de grabar, hagan la **checklist** del final.

---

## Scene 1 — Introduction (0:00 – 0:35)

**On screen:** title slide or the login page of the live app; both faces/names if you appear on camera.

**N:** "Hello! We are Nazareno Aranda and Julian Blanco Cortes, students of the University Technical Degree in Programming at UTN. This is our final integrative project: a cash and supplier management system for a chain of university dining halls."

**J:** "In the next six minutes we will explain the problem, show the system working online, and talk about how we built it."

## Scene 2 — The problem (0:35 – 1:25)

**On screen:** simple slide with three icons/words: *Owner · Cashier · Purchasing manager*.

**N:** "Imagine a chain of dining halls inside several universities. Every day each location sells hundreds of meals, and also buys supplies from different suppliers."

**J:** "Today, that information lives in spreadsheets and paper notes. Three people suffer from it. The cashier loses time closing the cash register every night. The purchasing manager cannot easily follow which orders arrived. And the owner cannot see, in one place, how every location is doing."

**N:** "Our goal was simple: one system where sales, cash closing and supplier orders are recorded once, and the owner can see everything together."

## Scene 3 — The solution and the architecture (1:25 – 2:25)

**On screen:** the architecture diagram from `docs/03-Arquitectura.md` (frontend → backend → database), then the list of seven modules.

**J:** "The system is a web application with three parts. The frontend is built with React and Vite, and it is deployed on Vercel. The backend is a REST API built with Python, Django and Django REST Framework, deployed on Render. And the data is stored in a PostgreSQL database hosted on Supabase."

**N:** "The backend is a modular monolith: one Django application split in seven modules — users, locations, suppliers, cash register, sales, orders and dashboard. Each module has its own models, serializers and views, so each one has a single responsibility."

**J:** "For security, users log in with their email and password and receive a token. The system has three roles: administration, cashier and purchasing. Each role only sees and does what it needs, and the backend checks that on every request."

## Scene 4 — Live demo (2:25 – 5:00)

> Use the **online** version (Vercel URL), not localhost. Open it **a few minutes before** recording so the free servers are awake. Use the sample users (password `Demo-1234`).

### 4.1 The cashier's day (2:25 – 3:35)

**On screen:** log in as `cajero.ciencias@comedores.test`. Go to *Caja*.

**N:** "Let's follow a normal day. I am a cashier at the Sciences dining hall. First, I open the cash register with the starting cash."

*(Open the register with 2,000.)*

**N:** "Now I record a sale. I choose the payment method and add the products: two daily menus and one bottle of water. The total is calculated automatically."

*(Go to *Ventas*, load the sale, show it at the top of the list, open *Ver detalle*.)*

**N:** "At the end of the day I go back to the cash screen. The system shows how many receipts there are, the total sold by payment method, and the expected cash: the opening amount plus the cash sales. Then I close the register."

*(Close the register; show the closing summary.)*

**N:** "Once it is closed, no more sales can be added to it. That closing used to take a lot of time with spreadsheets; now it is one click."

### 4.2 Purchasing (3:35 – 4:15)

**On screen:** log out; log in as `compras@comedores.test`. Go to *Pedidos*.

**J:** "Now I am the purchasing manager. Here are all the orders to suppliers with their status: pending, received or cancelled. I create a new order: I choose the supplier and the dining hall, add the products and register it. It is created as *pending*."

*(Create an order; then mark another pending order as *Recibido*.)*

**J:** "When the goods arrive, I mark the order as received and the system stores the date. A received or cancelled order cannot change anymore, so the history stays reliable."

### 4.3 The owner's dashboard (4:15 – 5:00)

**On screen:** log out; log in as `admin@comedores.test`. Go to *Panel*.

**J:** "Finally, the owner. In the dashboard we see the sales and the orders of the whole chain: totals, payment methods, order status, and a comparison by dining hall. The numbers we just created — the sale and the order — are already included."

*(Click *Últimos 7 días*, then pick one location in the filter. Scroll to the chart.)*

**J:** "The result is sales minus orders, and we can filter by period and by location. This is the single place the owner needed."

*(Optional, 10 seconds: show *Sedes*, mention that a cashier cannot enter this screen — log in as a cashier and open `/panel` to show "Sin acceso".)*

## Scene 5 — Design decisions (5:00 – 5:50)

**On screen:** the entity-relationship diagram (`docs/02-Diseno-BD-Modulos.md`) or a slide with 4 bullets.

**N:** "We made some important decisions. First, the database is relational, because sales, orders and cash registers are strongly related, and we need integrity between them. For example, the database itself guarantees that each location has only one open cash register."

**J:** "Second, records are never really deleted. Suppliers and locations are deactivated, and receipts cannot be edited, so the history is always available for the cash closing."

**N:** "Third, we chose token authentication instead of JWT or sessions, because the frontend and the backend live on different domains and we wanted the simplest option that is still secure."

**J:** "And fourth, everything is deployed in free cloud services, so the system is available online. The trade-off is that the free servers go to sleep after a while, and the first request of the day can take up to a minute."

## Scene 6 — What we learned and what is next (5:50 – 6:30)

**On screen:** slide with *Learned* and *Next steps*.

**N:** "We learned how to design a system in layers and modules, to model a relational database, to build and secure a REST API, and to deploy a full application in the cloud — and also to work as a team with Git and GitHub, using one commit per task."

**J:** "As future work, we would add printable reports, automatic notifications for late orders, and an app version for tablets used by the cashiers."

## Scene 7 — Closing (6:30 – 6:45)

**On screen:** the repository page and the live app URL.

**J:** "Everything is in our GitHub repository, with the installation instructions and the documentation."

**N:** "Thank you very much for watching!"

---

## Checklist before recording

- [ ] The backend (Render), the database (Supabase) and the frontend (Vercel) are working. Open the app **5 minutes before** to wake up the servers.
- [ ] The sample data is loaded (`database/datos_ejemplo.sql`). The *Ciencias* location has **no open cash register**: if you already recorded a test, reload the sample data (see `database/README.md`) so the demo starts clean.
- [ ] Browser: full-screen window, zoom 100–110 %, no unrelated tabs or bookmarks visible, notifications turned off.
- [ ] Have the diagrams ready in tabs or slides: `docs/03-Arquitectura.md` (architecture) and `docs/02-Diseno-BD-Modulos.md` (entity-relationship).
- [ ] Do a **dry run** with a timer. If you go over 7 minutes, shorten Scene 5 and 6 first.
- [ ] Record the audio in a quiet room and speak slowly. Do not read the screen; look at the script only for the key phrases.
- [ ] Never show passwords other than the sample ones (`Demo-1234`), and never show the `.env` file or the Supabase / Render panels with credentials.

## After recording

1. Upload the video to YouTube as **Unlisted** (or to Drive with link access) and check that it plays without logging in.
2. Paste the link in the final `README.md` (planned for 6/11) and in the aula virtual task.
3. If you add English subtitles, YouTube can generate them automatically; review them before publishing.
