--
-- TOC entry 327 (class 1259 OID 27625)
-- Name: dictionary_algo_events; Type: TABLE; Schema: public; Owner: piotradamczyk
--

CREATE TABLE public.dictionary_algo_events (
    id integer NOT NULL,
    phase_code character varying(100) NOT NULL,
    region_code character varying(10),
    label character varying(200) NOT NULL,
    description text,
    utc_start time without time zone NOT NULL,
    utc_end time without time zone NOT NULL,
    wraps_midnight boolean DEFAULT false NOT NULL,
    priority integer DEFAULT 10 NOT NULL,
    volatility_level character varying(20),
    volume_impact character varying(20),
    typical_duration_min integer,
    trading_pattern character varying(20),
    dominant_actors character varying(20) DEFAULT 'ALGO'::character varying,
    news_sensitivity character varying(20),
    category character varying(20) DEFAULT 'ALGO'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.dictionary_algo_events OWNER TO piotradamczyk;

--
-- TOC entry 4876 (class 0 OID 0)
-- Dependencies: 327
-- Name: TABLE dictionary_algo_events; Type: COMMENT; Schema: public; Owner: piotradamczyk
--

COMMENT ON TABLE public.dictionary_algo_events IS 'Słownik wydarzeń związanych z handlem algorytmicznym';


--
-- TOC entry 326 (class 1259 OID 27624)
-- Name: dictionary_algo_events_id_seq; Type: SEQUENCE; Schema: public; Owner: piotradamczyk
--

CREATE SEQUENCE public.dictionary_algo_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dictionary_algo_events_id_seq OWNER TO piotradamczyk;

--
-- TOC entry 4877 (class 0 OID 0)
-- Dependencies: 326
-- Name: dictionary_algo_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: piotradamczyk
--

ALTER SEQUENCE public.dictionary_algo_events_id_seq OWNED BY public.dictionary_algo_events.id;


--
-- TOC entry 321 (class 1259 OID 27572)
-- Name: dictionary_global_events; Type: TABLE; Schema: public; Owner: piotradamczyk
--

CREATE TABLE public.dictionary_global_events (
    id integer NOT NULL,
    phase_code character varying(100) NOT NULL,
    region_code character varying(10) DEFAULT 'GLOBAL'::character varying,
    label character varying(200) NOT NULL,
    description text,
    utc_start time without time zone NOT NULL,
    utc_end time without time zone NOT NULL,
    wraps_midnight boolean DEFAULT false NOT NULL,
    priority integer DEFAULT 10 NOT NULL,
    volatility_level character varying(20),
    volume_impact character varying(20),
    typical_duration_min integer,
    trading_pattern character varying(20),
    dominant_actors character varying(20),
    news_sensitivity character varying(20),
    category character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.dictionary_global_events OWNER TO piotradamczyk;

--
-- TOC entry 4878 (class 0 OID 0)
-- Dependencies: 321
-- Name: TABLE dictionary_global_events; Type: COMMENT; Schema: public; Owner: piotradamczyk
--

COMMENT ON TABLE public.dictionary_global_events IS 'Słownik wydarzeń globalnych wpływających na cały rynek BTC';


--
-- TOC entry 320 (class 1259 OID 27571)
-- Name: dictionary_global_events_id_seq; Type: SEQUENCE; Schema: public; Owner: piotradamczyk
--

CREATE SEQUENCE public.dictionary_global_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dictionary_global_events_id_seq OWNER TO piotradamczyk;

--
-- TOC entry 4879 (class 0 OID 0)
-- Dependencies: 320
-- Name: dictionary_global_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: piotradamczyk
--

ALTER SEQUENCE public.dictionary_global_events_id_seq OWNED BY public.dictionary_global_events.id;


--
-- TOC entry 323 (class 1259 OID 27590)
-- Name: dictionary_macro_events; Type: TABLE; Schema: public; Owner: piotradamczyk
--

CREATE TABLE public.dictionary_macro_events (
    id integer NOT NULL,
    phase_code character varying(100) NOT NULL,
    region_code character varying(10),
    label character varying(200) NOT NULL,
    description text,
    utc_start time without time zone NOT NULL,
    utc_end time without time zone NOT NULL,
    wraps_midnight boolean DEFAULT false NOT NULL,
    priority integer DEFAULT 10 NOT NULL,
    volatility_level character varying(20),
    volume_impact character varying(20),
    typical_duration_min integer,
    trading_pattern character varying(20),
    dominant_actors character varying(20),
    news_sensitivity character varying(20),
    category character varying(20) DEFAULT 'MACRO'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.dictionary_macro_events OWNER TO piotradamczyk;

--
-- TOC entry 4880 (class 0 OID 0)
-- Dependencies: 323
-- Name: TABLE dictionary_macro_events; Type: COMMENT; Schema: public; Owner: piotradamczyk
--

COMMENT ON TABLE public.dictionary_macro_events IS 'Słownik wydarzeń makroekonomicznych wpływających na rynek BTC';


--
-- TOC entry 322 (class 1259 OID 27589)
-- Name: dictionary_macro_events_id_seq; Type: SEQUENCE; Schema: public; Owner: piotradamczyk
--

CREATE SEQUENCE public.dictionary_macro_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dictionary_macro_events_id_seq OWNER TO piotradamczyk;

--
-- TOC entry 4881 (class 0 OID 0)
-- Dependencies: 322
-- Name: dictionary_macro_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: piotradamczyk
--

ALTER SEQUENCE public.dictionary_macro_events_id_seq OWNED BY public.dictionary_macro_events.id;


--
-- TOC entry 325 (class 1259 OID 27608)
-- Name: dictionary_options_events; Type: TABLE; Schema: public; Owner: piotradamczyk
--

CREATE TABLE public.dictionary_options_events (
    id integer NOT NULL,
    phase_code character varying(100) NOT NULL,
    region_code character varying(10),
    label character varying(200) NOT NULL,
    description text,
    utc_start time without time zone NOT NULL,
    utc_end time without time zone NOT NULL,
    wraps_midnight boolean DEFAULT false NOT NULL,
    priority integer DEFAULT 10 NOT NULL,
    volatility_level character varying(20),
    volume_impact character varying(20),
    typical_duration_min integer,
    trading_pattern character varying(20),
    dominant_actors character varying(20),
    news_sensitivity character varying(20),
    category character varying(20) DEFAULT 'EVENT'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.dictionary_options_events OWNER TO piotradamczyk;

--
-- TOC entry 4882 (class 0 OID 0)
-- Dependencies: 325
-- Name: TABLE dictionary_options_events; Type: COMMENT; Schema: public; Owner: piotradamczyk
--

COMMENT ON TABLE public.dictionary_options_events IS 'Słownik wydarzeń związanych z wygaśnięciem opcji i futures na BTC';


--
-- TOC entry 324 (class 1259 OID 27607)
-- Name: dictionary_options_events_id_seq; Type: SEQUENCE; Schema: public; Owner: piotradamczyk
--

CREATE SEQUENCE public.dictionary_options_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dictionary_options_events_id_seq OWNER TO piotradamczyk;

--
-- TOC entry 4883 (class 0 OID 0)
-- Dependencies: 324
-- Name: dictionary_options_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: piotradamczyk
--

ALTER SEQUENCE public.dictionary_options_events_id_seq OWNED BY public.dictionary_options_events.id;


--
-- TOC entry 319 (class 1259 OID 27549)
-- Name: dictionary_region_events; Type: TABLE; Schema: public; Owner: piotradamczyk
--

CREATE TABLE public.dictionary_region_events (
    id integer NOT NULL,
    phase_code character varying(100) NOT NULL,
    region_code character varying(10) NOT NULL,
    label character varying(200) NOT NULL,
    description text,
    utc_start time without time zone NOT NULL,
    utc_end time without time zone NOT NULL,
    wraps_midnight boolean DEFAULT false NOT NULL,
    priority integer DEFAULT 10 NOT NULL,
    volatility_level character varying(20),
    volume_impact character varying(20),
    typical_duration_min integer,
    trading_pattern character varying(20),
    dominant_actors character varying(20),
    news_sensitivity character varying(20),
    category character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.dictionary_region_events OWNER TO piotradamczyk;

--
-- TOC entry 4884 (class 0 OID 0)
-- Dependencies: 319
-- Name: TABLE dictionary_region_events; Type: COMMENT; Schema: public; Owner: piotradamczyk
--

COMMENT ON TABLE public.dictionary_region_events IS 'Słownik wydarzeń specyficznych dla poszczególnych regionów';


--
-- TOC entry 4885 (class 0 OID 0)
-- Dependencies: 319
-- Name: COLUMN dictionary_region_events.phase_code; Type: COMMENT; Schema: public; Owner: piotradamczyk
--

COMMENT ON COLUMN public.dictionary_region_events.phase_code IS 'Unikalny kod fazy/wydarzenia';


--
-- TOC entry 4886 (class 0 OID 0)
-- Dependencies: 319
-- Name: COLUMN dictionary_region_events.region_code; Type: COMMENT; Schema: public; Owner: piotradamczyk
--

COMMENT ON COLUMN public.dictionary_region_events.region_code IS 'Kod regionu (FK do regions)';


--
-- TOC entry 4887 (class 0 OID 0)
-- Dependencies: 319
-- Name: COLUMN dictionary_region_events.priority; Type: COMMENT; Schema: public; Owner: piotradamczyk
--

COMMENT ON COLUMN public.dictionary_region_events.priority IS 'Priorytet wydarzenia (niższy = ważniejsze)';


--
-- TOC entry 318 (class 1259 OID 27548)
-- Name: dictionary_region_events_id_seq; Type: SEQUENCE; Schema: public; Owner: piotradamczyk
--

CREATE SEQUENCE public.dictionary_region_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dictionary_region_events_id_seq OWNER TO piotradamczyk;

--
-- TOC entry 4888 (class 0 OID 0)
-- Dependencies: 318
-- Name: dictionary_region_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: piotradamczyk
--

ALTER SEQUENCE public.dictionary_region_events_id_seq OWNED BY public.dictionary_region_events.id;


--
-- TOC entry 331 (class 1259 OID 27660)
-- Name: dictionary_social_events; Type: TABLE; Schema: public; Owner: piotradamczyk
--

CREATE TABLE public.dictionary_social_events (
    id integer NOT NULL,
    phase_code character varying(100) NOT NULL,
    region_code character varying(10),
    label character varying(200) NOT NULL,
    description text,
    utc_start time without time zone NOT NULL,
    utc_end time without time zone NOT NULL,
    wraps_midnight boolean DEFAULT false NOT NULL,
    priority integer DEFAULT 10 NOT NULL,
    volatility_level character varying(20),
    volume_impact character varying(20),
    typical_duration_min integer,
    trading_pattern character varying(20),
    dominant_actors character varying(20) DEFAULT 'RETAIL'::character varying,
    news_sensitivity character varying(20) DEFAULT 'HIGH'::character varying,
    category character varying(20) DEFAULT 'SESSION'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.dictionary_social_events OWNER TO piotradamczyk;

--
-- TOC entry 4889 (class 0 OID 0)
-- Dependencies: 331
-- Name: TABLE dictionary_social_events; Type: COMMENT; Schema: public; Owner: piotradamczyk
--

COMMENT ON TABLE public.dictionary_social_events IS 'Słownik wydarzeń związanych z aktywnością w mediach społecznościowych';


--
-- TOC entry 330 (class 1259 OID 27659)
-- Name: dictionary_social_events_id_seq; Type: SEQUENCE; Schema: public; Owner: piotradamczyk
--

CREATE SEQUENCE public.dictionary_social_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dictionary_social_events_id_seq OWNER TO piotradamczyk;

--
-- TOC entry 4890 (class 0 OID 0)
-- Dependencies: 330
-- Name: dictionary_social_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: piotradamczyk
--

ALTER SEQUENCE public.dictionary_social_events_id_seq OWNED BY public.dictionary_social_events.id;


--
-- TOC entry 329 (class 1259 OID 27643)
-- Name: dictionary_special_events; Type: TABLE; Schema: public; Owner: piotradamczyk
--

CREATE TABLE public.dictionary_special_events (
    id integer NOT NULL,
    phase_code character varying(100) NOT NULL,
    region_code character varying(10),
    label character varying(200) NOT NULL,
    description text,
    utc_start time without time zone NOT NULL,
    utc_end time without time zone NOT NULL,
    wraps_midnight boolean DEFAULT false NOT NULL,
    priority integer DEFAULT 10 NOT NULL,
    volatility_level character varying(20),
    volume_impact character varying(20),
    typical_duration_min integer,
    trading_pattern character varying(20),
    dominant_actors character varying(20),
    news_sensitivity character varying(20),
    category character varying(20) DEFAULT 'EVENT'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.dictionary_special_events OWNER TO piotradamczyk;

--
-- TOC entry 4891 (class 0 OID 0)
-- Dependencies: 329
-- Name: TABLE dictionary_special_events; Type: COMMENT; Schema: public; Owner: piotradamczyk
--

COMMENT ON TABLE public.dictionary_special_events IS 'Słownik specjalnych wydarzeń rynkowych (Halving, CME Gap, Funding Rate, etc.)';


--
-- TOC entry 328 (class 1259 OID 27642)
-- Name: dictionary_special_events_id_seq; Type: SEQUENCE; Schema: public; Owner: piotradamczyk
--

CREATE SEQUENCE public.dictionary_special_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dictionary_special_events_id_seq OWNER TO piotradamczyk;

--
-- TOC entry 4892 (class 0 OID 0)
-- Dependencies: 328
-- Name: dictionary_special_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: piotradamczyk
--

ALTER SEQUENCE public.dictionary_special_events_id_seq OWNED BY public.dictionary_special_events.id;

-
-- TOC entry 4860 (class 0 OID 27625)
-- Dependencies: 327
-- Data for Name: dictionary_algo_events; Type: TABLE DATA; Schema: public; Owner: piotradamczyk
--

INSERT INTO public.dictionary_algo_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (1, 'ALGO_HOURLY_SPIKE', 'ALGO', 'Hourly Algo Spike', 'Wzrost aktywności algorytmicznej na pełne godziny (wzorzec: co godzinę o pełnej godzinie)', '00:00:00', '00:05:00', false, 15, 'MEDIUM', 'MEDIUM', 5, 'VOLATILE', 'ALGO', 'LOW', 'ALGO', '2025-12-18 22:30:53.169804') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_algo_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (2, 'ALGO_15MIN_PATTERN', 'ALGO', '15-Minute Algo Pattern', 'Cykliczny wzorzec algorytmiczny co 15 minut (wzorzec: co 15 minut)', '00:00:00', '00:15:00', false, 18, 'LOW', 'LOW', 15, 'MIXED', 'ALGO', 'LOW', 'ALGO', '2025-12-18 22:30:53.169804') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_algo_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (3, 'ALGO_REBALANCE_DAILY', 'ALGO', 'Daily Rebalancing Window', 'Okno dziennego rebalancingu funduszy i ETF', '20:00:00', '21:00:00', false, 10, 'MEDIUM', 'HIGH', 60, 'VOLATILE', 'INSTITUTIONAL', 'LOW', 'ALGO', '2025-12-18 22:30:53.169804') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_algo_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (4, 'ALGO_WEEKEND_REDUCED', 'ALGO', 'Weekend Algo Reduction', 'Zmniejszona aktywność algorytmów w weekend', '00:00:00', '23:59:00', false, 20, 'LOW', 'LOW', 1440, 'RANGING', 'RETAIL', 'LOW', 'ALGO', '2025-12-18 22:30:53.169804') ON CONFLICT DO NOTHING;


--
-- TOC entry 4854 (class 0 OID 27572)
-- Dependencies: 321
-- Data for Name: dictionary_global_events; Type: TABLE DATA; Schema: public; Owner: piotradamczyk
--

INSERT INTO public.dictionary_global_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (1, 'GLOBAL_ASIAN_SESSION', 'GLOBAL', 'Global Asian Session', 'Pełna azjatycka sesja handlowa (Tokio, Hongkong, Singapur, Seul)', '00:00:00', '08:00:00', false, 10, 'MEDIUM', 'MEDIUM', 480, 'MIXED', 'RETAIL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.165745') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_global_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (2, 'GLOBAL_EUROPE_SESSION', 'GLOBAL', 'Global Europe Session', 'Pełna europejska sesja handlowa (Londyn, Frankfurt, Paryż)', '08:00:00', '16:00:00', false, 10, 'MEDIUM', 'HIGH', 480, 'TRENDING', 'INSTITUTIONAL', 'HIGH', 'SESSION', '2025-12-18 22:30:53.165745') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_global_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (3, 'GLOBAL_US_SESSION', 'GLOBAL', 'Global US Session', 'Pełna amerykańska sesja handlowa (NYC, Chicago)', '13:00:00', '21:00:00', false, 10, 'HIGH', 'HIGH', 480, 'VOLATILE', 'INSTITUTIONAL', 'HIGH', 'SESSION', '2025-12-18 22:30:53.165745') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_global_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (4, 'GLOBAL_ASIAN_PEAK', 'GLOBAL', 'Global Asian Peak', 'Szczyt aktywności azjatyckiej', '02:00:00', '04:00:00', false, 8, 'MEDIUM', 'HIGH', 120, 'MIXED', 'RETAIL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.165745') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_global_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (5, 'GLOBAL_EUROPE_PEAK', 'GLOBAL', 'Global Europe Peak', 'Szczyt aktywności europejskiej', '08:00:00', '11:00:00', false, 8, 'MEDIUM', 'HIGH', 180, 'TRENDING', 'INSTITUTIONAL', 'HIGH', 'SESSION', '2025-12-18 22:30:53.165745') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_global_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (6, 'GLOBAL_US_PEAK', 'GLOBAL', 'Global US Peak', 'Szczyt aktywności amerykańskiej', '14:00:00', '17:00:00', false, 8, 'HIGH', 'HIGH', 180, 'VOLATILE', 'INSTITUTIONAL', 'HIGH', 'SESSION', '2025-12-18 22:30:53.165745') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_global_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (7, 'GLOBAL_ASIA_EU_OVERLAP', 'GLOBAL', 'Asia-Europe Overlap', 'Nakładanie się sesji azjatyckiej i europejskiej - przejście płynności', '06:00:00', '08:00:00', false, 4, 'MEDIUM', 'MEDIUM', 120, 'MIXED', 'MIXED', 'MEDIUM', 'OVERLAP', '2025-12-18 22:30:53.165745') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_global_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (8, 'GLOBAL_EU_US_OVERLAP', 'GLOBAL', 'EU-US Overlap', 'Nakładanie się sesji europejskiej i amerykańskiej - największa płynność i zmienność', '13:00:00', '17:00:00', false, 3, 'HIGH', 'HIGH', 240, 'VOLATILE', 'INSTITUTIONAL', 'HIGH', 'OVERLAP', '2025-12-18 22:30:53.165745') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_global_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (9, 'GLOBAL_US_ASIA_OVERLAP', 'GLOBAL', 'US-Asia Overlap', 'Nakładanie się sesji amerykańskiej i azjatyckiej - przejście nocne', '21:00:00', '00:00:00', true, 5, 'MEDIUM', 'LOW', 180, 'RANGING', 'RETAIL', 'LOW', 'OVERLAP', '2025-12-18 22:30:53.165745') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_global_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (10, 'GLOBAL_LIQUIDITY_TROUGH', 'GLOBAL', 'Global Liquidity Trough', 'Najniższa płynność globalna - niebezpieczne flash crashe', '04:00:00', '06:00:00', false, 20, 'LOW', 'LOW', 120, 'RANGING', 'ALGO', 'LOW', 'LIQUIDITY', '2025-12-18 22:30:53.165745') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_global_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (11, 'GLOBAL_WEEKEND_LOW', 'GLOBAL', 'Weekend Liquidity Low', 'Weekendowa niska płynność (sobota-niedziela)', '00:00:00', '23:59:00', false, 25, 'LOW', 'LOW', 1440, 'RANGING', 'RETAIL', 'LOW', 'WEEKEND', '2025-12-18 22:30:53.165745') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_global_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (12, 'GLOBAL_SUNDAY_GAP_RISK', 'GLOBAL', 'Sunday Gap Risk', 'Ryzyko luki cenowej przed poniedziałkiem', '18:00:00', '23:59:00', false, 15, 'MEDIUM', 'LOW', 360, 'VOLATILE', 'RETAIL', 'MEDIUM', 'WEEKEND', '2025-12-18 22:30:53.165745') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_global_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (13, 'GLOBAL_VOLATILITY_PEAK', 'GLOBAL', 'Global Volatility Peak', 'Okno najwyższej zmienności dziennej', '14:30:00', '16:00:00', false, 6, 'HIGH', 'HIGH', 90, 'VOLATILE', 'MIXED', 'HIGH', 'SESSION', '2025-12-18 22:30:53.165745') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_global_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (14, 'GLOBAL_VOLATILITY_ASIAN', 'GLOBAL', 'Asian Volatility Window', 'Okno zmienności azjatyckiej (2-3 w nocy UTC)', '01:00:00', '03:00:00', false, 12, 'HIGH', 'MEDIUM', 120, 'VOLATILE', 'RETAIL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.165745') ON CONFLICT DO NOTHING;


--
-- TOC entry 4856 (class 0 OID 27590)
-- Dependencies: 323
-- Data for Name: dictionary_macro_events; Type: TABLE DATA; Schema: public; Owner: piotradamczyk
--

INSERT INTO public.dictionary_macro_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (1, 'CN_PBC_ANNOUNCEMENT', 'CN', 'PBC Announcement Window', 'Okno ogłoszeń Ludowego Banku Chin', '01:00:00', '03:00:00', false, 7, 'HIGH', 'HIGH', 120, 'VOLATILE', 'INSTITUTIONAL', 'HIGH', 'MACRO', '2025-12-18 22:30:53.166963') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_macro_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (2, 'JP_BOJ_WATCH', 'JP', 'BOJ Announcement Watch', 'Okno potencjalnych ogłoszeń Banku Japonii', '23:00:00', '02:00:00', true, 6, 'HIGH', 'HIGH', 180, 'VOLATILE', 'INSTITUTIONAL', 'HIGH', 'MACRO', '2025-12-18 22:30:53.166963') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_macro_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (3, 'MACRO_US_NFP', 'MACRO', 'US Nonfarm Payrolls', 'Publikacja danych o zatrudnieniu w USA (1. piątek miesiąca)', '12:30:00', '14:00:00', false, 2, 'EXTREME', 'HIGH', 90, 'VOLATILE', 'INSTITUTIONAL', 'HIGH', 'MACRO', '2025-12-18 22:30:53.166963') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_macro_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (4, 'MACRO_US_CPI', 'MACRO', 'US CPI Release', 'Publikacja danych o inflacji CPI w USA', '12:30:00', '14:00:00', false, 2, 'EXTREME', 'HIGH', 90, 'VOLATILE', 'INSTITUTIONAL', 'HIGH', 'MACRO', '2025-12-18 22:30:53.166963') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_macro_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (5, 'MACRO_US_FOMC', 'MACRO', 'FOMC Decision', 'Decyzja FOMC dot. stóp procentowych', '18:00:00', '20:00:00', false, 1, 'EXTREME', 'HIGH', 120, 'VOLATILE', 'INSTITUTIONAL', 'HIGH', 'MACRO', '2025-12-18 22:30:53.166963') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_macro_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (6, 'MACRO_US_FOMC_MINUTES', 'MACRO', 'FOMC Minutes Release', 'Publikacja minutek FOMC', '18:00:00', '19:30:00', false, 3, 'HIGH', 'HIGH', 90, 'VOLATILE', 'INSTITUTIONAL', 'HIGH', 'MACRO', '2025-12-18 22:30:53.166963') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_macro_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (7, 'MACRO_EU_ECB', 'MACRO', 'ECB Decision', 'Decyzja EBC dot. stóp procentowych', '12:15:00', '14:00:00', false, 2, 'HIGH', 'HIGH', 105, 'VOLATILE', 'INSTITUTIONAL', 'HIGH', 'MACRO', '2025-12-18 22:30:53.166963') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_macro_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (8, 'MACRO_EU_CPI', 'MACRO', 'EU CPI Release', 'Publikacja danych o inflacji w strefie euro', '09:00:00', '10:30:00', false, 4, 'MEDIUM', 'MEDIUM', 90, 'VOLATILE', 'INSTITUTIONAL', 'HIGH', 'MACRO', '2025-12-18 22:30:53.166963') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_macro_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (9, 'MACRO_JP_BOJ', 'MACRO', 'BOJ Decision', 'Decyzja Banku Japonii', '03:00:00', '05:00:00', false, 3, 'HIGH', 'MEDIUM', 120, 'VOLATILE', 'INSTITUTIONAL', 'HIGH', 'MACRO', '2025-12-18 22:30:53.166963') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_macro_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (10, 'MACRO_CN_PMI', 'MACRO', 'China PMI Release', 'Publikacja PMI z Chin', '01:00:00', '02:30:00', false, 5, 'MEDIUM', 'MEDIUM', 90, 'VOLATILE', 'INSTITUTIONAL', 'MEDIUM', 'MACRO', '2025-12-18 22:30:53.166963') ON CONFLICT DO NOTHING;


--
-- TOC entry 4858 (class 0 OID 27608)
-- Dependencies: 325
-- Data for Name: dictionary_options_events; Type: TABLE DATA; Schema: public; Owner: piotradamczyk
--

INSERT INTO public.dictionary_options_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (1, 'OPTIONS_DERIBIT_DAILY', 'OPTIONS', 'Deribit Daily Expiry', 'Dzienne wygaśnięcie opcji na Deribit', '08:00:00', '08:30:00', false, 8, 'MEDIUM', 'MEDIUM', 30, 'VOLATILE', 'INSTITUTIONAL', 'LOW', 'EVENT', '2025-12-18 22:30:53.168642') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_options_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (2, 'OPTIONS_DERIBIT_WEEKLY', 'OPTIONS', 'Deribit Weekly Expiry', 'Tygodniowe wygaśnięcie opcji na Deribit (piątek)', '08:00:00', '09:00:00', false, 5, 'HIGH', 'HIGH', 60, 'VOLATILE', 'INSTITUTIONAL', 'LOW', 'EVENT', '2025-12-18 22:30:53.168642') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_options_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (3, 'OPTIONS_DERIBIT_MONTHLY', 'OPTIONS', 'Deribit Monthly Expiry', 'Miesięczne wygaśnięcie opcji na Deribit (ostatni piątek)', '08:00:00', '10:00:00', false, 3, 'EXTREME', 'HIGH', 120, 'VOLATILE', 'INSTITUTIONAL', 'LOW', 'EVENT', '2025-12-18 22:30:53.168642') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_options_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (4, 'OPTIONS_CME_MONTHLY', 'OPTIONS', 'CME Monthly Expiry', 'Miesięczne wygaśnięcie opcji CME na BTC', '15:00:00', '16:00:00', false, 3, 'EXTREME', 'HIGH', 60, 'VOLATILE', 'INSTITUTIONAL', 'LOW', 'EVENT', '2025-12-18 22:30:53.168642') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_options_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (5, 'OPTIONS_CME_QUARTERLY', 'OPTIONS', 'CME Quarterly Expiry', 'Kwartalne wygaśnięcie futures CME', '15:00:00', '17:00:00', false, 2, 'EXTREME', 'HIGH', 120, 'VOLATILE', 'INSTITUTIONAL', 'LOW', 'EVENT', '2025-12-18 22:30:53.168642') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_options_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (6, 'OPTIONS_BINANCE_QUARTERLY', 'OPTIONS', 'Binance Quarterly Expiry', 'Kwartalne wygaśnięcie kontraktów Binance Futures', '08:00:00', '10:00:00', false, 4, 'HIGH', 'HIGH', 120, 'VOLATILE', 'MIXED', 'LOW', 'EVENT', '2025-12-18 22:30:53.168642') ON CONFLICT DO NOTHING;


--
-- TOC entry 4852 (class 0 OID 27549)
-- Dependencies: 319
-- Data for Name: dictionary_region_events; Type: TABLE DATA; Schema: public; Owner: piotradamczyk
--

INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (1, 'CN_MORNING_PEAK', 'CN', 'China Morning Peak', 'Poranne okno aktywności w Chinach (lokalny 7:00-10:00)', '23:00:00', '02:00:00', true, 10, 'MEDIUM', 'HIGH', 180, 'TRENDING', 'RETAIL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (2, 'CN_LUNCH_BREAK', 'CN', 'China Lunch Break', 'Przerwa obiadowa - spadek aktywności (lokalny 12:00-14:00)', '04:00:00', '06:00:00', false, 18, 'LOW', 'LOW', 120, 'RANGING', 'RETAIL', 'LOW', 'LIQUIDITY', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (3, 'CN_EVENING_PEAK', 'CN', 'China Evening Peak', 'Wieczorne okno aktywności w Chinach (lokalny 19:00-23:00)', '11:00:00', '15:00:00', false, 10, 'MEDIUM', 'HIGH', 240, 'MIXED', 'RETAIL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (4, 'RU_MORNING_PEAK', 'RU', 'Russia Morning Peak', 'Poranna aktywność w Rosji (MSK 7:00-10:00)', '04:00:00', '07:00:00', false, 10, 'MEDIUM', 'MEDIUM', 180, 'MIXED', 'RETAIL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (5, 'RU_EVENING_PEAK', 'RU', 'Russia Evening Peak', 'Wieczorne okno aktywności w Rosji (MSK 18:00-22:00)', '15:00:00', '19:00:00', false, 10, 'MEDIUM', 'MEDIUM', 240, 'MIXED', 'RETAIL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (6, 'SG_MORNING_PEAK', 'SG', 'Singapore Morning Peak', 'Poranne okno aktywności w Singapurze', '22:00:00', '01:00:00', true, 10, 'MEDIUM', 'HIGH', 180, 'TRENDING', 'INSTITUTIONAL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (7, 'SG_TRADING_HOURS', 'SG', 'Singapore Trading Hours', 'Główne godziny handlu w Singapurze', '00:00:00', '08:00:00', false, 12, 'MEDIUM', 'HIGH', 480, 'MIXED', 'INSTITUTIONAL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (8, 'SG_EVENING_PEAK', 'SG', 'Singapore Evening Peak', 'Wieczorne okno aktywności w Singapurze', '10:00:00', '14:00:00', false, 10, 'MEDIUM', 'MEDIUM', 240, 'MIXED', 'MIXED', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (9, 'US_PREMARKET', 'US', 'US Pre-Market', 'Aktywność przed otwarciem giełd USA', '12:00:00', '13:30:00', false, 9, 'MEDIUM', 'MEDIUM', 90, 'RANGING', 'INSTITUTIONAL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (10, 'US_MORNING_PEAK', 'US', 'US Morning Peak', 'Poranna aktywność inwestorów w USA (NYSE open)', '13:30:00', '15:00:00', false, 7, 'HIGH', 'HIGH', 90, 'VOLATILE', 'INSTITUTIONAL', 'HIGH', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (11, 'US_AFTERNOON_PEAK', 'US', 'US Afternoon Peak', 'Popołudniowy szczyt aktywności w USA', '15:00:00', '17:00:00', false, 8, 'HIGH', 'HIGH', 120, 'TRENDING', 'INSTITUTIONAL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (12, 'US_POWER_HOUR', 'US', 'US Power Hour', 'Ostatnia godzina sesji NYSE - intensywny handel', '19:00:00', '20:00:00', false, 6, 'HIGH', 'HIGH', 60, 'VOLATILE', 'INSTITUTIONAL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (13, 'US_EVENING_PEAK', 'US', 'US Evening Peak', 'Wieczorne okno aktywności w USA', '20:00:00', '23:00:00', false, 12, 'MEDIUM', 'MEDIUM', 180, 'RANGING', 'RETAIL', 'LOW', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (14, 'KR_MORNING_PEAK', 'KR', 'Korea Morning Peak', 'Poranna aktywność w Korei Południowej', '23:00:00', '02:00:00', true, 10, 'MEDIUM', 'HIGH', 180, 'TRENDING', 'RETAIL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (15, 'KR_KIMCHI_PREMIUM', 'KR', 'Korea Kimchi Premium Window', 'Okno potencjalnej premii Kimchi (różnica cen KR vs. globalne)', '00:00:00', '04:00:00', false, 8, 'MEDIUM', 'HIGH', 240, 'MIXED', 'RETAIL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (16, 'KR_EVENING_PEAK', 'KR', 'Korea Evening Peak', 'Wieczorne okno aktywności w Korei', '10:00:00', '14:00:00', false, 10, 'MEDIUM', 'MEDIUM', 240, 'MIXED', 'RETAIL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (17, 'JP_MORNING_PEAK', 'JP', 'Japan Morning Peak', 'Poranna aktywność w Japonii (TSE open)', '00:00:00', '03:00:00', false, 10, 'MEDIUM', 'HIGH', 180, 'TRENDING', 'INSTITUTIONAL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (18, 'JP_EVENING_PEAK', 'JP', 'Japan Evening Peak', 'Wieczorne okno aktywności w Japonii', '10:00:00', '14:00:00', false, 10, 'MEDIUM', 'MEDIUM', 240, 'MIXED', 'MIXED', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (19, 'GB_MORNING_PEAK', 'GB', 'UK Morning Peak', 'Poranna aktywność w Wielkiej Brytanii (LSE open)', '07:00:00', '10:00:00', false, 9, 'MEDIUM', 'HIGH', 180, 'TRENDING', 'INSTITUTIONAL', 'HIGH', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (20, 'GB_AFTERNOON_PEAK', 'GB', 'UK Afternoon Peak', 'Popołudniowa aktywność w UK', '14:00:00', '16:30:00', false, 10, 'HIGH', 'HIGH', 150, 'VOLATILE', 'INSTITUTIONAL', 'HIGH', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (21, 'GB_EVENING_PEAK', 'GB', 'UK Evening Peak', 'Wieczorne okno aktywności w UK', '18:00:00', '21:00:00', false, 12, 'MEDIUM', 'MEDIUM', 180, 'RANGING', 'RETAIL', 'LOW', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (22, 'DE_MORNING_PEAK', 'DE', 'Germany Morning Peak', 'Poranna aktywność w Niemczech (Xetra open)', '07:00:00', '10:00:00', false, 10, 'MEDIUM', 'HIGH', 180, 'TRENDING', 'INSTITUTIONAL', 'HIGH', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (23, 'DE_AFTERNOON_PEAK', 'DE', 'Germany Afternoon Peak', 'Popołudniowa aktywność w Niemczech', '13:00:00', '16:00:00', false, 10, 'HIGH', 'HIGH', 180, 'VOLATILE', 'INSTITUTIONAL', 'HIGH', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (24, 'DE_EVENING_PEAK', 'DE', 'Germany Evening Peak', 'Wieczorne okno aktywności w Niemczech', '17:00:00', '20:00:00', false, 12, 'MEDIUM', 'MEDIUM', 180, 'RANGING', 'RETAIL', 'LOW', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (25, 'PL_MORNING_PEAK', 'PL', 'Poland Morning Peak', 'Poranne okno aktywności inwestorów w Polsce', '06:00:00', '09:00:00', false, 10, 'MEDIUM', 'MEDIUM', 180, 'MIXED', 'RETAIL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (26, 'PL_AFTERNOON_PEAK', 'PL', 'Poland Afternoon Peak', 'Popołudniowa aktywność w Polsce', '13:00:00', '16:00:00', false, 12, 'MEDIUM', 'MEDIUM', 180, 'MIXED', 'RETAIL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (27, 'PL_EVENING_PEAK', 'PL', 'Poland Evening Peak', 'Wieczorne okno aktywności inwestorów w Polsce', '17:00:00', '21:00:00', false, 10, 'MEDIUM', 'MEDIUM', 240, 'MIXED', 'RETAIL', 'LOW', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (28, 'HK_MORNING_PEAK', 'HK', 'Hong Kong Morning Peak', 'Poranna aktywność w Hong Kongu (HKEX open)', '01:00:00', '04:00:00', false, 9, 'MEDIUM', 'HIGH', 180, 'TRENDING', 'INSTITUTIONAL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (29, 'HK_AFTERNOON_PEAK', 'HK', 'Hong Kong Afternoon Peak', 'Popołudniowa aktywność w Hong Kongu', '05:00:00', '08:00:00', false, 10, 'MEDIUM', 'HIGH', 180, 'MIXED', 'INSTITUTIONAL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (30, 'HK_EVENING_PEAK', 'HK', 'Hong Kong Evening Peak', 'Wieczorne okno aktywności w Hong Kongu', '10:00:00', '14:00:00', false, 12, 'MEDIUM', 'MEDIUM', 240, 'MIXED', 'MIXED', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (31, 'AE_MORNING_PEAK', 'AE', 'UAE Morning Peak', 'Poranna aktywność w Dubaju (DFM open)', '04:00:00', '07:00:00', false, 10, 'MEDIUM', 'MEDIUM', 180, 'MIXED', 'INSTITUTIONAL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (32, 'AE_BRIDGE_SESSION', 'AE', 'UAE Bridge Session', 'Dubaj jako most między Azją a Europą', '05:00:00', '08:00:00', false, 8, 'MEDIUM', 'MEDIUM', 180, 'TRENDING', 'INSTITUTIONAL', 'MEDIUM', 'OVERLAP', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (33, 'AE_EVENING_PEAK', 'AE', 'UAE Evening Peak', 'Wieczorne okno aktywności w Dubaju', '14:00:00', '18:00:00', false, 12, 'MEDIUM', 'MEDIUM', 240, 'MIXED', 'MIXED', 'LOW', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (34, 'AU_MORNING_PEAK', 'AU', 'Australia Morning Peak', 'Poranna aktywność w Australii (ASX open)', '22:00:00', '01:00:00', true, 10, 'MEDIUM', 'MEDIUM', 180, 'MIXED', 'INSTITUTIONAL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (35, 'AU_AFTERNOON_PEAK', 'AU', 'Australia Afternoon Peak', 'Popołudniowa aktywność w Australii', '03:00:00', '06:00:00', false, 12, 'LOW', 'LOW', 180, 'RANGING', 'RETAIL', 'LOW', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (36, 'AU_EVENING_PEAK', 'AU', 'Australia Evening Peak', 'Wieczorne okno aktywności w Australii', '08:00:00', '12:00:00', false, 12, 'MEDIUM', 'MEDIUM', 240, 'MIXED', 'RETAIL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (37, 'BR_MORNING_PEAK', 'BR', 'Brazil Morning Peak', 'Poranna aktywność w Brazylii (B3 open)', '12:00:00', '15:00:00', false, 10, 'MEDIUM', 'MEDIUM', 180, 'MIXED', 'MIXED', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (38, 'BR_AFTERNOON_PEAK', 'BR', 'Brazil Afternoon Peak', 'Popołudniowa aktywność w Brazylii', '17:00:00', '20:00:00', false, 12, 'MEDIUM', 'MEDIUM', 180, 'MIXED', 'RETAIL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (39, 'BR_EVENING_PEAK', 'BR', 'Brazil Evening Peak', 'Wieczorne okno aktywności w Brazylii', '21:00:00', '00:00:00', true, 14, 'MEDIUM', 'LOW', 180, 'RANGING', 'RETAIL', 'LOW', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (40, 'IN_MORNING_PEAK', 'IN', 'India Morning Peak', 'Poranna aktywność w Indiach (NSE open)', '03:30:00', '06:30:00', false, 10, 'MEDIUM', 'MEDIUM', 180, 'MIXED', 'RETAIL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (41, 'IN_AFTERNOON_PEAK', 'IN', 'India Afternoon Peak', 'Popołudniowa aktywność w Indiach', '09:00:00', '12:00:00', false, 12, 'MEDIUM', 'MEDIUM', 180, 'MIXED', 'RETAIL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (42, 'IN_EVENING_PEAK', 'IN', 'India Evening Peak', 'Wieczorne okno aktywności w Indiach', '14:00:00', '18:00:00', false, 12, 'MEDIUM', 'MEDIUM', 240, 'MIXED', 'RETAIL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (43, 'TR_MORNING_PEAK', 'TR', 'Turkey Morning Peak', 'Poranna aktywność w Turcji (Borsa Istanbul open)', '06:00:00', '09:00:00', false, 10, 'MEDIUM', 'MEDIUM', 180, 'MIXED', 'RETAIL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (44, 'TR_AFTERNOON_PEAK', 'TR', 'Turkey Afternoon Peak', 'Popołudniowa aktywność w Turcji', '12:00:00', '15:00:00', false, 12, 'MEDIUM', 'MEDIUM', 180, 'MIXED', 'RETAIL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (45, 'TR_EVENING_PEAK', 'TR', 'Turkey Evening Peak', 'Wieczorne okno aktywności w Turcji (wysoka adopcja crypto)', '16:00:00', '20:00:00', false, 10, 'MEDIUM', 'MEDIUM', 240, 'MIXED', 'RETAIL', 'LOW', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (46, 'CA_MORNING_PEAK', 'CA', 'Canada Morning Peak', 'Poranna aktywność w Kanadzie (TSX open)', '13:30:00', '16:00:00', false, 10, 'MEDIUM', 'MEDIUM', 150, 'MIXED', 'INSTITUTIONAL', 'HIGH', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_region_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (47, 'CA_AFTERNOON_PEAK', 'CA', 'Canada Afternoon Peak', 'Popołudniowa aktywność w Kanadzie', '17:00:00', '20:00:00', false, 12, 'MEDIUM', 'MEDIUM', 180, 'MIXED', 'RETAIL', 'MEDIUM', 'SESSION', '2025-12-18 22:30:53.160565') ON CONFLICT DO NOTHING;


--
-- TOC entry 4864 (class 0 OID 27660)
-- Dependencies: 331
-- Data for Name: dictionary_social_events; Type: TABLE DATA; Schema: public; Owner: piotradamczyk
--

INSERT INTO public.dictionary_social_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (1, 'SOCIAL_US_PEAK', 'SOCIAL', 'US Social Media Peak', 'Szczyt aktywności social media w USA (Twitter/X)', '14:00:00', '22:00:00', false, 14, 'MEDIUM', 'MEDIUM', 480, 'MIXED', 'RETAIL', 'HIGH', 'SESSION', '2025-12-18 22:30:53.171885') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_social_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (2, 'SOCIAL_ASIA_PEAK', 'SOCIAL', 'Asia Social Media Peak', 'Szczyt aktywności social media w Azji', '00:00:00', '06:00:00', false, 14, 'MEDIUM', 'MEDIUM', 360, 'MIXED', 'RETAIL', 'HIGH', 'SESSION', '2025-12-18 22:30:53.171885') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_social_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (3, 'SOCIAL_EUROPE_PEAK', 'SOCIAL', 'Europe Social Media Peak', 'Szczyt aktywności social media w Europie', '08:00:00', '14:00:00', false, 14, 'MEDIUM', 'MEDIUM', 360, 'MIXED', 'RETAIL', 'HIGH', 'SESSION', '2025-12-18 22:30:53.171885') ON CONFLICT DO NOTHING;


--
-- TOC entry 4862 (class 0 OID 27643)
-- Dependencies: 329
-- Data for Name: dictionary_special_events; Type: TABLE DATA; Schema: public; Owner: piotradamczyk
--

INSERT INTO public.dictionary_special_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (1, 'EVENT_BTC_HALVING', 'EVENT', 'Bitcoin Halving', 'Halving nagrody blokowej BTC (co ~4 lata)', '00:00:00', '23:59:00', false, 1, 'EXTREME', 'HIGH', 1440, 'VOLATILE', 'MIXED', 'HIGH', 'EVENT', '2025-12-18 22:30:53.171095') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_special_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (2, 'EVENT_CME_GAP', 'EVENT', 'CME Gap Window', 'Potencjalna luka cenowa CME (poniedziałek open)', '22:00:00', '23:30:00', true, 6, 'HIGH', 'MEDIUM', 90, 'VOLATILE', 'INSTITUTIONAL', 'LOW', 'EVENT', '2025-12-18 22:30:53.171095') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_special_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (3, 'EVENT_FUNDING_8H', 'EVENT', '8-Hour Funding Rate', 'Rozliczenie funding rate co 8 godzin', '00:00:00', '00:15:00', false, 12, 'MEDIUM', 'MEDIUM', 15, 'VOLATILE', 'MIXED', 'LOW', 'EVENT', '2025-12-18 22:30:53.171095') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_special_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (4, 'EVENT_FUNDING_8H_2', 'EVENT', '8-Hour Funding Rate 2', 'Drugie rozliczenie funding rate', '08:00:00', '08:15:00', false, 12, 'MEDIUM', 'MEDIUM', 15, 'VOLATILE', 'MIXED', 'LOW', 'EVENT', '2025-12-18 22:30:53.171095') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_special_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (5, 'EVENT_FUNDING_8H_3', 'EVENT', '8-Hour Funding Rate 3', 'Trzecie rozliczenie funding rate', '16:00:00', '16:15:00', false, 12, 'MEDIUM', 'MEDIUM', 15, 'VOLATILE', 'MIXED', 'LOW', 'EVENT', '2025-12-18 22:30:53.171095') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_special_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (6, 'EVENT_GRAYSCALE_UNLOCK', 'EVENT', 'Grayscale Unlock Period', 'Okres odblokowania udziałów GBTC (historycznie znaczący)', '13:00:00', '21:00:00', false, 5, 'HIGH', 'HIGH', 480, 'VOLATILE', 'INSTITUTIONAL', 'MEDIUM', 'EVENT', '2025-12-18 22:30:53.171095') ON CONFLICT DO NOTHING;
INSERT INTO public.dictionary_special_events (id, phase_code, region_code, label, description, utc_start, utc_end, wraps_midnight, priority, volatility_level, volume_impact, typical_duration_min, trading_pattern, dominant_actors, news_sensitivity, category, created_at) VALUES (7, 'EVENT_ETF_REBALANCE', 'EVENT', 'ETF Rebalancing', 'Miesięczne/kwartalne rebalancowanie ETF BTC', '19:00:00', '21:00:00', false, 6, 'HIGH', 'HIGH', 120, 'VOLATILE', 'INSTITUTIONAL', 'LOW', 'EVENT', '2025-12-18 22:30:53.171095') ON CONFLICT DO NOTHING;

