package com.schoolagent.core.config;

import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.Map;
import org.junit.jupiter.api.Test;

class RequiredEnvironmentTest {

  @Test
  void reportsMissingConfigurationBeforeSpringStarts() {
    assertThatThrownBy(() -> RequiredEnvironment.validate(Map.of()))
        .isInstanceOf(IllegalStateException.class)
        .hasMessageContaining("SCHOOL_AGENT_DB_URL")
        .hasMessageContaining("SCHOOL_AGENT_DB_PASSWORD");
  }

  @Test
  void rejectsUnchangedExamplePlaceholders() {
    Map<String, String> environment =
        Map.of(
            "SCHOOL_AGENT_DB_URL", "jdbc:postgresql://127.0.0.1/school_agent",
            "SCHOOL_AGENT_DB_USERNAME", "school_agent",
            "SCHOOL_AGENT_DB_PASSWORD", "replace_with_local_password",
            "SCHOOL_AGENT_AGENT_URL", "http://127.0.0.1:8000",
            "SCHOOL_AGENT_WEB_ORIGIN", "http://127.0.0.1:5173");

    assertThatThrownBy(() -> RequiredEnvironment.validate(environment))
        .hasMessageContaining("SCHOOL_AGENT_DB_PASSWORD");
  }
}
