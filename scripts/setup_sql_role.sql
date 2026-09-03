-- Create a read-only role for the SQL Agent
CREATE ROLE sql_agent_user WITH LOGIN PASSWORD 'read_only_password';

-- Grant usage on the public schema
GRANT USAGE ON SCHEMA public TO sql_agent_user;

-- Grant select on all existing tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO sql_agent_user;

-- Ensure future tables are also read-only
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO sql_agent_user;
