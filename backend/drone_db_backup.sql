--
-- PostgreSQL database dump
--

\restrict vayZstzbFEjHF5Joed7C6pDHgFtc2XPehGleK47ywBpNTV4XQbgZi7MpHD8SRwS

-- Dumped from database version 17.9 (Homebrew)
-- Dumped by pg_dump version 17.9 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: airspace_zones; Type: TABLE; Schema: public; Owner: drone
--

CREATE TABLE public.airspace_zones (
    id integer NOT NULL,
    name character varying(120) NOT NULL,
    zone_type character varying(60) NOT NULL,
    polygon public.geometry(Polygon,4326) NOT NULL,
    coordinates json,
    active boolean,
    created_at timestamp without time zone
);


ALTER TABLE public.airspace_zones OWNER TO drone;

--
-- Name: airspace_zones_id_seq; Type: SEQUENCE; Schema: public; Owner: drone
--

CREATE SEQUENCE public.airspace_zones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.airspace_zones_id_seq OWNER TO drone;

--
-- Name: airspace_zones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: drone
--

ALTER SEQUENCE public.airspace_zones_id_seq OWNED BY public.airspace_zones.id;


--
-- Name: assignments; Type: TABLE; Schema: public; Owner: drone
--

CREATE TABLE public.assignments (
    id integer NOT NULL,
    order_id integer NOT NULL,
    drone_id integer NOT NULL,
    score double precision,
    eta_minutes double precision,
    created_at timestamp without time zone
);


ALTER TABLE public.assignments OWNER TO drone;

--
-- Name: assignments_id_seq; Type: SEQUENCE; Schema: public; Owner: drone
--

CREATE SEQUENCE public.assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.assignments_id_seq OWNER TO drone;

--
-- Name: assignments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: drone
--

ALTER SEQUENCE public.assignments_id_seq OWNED BY public.assignments.id;


--
-- Name: carts; Type: TABLE; Schema: public; Owner: drone
--

CREATE TABLE public.carts (
    id integer NOT NULL,
    user_id integer NOT NULL,
    product_id integer NOT NULL,
    quantity integer
);


ALTER TABLE public.carts OWNER TO drone;

--
-- Name: carts_id_seq; Type: SEQUENCE; Schema: public; Owner: drone
--

CREATE SEQUENCE public.carts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.carts_id_seq OWNER TO drone;

--
-- Name: carts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: drone
--

ALTER SEQUENCE public.carts_id_seq OWNED BY public.carts.id;


--
-- Name: dark_stores; Type: TABLE; Schema: public; Owner: drone
--

CREATE TABLE public.dark_stores (
    id integer NOT NULL,
    name character varying(120) NOT NULL,
    latitude double precision NOT NULL,
    longitude double precision NOT NULL,
    address character varying(255) NOT NULL,
    inventory_capacity integer,
    charging_slots integer,
    active_drones integer,
    available_stock integer,
    created_at timestamp without time zone,
    location public.geometry(Point,4326)
);


ALTER TABLE public.dark_stores OWNER TO drone;

--
-- Name: dark_stores_id_seq; Type: SEQUENCE; Schema: public; Owner: drone
--

CREATE SEQUENCE public.dark_stores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dark_stores_id_seq OWNER TO drone;

--
-- Name: dark_stores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: drone
--

ALTER SEQUENCE public.dark_stores_id_seq OWNED BY public.dark_stores.id;


--
-- Name: drones; Type: TABLE; Schema: public; Owner: drone
--

CREATE TABLE public.drones (
    id integer NOT NULL,
    model character varying(120) NOT NULL,
    max_payload double precision NOT NULL,
    max_range double precision NOT NULL,
    battery_capacity double precision NOT NULL,
    current_battery double precision NOT NULL,
    latitude double precision NOT NULL,
    longitude double precision NOT NULL,
    status character varying(40),
    dark_store_id integer,
    location public.geometry(Point,4326)
);


ALTER TABLE public.drones OWNER TO drone;

--
-- Name: drones_id_seq; Type: SEQUENCE; Schema: public; Owner: drone
--

CREATE SEQUENCE public.drones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.drones_id_seq OWNER TO drone;

--
-- Name: drones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: drone
--

ALTER SEQUENCE public.drones_id_seq OWNED BY public.drones.id;


--
-- Name: orders; Type: TABLE; Schema: public; Owner: drone
--

CREATE TABLE public.orders (
    id integer NOT NULL,
    customer_id integer NOT NULL,
    dark_store_id integer,
    order_type character varying(30) NOT NULL,
    status character varying(40),
    payload_weight double precision,
    priority boolean,
    fragile boolean,
    pickup_lat double precision NOT NULL,
    pickup_lng double precision NOT NULL,
    dropoff_lat double precision NOT NULL,
    dropoff_lng double precision NOT NULL,
    eta_minutes double precision,
    predicted_battery_usage double precision,
    route public.geometry(LineString,4326),
    route_points json,
    items json,
    created_at timestamp without time zone,
    delivered_at timestamp without time zone
);


ALTER TABLE public.orders OWNER TO drone;

--
-- Name: orders_id_seq; Type: SEQUENCE; Schema: public; Owner: drone
--

CREATE SEQUENCE public.orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.orders_id_seq OWNER TO drone;

--
-- Name: orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: drone
--

ALTER SEQUENCE public.orders_id_seq OWNED BY public.orders.id;


--
-- Name: products; Type: TABLE; Schema: public; Owner: drone
--

CREATE TABLE public.products (
    id integer NOT NULL,
    name character varying(120) NOT NULL,
    category character varying(80) NOT NULL,
    price double precision NOT NULL,
    weight_kg double precision,
    stock integer,
    dark_store_id integer
);


ALTER TABLE public.products OWNER TO drone;

--
-- Name: products_id_seq; Type: SEQUENCE; Schema: public; Owner: drone
--

CREATE SEQUENCE public.products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.products_id_seq OWNER TO drone;

--
-- Name: products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: drone
--

ALTER SEQUENCE public.products_id_seq OWNED BY public.products.id;


--
-- Name: simulation_configs; Type: TABLE; Schema: public; Owner: drone
--

CREATE TABLE public.simulation_configs (
    id integer NOT NULL,
    running boolean,
    failure_probability double precision,
    telemetry_interval integer,
    max_orders integer,
    notes text
);


ALTER TABLE public.simulation_configs OWNER TO drone;

--
-- Name: simulation_configs_id_seq; Type: SEQUENCE; Schema: public; Owner: drone
--

CREATE SEQUENCE public.simulation_configs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.simulation_configs_id_seq OWNER TO drone;

--
-- Name: simulation_configs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: drone
--

ALTER SEQUENCE public.simulation_configs_id_seq OWNED BY public.simulation_configs.id;


--
-- Name: telemetry; Type: TABLE; Schema: public; Owner: drone
--

CREATE TABLE public.telemetry (
    id integer NOT NULL,
    drone_id integer NOT NULL,
    order_id integer,
    latitude double precision NOT NULL,
    longitude double precision NOT NULL,
    battery double precision NOT NULL,
    speed double precision,
    status character varying(40) NOT NULL,
    created_at timestamp without time zone,
    location public.geometry(Point,4326)
);


ALTER TABLE public.telemetry OWNER TO drone;

--
-- Name: telemetry_id_seq; Type: SEQUENCE; Schema: public; Owner: drone
--

CREATE SEQUENCE public.telemetry_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.telemetry_id_seq OWNER TO drone;

--
-- Name: telemetry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: drone
--

ALTER SEQUENCE public.telemetry_id_seq OWNED BY public.telemetry.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: drone
--

CREATE TABLE public.users (
    id integer NOT NULL,
    name character varying(120) NOT NULL,
    email character varying(255) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    role character varying(30) NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.users OWNER TO drone;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: drone
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO drone;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: drone
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: weather_data; Type: TABLE; Schema: public; Owner: drone
--

CREATE TABLE public.weather_data (
    id integer NOT NULL,
    latitude double precision NOT NULL,
    longitude double precision NOT NULL,
    wind_speed double precision,
    temperature double precision,
    humidity double precision,
    source character varying(60),
    created_at timestamp without time zone
);


ALTER TABLE public.weather_data OWNER TO drone;

--
-- Name: weather_data_id_seq; Type: SEQUENCE; Schema: public; Owner: drone
--

CREATE SEQUENCE public.weather_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.weather_data_id_seq OWNER TO drone;

--
-- Name: weather_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: drone
--

ALTER SEQUENCE public.weather_data_id_seq OWNED BY public.weather_data.id;


--
-- Name: airspace_zones id; Type: DEFAULT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.airspace_zones ALTER COLUMN id SET DEFAULT nextval('public.airspace_zones_id_seq'::regclass);


--
-- Name: assignments id; Type: DEFAULT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.assignments ALTER COLUMN id SET DEFAULT nextval('public.assignments_id_seq'::regclass);


--
-- Name: carts id; Type: DEFAULT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.carts ALTER COLUMN id SET DEFAULT nextval('public.carts_id_seq'::regclass);


--
-- Name: dark_stores id; Type: DEFAULT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.dark_stores ALTER COLUMN id SET DEFAULT nextval('public.dark_stores_id_seq'::regclass);


--
-- Name: drones id; Type: DEFAULT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.drones ALTER COLUMN id SET DEFAULT nextval('public.drones_id_seq'::regclass);


--
-- Name: orders id; Type: DEFAULT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.orders ALTER COLUMN id SET DEFAULT nextval('public.orders_id_seq'::regclass);


--
-- Name: products id; Type: DEFAULT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.products ALTER COLUMN id SET DEFAULT nextval('public.products_id_seq'::regclass);


--
-- Name: simulation_configs id; Type: DEFAULT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.simulation_configs ALTER COLUMN id SET DEFAULT nextval('public.simulation_configs_id_seq'::regclass);


--
-- Name: telemetry id; Type: DEFAULT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.telemetry ALTER COLUMN id SET DEFAULT nextval('public.telemetry_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: weather_data id; Type: DEFAULT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.weather_data ALTER COLUMN id SET DEFAULT nextval('public.weather_data_id_seq'::regclass);


--
-- Data for Name: airspace_zones; Type: TABLE DATA; Schema: public; Owner: drone
--

COPY public.airspace_zones (id, name, zone_type, polygon, coordinates, active, created_at) FROM stdin;
1	Rajiv Gandhi Airport Restriction	airport	0103000020E61000000100000005000000355EBA490C9A5340D34D621058393140355EBA490C9A53406ABC749318443140CBA145B6F39D53406ABC749318443140CBA145B6F39D5340D34D621058393140355EBA490C9A5340D34D621058393140	[[17.224, 78.407], [17.266, 78.407], [17.266, 78.468], [17.224, 78.468]]	t	2026-05-11 12:56:34.676967
2	Hakimpet Air Force Restriction	military	0103000020E61000000100000005000000295C8FC2F5A05340F0A7C64B37893140295C8FC2F5A05340C520B07268913140EC51B81E85A35340C520B07268913140EC51B81E85A35340F0A7C64B37893140295C8FC2F5A05340F0A7C64B37893140	[[17.536, 78.515], [17.568, 78.515], [17.568, 78.555], [17.536, 78.555]]	t	2026-05-11 12:56:34.677875
3	Bolarum Cantonment Restriction	military	0103000020E610000001000000050000000000000000A05340CBA145B6F37D31400000000000A0534066666666668631400AD7A3703DA2534066666666668631400AD7A3703DA25340CBA145B6F37D31400000000000A05340CBA145B6F37D3140	[[17.492, 78.5], [17.525, 78.5], [17.525, 78.535], [17.492, 78.535]]	t	2026-05-11 12:56:34.678215
4	CRPF	temporary restriction	0103000020E61000000100000005000000010000C4209E5340F350DF7D0F52314001000028BC9E53401C9EFE45B352314000000058B99E5340F077E16C7F50314001000094239E53405BE36F2EBD503140010000C4209E5340F350DF7D0F523140	[[17.32054888441139, 78.47074985504152], [17.32304799524546, 78.48023414611818], [17.31444435600855, 78.48006248474121], [17.315386678997452, 78.47092151641847]]	t	2026-05-11 15:40:15.042917
5	Zoo Park	government	0103000020E6100000010000000600000001000008FD9B5340EC7C26EB0B5A314001000030D49C5340B464F2961858314001000048169D5340E29F5BFF125B314001000050C39C5340347F9201795B3140010000F81B9C5340B8F77A42085B314001000008FD9B5340EC7C26EB0B5A3140	[[17.35174436273239, 78.4373188018799], [17.34412520807082, 78.45045089721681], [17.355758628720544, 78.45448493957521], [17.357315157190172, 78.44942092895509], [17.355594782849693, 78.43920707702638]]	t	2026-05-11 15:41:34.322497
6	Research Institute	government	0103000020E61000000100000008000000010000F036985340B5CC65BCBB53314001000000F9985340E0EC810B7D543140010000C047995340F4AF9CEF6C543140010000C074995340ACA6E8A1A254314001000048BF995340FEBF65278D543140010000F0259A5340B2A8552127543140010000702E995340DCBF0457C8513140010000F036985340B5CC65BCBB533140	[[17.32708337292998, 78.3783531188965], [17.330033034534495, 78.39019775390626], [17.32978723121046, 78.39500427246095], [17.33060657434423, 78.3977508544922], [17.33027883752947, 78.40229988098146], [17.328722079670747, 78.40856552124025], [17.319463194522413, 78.39345932006837]]	t	2026-05-11 15:42:09.447063
7	Research Center Imarat	government	0103000020E6100000010000000B000000000000107A9E534035AEE44DD944314001000050859E5340A72212D87D4131400100008044A053400540139FC83B3140010000E04CA15340C296A8D03E3C31400100004074A153403258F0322B3D3140010000D0B7A05340999124C48D3E3140010000A0E7A05340145F50755F4231400100007090A05340DDDDBECF4B4331400100007063A05340F57D5B13B9443140010000E08A9F5340B913D1375A453140000000107A9E534035AEE44DD9443140	[[17.268940800028037, 78.47620010375977], [17.25582647745855, 78.47688674926759], [17.233529989433027, 78.50418090820314], [17.23533348194065, 78.52031707763673], [17.238940414121494, 78.52272033691408], [17.244350680282512, 78.51121902465822], [17.2592690774173, 78.51413726806642], [17.262875541780762, 78.50881576538087], [17.26844902976696, 78.50606918334962], [17.27090786795063, 78.49285125732423]]	t	2026-05-11 15:42:52.641286
\.


--
-- Data for Name: assignments; Type: TABLE DATA; Schema: public; Owner: drone
--

COPY public.assignments (id, order_id, drone_id, score, eta_minutes, created_at) FROM stdin;
1	1	13	0	14	2026-05-11 13:10:59.159841
2	2	21	13.919882383042589	25.9	2026-05-11 15:19:11.411251
3	3	13	0	15.2	2026-05-11 16:04:42.987147
4	4	17	0	19.3	2026-05-11 16:15:32.972123
5	5	22	17.690725632935617	26.1	2026-05-11 16:15:50.688626
6	6	21	0	12.9	2026-05-13 05:38:30.683189
7	7	21	0	15.4	2026-05-13 07:56:54.407144
8	8	2	7.314411050493542	9.4	2026-05-13 08:00:24.086262
9	9	16	0	16	2026-05-13 08:06:09.398266
10	10	22	7.845496547814526	13.1	2026-05-13 08:13:13.000758
\.


--
-- Data for Name: carts; Type: TABLE DATA; Schema: public; Owner: drone
--

COPY public.carts (id, user_id, product_id, quantity) FROM stdin;
\.


--
-- Data for Name: dark_stores; Type: TABLE DATA; Schema: public; Owner: drone
--

COPY public.dark_stores (id, name, latitude, longitude, address, inventory_capacity, charging_slots, active_drones, available_stock, created_at, location) FROM stdin;
1	Gachibowli Hub	17.4401	78.3489	Gachibowli, Hyderabad	5200	14	0	4800	2026-05-11 12:56:34.664676	0101000020E6100000C364AA605496534038F8C264AA703140
2	Madhapur Hub	17.4483	78.3915	Madhapur, Hyderabad	4600	12	0	4100	2026-05-11 12:56:34.666577	0101000020E6100000931804560E995340FBCBEEC9C3723140
3	Kukatpally Hub	17.4948	78.3996	Kukatpally, Hyderabad	4300	10	0	3900	2026-05-11 12:56:34.666956	0101000020E6100000D3DEE00B93995340910F7A36AB7E3140
5	LB Nagar Hub	17.3457	78.5522	LB Nagar, Hyderabad	3900	9	0	3598	2026-05-11 12:56:34.667616	0101000020E61000007A36AB3E57A353402A3A92CB7F583140
6	Uppal Hub	17.4058	78.5591	Uppal, Hyderabad	4100	10	0	3746	2026-05-11 12:56:34.66793	0101000020E610000064CC5D4BC8A3534080B74082E2673140
4	Secunderabad Hub	17.4399	78.4983	Secunderabad, Hyderabad	5000	13	0	4543	2026-05-11 12:56:34.667293	0101000020E610000032E6AE25E49F5340AA8251499D703140
\.


--
-- Data for Name: drones; Type: TABLE DATA; Schema: public; Owner: drone
--

COPY public.drones (id, model, max_payload, max_range, battery_capacity, current_battery, latitude, longitude, status, dark_store_id, location) FROM stdin;
3	AeroSwift-12	6	38	100	100	17.4401	78.3489	idle	1	0101000020E6100000C364AA605496534038F8C264AA703140
4	AeroSwift-13	6.5	38	100	100	17.4401	78.3489	idle	1	0101000020E6100000C364AA605496534038F8C264AA703140
5	AeroSwift-20	5	38	100	100	17.4483	78.3915	idle	2	0101000020E6100000931804560E995340FBCBEEC9C3723140
6	AeroSwift-21	5.5	38	100	100	17.4483	78.3915	idle	2	0101000020E6100000931804560E995340FBCBEEC9C3723140
7	AeroSwift-22	6	38	100	100	17.4483	78.3915	idle	2	0101000020E6100000931804560E995340FBCBEEC9C3723140
8	AeroSwift-23	6.5	38	100	100	17.4483	78.3915	idle	2	0101000020E6100000931804560E995340FBCBEEC9C3723140
9	AeroSwift-30	5	38	100	100	17.4948	78.3996	idle	3	0101000020E6100000D3DEE00B93995340910F7A36AB7E3140
10	AeroSwift-31	5.5	38	100	100	17.4948	78.3996	idle	3	0101000020E6100000D3DEE00B93995340910F7A36AB7E3140
11	AeroSwift-32	6	38	100	100	17.4948	78.3996	idle	3	0101000020E6100000D3DEE00B93995340910F7A36AB7E3140
12	AeroSwift-33	6.5	38	100	100	17.4948	78.3996	idle	3	0101000020E6100000D3DEE00B93995340910F7A36AB7E3140
13	AeroSwift-40	5	38	100	100	17.4399	78.4983	idle	4	0101000020E610000032E6AE25E49F5340AA8251499D703140
14	AeroSwift-41	5.5	38	100	100	17.4399	78.4983	idle	4	0101000020E610000032E6AE25E49F5340AA8251499D703140
15	AeroSwift-42	6	38	100	100	17.4399	78.4983	idle	4	0101000020E610000032E6AE25E49F5340AA8251499D703140
16	AeroSwift-43	6.5	38	100	100	17.4399	78.4983	idle	4	0101000020E610000032E6AE25E49F5340AA8251499D703140
17	AeroSwift-50	5	38	100	100	17.3457	78.5522	idle	5	0101000020E61000007A36AB3E57A353402A3A92CB7F583140
18	AeroSwift-51	5.5	38	100	100	17.3457	78.5522	idle	5	0101000020E61000007A36AB3E57A353402A3A92CB7F583140
19	AeroSwift-52	6	38	100	100	17.3457	78.5522	idle	5	0101000020E61000007A36AB3E57A353402A3A92CB7F583140
20	AeroSwift-53	6.5	38	100	100	17.3457	78.5522	idle	5	0101000020E61000007A36AB3E57A353402A3A92CB7F583140
22	AeroSwift-61	5.5	38	100	100	17.4058	78.5591	assigned	6	0101000020E610000064CC5D4BC8A3534080B74082E2673140
23	AeroSwift-62	6	38	100	100	17.4058	78.5591	idle	6	0101000020E610000064CC5D4BC8A3534080B74082E2673140
24	AeroSwift-63	6.5	38	100	100	17.4058	78.5591	idle	6	0101000020E610000064CC5D4BC8A3534080B74082E2673140
21	AeroSwift-60	5	38	100	91.38411210361804	17.3875	78.577143	failed	6	0101000020E6100000628731E9EFA453403333333333633140
2	AeroSwift-11	5.5	38	100	0	17.438256872118384	78.36513519287111	failed	1	0101000020E6100000010000605E975340E7FE349A31703140
1	AeroSwift-10	5	38	100	100	17.4401	78.3489	idle	1	0101000020E6100000C364AA605496534038F8C264AA703140
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: drone
--

COPY public.orders (id, customer_id, dark_store_id, order_type, status, payload_weight, priority, fragile, pickup_lat, pickup_lng, dropoff_lat, dropoff_lng, eta_minutes, predicted_battery_usage, route, route_points, items, created_at, delivered_at) FROM stdin;
6	2	6	grocery	Delivered	1.5	f	f	17.4058	78.5591	17.38242259206954	78.57284545898439	12.9	20.619688129889372	0102000020E61000000400000064CC5D4BC8A3534080B74082E26731400F9D9E7763A4534085EB51B81E6531400F9D9E7763A45340333333333363314001000080A9A45340B2306E72E6613140	[[17.4058, 78.5591], [17.395, 78.568571], [17.3875, 78.568571], [17.38242259206954, 78.57284545898439]]	[{"product_id": 1, "name": "Fresh Milk", "quantity": 1}, {"product_id": 2, "name": "Greek Yogurt", "quantity": 1}]	2026-05-13 05:38:30.677275	2026-05-13 05:38:59.090923
1	2	4	grocery	Delivered	1	f	f	17.4399	78.4983	17.406666634018343	78.4962844848633	14	17.74192282451741	0102000020E61000000500000032E6AE25E49F5340AA8251499D7031400000000000A053401F85EB51B86E31400000000000A05340CDCCCCCCCC6C31400000000000A053407B14AE47E16A314001000020C39F5340B27BF54D1B683140	[[17.4399, 78.4983], [17.4325, 78.5], [17.425, 78.5], [17.4175, 78.5], [17.406666634018343, 78.4962844848633]]	[{"product_id": 1, "name": "Fresh Milk", "quantity": 1}]	2026-05-11 13:10:59.155703	2026-05-11 13:11:06.861359
2	2	\N	package	Delivered	1.5	f	f	17.397329782184343	78.52752685546875	17.401916365483153	78.42212677001953	25.9	36.571272730382574	0102000020E61000000D00000000000000C3A1534064359467B7653140BE16F4DE18A15340D7A3703D0A6731406B2C616D8CA05340D7A3703D0A6731400000000000A05340D7A3703D0A67314095D39E92739F5340D7A3703D0A67314042E90B21E79E5340D7A3703D0A673140D8BCAAB35A9E5340D7A3703D0A67314085D21742CE9D5340D7A3703D0A6731401AA6B6D4419D5340D7A3703D0A673140C7BB2363B59C5340D7A3703D0A6731405C8FC2F5289C5340D7A3703D0A673140F16261889C9B5340D7A3703D0A67314000000020049B5340327AADFDE3663140	[[17.397329782184343, 78.52752685546875], [17.4025, 78.517143], [17.4025, 78.508571], [17.4025, 78.5], [17.4025, 78.491429], [17.4025, 78.482857], [17.4025, 78.474286], [17.4025, 78.465714], [17.4025, 78.457143], [17.4025, 78.448571], [17.4025, 78.44], [17.4025, 78.431429], [17.401916365483153, 78.42212677001953]]	[{"type": "Documents"}]	2026-05-11 15:19:11.407029	2026-05-11 15:19:34.320589
5	2	\N	package	Delivered	1.5	f	f	17.425175122940146	78.5955047607422	17.381931125561547	78.50589752197266	26.1	38.23885206270781	0102000020E61000000B000000010000C01CA65340C819E046D86C3140CCB392567CA553407B14AE47E16A3140628731E9EFA45340295C8FC2F56831400F9D9E7763A45340D7A3703D0A673140A4703D0AD7A3534085EB51B81E6531403944DC9C4AA353403333333333633140E659492BBEA25340E17A14AE476131407B2DE8BD31A25340E17A14AE476131402843554CA5A15340E17A14AE47613140BE16F4DE18A15340E17A14AE47613140000000A060A053407F9CFD3CC6613140	[[17.425175122940146, 78.5955047607422], [17.4175, 78.585714], [17.41, 78.577143], [17.4025, 78.568571], [17.395, 78.56], [17.3875, 78.551429], [17.38, 78.542857], [17.38, 78.534286], [17.38, 78.525714], [17.38, 78.517143], [17.381931125561547, 78.50589752197266]]	[{"type": "Documents"}]	2026-05-11 16:15:50.686707	2026-05-11 16:18:28.239451
4	2	5	grocery	Delivered	1.5	f	f	17.3457	78.5522	17.35489843626487	78.61507415771486	19.3	25.476900619939276	0102000020E6100000080000007A36AB3E57A353402A3A92CB7F583140A4703D0AD7A353409A999999995931400F9D9E7763A45340EC51B81E855B3140628731E9EFA45340EC51B81E855B3140CCB392567CA55340EC51B81E855B31401F9E25C808A65340EC51B81E855B31408ACA863595A65340EC51B81E855B3140010000605DA75340BF28B99FDA5A3140	[[17.3457, 78.5522], [17.35, 78.56], [17.3575, 78.568571], [17.3575, 78.577143], [17.3575, 78.585714], [17.3575, 78.594286], [17.3575, 78.602857], [17.35489843626487, 78.61507415771486]]	[{"product_id": 1, "name": "Fresh Milk", "quantity": 1}, {"product_id": 2, "name": "Greek Yogurt", "quantity": 1}]	2026-05-11 16:15:32.956971	2026-05-11 16:18:41.257528
3	2	4	grocery	Delivered	1.6	f	f	17.4399	78.4983	17.405356227442883	78.48117828369142	15.2	20.451452210593036	0102000020E61000000600000032E6AE25E49F5340AA8251499D70314095D39E92739F53401F85EB51B86E314042E90B21E79E5340CDCCCCCCCC6C314042E90B21E79E53407B14AE47E16A314042E90B21E79E5340295C8FC2F5683140010000A0CB9E5340DD18FC6CC5673140	[[17.4399, 78.4983], [17.4325, 78.491429], [17.425, 78.482857], [17.4175, 78.482857], [17.41, 78.482857], [17.405356227442883, 78.48117828369142]]	[{"product_id": 27, "name": "Orange Juice", "quantity": 1}, {"product_id": 20, "name": "Cornflakes", "quantity": 1}]	2026-05-11 16:04:42.980143	2026-05-11 16:04:52.390924
9	2	4	grocery	Delivered	6.2	f	f	17.4399	78.4983	17.40117924378447	78.47954750061037	16	39.313676308090294	0102000020E61000000600000032E6AE25E49F5340AA8251499D70314095D39E92739F53401F85EB51B86E314042E90B21E79E5340CDCCCCCCCC6C314042E90B21E79E53407B14AE47E16A314042E90B21E79E5340295C8FC2F5683140010000E8B09E534068E3D3AEB3663140	[[17.4399, 78.4983], [17.4325, 78.491429], [17.425, 78.482857], [17.4175, 78.482857], [17.41, 78.482857], [17.40117924378447, 78.47954750061037]]	[{"product_id": 1, "name": "Fresh Milk", "quantity": 1}, {"product_id": 4, "name": "Bananas", "quantity": 1}, {"product_id": 9, "name": "Basmati Rice", "quantity": 1}, {"product_id": 5, "name": "Tomatoes", "quantity": 2}]	2026-05-13 08:06:09.396205	2026-05-13 08:07:01.488096
10	2	\N	package	Assigned	2	f	f	17.404578169093373	78.54065895080568	17.39483168395773	78.51551055908205	13.1	23.046037548231983	0102000020E610000004000000010000289AA253407DEE546F926731407B2DE8BD31A2534085EB51B81E6531402843554CA5A1534085EB51B81E65314001000020FEA05340E70572B013653140	[[17.404578169093373, 78.54065895080568], [17.395, 78.534286], [17.395, 78.525714], [17.39483168395773, 78.51551055908205]]	[{"type": "Parcel"}]	2026-05-13 08:13:12.999258	\N
7	2	6	grocery	Failed	0.8	f	f	17.4058	78.5591	17.374558969601914	78.58795166015626	15.4	21.53971974095489	0102000020E61000000500000064CC5D4BC8A3534080B74082E26731400F9D9E7763A4534085EB51B81E653140628731E9EFA453403333333333633140CCB392567CA55340E17A14AE4761314001000000A1A553401ADDBC18E35F3140	[[17.4058, 78.5591], [17.395, 78.568571], [17.3875, 78.577143], [17.38, 78.585714], [17.374558969601914, 78.58795166015626]]	[{"product_id": 2, "name": "Greek Yogurt", "quantity": 1}, {"product_id": 3, "name": "Cheese Slices", "quantity": 1}]	2026-05-13 07:56:54.398569	\N
8	2	\N	package	Failed	1.5	f	f	17.430743681670446	78.36307525634767	17.438256872118384	78.36513519287111	9.4	16.575802487252346	0102000020E610000002000000010000A03C975340B3BBC937456E3140010000605E975340E7FE349A31703140	[[17.430743681670446, 78.36307525634767], [17.438256872118384, 78.36513519287111]]	[{"type": "Documents"}]	2026-05-13 08:00:24.084543	\N
\.


--
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: drone
--

COPY public.products (id, name, category, price, weight_kg, stock, dark_store_id) FROM stdin;
1	Fresh Milk	Dairy	68	1	240	1
2	Greek Yogurt	Dairy	95	0.5	240	1
3	Cheese Slices	Dairy	140	0.3	240	1
4	Bananas	Produce	55	1.2	240	1
5	Tomatoes	Produce	42	1	240	1
6	Potatoes	Produce	38	1	240	1
7	Onions	Produce	36	1	240	1
8	Coriander Bunch	Produce	18	0.1	240	1
9	Basmati Rice	Staples	210	2	240	1
10	Toor Dal	Staples	165	1	240	1
11	Atta	Staples	235	5	240	1
12	Sunflower Oil	Staples	155	1	240	1
13	Bread	Bakery	45	0.4	240	1
14	Brown Bread	Bakery	60	0.45	240	1
15	Croissant Pack	Bakery	120	0.35	240	1
16	Eggs Pack	Dairy	92	0.7	240	1
17	Instant Coffee	Pantry	180	0.2	240	1
18	Tea Powder	Pantry	145	0.25	240	1
19	Peanut Butter	Pantry	220	0.5	240	1
20	Cornflakes	Breakfast	185	0.6	240	1
21	Oats	Breakfast	150	1	240	1
22	Apples	Produce	160	1	240	1
23	Paneer	Dairy	120	0.5	240	1
24	Dark Chocolate	Snacks	110	0.1	240	1
25	Potato Chips	Snacks	40	0.08	240	1
26	Cookies	Snacks	75	0.2	240	1
27	Orange Juice	Beverages	115	1	240	1
28	Mineral Water	Beverages	30	1	240	1
29	Energy Drink	Beverages	95	0.3	240	1
30	Toothpaste	Personal Care	85	0.15	240	1
31	Shampoo	Personal Care	190	0.35	240	1
32	Dishwash Liquid	Home Care	125	0.7	240	1
33	Laundry Detergent	Home Care	260	1	240	1
34	Fresh Milk	Dairy	68	1	240	2
35	Greek Yogurt	Dairy	95	0.5	240	2
36	Cheese Slices	Dairy	140	0.3	240	2
37	Bananas	Produce	55	1.2	240	2
38	Tomatoes	Produce	42	1	240	2
39	Potatoes	Produce	38	1	240	2
40	Onions	Produce	36	1	240	2
41	Coriander Bunch	Produce	18	0.1	240	2
42	Basmati Rice	Staples	210	2	240	2
43	Toor Dal	Staples	165	1	240	2
44	Atta	Staples	235	5	240	2
45	Sunflower Oil	Staples	155	1	240	2
46	Bread	Bakery	45	0.4	240	2
47	Brown Bread	Bakery	60	0.45	240	2
48	Croissant Pack	Bakery	120	0.35	240	2
49	Eggs Pack	Dairy	92	0.7	240	2
50	Instant Coffee	Pantry	180	0.2	240	2
51	Tea Powder	Pantry	145	0.25	240	2
52	Peanut Butter	Pantry	220	0.5	240	2
53	Cornflakes	Breakfast	185	0.6	240	2
54	Oats	Breakfast	150	1	240	2
55	Apples	Produce	160	1	240	2
56	Paneer	Dairy	120	0.5	240	2
57	Dark Chocolate	Snacks	110	0.1	240	2
58	Potato Chips	Snacks	40	0.08	240	2
59	Cookies	Snacks	75	0.2	240	2
60	Orange Juice	Beverages	115	1	240	2
61	Mineral Water	Beverages	30	1	240	2
62	Energy Drink	Beverages	95	0.3	240	2
63	Toothpaste	Personal Care	85	0.15	240	2
64	Shampoo	Personal Care	190	0.35	240	2
65	Dishwash Liquid	Home Care	125	0.7	240	2
66	Laundry Detergent	Home Care	260	1	240	2
67	Fresh Milk	Dairy	68	1	240	3
68	Greek Yogurt	Dairy	95	0.5	240	3
69	Cheese Slices	Dairy	140	0.3	240	3
70	Bananas	Produce	55	1.2	240	3
71	Tomatoes	Produce	42	1	240	3
72	Potatoes	Produce	38	1	240	3
73	Onions	Produce	36	1	240	3
74	Coriander Bunch	Produce	18	0.1	240	3
75	Basmati Rice	Staples	210	2	240	3
76	Toor Dal	Staples	165	1	240	3
77	Atta	Staples	235	5	240	3
78	Sunflower Oil	Staples	155	1	240	3
79	Bread	Bakery	45	0.4	240	3
80	Brown Bread	Bakery	60	0.45	240	3
81	Croissant Pack	Bakery	120	0.35	240	3
82	Eggs Pack	Dairy	92	0.7	240	3
83	Instant Coffee	Pantry	180	0.2	240	3
84	Tea Powder	Pantry	145	0.25	240	3
85	Peanut Butter	Pantry	220	0.5	240	3
86	Cornflakes	Breakfast	185	0.6	240	3
87	Oats	Breakfast	150	1	240	3
88	Apples	Produce	160	1	240	3
89	Paneer	Dairy	120	0.5	240	3
90	Dark Chocolate	Snacks	110	0.1	240	3
91	Potato Chips	Snacks	40	0.08	240	3
92	Cookies	Snacks	75	0.2	240	3
93	Orange Juice	Beverages	115	1	240	3
94	Mineral Water	Beverages	30	1	240	3
95	Energy Drink	Beverages	95	0.3	240	3
96	Toothpaste	Personal Care	85	0.15	240	3
97	Shampoo	Personal Care	190	0.35	240	3
98	Dishwash Liquid	Home Care	125	0.7	240	3
99	Laundry Detergent	Home Care	260	1	240	3
100	Fresh Milk	Dairy	68	1	240	4
101	Greek Yogurt	Dairy	95	0.5	240	4
102	Cheese Slices	Dairy	140	0.3	240	4
103	Bananas	Produce	55	1.2	240	4
104	Tomatoes	Produce	42	1	240	4
105	Potatoes	Produce	38	1	240	4
106	Onions	Produce	36	1	240	4
107	Coriander Bunch	Produce	18	0.1	240	4
108	Basmati Rice	Staples	210	2	240	4
109	Toor Dal	Staples	165	1	240	4
110	Atta	Staples	235	5	240	4
111	Sunflower Oil	Staples	155	1	240	4
112	Bread	Bakery	45	0.4	240	4
113	Brown Bread	Bakery	60	0.45	240	4
114	Croissant Pack	Bakery	120	0.35	240	4
115	Eggs Pack	Dairy	92	0.7	240	4
116	Instant Coffee	Pantry	180	0.2	240	4
117	Tea Powder	Pantry	145	0.25	240	4
118	Peanut Butter	Pantry	220	0.5	240	4
119	Cornflakes	Breakfast	185	0.6	240	4
120	Oats	Breakfast	150	1	240	4
121	Apples	Produce	160	1	240	4
122	Paneer	Dairy	120	0.5	240	4
123	Dark Chocolate	Snacks	110	0.1	240	4
124	Potato Chips	Snacks	40	0.08	240	4
125	Cookies	Snacks	75	0.2	240	4
126	Orange Juice	Beverages	115	1	240	4
127	Mineral Water	Beverages	30	1	240	4
128	Energy Drink	Beverages	95	0.3	240	4
129	Toothpaste	Personal Care	85	0.15	240	4
130	Shampoo	Personal Care	190	0.35	240	4
131	Dishwash Liquid	Home Care	125	0.7	240	4
132	Laundry Detergent	Home Care	260	1	240	4
133	Fresh Milk	Dairy	68	1	240	5
134	Greek Yogurt	Dairy	95	0.5	240	5
135	Cheese Slices	Dairy	140	0.3	240	5
136	Bananas	Produce	55	1.2	240	5
137	Tomatoes	Produce	42	1	240	5
138	Potatoes	Produce	38	1	240	5
139	Onions	Produce	36	1	240	5
140	Coriander Bunch	Produce	18	0.1	240	5
141	Basmati Rice	Staples	210	2	240	5
142	Toor Dal	Staples	165	1	240	5
143	Atta	Staples	235	5	240	5
144	Sunflower Oil	Staples	155	1	240	5
145	Bread	Bakery	45	0.4	240	5
146	Brown Bread	Bakery	60	0.45	240	5
147	Croissant Pack	Bakery	120	0.35	240	5
148	Eggs Pack	Dairy	92	0.7	240	5
149	Instant Coffee	Pantry	180	0.2	240	5
150	Tea Powder	Pantry	145	0.25	240	5
151	Peanut Butter	Pantry	220	0.5	240	5
152	Cornflakes	Breakfast	185	0.6	240	5
153	Oats	Breakfast	150	1	240	5
154	Apples	Produce	160	1	240	5
155	Paneer	Dairy	120	0.5	240	5
156	Dark Chocolate	Snacks	110	0.1	240	5
157	Potato Chips	Snacks	40	0.08	240	5
158	Cookies	Snacks	75	0.2	240	5
159	Orange Juice	Beverages	115	1	240	5
160	Mineral Water	Beverages	30	1	240	5
161	Energy Drink	Beverages	95	0.3	240	5
162	Toothpaste	Personal Care	85	0.15	240	5
163	Shampoo	Personal Care	190	0.35	240	5
164	Dishwash Liquid	Home Care	125	0.7	240	5
165	Laundry Detergent	Home Care	260	1	240	5
166	Fresh Milk	Dairy	68	1	240	6
167	Greek Yogurt	Dairy	95	0.5	240	6
168	Cheese Slices	Dairy	140	0.3	240	6
169	Bananas	Produce	55	1.2	240	6
170	Tomatoes	Produce	42	1	240	6
171	Potatoes	Produce	38	1	240	6
172	Onions	Produce	36	1	240	6
173	Coriander Bunch	Produce	18	0.1	240	6
174	Basmati Rice	Staples	210	2	240	6
175	Toor Dal	Staples	165	1	240	6
176	Atta	Staples	235	5	240	6
177	Sunflower Oil	Staples	155	1	240	6
178	Bread	Bakery	45	0.4	240	6
179	Brown Bread	Bakery	60	0.45	240	6
180	Croissant Pack	Bakery	120	0.35	240	6
181	Eggs Pack	Dairy	92	0.7	240	6
182	Instant Coffee	Pantry	180	0.2	240	6
183	Tea Powder	Pantry	145	0.25	240	6
184	Peanut Butter	Pantry	220	0.5	240	6
185	Cornflakes	Breakfast	185	0.6	240	6
186	Oats	Breakfast	150	1	240	6
187	Apples	Produce	160	1	240	6
188	Paneer	Dairy	120	0.5	240	6
189	Dark Chocolate	Snacks	110	0.1	240	6
190	Potato Chips	Snacks	40	0.08	240	6
191	Cookies	Snacks	75	0.2	240	6
192	Orange Juice	Beverages	115	1	240	6
193	Mineral Water	Beverages	30	1	240	6
194	Energy Drink	Beverages	95	0.3	240	6
195	Toothpaste	Personal Care	85	0.15	240	6
196	Shampoo	Personal Care	190	0.35	240	6
197	Dishwash Liquid	Home Care	125	0.7	240	6
198	Laundry Detergent	Home Care	260	1	240	6
\.


--
-- Data for Name: simulation_configs; Type: TABLE DATA; Schema: public; Owner: drone
--

COPY public.simulation_configs (id, running, failure_probability, telemetry_interval, max_orders, notes) FROM stdin;
1	f	1	13	20	
\.


--
-- Data for Name: spatial_ref_sys; Type: TABLE DATA; Schema: public; Owner: tejaramidi
--

COPY public.spatial_ref_sys (srid, auth_name, auth_srid, srtext, proj4text) FROM stdin;
\.


--
-- Data for Name: telemetry; Type: TABLE DATA; Schema: public; Owner: drone
--

COPY public.telemetry (id, drone_id, order_id, latitude, longitude, battery, speed, status, created_at, location) FROM stdin;
1	13	1	17.4325	78.5	96.45161543509651	38	Taking Off	2026-05-11 13:11:00.824243	0101000020E61000000000000000A053401F85EB51B86E3140
2	13	1	17.425	78.5	92.90323087019303	38	In Flight	2026-05-11 13:11:02.84102	0101000020E61000000000000000A05340CDCCCCCCCC6C3140
3	13	1	17.4175	78.5	89.35484630528954	38	In Flight	2026-05-11 13:11:04.851571	0101000020E61000000000000000A053407B14AE47E16A3140
4	13	1	17.4399	78.4983	100	38	Delivered	2026-05-11 13:11:06.864112	0101000020E610000032E6AE25E49F5340AA8251499D703140
5	21	2	17.4025	78.517143	97.18682517458596	38	Taking Off	2026-05-11 15:19:12.182639	0101000020E6100000BE16F4DE18A15340D7A3703D0A673140
6	21	2	17.4025	78.508571	94.37365034917192	38	In Flight	2026-05-11 15:19:14.197596	0101000020E61000006B2C616D8CA05340D7A3703D0A673140
7	21	2	17.4025	78.5	91.56047552375789	38	In Flight	2026-05-11 15:19:16.209262	0101000020E61000000000000000A05340D7A3703D0A673140
8	21	2	17.4025	78.491429	88.74730069834385	38	In Flight	2026-05-11 15:19:18.224266	0101000020E610000095D39E92739F5340D7A3703D0A673140
9	21	2	17.4025	78.482857	85.93412587292981	38	In Flight	2026-05-11 15:19:20.239608	0101000020E610000042E90B21E79E5340D7A3703D0A673140
10	21	2	17.4025	78.474286	83.12095104751577	38	In Flight	2026-05-11 15:19:22.252079	0101000020E6100000D8BCAAB35A9E5340D7A3703D0A673140
11	21	2	17.4025	78.465714	80.30777622210174	38	In Flight	2026-05-11 15:19:24.261532	0101000020E610000085D21742CE9D5340D7A3703D0A673140
12	21	2	17.4025	78.457143	77.4946013966877	38	In Flight	2026-05-11 15:19:26.273397	0101000020E61000001AA6B6D4419D5340D7A3703D0A673140
13	21	2	17.4025	78.448571	74.68142657127366	38	In Flight	2026-05-11 15:19:28.285691	0101000020E6100000C7BB2363B59C5340D7A3703D0A673140
14	21	2	17.4025	78.44	71.86825174585962	38	In Flight	2026-05-11 15:19:30.298403	0101000020E61000005C8FC2F5289C5340D7A3703D0A673140
15	21	2	17.4025	78.431429	69.05507692044559	38	In Flight	2026-05-11 15:19:32.310577	0101000020E6100000F16261889C9B5340D7A3703D0A673140
16	21	2	17.4058	78.5591	100	38	Delivered	2026-05-11 15:19:34.323312	0101000020E610000064CC5D4BC8A3534080B74082E2673140
17	13	3	17.4325	78.491429	96.59142463156783	38	Taking Off	2026-05-11 16:04:44.349955	0101000020E610000095D39E92739F53401F85EB51B86E3140
18	13	3	17.425	78.482857	93.18284926313567	38	In Flight	2026-05-11 16:04:46.358319	0101000020E610000042E90B21E79E5340CDCCCCCCCC6C3140
19	13	3	17.4175	78.482857	89.7742738947035	38	In Flight	2026-05-11 16:04:48.371517	0101000020E610000042E90B21E79E53407B14AE47E16A3140
20	13	3	17.41	78.482857	86.36569852627133	38	In Flight	2026-05-11 16:04:50.383701	0101000020E610000042E90B21E79E5340295C8FC2F5683140
21	13	3	17.4399	78.4983	100	38	Delivered	2026-05-11 16:04:52.392733	0101000020E610000032E6AE25E49F5340AA8251499D703140
22	22	5	17.3875	78.551429	96.52374072157201	38	In Flight	2026-05-11 16:17:23.155589	0101000020E61000003944DC9C4AA353403333333333633140
23	17	4	17.35	78.56	96.81538742250758	38	Taking Off	2026-05-11 16:17:23.157692	0101000020E6100000A4703D0AD7A353409A99999999593140
24	17	4	17.3575	78.568571	93.63077484501517	38	In Flight	2026-05-11 16:17:36.175943	0101000020E61000000F9D9E7763A45340EC51B81E855B3140
25	22	5	17.38	78.542857	93.04748144314402	38	In Flight	2026-05-11 16:17:36.177117	0101000020E6100000E659492BBEA25340E17A14AE47613140
26	22	5	17.38	78.534286	89.57122216471603	38	In Flight	2026-05-11 16:17:49.187774	0101000020E61000007B2DE8BD31A25340E17A14AE47613140
27	17	4	17.3575	78.577143	90.44616226752275	38	In Flight	2026-05-11 16:17:49.189991	0101000020E6100000628731E9EFA45340EC51B81E855B3140
28	22	5	17.38	78.525714	86.09496288628804	38	In Flight	2026-05-11 16:18:02.203152	0101000020E61000002843554CA5A15340E17A14AE47613140
29	17	4	17.3575	78.585714	87.26154969003034	38	In Flight	2026-05-11 16:18:02.204338	0101000020E6100000CCB392567CA55340EC51B81E855B3140
30	22	5	17.38	78.517143	82.61870360786006	38	In Flight	2026-05-11 16:18:15.228125	0101000020E6100000BE16F4DE18A15340E17A14AE47613140
31	17	4	17.3575	78.594286	84.07693711253792	38	In Flight	2026-05-11 16:18:15.229565	0101000020E61000001F9E25C808A65340EC51B81E855B3140
32	22	5	17.4058	78.5591	100	38	Delivered	2026-05-11 16:18:28.244621	0101000020E610000064CC5D4BC8A3534080B74082E2673140
33	17	4	17.3575	78.602857	80.8923245350455	38	In Flight	2026-05-11 16:18:28.246288	0101000020E61000008ACA863595A65340EC51B81E855B3140
34	17	4	17.3457	78.5522	100	38	Delivered	2026-05-11 16:18:41.259654	0101000020E61000007A36AB3E57A353402A3A92CB7F583140
35	21	6	17.395	78.568571	94.84507796752766	38	Taking Off	2026-05-13 05:38:33.066594	0101000020E61000000F9D9E7763A4534085EB51B81E653140
36	21	6	17.3875	78.568571	89.69015593505532	38	In Flight	2026-05-13 05:38:46.080696	0101000020E61000000F9D9E7763A453403333333333633140
37	21	6	17.4058	78.5591	100	38	Delivered	2026-05-13 05:38:59.094445	0101000020E610000064CC5D4BC8A3534080B74082E2673140
38	21	7	17.395	78.568571	95.69205605180902	38	Taking Off	2026-05-13 07:57:03.124327	0101000020E61000000F9D9E7763A4534085EB51B81E653140
39	21	7	17.3875	78.577143	91.38411210361804	38	In Flight	2026-05-13 07:57:16.140652	0101000020E6100000628731E9EFA453403333333333633140
40	2	8	17.438256872118384	78.36513519287111	91.71209875637382	38	Taking Off	2026-05-13 08:00:31.220289	0101000020E6100000010000605E975340E7FE349A31703140
41	2	8	17.438256872118384	78.36513519287111	83.42419751274764	38	Taking Off	2026-05-13 08:00:44.234695	0101000020E6100000010000605E975340E7FE349A31703140
42	2	8	17.438256872118384	78.36513519287111	75.13629626912146	38	Taking Off	2026-05-13 08:00:57.246652	0101000020E6100000010000605E975340E7FE349A31703140
43	2	8	17.438256872118384	78.36513519287111	66.84839502549528	38	Taking Off	2026-05-13 08:01:10.258165	0101000020E6100000010000605E975340E7FE349A31703140
44	2	8	17.438256872118384	78.36513519287111	58.560493781869106	38	Taking Off	2026-05-13 08:01:23.268668	0101000020E6100000010000605E975340E7FE349A31703140
45	2	8	17.438256872118384	78.36513519287111	50.27259253824293	38	Taking Off	2026-05-13 08:01:36.279244	0101000020E6100000010000605E975340E7FE349A31703140
46	2	8	17.438256872118384	78.36513519287111	41.98469129461676	38	Taking Off	2026-05-13 08:01:49.291254	0101000020E6100000010000605E975340E7FE349A31703140
47	2	8	17.438256872118384	78.36513519287111	33.696790050990586	38	Taking Off	2026-05-13 08:02:02.303134	0101000020E6100000010000605E975340E7FE349A31703140
48	2	8	17.438256872118384	78.36513519287111	25.408888807364413	38	Taking Off	2026-05-13 08:02:15.315261	0101000020E6100000010000605E975340E7FE349A31703140
49	2	8	17.438256872118384	78.36513519287111	17.12098756373824	38	Taking Off	2026-05-13 08:02:28.325724	0101000020E6100000010000605E975340E7FE349A31703140
50	2	8	17.438256872118384	78.36513519287111	8.833086320112066	38	Taking Off	2026-05-13 08:02:41.3384	0101000020E6100000010000605E975340E7FE349A31703140
51	2	8	17.438256872118384	78.36513519287111	0.5451850764858932	38	Taking Off	2026-05-13 08:02:54.351974	0101000020E6100000010000605E975340E7FE349A31703140
52	2	8	17.438256872118384	78.36513519287111	0	38	Taking Off	2026-05-13 08:03:07.363333	0101000020E6100000010000605E975340E7FE349A31703140
53	2	8	17.438256872118384	78.36513519287111	0	38	Taking Off	2026-05-13 08:03:20.375121	0101000020E6100000010000605E975340E7FE349A31703140
54	2	8	17.438256872118384	78.36513519287111	0	38	Taking Off	2026-05-13 08:03:33.386981	0101000020E6100000010000605E975340E7FE349A31703140
55	16	9	17.4325	78.491429	93.44772061531829	38	Taking Off	2026-05-13 08:06:09.449188	0101000020E610000095D39E92739F53401F85EB51B86E3140
56	16	9	17.425	78.482857	86.89544123063658	38	In Flight	2026-05-13 08:06:22.460521	0101000020E610000042E90B21E79E5340CDCCCCCCCC6C3140
57	16	9	17.4175	78.482857	80.34316184595487	38	In Flight	2026-05-13 08:06:35.467443	0101000020E610000042E90B21E79E53407B14AE47E16A3140
58	16	9	17.41	78.482857	73.79088246127316	38	In Flight	2026-05-13 08:06:48.48023	0101000020E610000042E90B21E79E5340295C8FC2F5683140
59	16	9	17.4399	78.4983	100	38	Delivered	2026-05-13 08:07:01.490113	0101000020E610000032E6AE25E49F5340AA8251499D703140
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: drone
--

COPY public.users (id, name, email, hashed_password, role, created_at) FROM stdin;
1	Admin	admin@hyd-drone.local	$2b$12$pK265OA/2UPkeqtfbr/a/OWvlZ3NeqkZjKqgGQrOy.83lW9wYgscS	admin	2026-05-11 12:56:34.668336
2	Customer	customer@hyd-drone.local	$2b$12$zREHzeDRewG4nn6RlXZ.cOL0icjAuYQcabK0K5Ct2SP9WqHy4hp66	customer	2026-05-11 12:56:34.668337
\.


--
-- Data for Name: weather_data; Type: TABLE DATA; Schema: public; Owner: drone
--

COPY public.weather_data (id, latitude, longitude, wind_speed, temperature, humidity, source, created_at) FROM stdin;
\.


--
-- Name: airspace_zones_id_seq; Type: SEQUENCE SET; Schema: public; Owner: drone
--

SELECT pg_catalog.setval('public.airspace_zones_id_seq', 7, true);


--
-- Name: assignments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: drone
--

SELECT pg_catalog.setval('public.assignments_id_seq', 10, true);


--
-- Name: carts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: drone
--

SELECT pg_catalog.setval('public.carts_id_seq', 1, false);


--
-- Name: dark_stores_id_seq; Type: SEQUENCE SET; Schema: public; Owner: drone
--

SELECT pg_catalog.setval('public.dark_stores_id_seq', 6, true);


--
-- Name: drones_id_seq; Type: SEQUENCE SET; Schema: public; Owner: drone
--

SELECT pg_catalog.setval('public.drones_id_seq', 24, true);


--
-- Name: orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: drone
--

SELECT pg_catalog.setval('public.orders_id_seq', 10, true);


--
-- Name: products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: drone
--

SELECT pg_catalog.setval('public.products_id_seq', 198, true);


--
-- Name: simulation_configs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: drone
--

SELECT pg_catalog.setval('public.simulation_configs_id_seq', 1, true);


--
-- Name: telemetry_id_seq; Type: SEQUENCE SET; Schema: public; Owner: drone
--

SELECT pg_catalog.setval('public.telemetry_id_seq', 59, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: drone
--

SELECT pg_catalog.setval('public.users_id_seq', 2, true);


--
-- Name: weather_data_id_seq; Type: SEQUENCE SET; Schema: public; Owner: drone
--

SELECT pg_catalog.setval('public.weather_data_id_seq', 1, false);


--
-- Name: airspace_zones airspace_zones_pkey; Type: CONSTRAINT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.airspace_zones
    ADD CONSTRAINT airspace_zones_pkey PRIMARY KEY (id);


--
-- Name: assignments assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT assignments_pkey PRIMARY KEY (id);


--
-- Name: carts carts_pkey; Type: CONSTRAINT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.carts
    ADD CONSTRAINT carts_pkey PRIMARY KEY (id);


--
-- Name: dark_stores dark_stores_pkey; Type: CONSTRAINT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.dark_stores
    ADD CONSTRAINT dark_stores_pkey PRIMARY KEY (id);


--
-- Name: drones drones_pkey; Type: CONSTRAINT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.drones
    ADD CONSTRAINT drones_pkey PRIMARY KEY (id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: simulation_configs simulation_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.simulation_configs
    ADD CONSTRAINT simulation_configs_pkey PRIMARY KEY (id);


--
-- Name: telemetry telemetry_pkey; Type: CONSTRAINT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.telemetry
    ADD CONSTRAINT telemetry_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: weather_data weather_data_pkey; Type: CONSTRAINT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.weather_data
    ADD CONSTRAINT weather_data_pkey PRIMARY KEY (id);


--
-- Name: idx_airspace_zones_polygon; Type: INDEX; Schema: public; Owner: drone
--

CREATE INDEX idx_airspace_zones_polygon ON public.airspace_zones USING gist (polygon);


--
-- Name: idx_dark_stores_location; Type: INDEX; Schema: public; Owner: drone
--

CREATE INDEX idx_dark_stores_location ON public.dark_stores USING gist (location);


--
-- Name: idx_drones_location; Type: INDEX; Schema: public; Owner: drone
--

CREATE INDEX idx_drones_location ON public.drones USING gist (location);


--
-- Name: idx_orders_route; Type: INDEX; Schema: public; Owner: drone
--

CREATE INDEX idx_orders_route ON public.orders USING gist (route);


--
-- Name: idx_telemetry_location; Type: INDEX; Schema: public; Owner: drone
--

CREATE INDEX idx_telemetry_location ON public.telemetry USING gist (location);


--
-- Name: ix_airspace_zones_id; Type: INDEX; Schema: public; Owner: drone
--

CREATE INDEX ix_airspace_zones_id ON public.airspace_zones USING btree (id);


--
-- Name: ix_assignments_id; Type: INDEX; Schema: public; Owner: drone
--

CREATE INDEX ix_assignments_id ON public.assignments USING btree (id);


--
-- Name: ix_carts_id; Type: INDEX; Schema: public; Owner: drone
--

CREATE INDEX ix_carts_id ON public.carts USING btree (id);


--
-- Name: ix_dark_stores_id; Type: INDEX; Schema: public; Owner: drone
--

CREATE INDEX ix_dark_stores_id ON public.dark_stores USING btree (id);


--
-- Name: ix_drones_id; Type: INDEX; Schema: public; Owner: drone
--

CREATE INDEX ix_drones_id ON public.drones USING btree (id);


--
-- Name: ix_orders_id; Type: INDEX; Schema: public; Owner: drone
--

CREATE INDEX ix_orders_id ON public.orders USING btree (id);


--
-- Name: ix_products_id; Type: INDEX; Schema: public; Owner: drone
--

CREATE INDEX ix_products_id ON public.products USING btree (id);


--
-- Name: ix_simulation_configs_id; Type: INDEX; Schema: public; Owner: drone
--

CREATE INDEX ix_simulation_configs_id ON public.simulation_configs USING btree (id);


--
-- Name: ix_telemetry_id; Type: INDEX; Schema: public; Owner: drone
--

CREATE INDEX ix_telemetry_id ON public.telemetry USING btree (id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: drone
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: drone
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_weather_data_id; Type: INDEX; Schema: public; Owner: drone
--

CREATE INDEX ix_weather_data_id ON public.weather_data USING btree (id);


--
-- Name: assignments assignments_drone_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT assignments_drone_id_fkey FOREIGN KEY (drone_id) REFERENCES public.drones(id);


--
-- Name: assignments assignments_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT assignments_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: carts carts_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.carts
    ADD CONSTRAINT carts_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: carts carts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.carts
    ADD CONSTRAINT carts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: drones drones_dark_store_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.drones
    ADD CONSTRAINT drones_dark_store_id_fkey FOREIGN KEY (dark_store_id) REFERENCES public.dark_stores(id);


--
-- Name: orders orders_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.users(id);


--
-- Name: orders orders_dark_store_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_dark_store_id_fkey FOREIGN KEY (dark_store_id) REFERENCES public.dark_stores(id);


--
-- Name: products products_dark_store_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_dark_store_id_fkey FOREIGN KEY (dark_store_id) REFERENCES public.dark_stores(id);


--
-- Name: telemetry telemetry_drone_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.telemetry
    ADD CONSTRAINT telemetry_drone_id_fkey FOREIGN KEY (drone_id) REFERENCES public.drones(id);


--
-- Name: telemetry telemetry_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: drone
--

ALTER TABLE ONLY public.telemetry
    ADD CONSTRAINT telemetry_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- PostgreSQL database dump complete
--

\unrestrict vayZstzbFEjHF5Joed7C6pDHgFtc2XPehGleK47ywBpNTV4XQbgZi7MpHD8SRwS

