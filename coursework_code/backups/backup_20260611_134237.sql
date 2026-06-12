--
-- PostgreSQL database dump
--

\restrict 34JRyxsBvewAq3rzoLYfh1aKs45AlYws9RrfhLoPtXLhjgtOoeBLCcF19asRszg

-- Dumped from database version 14.23 (Ubuntu 14.23-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.23 (Ubuntu 14.23-0ubuntu0.22.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: category; Type: TABLE; Schema: public; Owner: family_budget_user
--

CREATE TABLE public.category (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    type character varying(10) NOT NULL,
    color character varying(20),
    description text,
    family_id integer NOT NULL
);


ALTER TABLE public.category OWNER TO family_budget_user;

--
-- Name: category_id_seq; Type: SEQUENCE; Schema: public; Owner: family_budget_user
--

CREATE SEQUENCE public.category_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.category_id_seq OWNER TO family_budget_user;

--
-- Name: category_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: family_budget_user
--

ALTER SEQUENCE public.category_id_seq OWNED BY public.category.id;


--
-- Name: category_limit; Type: TABLE; Schema: public; Owner: family_budget_user
--

CREATE TABLE public.category_limit (
    id integer NOT NULL,
    category_id integer NOT NULL,
    amount_limit numeric(10,2) NOT NULL,
    period character varying(10) NOT NULL
);


ALTER TABLE public.category_limit OWNER TO family_budget_user;

--
-- Name: category_limit_id_seq; Type: SEQUENCE; Schema: public; Owner: family_budget_user
--

CREATE SEQUENCE public.category_limit_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.category_limit_id_seq OWNER TO family_budget_user;

--
-- Name: category_limit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: family_budget_user
--

ALTER SEQUENCE public.category_limit_id_seq OWNED BY public.category_limit.id;


--
-- Name: dashboard_stats; Type: TABLE; Schema: public; Owner: family_budget_user
--

CREATE TABLE public.dashboard_stats (
    id integer NOT NULL,
    user_id integer NOT NULL,
    period character varying(10) NOT NULL,
    total_income numeric(10,2),
    total_expense numeric(10,2),
    category_breakdown json,
    member_breakdown json,
    monthly_timeline json,
    daily_balance json,
    last_calculated timestamp without time zone
);


ALTER TABLE public.dashboard_stats OWNER TO family_budget_user;

--
-- Name: dashboard_stats_id_seq; Type: SEQUENCE; Schema: public; Owner: family_budget_user
--

CREATE SEQUENCE public.dashboard_stats_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dashboard_stats_id_seq OWNER TO family_budget_user;

--
-- Name: dashboard_stats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: family_budget_user
--

ALTER SEQUENCE public.dashboard_stats_id_seq OWNED BY public.dashboard_stats.id;


--
-- Name: family; Type: TABLE; Schema: public; Owner: family_budget_user
--

CREATE TABLE public.family (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    invite_code character varying(20) NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.family OWNER TO family_budget_user;

--
-- Name: family_id_seq; Type: SEQUENCE; Schema: public; Owner: family_budget_user
--

CREATE SEQUENCE public.family_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.family_id_seq OWNER TO family_budget_user;

--
-- Name: family_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: family_budget_user
--

ALTER SEQUENCE public.family_id_seq OWNED BY public.family.id;


--
-- Name: receipt; Type: TABLE; Schema: public; Owner: family_budget_user
--

CREATE TABLE public.receipt (
    id integer NOT NULL,
    transaction_id integer NOT NULL,
    filename character varying(255) NOT NULL,
    filepath character varying(500) NOT NULL,
    uploaded_at timestamp without time zone
);


ALTER TABLE public.receipt OWNER TO family_budget_user;

--
-- Name: receipt_id_seq; Type: SEQUENCE; Schema: public; Owner: family_budget_user
--

CREATE SEQUENCE public.receipt_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.receipt_id_seq OWNER TO family_budget_user;

--
-- Name: receipt_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: family_budget_user
--

ALTER SEQUENCE public.receipt_id_seq OWNED BY public.receipt.id;


--
-- Name: transaction; Type: TABLE; Schema: public; Owner: family_budget_user
--

CREATE TABLE public.transaction (
    id integer NOT NULL,
    user_id integer NOT NULL,
    category_id integer NOT NULL,
    amount numeric(10,2) NOT NULL,
    date date NOT NULL,
    description text
);


ALTER TABLE public.transaction OWNER TO family_budget_user;

--
-- Name: transaction_id_seq; Type: SEQUENCE; Schema: public; Owner: family_budget_user
--

CREATE SEQUENCE public.transaction_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.transaction_id_seq OWNER TO family_budget_user;

--
-- Name: transaction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: family_budget_user
--

ALTER SEQUENCE public.transaction_id_seq OWNED BY public.transaction.id;


--
-- Name: user; Type: TABLE; Schema: public; Owner: family_budget_user
--

CREATE TABLE public."user" (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role character varying(20) NOT NULL,
    family_id integer,
    created_at timestamp without time zone
);


ALTER TABLE public."user" OWNER TO family_budget_user;

--
-- Name: user_budget; Type: TABLE; Schema: public; Owner: family_budget_user
--

CREATE TABLE public.user_budget (
    id integer NOT NULL,
    user_id integer NOT NULL,
    amount_limit numeric(10,2) NOT NULL,
    period character varying(10) NOT NULL,
    description text
);


ALTER TABLE public.user_budget OWNER TO family_budget_user;

--
-- Name: user_budget_id_seq; Type: SEQUENCE; Schema: public; Owner: family_budget_user
--

CREATE SEQUENCE public.user_budget_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_budget_id_seq OWNER TO family_budget_user;

--
-- Name: user_budget_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: family_budget_user
--

ALTER SEQUENCE public.user_budget_id_seq OWNED BY public.user_budget.id;


--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: family_budget_user
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_id_seq OWNER TO family_budget_user;

--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: family_budget_user
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;


--
-- Name: category id; Type: DEFAULT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.category ALTER COLUMN id SET DEFAULT nextval('public.category_id_seq'::regclass);


--
-- Name: category_limit id; Type: DEFAULT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.category_limit ALTER COLUMN id SET DEFAULT nextval('public.category_limit_id_seq'::regclass);


--
-- Name: dashboard_stats id; Type: DEFAULT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.dashboard_stats ALTER COLUMN id SET DEFAULT nextval('public.dashboard_stats_id_seq'::regclass);


--
-- Name: family id; Type: DEFAULT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.family ALTER COLUMN id SET DEFAULT nextval('public.family_id_seq'::regclass);


--
-- Name: receipt id; Type: DEFAULT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.receipt ALTER COLUMN id SET DEFAULT nextval('public.receipt_id_seq'::regclass);


--
-- Name: transaction id; Type: DEFAULT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.transaction ALTER COLUMN id SET DEFAULT nextval('public.transaction_id_seq'::regclass);


--
-- Name: user id; Type: DEFAULT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Name: user_budget id; Type: DEFAULT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.user_budget ALTER COLUMN id SET DEFAULT nextval('public.user_budget_id_seq'::regclass);


--
-- Data for Name: category; Type: TABLE DATA; Schema: public; Owner: family_budget_user
--

COPY public.category (id, name, type, color, description, family_id) FROM stdin;
1	Продукты	expense	#dc3545	Покупка продуктов питания	1
2	Транспорт	expense	#ffc107	Проезд, такси, бензин	1
3	Коммунальные услуги	expense	#17a2b8	Квартплата, свет, вода	1
4	Зарплата	income	#28a745	Заработная плата	1
5	Подработка	income	#20c997	Дополнительный доход	1
6	Кафе и рестораны	expense	#fd7e14	Обеды вне дома	1
7	Развлечения	expense	#6f42c1	Кино, игры, хобби	1
8	Одежда	expense	#e83e8c	Покупка одежды и обуви	1
\.


--
-- Data for Name: category_limit; Type: TABLE DATA; Schema: public; Owner: family_budget_user
--

COPY public.category_limit (id, category_id, amount_limit, period) FROM stdin;
\.


--
-- Data for Name: dashboard_stats; Type: TABLE DATA; Schema: public; Owner: family_budget_user
--

COPY public.dashboard_stats (id, user_id, period, total_income, total_expense, category_breakdown, member_breakdown, monthly_timeline, daily_balance, last_calculated) FROM stdin;
1	2	month	0.00	0.00	{}	{}	{}	{"2026-06-01": -1000.0, "2026-06-02": -3000.0, "2026-06-03": -111.0, "2026-06-04": 9889.0, "2026-06-05": 4389.0, "2026-06-06": -2611.0, "2026-06-07": -3111.0, "2026-06-08": -1911.0, "2026-06-09": 4889.0, "2026-06-10": 3956.0}	2026-06-10 21:15:02.409949
\.


--
-- Data for Name: family; Type: TABLE DATA; Schema: public; Owner: family_budget_user
--

COPY public.family (id, name, invite_code, created_at) FROM stdin;
1	Семья owner	FAM-R7Z5GL	2026-06-09 22:58:31.384812
2	Семья test	FAM-5XKAK0	2026-06-10 18:08:20.345176
\.


--
-- Data for Name: receipt; Type: TABLE DATA; Schema: public; Owner: family_budget_user
--

COPY public.receipt (id, transaction_id, filename, filepath, uploaded_at) FROM stdin;
1	15	er_diagram.jpg	/home/admin/Desktop/web-coursework/coursework_code/uploads/15_er_diagram.jpg	2026-06-09 23:45:20.357317
2	16	sig.jpg	/home/admin/Desktop/web-coursework/coursework_code/uploads/16_sig.jpg	2026-06-10 21:15:02.40323
\.


--
-- Data for Name: transaction; Type: TABLE DATA; Schema: public; Owner: family_budget_user
--

COPY public.transaction (id, user_id, category_id, amount, date, description) FROM stdin;
1	3	1	-1000.00	2026-06-01	transaction1
2	4	7	-2000.00	2026-06-02	transaction2
3	6	5	3000.00	2026-06-03	transaction3
4	2	4	10000.00	2026-06-04	transaction4
5	2	2	-6000.00	2026-06-05	transaction5
6	3	8	-7000.00	2026-06-06	transaction6
7	4	6	-500.00	2026-06-07	transaction7
8	6	1	-800.00	2026-06-08	transaction8
9	3	4	8000.00	2026-06-09	transaction9
12	4	7	-1200.00	2026-06-09	transaction9.1
13	4	5	500.00	2026-06-05	transaction5.1
14	4	5	2000.00	2026-06-08	transaction8.1
11	2	6	-600.00	2026-06-10	transaction10
15	2	3	-111.00	2026-06-03	test
16	2	3	-333.00	2026-06-10	transaction10.1
\.


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: family_budget_user
--

COPY public."user" (id, username, email, password_hash, role, family_id, created_at) FROM stdin;
1	admin	admin@familybudget.com	$2b$12$/.Ew1ELgtpcRvQ.YEhcFSuSeXgWS/W5oJTXCiRYV2QQ6KnSqrok6C	admin	\N	2026-06-09 22:05:44.61356
3	user1	user1@email.com	$2b$12$V3AH62vzvofCmDrnRjJGdu.DADMCj1kj5hte5o5L4Hw1PopRSxODC	member	1	2026-06-09 23:01:16.872076
4	user2	user2@email.com	$2b$12$QyjhdqszfUCNcY7N8zhfx.D.7/vLOh/qLAlWHItkHHERiiADWlyq2	member	1	2026-06-09 23:03:18.131641
6	user3	user3@email.com	$2b$12$Tjl6mPjnt7dBZoy8omzWoedTfsRc4rSXx3eaP2C62m.B//U/bPOku	member	1	2026-06-09 23:10:18.696691
2	owner	owner@email.com	$2b$12$TQccZ1s4UvnXC6wrfwwOruiL1Uai2OuQMV7aXw1BSPCmuKDTtwJNq	owner	1	2026-06-09 22:58:31.580717
7	test	test@test.ru	$2b$12$L8HSXkQcM9tcQLzkxr5DA.jhRsl8/4CSpffi7xBL6wGZX6Le9I116	owner	2	2026-06-10 18:08:20.539578
9	212	212@tyu.uui	$2b$12$G.9iZyBUd/j2p/jOg/jvruJ4iR3dAaCZmZUu7BGgY1znZdasvkWSe	member	2	2026-06-10 18:29:59.700572
\.


--
-- Data for Name: user_budget; Type: TABLE DATA; Schema: public; Owner: family_budget_user
--

COPY public.user_budget (id, user_id, amount_limit, period, description) FROM stdin;
1	2	50000.00	month	
2	3	30000.00	month	
\.


--
-- Name: category_id_seq; Type: SEQUENCE SET; Schema: public; Owner: family_budget_user
--

SELECT pg_catalog.setval('public.category_id_seq', 8, true);


--
-- Name: category_limit_id_seq; Type: SEQUENCE SET; Schema: public; Owner: family_budget_user
--

SELECT pg_catalog.setval('public.category_limit_id_seq', 1, false);


--
-- Name: dashboard_stats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: family_budget_user
--

SELECT pg_catalog.setval('public.dashboard_stats_id_seq', 1, true);


--
-- Name: family_id_seq; Type: SEQUENCE SET; Schema: public; Owner: family_budget_user
--

SELECT pg_catalog.setval('public.family_id_seq', 2, true);


--
-- Name: receipt_id_seq; Type: SEQUENCE SET; Schema: public; Owner: family_budget_user
--

SELECT pg_catalog.setval('public.receipt_id_seq', 2, true);


--
-- Name: transaction_id_seq; Type: SEQUENCE SET; Schema: public; Owner: family_budget_user
--

SELECT pg_catalog.setval('public.transaction_id_seq', 16, true);


--
-- Name: user_budget_id_seq; Type: SEQUENCE SET; Schema: public; Owner: family_budget_user
--

SELECT pg_catalog.setval('public.user_budget_id_seq', 2, true);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: family_budget_user
--

SELECT pg_catalog.setval('public.user_id_seq', 9, true);


--
-- Name: category_limit category_limit_pkey; Type: CONSTRAINT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.category_limit
    ADD CONSTRAINT category_limit_pkey PRIMARY KEY (id);


--
-- Name: category category_pkey; Type: CONSTRAINT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.category
    ADD CONSTRAINT category_pkey PRIMARY KEY (id);


--
-- Name: dashboard_stats dashboard_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.dashboard_stats
    ADD CONSTRAINT dashboard_stats_pkey PRIMARY KEY (id);


--
-- Name: family family_invite_code_key; Type: CONSTRAINT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.family
    ADD CONSTRAINT family_invite_code_key UNIQUE (invite_code);


--
-- Name: family family_pkey; Type: CONSTRAINT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.family
    ADD CONSTRAINT family_pkey PRIMARY KEY (id);


--
-- Name: receipt receipt_pkey; Type: CONSTRAINT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.receipt
    ADD CONSTRAINT receipt_pkey PRIMARY KEY (id);


--
-- Name: receipt receipt_transaction_id_key; Type: CONSTRAINT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.receipt
    ADD CONSTRAINT receipt_transaction_id_key UNIQUE (transaction_id);


--
-- Name: transaction transaction_pkey; Type: CONSTRAINT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.transaction
    ADD CONSTRAINT transaction_pkey PRIMARY KEY (id);


--
-- Name: user_budget user_budget_pkey; Type: CONSTRAINT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.user_budget
    ADD CONSTRAINT user_budget_pkey PRIMARY KEY (id);


--
-- Name: user user_email_key; Type: CONSTRAINT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_email_key UNIQUE (email);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: user user_username_key; Type: CONSTRAINT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_username_key UNIQUE (username);


--
-- Name: category category_family_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.category
    ADD CONSTRAINT category_family_id_fkey FOREIGN KEY (family_id) REFERENCES public.family(id);


--
-- Name: category_limit category_limit_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.category_limit
    ADD CONSTRAINT category_limit_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.category(id);


--
-- Name: dashboard_stats dashboard_stats_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.dashboard_stats
    ADD CONSTRAINT dashboard_stats_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: receipt receipt_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.receipt
    ADD CONSTRAINT receipt_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transaction(id);


--
-- Name: transaction transaction_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.transaction
    ADD CONSTRAINT transaction_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.category(id);


--
-- Name: transaction transaction_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.transaction
    ADD CONSTRAINT transaction_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: user_budget user_budget_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public.user_budget
    ADD CONSTRAINT user_budget_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: user user_family_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: family_budget_user
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_family_id_fkey FOREIGN KEY (family_id) REFERENCES public.family(id);


--
-- PostgreSQL database dump complete
--

\unrestrict 34JRyxsBvewAq3rzoLYfh1aKs45AlYws9RrfhLoPtXLhjgtOoeBLCcF19asRszg

