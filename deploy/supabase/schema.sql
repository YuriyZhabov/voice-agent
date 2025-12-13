-- ============================================
-- VoxPulse Monitoring - Supabase Schema
-- ============================================
-- Run this in Supabase SQL Editor: Dashboard → SQL Editor → New Query

-- Enable UUID extension (usually already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- Table: calls - История звонков
-- ============================================
CREATE TABLE IF NOT EXISTS calls (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  call_id TEXT UNIQUE NOT NULL,
  phone_number TEXT NOT NULL,
  direction TEXT CHECK (direction IN ('inbound', 'outbound')) DEFAULT 'inbound',
  status TEXT CHECK (status IN ('active', 'completed', 'failed', 'transferred')) DEFAULT 'active',
  start_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  end_time TIMESTAMPTZ,
  duration_seconds INTEGER,
  room_name TEXT,
  agent_version TEXT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- Table: transcripts - Расшифровки разговоров
-- ============================================
CREATE TABLE IF NOT EXISTS transcripts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  call_id TEXT REFERENCES calls(call_id) ON DELETE CASCADE,
  role TEXT CHECK (role IN ('user', 'assistant', 'system')) NOT NULL,
  content TEXT NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================
-- Table: tool_executions - Логи вызовов инструментов
-- ============================================
CREATE TABLE IF NOT EXISTS tool_executions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  call_id TEXT REFERENCES calls(call_id) ON DELETE CASCADE,
  tool_name TEXT NOT NULL,
  parameters JSONB DEFAULT '{}',
  result JSONB DEFAULT '{}',
  success BOOLEAN DEFAULT TRUE,
  latency_ms INTEGER,
  executed_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- Table: alerts_history - История алертов
-- ============================================
CREATE TABLE IF NOT EXISTS alerts_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  severity TEXT CHECK (severity IN ('critical', 'warning', 'info')) NOT NULL,
  service TEXT NOT NULL,
  message TEXT NOT NULL,
  triggered_at TIMESTAMPTZ DEFAULT NOW(),
  resolved_at TIMESTAMPTZ,
  acknowledged BOOLEAN DEFAULT FALSE
);

-- ============================================
-- Indexes for fast queries
-- ============================================
CREATE INDEX IF NOT EXISTS idx_calls_start_time ON calls(start_time DESC);
CREATE INDEX IF NOT EXISTS idx_calls_status ON calls(status);
CREATE INDEX IF NOT EXISTS idx_calls_call_id ON calls(call_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_call_id ON transcripts(call_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_timestamp ON transcripts(timestamp);
CREATE INDEX IF NOT EXISTS idx_tool_executions_call_id ON tool_executions(call_id);
CREATE INDEX IF NOT EXISTS idx_tool_executions_tool_name ON tool_executions(tool_name);
CREATE INDEX IF NOT EXISTS idx_alerts_triggered ON alerts_history(triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts_history(severity);

-- ============================================
-- Row Level Security (RLS)
-- ============================================
ALTER TABLE calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE transcripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE tool_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts_history ENABLE ROW LEVEL SECURITY;

-- ============================================
-- Policies: Allow authenticated users to read
-- ============================================
CREATE POLICY "Allow authenticated read calls" ON calls 
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated read transcripts" ON transcripts 
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated read tool_executions" ON tool_executions 
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated read alerts" ON alerts_history 
  FOR SELECT TO authenticated USING (true);

-- ============================================
-- Policies: Allow service_role to write (for agent)
-- ============================================
CREATE POLICY "Allow service write calls" ON calls 
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow service write transcripts" ON transcripts 
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow service write tool_executions" ON tool_executions 
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow service write alerts" ON alerts_history 
  FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================
-- Policies: Allow anon to read (for public dashboard)
-- ============================================
CREATE POLICY "Allow anon read calls" ON calls 
  FOR SELECT TO anon USING (true);

CREATE POLICY "Allow anon read transcripts" ON transcripts 
  FOR SELECT TO anon USING (true);

CREATE POLICY "Allow anon read tool_executions" ON tool_executions 
  FOR SELECT TO anon USING (true);

CREATE POLICY "Allow anon read alerts" ON alerts_history 
  FOR SELECT TO anon USING (true);

-- ============================================
-- Enable Realtime for live updates
-- ============================================
ALTER PUBLICATION supabase_realtime ADD TABLE calls;
ALTER PUBLICATION supabase_realtime ADD TABLE alerts_history;

-- ============================================
-- Helper function: Update call duration on end
-- ============================================
CREATE OR REPLACE FUNCTION update_call_duration()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.end_time IS NOT NULL AND OLD.end_time IS NULL THEN
    NEW.duration_seconds := EXTRACT(EPOCH FROM (NEW.end_time - NEW.start_time))::INTEGER;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_call_duration
  BEFORE UPDATE ON calls
  FOR EACH ROW
  EXECUTE FUNCTION update_call_duration();

-- ============================================
-- Done! Tables created:
-- - calls (call history)
-- - transcripts (conversation logs)
-- - tool_executions (tool call logs)
-- - alerts_history (monitoring alerts)
-- ============================================


-- ============================================
-- Table: call_metrics - Метрики звонков (latency, usage)
-- ============================================
CREATE TABLE IF NOT EXISTS call_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  call_id TEXT REFERENCES calls(call_id) ON DELETE CASCADE,
  metric_type TEXT NOT NULL,  -- 'ttfw', 'stt_latency', 'llm_latency', 'tts_latency', 'llm_usage'
  value_ms FLOAT,
  metadata JSONB DEFAULT '{}',
  recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- Table: call_events - События звонков
-- ============================================
CREATE TABLE IF NOT EXISTS call_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  call_id TEXT REFERENCES calls(call_id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,  -- 'call_started', 'user_speaking', 'agent_speaking', 'tool_called', etc.
  data JSONB DEFAULT '{}',
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- Additional indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_call_metrics_call_id ON call_metrics(call_id);
CREATE INDEX IF NOT EXISTS idx_call_metrics_type ON call_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_call_metrics_recorded ON call_metrics(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_call_events_call_id ON call_events(call_id);
CREATE INDEX IF NOT EXISTS idx_call_events_type ON call_events(event_type);
CREATE INDEX IF NOT EXISTS idx_call_events_timestamp ON call_events(timestamp DESC);

-- ============================================
-- RLS for new tables
-- ============================================
ALTER TABLE call_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow authenticated read call_metrics" ON call_metrics 
  FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow service write call_metrics" ON call_metrics 
  FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Allow anon read call_metrics" ON call_metrics 
  FOR SELECT TO anon USING (true);

CREATE POLICY "Allow authenticated read call_events" ON call_events 
  FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow service write call_events" ON call_events 
  FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Allow anon read call_events" ON call_events 
  FOR SELECT TO anon USING (true);

-- ============================================
-- Enable Realtime for new tables
-- ============================================
ALTER PUBLICATION supabase_realtime ADD TABLE call_events;
ALTER PUBLICATION supabase_realtime ADD TABLE call_metrics;

-- ============================================
-- Views for analytics
-- ============================================

-- View: Call summary with metrics
CREATE OR REPLACE VIEW call_summary AS
SELECT 
  c.call_id,
  c.phone_number,
  c.direction,
  c.status,
  c.start_time,
  c.end_time,
  c.duration_seconds,
  c.agent_version,
  (SELECT COUNT(*) FROM transcripts t WHERE t.call_id = c.call_id AND t.role = 'user') as user_messages,
  (SELECT COUNT(*) FROM transcripts t WHERE t.call_id = c.call_id AND t.role = 'assistant') as assistant_messages,
  (SELECT COUNT(*) FROM tool_executions te WHERE te.call_id = c.call_id) as tool_calls,
  (SELECT AVG(value_ms) FROM call_metrics m WHERE m.call_id = c.call_id AND m.metric_type = 'ttfw') as avg_ttfw_ms
FROM calls c;

-- View: Hourly call stats
CREATE OR REPLACE VIEW hourly_call_stats AS
SELECT 
  date_trunc('hour', start_time) as hour,
  COUNT(*) as total_calls,
  COUNT(*) FILTER (WHERE status = 'completed') as completed_calls,
  COUNT(*) FILTER (WHERE status = 'failed') as failed_calls,
  AVG(duration_seconds) as avg_duration_seconds
FROM calls
WHERE start_time > NOW() - INTERVAL '7 days'
GROUP BY date_trunc('hour', start_time)
ORDER BY hour DESC;

-- View: Tool usage stats
CREATE OR REPLACE VIEW tool_usage_stats AS
SELECT 
  tool_name,
  COUNT(*) as total_calls,
  COUNT(*) FILTER (WHERE success = true) as successful_calls,
  AVG(latency_ms) as avg_latency_ms,
  MAX(latency_ms) as max_latency_ms
FROM tool_executions
WHERE executed_at > NOW() - INTERVAL '7 days'
GROUP BY tool_name
ORDER BY total_calls DESC;
