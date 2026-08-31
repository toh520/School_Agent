package com.schoolagent.core.config;

import java.util.List;
import java.util.Map;

/** Performs an explicit preflight check before Spring creates networked dependencies. */
public final class RequiredEnvironment {

  private static final List<String> REQUIRED_NAMES =
      List.of(
          "SCHOOL_AGENT_DB_URL",
          "SCHOOL_AGENT_DB_USERNAME",
          "SCHOOL_AGENT_DB_PASSWORD",
          "SCHOOL_AGENT_AGENT_URL",
          "SCHOOL_AGENT_WEB_ORIGIN",
          "SCHOOL_AGENT_AUTH_JWT_SECRET");

  private RequiredEnvironment() {}

  public static void validate(Map<String, String> environment) {
    List<String> missing =
        REQUIRED_NAMES.stream().filter(name -> isBlank(environment.get(name))).sorted().toList();
    if (!missing.isEmpty()) {
      throw new IllegalStateException(
          "Missing required environment variables: " + String.join(", ", missing));
    }
  }

  private static boolean isBlank(String value) {
    return value == null || value.isBlank() || value.startsWith("replace_with_");
  }
}
