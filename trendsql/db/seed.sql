-- Sample seed data for TrendsQL
-- This file contains example data for testing and development

-- Sample exploding topics data
INSERT INTO exploding_topics (topic, category, source, first_seen_date, growth_score, popularity_score, region, url) VALUES
('AI-powered pet care', 'Technology', 'exploding', '2024-01-15', 85.5, 92.3, 'US', 'https://example.com/ai-pet-care'),
('Sustainable fashion trends', 'Fashion', 'exploding', '2024-01-10', 78.2, 88.7, 'US', 'https://example.com/sustainable-fashion'),
('Plant-based protein', 'Health', 'exploding', '2024-01-12', 92.1, 95.4, 'US', 'https://example.com/plant-protein'),
('Remote work tools', 'Technology', 'exploding', '2024-01-08', 76.8, 89.2, 'US', 'https://example.com/remote-tools'),
('Mental health apps', 'Health', 'exploding', '2024-01-14', 88.9, 91.6, 'US', 'https://example.com/mental-health-apps'),
('Ayurvedic skincare', 'Beauty', 'exploding', '2024-01-05', 82.3, 87.9, 'IN', 'https://example.com/ayurvedic-skincare'),
('Electric vehicles', 'Automotive', 'exploding', '2024-01-03', 95.7, 98.1, 'US', 'https://example.com/electric-vehicles'),
('Cryptocurrency trading', 'Finance', 'exploding', '2024-01-07', 79.4, 85.6, 'US', 'https://example.com/crypto-trading'),
('Home fitness equipment', 'Fitness', 'exploding', '2024-01-11', 86.2, 93.8, 'US', 'https://example.com/home-fitness'),
('Organic food delivery', 'Food', 'exploding', '2024-01-09', 81.7, 90.3, 'US', 'https://example.com/organic-delivery')
ON CONFLICT (topic, COALESCE(region, '')) DO NOTHING;

-- Sample exploding topic history data
INSERT INTO exploding_topic_history (topic, date, score, region) VALUES
('AI-powered pet care', '2024-01-15', 85.5, 'US'),
('AI-powered pet care', '2024-01-16', 87.2, 'US'),
('AI-powered pet care', '2024-01-17', 89.1, 'US'),
('Sustainable fashion trends', '2024-01-10', 78.2, 'US'),
('Sustainable fashion trends', '2024-01-11', 80.5, 'US'),
('Sustainable fashion trends', '2024-01-12', 82.8, 'US'),
('Plant-based protein', '2024-01-12', 92.1, 'US'),
('Plant-based protein', '2024-01-13', 93.4, 'US'),
('Plant-based protein', '2024-01-14', 94.7, 'US'),
('Ayurvedic skincare', '2024-01-05', 82.3, 'IN'),
('Ayurvedic skincare', '2024-01-06', 84.1, 'IN'),
('Ayurvedic skincare', '2024-01-07', 86.2, 'IN')
ON CONFLICT (topic, date, COALESCE(region, '')) DO NOTHING;

-- Sample Google Trends interest over time data
INSERT INTO gt_interest_over_time (keyword, date, interest, geo, category, gprop) VALUES
('AI', '2024-01-15', 85, 'US', 0, ''),
('AI', '2024-01-16', 87, 'US', 0, ''),
('AI', '2024-01-17', 89, 'US', 0, ''),
('Dog food', '2024-01-15', 72, 'US', 0, ''),
('Dog food', '2024-01-16', 75, 'US', 0, ''),
('Dog food', '2024-01-17', 78, 'US', 0, ''),
('Ayurveda pets', '2024-01-15', 65, 'IN', 0, ''),
('Ayurveda pets', '2024-01-16', 68, 'IN', 0, ''),
('Ayurveda pets', '2024-01-17', 71, 'IN', 0, ''),
('Electric cars', '2024-01-15', 88, 'US', 0, ''),
('Electric cars', '2024-01-16', 91, 'US', 0, ''),
('Electric cars', '2024-01-17', 94, 'US', 0, ''),
('Mental health', '2024-01-15', 76, 'US', 0, ''),
('Mental health', '2024-01-16', 79, 'US', 0, ''),
('Mental health', '2024-01-17', 82, 'US', 0, ''),
('Sustainable fashion', '2024-01-15', 69, 'US', 0, ''),
('Sustainable fashion', '2024-01-16', 72, 'US', 0, ''),
('Sustainable fashion', '2024-01-17', 75, 'US', 0, '')
ON CONFLICT (keyword, date, COALESCE(geo, ''), COALESCE(gprop, ''), COALESCE(category, 0)) DO NOTHING;

-- Sample Google Trends related topics data
INSERT INTO gt_related_topics (keyword, related_topic, type, value, geo) VALUES
('AI', 'Machine Learning', 'top', 95, 'US'),
('AI', 'ChatGPT', 'rising', 100, 'US'),
('AI', 'Artificial Intelligence', 'top', 90, 'US'),
('AI', 'Deep Learning', 'top', 85, 'US'),
('Dog food', 'Pet Food', 'top', 88, 'US'),
('Dog food', 'Natural Dog Food', 'rising', 92, 'US'),
('Dog food', 'Grain Free Dog Food', 'top', 82, 'US'),
('Ayurveda pets', 'Natural Pet Care', 'top', 78, 'IN'),
('Ayurveda pets', 'Herbal Pet Medicine', 'rising', 85, 'IN'),
('Ayurveda pets', 'Pet Wellness', 'top', 75, 'IN'),
('Electric cars', 'Tesla', 'top', 95, 'US'),
('Electric cars', 'EV Charging', 'rising', 88, 'US'),
('Electric cars', 'Hybrid Cars', 'top', 80, 'US'),
('Mental health', 'Therapy', 'top', 85, 'US'),
('Mental health', 'Anxiety', 'rising', 90, 'US'),
('Mental health', 'Depression', 'top', 82, 'US'),
('Sustainable fashion', 'Thrift Shopping', 'top', 78, 'US'),
('Sustainable fashion', 'Eco Friendly Clothing', 'rising', 85, 'US'),
('Sustainable fashion', 'Fast Fashion', 'top', 72, 'US')
ON CONFLICT (keyword, related_topic, type, COALESCE(geo, '')) DO NOTHING;
