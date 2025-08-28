-- TrendsQL-KG Neo4j Schema
-- Knowledge Graph schema with constraints and indexes

-- Create constraints for node uniqueness
CREATE CONSTRAINT topic_unique IF NOT EXISTS
FOR (t:Topic) REQUIRE (t.topic, COALESCE(t.region,'')) IS NODE KEY;

CREATE CONSTRAINT keyword_unique IF NOT EXISTS
FOR (k:Keyword) REQUIRE (k.name, COALESCE(k.geo,''), COALESCE(k.gprop,'')) IS NODE KEY;

CREATE CONSTRAINT category_unique IF NOT EXISTS
FOR (c:Category) REQUIRE c.name IS UNIQUE;

CREATE CONSTRAINT region_unique IF NOT EXISTS
FOR (r:Region) REQUIRE r.code IS UNIQUE;

-- Create indexes for better query performance
CREATE INDEX topic_category IF NOT EXISTS FOR (t:Topic) ON (t.category);
CREATE INDEX topic_region IF NOT EXISTS FOR (t:Topic) ON (t.region);
CREATE INDEX topic_growth_score IF NOT EXISTS FOR (t:Topic) ON (t.growth_score);
CREATE INDEX topic_popularity_score IF NOT EXISTS FOR (t:Topic) ON (t.popularity_score);
CREATE INDEX topic_first_seen_date IF NOT EXISTS FOR (t:Topic) ON (t.first_seen_date);

CREATE INDEX keyword_geo IF NOT EXISTS FOR (k:Keyword) ON (k.geo);
CREATE INDEX keyword_gprop IF NOT EXISTS FOR (k:Keyword) ON (k.gprop);

CREATE INDEX category_name IF NOT EXISTS FOR (c:Category) ON (c.name);
CREATE INDEX region_code IF NOT EXISTS FOR (r:Region) ON (r.code);

-- Create text indexes for full-text search
CREATE TEXT INDEX topic_text IF NOT EXISTS FOR (t:Topic) ON (t.topic);
CREATE TEXT INDEX keyword_text IF NOT EXISTS FOR (k:Keyword) ON (k.name);
CREATE TEXT INDEX category_text IF NOT EXISTS FOR (c:Category) ON (c.name);

-- Create composite indexes for common query patterns
CREATE INDEX topic_category_region IF NOT EXISTS FOR (t:Topic) ON (t.category, t.region);
CREATE INDEX topic_growth_region IF NOT EXISTS FOR (t:Topic) ON (t.growth_score, t.region);
CREATE INDEX keyword_geo_gprop IF NOT EXISTS FOR (k:Keyword) ON (k.geo, k.gprop);

-- Create relationship indexes for better traversal performance
CREATE INDEX rel_belongs_to IF NOT EXISTS FOR ()-[r:BELONGS_TO]-() ON (r);
CREATE INDEX rel_seen_in IF NOT EXISTS FOR ()-[r:SEEN_IN]-() ON (r);
CREATE INDEX rel_also_relates_to IF NOT EXISTS FOR ()-[r:ALSO_RELATES_TO]-() ON (r);
CREATE INDEX rel_mentions IF NOT EXISTS FOR ()-[r:MENTIONS]-() ON (r);
CREATE INDEX rel_co_trends_with IF NOT EXISTS FOR ()-[r:CO_TRENDS_WITH]-() ON (r);

-- Create property indexes on relationships
CREATE INDEX rel_also_relates_to_type IF NOT EXISTS FOR ()-[r:ALSO_RELATES_TO]-() ON (r.type);
CREATE INDEX rel_also_relates_to_value IF NOT EXISTS FOR ()-[r:ALSO_RELATES_TO]-() ON (r.value);
CREATE INDEX rel_co_trends_with_window IF NOT EXISTS FOR ()-[r:CO_TRENDS_WITH]-() ON (r.window);
CREATE INDEX rel_co_trends_with_corr IF NOT EXISTS FOR ()-[r:CO_TRENDS_WITH]-() ON (r.corr);
