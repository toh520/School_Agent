package com.schoolagent.core.health;

import com.schoolagent.core.config.FoundationProperties;
import com.schoolagent.core.config.RequestIdFilter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

/** Aggregates only M01 infrastructure health; it contains no business readiness rules. */
@Service
public class HealthService {

  private static final Logger LOGGER = LoggerFactory.getLogger(HealthService.class);
  private static final String CORE_VERSION = "0.1.0";

  private final JdbcTemplate jdbcTemplate;
  private final RestClient restClient;
  private final FoundationProperties properties;

  public HealthService(
      JdbcTemplate jdbcTemplate,
      RestClient.Builder restClientBuilder,
      FoundationProperties properties) {
    this.jdbcTemplate = jdbcTemplate;
    this.restClient = restClientBuilder.build();
    this.properties = properties;
  }

  public SystemHealth inspect(String requestId) {
    DependencyHealth database = inspectDatabase();
    DependencyHealth agent = inspectAgent(requestId);
    String status = isUp(database) && isUp(agent) ? "UP" : "DOWN";
    return new SystemHealth(status, DependencyHealth.up(CORE_VERSION), agent, database);
  }

  private DependencyHealth inspectDatabase() {
    try {
      String postgresVersion =
          jdbcTemplate.queryForObject("SELECT current_setting('server_version')", String.class);
      String vectorVersion =
          jdbcTemplate.queryForObject(
              "SELECT extversion FROM pg_extension WHERE extname = 'vector'", String.class);
      return DependencyHealth.up("PostgreSQL " + postgresVersion + " / pgvector " + vectorVersion);
    } catch (RuntimeException exception) {
      LOGGER.warn("Database health check failed: {}", exception.getClass().getSimpleName());
      return DependencyHealth.down();
    }
  }

  private DependencyHealth inspectAgent(String requestId) {
    try {
      AgentHealthEnvelope response =
          restClient
              .get()
              .uri(properties.getAgentBaseUrl() + "/health")
              .header(RequestIdFilter.REQUEST_ID_HEADER, requestId)
              .retrieve()
              .body(AgentHealthEnvelope.class);
      if (response == null || !response.success() || response.data() == null) {
        return DependencyHealth.down();
      }
      return new DependencyHealth(response.data().status(), response.data().version());
    } catch (RestClientException exception) {
      LOGGER.warn("Agent health check failed: {}", exception.getClass().getSimpleName());
      return DependencyHealth.down();
    }
  }

  private boolean isUp(DependencyHealth health) {
    return "UP".equals(health.status());
  }

  private record AgentHealthEnvelope(boolean success, AgentHealthData data) {}

  private record AgentHealthData(String status, String version) {}
}
